from bitarray import *
import bitarray.util as bau
from libs.utils_bitarray import *
from libs.utils_int import *
from libs.aio import *
from multiprocessing import *
from p_tqdm import *

_BF_List = []
_BF_Results = []

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
    MinDistance = (1 << (InputCount-1)) - (1 << ((InputCount>>1) - 1))
    MaxDistance = Len
    #for W in List:
    #  print(W)
    global _BF_Results, _BF_List
    _BF_List = List
    #Manager = multiprocess
    
    Results = []
    LowestDistance = None
    for Counter in range(1, (1<<Len)-1):
      Break = 0
      Candidate = bau.int2ba(Counter, Len)
      #print("CANDIDATE =", Candidate)
      LowestDistance = MaxDistance
      for _ in range(2):
        for K in List:
          Distance = bau.count_xor(Candidate, K)
          #print("        K =", K, Distance)
          if Distance < LowestDistance:
            LowestDistance = Distance
            if Distance < MinDistance:
              Break = 1
              break
          K.invert()
        if Break:
          break
      if LowestDistance >= MinDistance:
        Results.append([Candidate, LowestDistance])
      if len(Results) >= n > 0:
        break
    return Results
    for R in Results:
      print(R)