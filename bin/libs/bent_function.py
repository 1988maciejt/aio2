from bitarray import *
import bitarray.util as bau
from math import log2
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
  
  __slots__ = ("_lut")
  
  def __init__(self, LUT : bitarray) -> None:
    self._lut = LUT.copy()
  def __str__(self) -> str:
    return str(self.value())
  def __repr__(self) -> str:
    return f'BentFunction({repr(self._lut)})'
  
  def value(self, Source : bitarray, MapList : list) -> int:
    return self._lut[bau.ba2int(Bitarray.mapBits(Source, MapList), "little")]
  
  def listBentFunctionLuts(InputCount : int, n = 0) -> list:
    if InputCount <= 1:
      Aio.printError("InputCount must be > 1")
      return
    if InputCount & 1:
      Aio.printError("InputCount must be even")
      return
    Len = (1 << InputCount)
    Zeros = bau.zeros(Len)
    Ones = bitarray(Len)
    Ones.setall(1)
    List0 = [bitarray(Len) for _ in range(InputCount)]
    for Counter in range(Len):
      Bindex = 0
      for Bit in Int.iterateFromLsb(Counter, InputCount):
        List0[Bindex][Counter] = Bit
        Bindex += 1
    List = []
    List.append(Zeros)
    List.append(Ones)
    for Counter in range(1,Len):
      BACounter = bau.int2ba(Counter, InputCount)
      Indexes = BACounter.search(1)
      Res = Zeros.copy()
      for Index in Indexes:
        Res ^= List0[Index]
      List.append(Res)
      Res2 = Res.copy()
      Res2.invert()
      List.append(Res2)
    Stop = (1<<(Len-1))
    if (InputCount > 4) or ((n >= 15000) and (InputCount > 2)):
      global _BF_STATE
      _BF_STATE = None
      _BF_STATE = Value('i', 0)
      with _BF_STATE.get_lock():
        _BF_STATE.value = 0
      Chunk = 5000
      Total = Stop // Chunk + (1 if Stop % Chunk > 0 else 0)
      Generator = Generators()
      PResults = p_uimap(partial(_bent_searcher_helper, Listx=List, Len=Len, InputCount=InputCount, N=n), Generator.subRanges(1, Stop, Chunk), total=Total, desc=f'{Chunk} checks per iteration')
      Results = []
      for PR in PResults:
        Results += PR
        if len(Results) >= n > 0:
          Generator.disable()
      del Generator
      if len(Results) > n > 0:
        Results = Results[:n]
      _BF_STATE = None
      return Results
    else:
      MinDistance = (1 << (InputCount-1)) - (1 << ((InputCount>>1) - 1))
      Results = []
      for Counter in range(1, Stop):
        Candidate = bau.int2ba(Counter, Len)
        if Candidate in List:
          continue
        Add = 1
        for K in List:
          Distance = bau.count_xor(Candidate, K)
          if Distance < MinDistance:
            Add = 0
            break
        if Add:
          InvCandidate = Candidate.copy()
          InvCandidate.invert()
          Results.append(Candidate)
          Results.append(InvCandidate)
        if len(Results) >= n > 0:
          break
      return Results
  
  def getInputCount(self):
    return int(log2(len(self._lut)))
  
  def toVerilog(self, ModuleName : str):
    ICount = self.getInputCount()
    Module = \
f'''module {ModuleName} (
  input wire [{ICount-1}:0] I,
  output wire O
);

always @ (*) begin
  O = '''
    Second = False;
    Lut = self._lut;
    for i in range(len(Lut)):
      if Lut[i]:
        if Second:
          Module += "\n    | "
        else:
          Second = True
        Expr = ""
        for j in range(ICount):
          if j:
            Expr += " & "
          if i & 1:
            Expr += f"I[{j}]"
          else:
            Expr += f"~I[{j}]"
          i >>= 1
        Module += Expr
    Module += \
f''';
end

endmodule'''
    return Module

    
    
    
      
def _bent_searcher_helper(rng, Listx, Len, InputCount, N) -> list:
  global _BF_STATE
  if _BF_STATE.value > N > 0:
    return []
  List = Listx
  MinDistance = (1 << (InputCount-1)) - (1 << ((InputCount>>1) - 1))
  Results = []
  Found = 0
  for Counter in rng:
    Candidate = bau.int2ba(Counter, Len)
    if Candidate in List:
      continue
    Add = 1
    for K in List:
      Distance = bau.count_xor(Candidate, K)
      if Distance < MinDistance:
        Add = 0
        break
    if Add:
      InvCandidate = Candidate.copy()
      InvCandidate.invert()
      Results.append(Candidate)
      Results.append(InvCandidate)
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
