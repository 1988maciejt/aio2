from bitarray import *
import bitarray.util as bau
from libs.utils_bitarray import *
from libs.utils_int import *
from libs.aio import *
from libs.generators import *
from tqdm import *
from p_tqdm import *
#from libs.p_tqdm_modified import *
from functools import partial
from multiprocessing import Value
from pathos.multiprocessing import ProcessPool as Pool
import copy


_BF_STATE = None

class BentFunction:
  __slots__ = ("_source", "_map_list", "_lut")
  def __init__(self, Source : bitarray, MapList : list, LUT : bitarray) -> None:
    self._source = Source
    self._map_list = MapList
    self._lut = LUT.copy()
    if len(LUT) < (1<<len(MapList)):
      self._lut += bau.zeros((1<<len(MapList)) - len(LUT))
  def __str__(self) -> str:
    return str(self.value())
  def __repr__(self) -> str:
    return f'BentFunction({repr(self._lut)})'
  def value(self) -> int:
    return self._lut[bau.ba2int(Bitarray.mapBits(self._source, self._map_list))]
  
  def listBentFunctionLuts(InputCount : int, n = 0) -> list:
    if InputCount <= 1:
      Aio.printError("InputCount must be > 1")
      return
    if InputCount & 1:
      Aio.printError("InputCount must be even")
      return
    Len = (1 << InputCount)
    Zeros = bau.zeros(Len)
    List = [bitarray(Len) for _ in range(InputCount)]
    for Counter in range(Len):
      Bindex = 0
      for Bit in Int.iterateFromLsb(Counter, InputCount):
        List[Bindex][Counter] = Bit
        Bindex += 1
    for Counter in range(2,Len):
      BACounter = bau.int2ba(Counter, InputCount)
      if BACounter.count(1) < 2:
        continue
      Indexes = BACounter.search(1)
      Res = Zeros.copy()
      for Index in Indexes:
        Res ^= List[Index]
      List.append(Res)
      Res2 = Res.copy()
      Res2.invert()
      List.append(Res2)
    Stop = (1<<(Len-1))
    if (InputCount >= 4) and not (10000 >= n > 0):
      global _BF_STATE
      _BF_STATE = None
      _BF_STATE = Value('i', 0)
      with _BF_STATE.get_lock():
        _BF_STATE.value = 0
      Chunk = 100000
      PResults = p_uimap(partial(_bent_searcher_helper, Listx=List, Len=Len, InputCount=InputCount, N=n), Generators.subRanges(1, Stop, Chunk), desc=f'{Chunk} checks per iteration')
      Results = []
      for PR in PResults:
        Results += PR
        if len(Results) >= n > 0:
          Generators.disable()
      Generators.enable()
      if len(Results) > n > 0:
        Results = Results[:n]
      _BF_STATE = None
      return Results
    else:
      MinDistance = (1 << (InputCount-1)) - (1 << ((InputCount>>1) - 1))
      MaxDistance = Len
      Results = []
      LowestDistance = None
      for Counter in range(1, Stop):
        Candidate = bau.int2ba(Counter, Len)
        #print("CANDIDATE =", Candidate)
        LowestDistance = MaxDistance
        if Candidate in List:
          continue
        for K in List:
          Distance = bau.count_xor(Candidate, K)
          #print("        K =", K, Distance)
          if Distance < LowestDistance:
            LowestDistance = Distance
            if Distance < MinDistance:
              break
        if LowestDistance >= MinDistance:
          NCandidate = Candidate.copy()
          NCandidate.invert()
          Results.append(Candidate)
          Results.append(NCandidate)
        if len(Results) >= n > 0:
          break
      return Results
      
def _bent_searcher_helper(rng, Listx, Len, InputCount, N) -> list:
  global _BF_STATE
  if _BF_STATE.value > N > 0:
    return []
  List = Listx
  MinDistance = (1 << (InputCount-1)) - (1 << ((InputCount>>1) - 1))
  MaxDistance = Len
  Results = []
  LowestDistance = None
  Found = 0
  for Counter in rng:
    Break = 0
    Candidate = bau.int2ba(Counter, Len)
    if Candidate in List:
      continue
    LowestDistance = MaxDistance
    for K in List:
      Distance = bau.count_xor(Candidate, K)
      #print("        K =", K, Distance)
      if Distance < LowestDistance:
        LowestDistance = Distance
        if Distance < MinDistance:
          break
    if LowestDistance >= MinDistance:
      NCandidate = Candidate.copy()
      NCandidate.invert()
      Results.append(Candidate)
      Results.append(NCandidate)
      Found += 2
    if _BF_STATE.value + Found > N > 0:
      with _BF_STATE.get_lock():
        _BF_STATE.value += Found
      return Results
  #print(rng, len(Results), _BF_N)
  with _BF_STATE.get_lock():
    _BF_STATE.value += Found
#  print(rng, _BF_STATE.value)
  return Results