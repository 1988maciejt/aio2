from bitarray import *
import bitarray.util as bau
from math import log2
from libs.utils_bitarray import *
from libs.utils_int import *
from libs.utils_list import *
from libs.aio import *
from libs.generators import *
from tqdm import *
from p_tqdm import *
#from libs.p_tqdm_modified import *
from functools import partial
from multiprocessing import Value
from pathos.multiprocessing import ProcessPool as Pool
from sympy import *
from sympy.logic import SOPform
import sympy.logic.boolalg as SympyBoolalg
from libs.utils_sympy import *
from libs.fast_anf_algebra import *
from functools import partial
from libs.simple_threading import *


_BF_STATE = None

class BentFunction:
  
  __slots__ = ("_lut", "_minterms", "_anf", "_notanf", "_iList", "_FastAnfList", '_FastAnfNot')
  
  def __init__(self, LUT : bitarray) -> None:
    self._lut = LUT.copy()
    self._minterms = None
    self._anf = None
    self._notanf = 0
    self._iList = None
    self._FastAnfList = None
    self._FastAnfNot = 0
        
  def __str__(self) -> str:
    return str(self.value())
  
  def __repr__(self) -> str:
    return f'BentFunction({repr(self._lut)})'
  
  @staticmethod
  def constructBentLUT(LUT1 : bitarray, LUT2 : bitarray) -> bitarray:
    Aio.printError("Not yet implemented!!")
  
  def value(self, Source : bitarray, MapList : list) -> int:
    return self._lut[bau.ba2int(Bitarray.mapBits(Source, MapList))]
  
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
  
  def getMinterms(self) -> list:
    if self._minterms is None:
      self._minterms = self._lut.search(1)
    return self._minterms.copy()
  
  def getFastANFValue(self, ANFSpace : FastANFSpace, InputList : List, Parallel = False):
    if self._anf is None:
      self._iList = [symbols(f'_bf_x_{i}') for i in range(self.getInputCount())]
      self._anf = SOPform(self._iList, self.getMinterms()).to_anf()
      if type(self._anf) == Not:
        self._notanf = 1
        self._anf = self._ang.args[0]
    if self._FastAnfList is None:
      AnfList = []
      self._FastAnfNot = self._notanf
      try:
        for SymMonomial in self._anf.args:
          MonoList = []
          SymAtoms = SymMonomial.atoms()
          for SymAtom in SymAtoms:
            if SymAtom == True:
              self._FastAnfNot = 1
            else:
              R = re.search(r'_bf_x_([0-9]+)', str(SymAtom))
              if R:
                MonoList.append(int(R.group(1)))
          if len(MonoList) > 0:
            AnfList.append(MonoList)
        self._FastAnfList = AnfList
      except:
        pass
    Result = ANFSpace.createExpression()
    if Parallel:
      Len = 0
      for IV in InputList:
        Len += len(IV)
      if Len < 50000:
        Parallel = 0
    if Parallel:
      Combos = []
      for Mono in self._FastAnfList:
        Combo = []
        for i in Mono:
          Combo.append(InputList[i])
        if len(Combo) == 1:
          Result.add(Combo[0])
        else:
          Combos.append(Combo)
      pm = 1
      for N in SimpleThread.uimap(partial(ANFSpace.multiplyList), Combos):
        Result.add(N)
        print(f"// BentFunction: parallel AND {pm} / {len(Combos)}")
        pm += 1
    else:
      for Mono in self._FastAnfList:
        First = 1
        MonoResult = None
        for i in Mono:
          if First:
            MonoResult = InputList[i].copy()
            First = 0
          else:
            MonoResult.mul(InputList[i])
        Result.add(MonoResult)
    if self._FastAnfNot:
      Result.negate()
    return Result
    
              
    
  
  def getSymbolicValue(self, InputList : list):
    if self._anf is None:
      self._iList = [symbols(f'_bf_x_{i}') for i in range(self.getInputCount())]
      self._anf = SOPform(self._iList, self.getMinterms()).to_anf()
      if type(self._anf) == Not:
        self._notanf = 1
        self._anf = self._ang.args[0]
    iDict = {}
    for i in range(len(self._iList)):
      iDict[self._iList[i]] = InputList[i]
    Result = self._anf.copy()
    Result = Result.subs(iDict)
    if self._notanf:
      Result ^= True
    try:
      Result = Result.to_anf()
    except:
      pass
    return Result
  
  def getLut(self) -> bitarray:
    return self._lut 
  
  def getMonomialsCount(self, Degree = None) -> list:
    InputCount = self.getInputCount()
    InputIndexes = [i for i in range(0, InputCount)]
    NoVarList = []
    SLen = 1
    EveryN = 2
    for _ in range(InputCount):
      Lut = self._lut.copy()
      Bitarray.resetSeriesOfBits(Lut, SLen, EveryN, SLen)
      NoVarList.append(Lut)
      SLen <<= 1
      EveryN <<= 1    
    ResultList = []
    ReturnList = 1
    if Degree is not None:
      Iter = [Degree]
      ReturnList = 0
    else:
      Iter = range(InputCount+1)
    for Degree in Iter:
      Result = 0
      for NoVarComb in List.getCombinations(InputIndexes, InputCount-Degree):
        Lut = self._lut.copy()
        for i in NoVarComb:
          Lut &= NoVarList[i]
        Result += (Lut.count(1) & 1)
      ResultList.append(Result)
    if ReturnList:
      return ResultList
    return Result
    
  def toVerilog(self, ModuleName : str):
    ICount = self.getInputCount()
    Module = \
f'''module {ModuleName} (
  input wire [{ICount-1}:0] I,
  output reg O
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
