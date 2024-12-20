from libs.cpp_program import *
from libs.lfsr import *
from libs.utils_list import *
from libs.utils_bitarray import *
from libs.utils_str import *
from libs.asci_drawing import *
from libs.pandas_table import *
from libs.simple_threading import *
from libs.temp_transcript import *
from p_tqdm import *
from bitarray import *
from libs.generators import *
from libs.remote_aio import *
import hashlib
from libs.cython import *
from libs.utils_serial import *
from libs.aio_auto import *
import numpy
import asyncio
try:
  from numba import cuda
except:
  pass

# TUI =====================================================

import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive
import textual.containers as TextualContainers

_NLFSR = None
_NLFSR_UNDO = None
_NLFSR_SIM = []


def _to_taps_templates(expr : str) -> list:
  exprf = expr.replace("+", "^")
  exprf = exprf.replace("*", "&")
  e = sympy.parsing.parse_expr(exprf)
  Result = []
  VarNames = 'abcdefghijklmnopqrstuvwxyz'
  for monomial in e.args:
    if monomial.func is Not:
      GlobalInv = 1
      args = monomial.args[0].args
    else:
      GlobalInv = 0
      args = monomial.args
    if len(args) == 0:
      args = [monomial]
    D = -1 if GlobalInv else 1
    Ss = []
    for arg in args:
      if arg.func is Not:
        var = str(arg.args[0])
        VInv = 1
      else:
        var = str(arg)
        VInv = 0
      Si = VarNames.index(var) + 1
      Ss.append(-Si if VInv else Si)
    Tap = [D, Ss]
    Result.append(Tap)
  return Result
  

class Nlfsr(Lfsr):
  pass
class Nlfsr(Lfsr):
  _baValue = None
  _size = 0
  _Config = []
  _points = []
  _start = bitarray()
  _offset = 0
  _exename = ""
  _period = None
  _anf_temp = None
  Accepted = False
  _prediction = None
  
  def clear(self):
    pass
  def copy(self):
    return Nlfsr(self)
  def __del__(self):
    pass
  def _refreshFastANF(self):
    self._anf_temp = self.toBooleanExpressionFromRing(ReturnSympyExpr=1)
    if self._anf_temp is None:
      self._anf_temp = -1
  def _getFastANF(self):
    if self._anf_temp is None:
      self._refreshFastANF()
    if type(self._anf_temp) is type(int):
      return None
    return self._anf_temp
  
  def __hash__(self) -> int:
    Taps = [self._size]
    for tap in self._Config:
      d = tap[0]
      s = tuple(tap[1])
      Taps.append(tuple([d, s]))
    return hash(tuple(Taps))
      
  def __eq__(self, other) -> bool:
    if self._size != other._size:
      return False
    if self._Config != other._Config:
      return False
    return True
  
  def __neq__(self, other) -> bool:
    return not self.__eq__(self, other)
  
  def getTapsStats(self) -> tuple:
    AndInputs = 0
    for Tap in self._Config:
      l = len(Tap[1])
      if l > AndInputs:
        AndInputs = l
    return len(self._Config), AndInputs
  
  def getTapMostRightInputIndex(self, TapIndex : int):
    if TapIndex >= len(self._Config):
      return None
    Tap = self._Config[TapIndex]
    Inputs = Tap[1]
    Output = abs(Tap[0]) % self._size
    MostRight = None
    MostRightNorm = None
    for Inp in Inputs:
      I = abs(Inp) % self._size
      if MostRight is None:
        MostRight = I
        MostRightNorm = (I - Output) % self._size
      else:
        INorm = (I - Output) % self._size
        if INorm > MostRightNorm:
          MostRightNorm = INorm
          MostRight = I
    return MostRight
  
  def moveTapsToShareTheSameFFs(self):
    self.sortTaps()
    Half = self._size // 2
    for step in range(self._size):
      AllDone = True
      for i in range(len(self._Config)-1, -1, -1):
        IIndex = self.getTapMostRightInputIndex(i)
        if IIndex != 0:
          AllDone = False
          if IIndex > Half:
            self.rotateTap(i, 1, True, False, True)
          else:
            self.rotateTap(i, -1, True, False, True)
      if AllDone:
        break
    self.sortTaps()
    
  def getTapMostLeftSourceIndex(self) -> int:
    S = self.getTapsSources()
    D = self.getTapsDestinations()
    DMax = D[-1]
    for Sx in S:
      if Sx > DMax:
        return Sx
    return S[-1]
  
  def getFirstFreeFFIndex(self) -> int:
    S = self.getTapsSources()
    D = self.getTapsDestinations()
    for i in range(self._size):
      if i not in S and i not in D:
        iabs = (i-1) % self._size
        if iabs not in D:
          return iabs
        return i
    return None
  
  def addTwoLinearTaps(self, SortTaps = False):
    Dests = self.getTapsDestinations()
    #Seour = self.getTapsSources()
    D = self.getFirstFreeFFIndex()
    S = self.getTapMostLeftSourceIndex()
    TI = len(self._Config)
    self._Config.append([D, [S]])
    DNew = (D + 3) % self._size
    while DNew in Dests and DNew < 5:
      DNew += 1 
    self.rotateTap(TI, DNew-D, True, False, True)
    self._Config.append([D, [S]])
    self._period = None
    if SortTaps:
      self.sortTaps()
          
  
  def getCudaConfig(self, MaxTaps : int, MaxAndInputs : int):
    Result = numpy.zeros([MaxTaps + 1, MaxAndInputs + 1], dtype="uint64")
    Result[0][0] = numpy.uint64(1 << (self._size - 1))
    Index = 1
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      Didx = abs(D) % self._size
      Dint = numpy.uint64(1 << Didx)
      if D < 0:
        Dint |= (1 << 63)
      Result[Index][0] = Dint
      Sindex = 1
      for Si in S:
        Sidx = abs(Si) % self._size
        Sint = numpy.uint64(1 << Sidx)
        if Si < 0:
          Sint |= (1 << 63)
        Result[Index][Sindex] = Sint
        Sindex += 1
      Index += 1
    return Result
    
  
  def _getCudaNextProcedure(self, indent = "      "):
    Result = f"""
{indent}New = (Old >> 1)
{indent}if Old & 1:
{indent}  New |= {1 << (self._size - 1)}"""
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      Dest = (1 << (abs(D) % self._size))
      DInv = 1 if D < 0 else 0
      if len(S) == 1:
        Source = (1 << (abs(S[0]) % self._size))
        SInv = 1 if S[0] < 0 else 0
        if DInv == SInv:
          Result += f"""
{indent}if (Old & {Source}):
{indent}  New ^= {Dest}"""
        else:
          Result += f"""
{indent}if not (Old & {Source}):
{indent}  New ^= {Dest}"""
      else:
        First = 1
        for Si in S:
          SiS = (1 << (abs(Si) % self._size))
          SiI = 1 if Si < 0 else 0
          if First:
            if SiI:
              Result += f"""
{indent}And = 0 if (Old & {SiS}) else 1"""
            else:
              Result += f"""
{indent}And = 1 if (Old & {SiS}) else 0"""
            First = 0
          else:
            if SiI:
              Result += f"""
{indent}if (Old & {SiS}):
{indent}  And = 0"""
            else:
              Result += f"""
{indent}if not (Old & {SiS}):
{indent}  And = 0"""
            First = 0
        if DInv:
          Result += f"""
{indent}if not And:
{indent}  New ^= {Dest}"""
        else:
          Result += f"""
{indent}if And:
{indent}  New ^= {Dest}"""
    return Result

  def _getCudaFillGapsCode(self, GapSize : int) -> str:
    Result = f"""global cudafill
@cuda.jit
def cudafill(begins, result):
  pos = cuda.grid(1)
  bsize = cuda.gridsize(1)
  while pos < begins.size:
    index = {GapSize} * pos
    result[index] = begins[pos]
    for i in range(1, {GapSize}):
      index += 1
      Old = result[index-1] {self._getCudaNextProcedure()}
      result[index] = New
    pos += bsize    
    """
    return Result
    
  
  def getCudaNextCode(self, FunctionName : str = "Next", Global = False, Steps = 1) -> str:
    Result = f"""from numba import cuda"""
    if Global:
      Result += f"""
global {FunctionName}"""
    Result += f"""
@cuda.jit
def {FunctionName}(States):
  pos = cuda.grid(1)
  bsize = cuda.gridsize(1)
  while pos < States.size:
    for _ in range({Steps}):
      Old = States[pos]"""
    Result += self._getCudaNextProcedure()
    Result += f"""
      States[pos] = New
    pos += bsize"""
    return Result
  
  def getTransitionTableCuda(self, Steps=1):
    exec(self.getCudaNextCode("NXT", True, Steps=Steps))
    Max = (1 << self._size)
    Threads = 1024
    BlockSIze = int(ceil(Max / Threads))
    if BlockSIze > 1024:
      BlockSIze = 1024
    if self._size >= 31:
      AllStates = numpy.asarray([i for i in range(Max)], dtype="int64")
    else:
      AllStates = numpy.asarray([i for i in range(Max)], dtype="int32")
    NXT[BlockSIze, Threads](AllStates)
    return AllStates
    
  def getValuesCuda(self, Debug=False) -> list:
    Max = (1 << self._size)
    BigStep = 512
    BlocksCount = int((Max - 1) / BigStep) + 1
    t = self.getTransitionTableCuda(BigStep) 
    if Debug:
      print(f"// Generaed transition by {BigStep}")
    if self._size >= 31:
      Steps = numpy.zeros(BlocksCount, dtype="int64")
      Steps[0] = numpy.int64(1)
    else:
      Steps = numpy.zeros(BlocksCount, dtype="int32")
      Steps[0] = numpy.int32(1)
    for i in range(1, Steps.size):
      Steps[i] = t[Steps[i-1]]
    if Debug:
      print(f"// Got every {BigStep} values")
    exec(self._getCudaFillGapsCode(BigStep))
    del t
    if self._size >= 31:
      Result = numpy.zeros(Max, dtype="int64")
    else:
      Result = numpy.zeros(Max, dtype="int32")
    cudafill[1024, 1024](Steps, Result)
    if Debug:
      print(f"// Filled gaps in the sequence. Finished.")
    if self._period is None:
      @cuda.jit
      def check(seq, result):
        pos = cuda.grid(1)
        bsize = cuda.gridsize(1)
        while pos < seq.size:
          if pos > 0:
            if seq[pos] == 1:
              if result[0] == 0:
                result[0] = pos
              elif pos < result[0]:
                result[0] = pos
              break
          pos += bsize
      if Debug:
        print(f"// + Period determined.")
      if self._size >= 31:
        period = numpy.zeros(1, dtype="int64")
      else:
        period = numpy.zeros(1, dtype="int32")
      check[1024, 1024](Result, period)
      self._period = period[0]
      self._period_verified = Int.hash(self._period)
    if self._period is None:
      return Result
    return Result[:self._period]
    
  def gpc(self):
    @cuda.jit
    def foo(transition, values, trajectory):
      pos = cuda.grid(1)
      bsize = cuda.gridsize(1)
      if pos == 1:
        i = 0
        val = pos
        trajectory[i] = val
        while not values[val]:
          val = transition[val]
          i += 1
          trajectory[i] = val
        pos += bsize
      while pos < transition.size:
        val = pos
        values[val] = 1
        val = transition[val]
        while not values[val]:
          val = transition[val]
        pos += bsize
    t = self.getTransitionTableCuda()
    v = numpy.zeros(len(t), dtype="int8")
    traj = numpy.zeros(len(t), dtype="int32")
    foo[1024, 1024](t, v, traj)
    return v, traj
  
  def getPeriodCuda(self, MinimumExpectedPeriodRatio = 0.8):
    if self._period is None:
      Max = Int.mersenne(self._size)
      MinP = int(Max * MinimumExpectedPeriodRatio)
      Pert = ceil(sqrt(MinP) * 1.2)
      if Pert < 1:
        Pert = 1
      if Pert > 2000:
        Pert = 2000
      t = self.getTransitionTableCuda(Pert)
      if t is None:
        return None
      if self._size >= 31:
        val = numpy.int64(1)
      else:
        val = numpy.int32(1)
      v0 = val
      p = 0
      while (p + Pert) <= MinP:
        p += Pert
        val = t[val]
      Found = 0
      t = self.getTransitionTableCuda(1)
      while p <= Max:
        if val == v0:
          Found = 1
          break
        p += 1
        val = t[val]
      if Found:
        Period = int(p)
        self._period = Period
        self._period_verified = Int.hash(self._period)
      else:
        self._period = None
    return self._period
  
  def getSequencesCuda(self, AsBitarrays = False, Debug = False) -> list:
    from libs.cuda_utils import cuda_transposeto64
    Values = self.getValuesCuda(Debug)
    SeqWordsCount = int(ceil(Values.size/64))
    Sequences = numpy.zeros([SeqWordsCount, self._size], dtype="uint64")
    blocks = SeqWordsCount
    if blocks > 1024:
      blocks = 1024
    cuda_transposeto64[blocks, self._size](Values, Sequences)
    if AsBitarrays:
      Result = [bitarray() for _ in range(self._size)]
      for WordIdx in range(SeqWordsCount):
        for SeqIdx in range(self._size):
          Result[SeqIdx] += bau.int2ba(int(Sequences[WordIdx][SeqIdx]), 64, 'little')
      if Debug:
        print(f"// + Converted to bitarrays.")
      try:
        for SeqIdx in range(self._size):
          Result[SeqIdx] = Result[SeqIdx][:self._period]
      except:
        if Debug:
          print(f"// ERROR: Couldn't trim bitarrays.")
      return Result
    return Sequences
      
  def getExprFromTap(self, Tap) -> str:
    Result = ""
    C = Tap
    D = C[0]
    Slist = C[1]
    DInv = False
    if D < 0:
      DInv = True      
    D = abs(D) % self._size
    Result += f' {D} <= '
    if DInv:
      Result += "~("
    if Aio.isType(Slist, 0):
      Result += " "
      if Slist < 0:
        Result += "~"
      Slist = abs(Slist) % self._size
      Result += f'{Slist}'
    else:
      First = True
      for S in Slist:
        if not First:
          Result += " " + AsciiDrawing_Characters.MULTIPLY
        First = False
        Result += " "
        if S < 0:
          Result += "~"
        S = abs(S) % self._size
        Result += f'{S}'
    if DInv:
      Result += " )"
    return Result.strip()
  
  def getLinearSourcesOf(self, FFIndex : int) -> list:
    Result = []
    for Tap in self._Config:
      D = abs(Tap[0]) % self._size
      if D == FFIndex:
        if len(Tap[1]) > 1:
          return []
        S = abs(Tap[1][0]) % self._size
        if Tap[0] * Tap[1][0] < 0:
          if S == 0:
            S += self._size
          S *= -1
        if S in Result:
          Result.remove(S)
        else:
          Result.append(S)
    return Result

  def getReducedSequenceSymbols(self, NamePrefix = "") -> list:
    SSymbols = self.getSequenceSymbols(NamePrefix)
    Dests = self.getTapsDestinations()
    Dests.sort(reverse=1)
    #self.print()
    #print(SSymbols)
    #print(Dests)
    cntr = 0
    DidSomething = True
    while DidSomething:
      DidSomething = False
      for Dest in Dests:
        Sym = SSymbols[Dest].getSymbols()
        #print(f"DEST = {Dest}")
        if len(Sym) == 1 and Sym[0] == str(NamePrefix) + str(0):
          #print("  is OK")
          continue
        LS = self.getLinearSourcesOf(Dest)
        if len(LS) < 1:
          #print("  not reducible")
          continue
        DidSomething = True
        Prev = (Dest + 1) % self._size
        SSymbols[Dest] = SSymbols[Prev].copy()
        #print(f" >> {SSymbols[Dest]}")
        for ls in LS:
          SSymbols[Dest] += SSymbols[abs(ls) % self._size]
          if ls < 0:
            SSymbols[Dest].invert()
          #print(f" >> {SSymbols[Dest]}")
        SSymbols[Dest].delay(1)
        #print(f" >> {SSymbols[Dest]}")
        Next = Dest - 1
        if Next < 0:
          Next += self._size
        while Next not in Dests:
          Prev = (Next + 1) % self._size
          SSymbols[Next] = SSymbols[Prev].copy()
          SSymbols[Next].delay(1)
          Next -= 1
          if Next < 0:
            Next += self._size
        #print(SSymbols)
      cntr += 1
      if cntr == 4:
        return None
    return SSymbols
      
    
  
  def getArchitecture(self) -> str:
    Result = ""
    for C in self._Config:
      Result += self.getExprFromTap(C)
      Result += "\n"
    return Result[:-1]
  def printFullInfo(self, Repr = True, Draw = False):
    Aio.print(self.getFullInfo(Repr, Draw))
  def getFullInfo(self, Repr = True, Draw = False):
    Result = ""
    if Repr:
      Result = f'{repr(self)}\n'
    Result += f"Period = {self.getPeriod()}"
    if self.isMaximum():
      Result += ", MAXIMUM"
    if Int.isPrime(self.getPeriod()):
      Result += ", PRIME"
    Result += "\n"
    Result += self.getArchitecture() + "\n"
    ExprAnf = self.toBooleanExpressionFromRing(0, 0)
    if ExprAnf is not None:
      Result += "          " + ExprAnf + "\n"
      Result += "Comp:     " + self.toBooleanExpressionFromRing(1, 0) + "\n"
      Result += "Rev:      " + self.toBooleanExpressionFromRing(0, 1) + "\n"
      Result += "RevComp:  " + self.toBooleanExpressionFromRing(1, 1) + "\n"
    if Draw:
      Result += self.getDraw() + "\n"
    return Result
  def getTaps(self) -> int:
    return self._Config.copy()
  def __init__(self, Size : int, Config = [], **kwargs) -> None:
    self.Accepted = False
    self._anf_temp = None
    self._period_verified = None
    self._prediction = None
    if Aio.isType(Size, []):
      Size = Polynomial(Size)
    if Aio.isType(Size, "Polynomial"):
      Size = Lfsr(Size, LfsrType.HybridRing)
    if Aio.isType(Size, "Nlfsr"):
      self._size = Size._size      
      self._Config = Size._Config.copy()
      self._baValue = Size._baValue.copy()
      self._points = Size._points
      self._exename = Size._exename
      self._period = Size._period
      self._period_verified = Size._period_verified
      self._anf_temp = Size._anf_temp
      self.Accepted = Size.Accepted
    elif Aio.isType(Size, "Lfsr"):
      self._size = Size._size
      self._period = None
      self._baValue = Size._baValue
      self._exename = ""
      self.Accepted = False
      self._Config = []
      if Size._type == LfsrType.Fibonacci:
        for i in range(1, len(Size._bamask)):
          if Size._bamask[i]:
            self._Config.append([Size._size-1, [i]])
      elif Size._type == LfsrType.Galois:
        for i in range(len(Size._bamask)-1):
          if Size._bamask[i]:
            self._Config.append([i, [0]])
      else:
        for tap in Size._taps:
          self._Config.append([tap[1], [tap[0]]])
      self.sortTaps()
    else:  
      self._size = Size
      if Aio.isType(Config, "str"):
        if ":" in Config:
          self._Config = Nlfsr.parseFromArticleString(Size, Config)._Config
        else:
          self._Config = Nlfsr.parseFromANF(Size, Config)._Config
      else:
        self._Config = []
        for C in Config:
          D = C[0]
          S = C[1]
          if Aio.isType(S, []):
            S = list(set(S))
            for Si in S:
              if Si != 0 and (-1 * Si) in S:
                S = [Si, -1 * Si]
                break
            #S.sort()
          self._Config.append([D, S])
        #def msortf(e):
        #  return abs(e[0])%Size
        #self._Config.sort(key=msortf)
        self.sortTaps()
      self._baValue = bitarray(self._size)
      self._exename = ""
      self._period = None
      self.reset()
      if kwargs.get("SET_PERIOD", None) is not None:
        _period = kwargs["SET_PERIOD"]
        if type(_period) is int:
          self._period = _period
          Aio.print(f"// WARNING: Period of Nlfsr was set to {self._period} and WILL NOT be verified again!")
        elif type(_period) is tuple:
          p = _period[0]
          h = _period[1]
          if Int.hash(p) == h:
            self._period = p
            self._period_verified = h
          else:
            Aio.print(f"// WARNING: Period of Nlfsr was set to {self._period} but IS INCORRECT!!!")
            
  def __repr__(self) -> str:
    if self._period is None:
      result = "Nlfsr(" + str(self._size) + ", " + str(self._Config) + ")"
    else:
      if self._period_verified is not None:
        result = "Nlfsr(" + str(self._size) + ", " + str(self._Config) + ", SET_PERIOD=(" + str(self._period) + "," + str(self._period_verified) + "))"
      else:
        result = "Nlfsr(" + str(self._size) + ", " + str(self._Config) + ", SET_PERIOD=" + str(self._period) + ")"
    return result
    
  def _next1(self):
    NewVal = Bitarray.rotl(self._baValue)
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      DIndex = (abs(D) % self._size)
      AndResult = 1
      for Si in S:
        SIndex = (abs(Si) % self._size)
        Bit = self._baValue[SIndex]
        if Si < 0:
          Bit = 1-Bit
        AndResult &= Bit
      if D < 0:
        AndResult = 1 - AndResult
      NewVal[DIndex] ^= AndResult
    self._baValue = NewVal
    return self._baValue
  
  def _make_next1_cache(self):
    self._Dests = []
    self._Dinvs = []
    self._Sources = []
    self._Sinvs = []
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      self._Dests.append(abs(D) % self._size)
      self._Dinvs.append(1 if (D<0) else 0)
      SList = []
      SInvList = []
      for Si in S:
        SList.append(abs(Si) % self._size)
        SInvList.append(1 if (Si<0) else 0)
      self._Sources.append(SList)
      self._Sinvs.append(SInvList)
    
  def _next1_cached(self):
    NewVal = Bitarray.rotl(self._baValue)
    for TIndex in range(len(self._Config)):
      AndResult = 1
      Sources = self._Sources[TIndex]
      Sinvx = self._Sinvs[TIndex]
      for Sindex in range(len(Sources)):
        Bit = self._baValue[Sources[Sindex]]
        if Sinvx[Sindex]:
          Bit = 1-Bit
        AndResult &= Bit
      if self._Dinvs[TIndex]:
        AndResult = 1 - AndResult
      NewVal[self._Dests[TIndex]] ^= AndResult
    self._baValue = NewVal
    return self._baValue
  
  def __DEV__getSequenceUsingCythonModule(self, BitIndex = 0):
    if Aio.isType(BitIndex, 0):
      BitIndex = [BitIndex]
    Length = ((1<<self._size)-1)
    Size = self._size
    Taps = self._Config
    CCode = f"""
from bitarray import *
import bitarray.util as bau
def f():
  Result = [bau.zeros({Length}) for _ in range({len(BitIndex)})]
  cdef int[{Size}] State
  cdef int[{Size}] AuxState
  cdef int Offset = 0
  for i in range({Size}):
    State[i] = 0
    AuxState[i] = 0
  State[0] = 1
  for i in range({Length}):"""
    ModifiedBits = []
    for Tap in Taps:
      D = abs(Tap[0])
      if D in ModifiedBits:
        continue
      CCode += f"""
    AuxState[{D}] = State[({D}+Offset)%{Size}]"""
      ModifiedBits.append(D)
    for Tap in Taps:
      pass
    for ModifiedBit in ModifiedBits:
      CCode += f"""
    State[({ModifiedBit}+Offset)%{Size}] == AuxState[{ModifiedBit}]"""
    RIndex = 0
    for Bit in BitIndex:
      CCode += f"""
    if State[({Bit}+Offset)%{Size}] == 1:
      Result[{RIndex}][i] = 1"""
      RIndex += 1
    CCode += f"""
    Offset = (Offset + 1) % Size
  return Result"""
    print(CCode)
  
  def next(self, steps=1):
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return None
    else:
      for _ in range(steps):
        self._next1()
    return self._baValue
  
  def prev(self, steps=1):
    Aio.printError("Method 'prev()' for Nlfsr class is not implemented yet.")
    return None
  
  def getTapsDestinations(self, ExceptTapIndex = None):
    Result = []
    for i in range(len(self._Config)):
      if ExceptTapIndex == i:
        continue
      D = abs(self._Config[i][0]) % self._size
      if D not in Result:
        Result.append(D)
    Result.sort()
    return Result
  
  def createSimpleExpander(self, MinXorInputs = 1, MaxXorInputs = 3, Verify = False) -> PhaseShifter:
    SeqSymbols = self.getReducedSequenceSymbols()
    if SeqSymbols is None:
      return None
    #print(SeqSymbols)
    Xors = []
    if Verify:
      SingleSequences = self.getSequences()
      SUniques = []
      BlockSize = self._size-4
      if BlockSize < 3:
        BlockSize = 3
    Uniques = []
    #Off = 0
    for k in range(MinXorInputs, MaxXorInputs+1):
      for combi in List.getCombinations([i for i in range(self._size)], k):
        comb = []
        for ci in combi:
          comb.append(SeqSymbols[ci])
#      for comb in List.getCombinations(SeqSymbols, k):
        Sym = comb[0]
        for i in range(1, k):
          Sym += comb[i]
        if Sym not in Uniques:
          Ok = True
          if Verify:
            S = Nlfsr._getSequence(SingleSequences, combi)
            SH = Bitarray.getRotationInsensitiveSignature(S, BlockSize)
            if SH in SUniques:
              print("NO!!!!")
              print(SH)
              print(f"{comb}")
              print(f"{SUniques}")
              print(f"{Uniques}")
              print(f"{SH}")
              Ok = False
          if Ok:
            Uniques.append(Sym)
            Xors.append(list(combi))
            if Verify:
              SUniques.append(SH)
      #print(len(Uniques)-Off)
      #Off = len(Uniques)
    return PhaseShifter(self, Xors)
        
    
  
  def getSingleTapSources(self, TapIndex : int):
    Result = []
    try:
      Ss = self._Config[TapIndex][1]
      for S in Ss:
        S = abs(S) % self._size
        if S not in Result:
          Result.append(S)
    except:
      Aio.printError(f"TapIndex '{TapIndex}' out of range.")
    return Result
  
  def getTapsSources(self, ExceptTapIndex = None):
    Result = []
    for i in range(len(self._Config)):
      if ExceptTapIndex == i:
        continue
      Ss = self._Config[i][1]
      for S in Ss:
        S = abs(S) % self._size
        if S not in Result:
          Result.append(S)
    Result.sort()
    return Result
  
  def _getCheckPeriodArgStr(self) -> tuple:
    ArgStr = str(self._size)
    WithInverters = 0
    for C in self._Config:
      Dest = C[0]
      Source = C[1]
      TString = str(Dest)
      if Dest < 0:
        WithInverters = 1
      if Aio.isType(Source, 0):
        TString += "_" + str(Source)
        if Source < 0:
          WithInverters = 1
      else:
        for S in Source:
          TString += "_" + str(S)
          if S < 0:
            WithInverters = 1
      ArgStr += " " + TString
    return ArgStr, WithInverters
    
  def getPeriod(self, ForceRecalculation = False, ExeName = None):
    if type(self) is NlfsrCascade:
      return NlfsrCascade.getPeriod(self)
    if ExeName is not None:
      self._exename = ExeName
    if ForceRecalculation:
      self._period = None
    if self._period is not None:
      return self._period
    ArgStr, WithInverters = self._getCheckPeriodArgStr()
    if len(self._exename) > 0:
      try:
        Res = Aio.shellExecute(self._exename + " " + ArgStr)   
        x = int(Res)
      except:
        try:
          Res = Aio.shellExecute(self._exename + " " + ArgStr)   
        except:
          Aio.printError("Cannot run Cpp program to compute Nlfsr's period.")
          Res = "0"
    else:
      try:
        if WithInverters:
          if self._size <= 64:
            Res = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.run(ArgStr)
          else:
            Res = CppPrograms.NLSFRPeriodCounterInvertersAllowed.run(ArgStr)
        else:
          Res = CppPrograms.NLSFRPeriodCounter.run(ArgStr)
        x = int(Res)
      except:
        try:
          if WithInverters:
            if self._size <= 64:
              Res = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.run(ArgStr)
            else:
              Res = CppPrograms.NLSFRPeriodCounterInvertersAllowed.run(ArgStr)
          else:
            Res = CppPrograms.NLSFRPeriodCounter.run(ArgStr)
        except:
          Aio.printError("Cannot run Cpp program to compute Nlfsr's period.")
          Res = "x"
      #print(Res)
    try:
      self._period = int(Res)
      self._period_verified = Int.hash(self._period)
      return self._period
    except Exception as inst:
      self._period = None
      self._period_verified = None
      Aio.printError(f"Nlfsr.getPeriod - cpp program returns weird result:\n{Res}\nArgs: {ArgStr}", inst)
      return -1
    
  def getSingleSequenceCpp64b(self) -> bitarray:
    if self._size > 64:
      Aio.printError("getSingleSequenceCpp64b needs size to be <= 64.")
      return None
    ArgStr, WithInverters = self._getCheckPeriodArgStr()
    FileName = File.getRandomTempFileName()
    Res = CppPrograms.NLSFRGetSequence64b.run(f"{FileName} {ArgStr}")
    try:
      Res = int(Res)
    except:
      Aio.printError("It looks like the 'NLSFRGetSequence64b' program didn't work...")
      return None
    Result = Bitarray.fromFile(FileName, Res)
    File.remove(FileName)
    return Result
    
  def getAllSequencesCpp64b(self) -> BufferedList:
    if self._size > 64:
      Aio.printError("getSingleSequenceCpp64b needs size to be <= 64.")
      return None
    ArgStr, WithInverters = self._getCheckPeriodArgStr()
    FileName = File.getRandomTempFileName()
    for i in range(self._size):
      AioAuto.registerFileToClean(FileName + f".{i}")
    Res = CppPrograms.NLSFRGetSequences64b.run(f"{FileName} {ArgStr}")
    try:
      Res = int(Res)
    except:
      Aio.printError("It looks like the 'NLSFRGetSequences64b' program didn't work...")
      return None
    Result = BufferedList()
    for i in range(self._size):
      Result.append(Bitarray.fromFile(FileName + f".{i}", Res))
      File.remove(FileName + f".{i}")
      AioAuto.unregisterFileToClean(FileName + f".{i}")
    return Result
    
  def getDestinationsDictionary(self) -> dict:
    DestDict = {}
    Size = self._size
    for i in range(Size):
      DestDict[i] = [(i + 1) % Size]
    Taps = self._Config
    for Tap in Taps:
      S = Tap[1].copy()
      D = Tap[0]
      f = "AND"
      if D < 0:
        f = "OR"
        D = abs(D)
        for i in range(len(S)):
          Si = S[i]
          if Si == 0:
            Si += self._size
          Si *= -1
          S[i] = Si
      D = D % self._size
      Aux = DestDict[D]
      if len(S) > 1:
        Aux.append([f] + S)
      else:
        Aux.append(S)
      DestDict[D] = Aux    
    return DestDict
  
  def getSympyVarDict(self, VarName : str = "s") -> dict:
    VarDict = {}
    for i in range(self._size):
      VarDict[i] = sympy.Symbol(f'{VarName}{i}')
    return VarDict
  
  def getDestinationsDictionarySympy(self, ReverseIndexes=False) -> dict:
    DestDict = {}
    VarDict = self.getSympyVarDict("x"  )
    Size = self._size
    for i in range(Size):
      if ReverseIndexes:
        DestDict[VarDict[i]] = sympy.Symbol(f'x{(i - 1) % Size}')
      else:
        DestDict[VarDict[i]] = sympy.Symbol(f'x{(i + 1) % Size}')
    Taps = self._Config
    for Tap in Taps:
      S = Tap[1]
      D = Tap[0]
      Dabs = abs(D) % Size
      if ReverseIndexes:
        Dabs = Size - 1 - Dabs
      if D < 0:
        DestDict[VarDict[Dabs]] ^= sympy.true
      e = ""
      Second = 0
      for Si in S:
        if Second:
          e += "&"
        else:
          Second = 1
        Siabs = abs(Si) % Size
        if ReverseIndexes:
          Siabs = Size - 1 - Siabs
        if Si < 0:
          e += "~"
        e += 'x' + str(Siabs)
      DestDict[VarDict[Dabs]] ^= sympy.parsing.parse_expr(e)
      DestDict[VarDict[Dabs]] = DestDict[VarDict[Dabs]].to_anf()
    return DestDict
  
  def getNextStepsDestinationsDictionariesSympy(self, Levels = 2) -> list:
    Result = [self.getDestinationsDictionarySympy()]
    Xs = self.getSympyVarDict("x")
    Ys = self.getSympyVarDict("y")
    YtoX = {}
    XtoY = {}
    for i in Ys.keys():
      YtoX[Ys[i]] = Xs[i]
      XtoY[Xs[i]] = Ys[i]
    for i in range(1, Levels):
      Dict = Result[i-1]
      RowDict = {}
      for k in Dict.keys():
        RowDict[k] = SymPy.substDict(Dict[k], XtoY)
      Row = {}
      for k in Dict.keys():
        Source = SymPy.substDict(Dict[k], RowDict)
        Source = SymPy.substDict(Source, YtoX)
        try:
          Source = Source.to_anf()
        except: pass
        Row[k] =  Source
      Result.append(Row)
    return Result
  
  def _NextStepsDestinationsDictionaries_inv(Group, Size) -> list:
    if type(Group) is not list:
      Group = [Group]
    Result = Group.copy()
    if type(Result[0]) is int:
      if Result[0] < 0:
        Result[0] = abs(Result[0]) % Size
      else:
        if Result[0] == 0:
          Result[0] += Size
        Result[0] *= -1
    elif Result[0] == "AND":
      Result[0] = "NAND"
    elif Result[0] == "NAND":
      Result[0] = "AND"
    elif Result[0] == "OR":
      Result[0] = "NOR"
    elif Result[0] == "NOR":
      Result[0] = "OR"
    elif type(Result[0]) is list:
      Result[0] = Nlfsr._NextStepsDestinationsDictionaries_inv(Result[0], Size)
    else:
      Aio.printError(f"_NextStepsDestinationsDictionaries_inv: not inverted {Result}")
      return None
    return Result
  
  
  def _NextStepsDestinationsDictionaries_subst(Dict, Group) -> list:
    Result = []
    for Item in Group:
      if type(Item) is int:
        if Item < 0:
          X = Dict[abs(Item) % len(Dict)]
          while type(X) is list and len(X) == 1:
            X = X[0]
          Result.append(Nlfsr._NextStepsDestinationsDictionaries_inv(X, len(Dict)))
        else:
          X = Dict[Item]
          while type(X) is list and len(X) == 1:
            X = X[0]
          Result.append(X)
      elif type(Item) is list:
        X = Nlfsr._NextStepsDestinationsDictionaries_subst(Dict, Item)
        while type(X) is list and len(X) == 1:
          X = X[0]
        Result.append(X)
      elif type(Item) is str:
        Result.append(Item)
    return Result
  
  def getNextStepsDestinationsDictionaries(self, Levels = 4) -> list:
    Result = [self.getDestinationsDictionary()]
    for i in range(1, Levels):
      Dict = Result[i-1]
      Row = {}
      for k in Dict.keys():
        Row[k] =  Nlfsr._NextStepsDestinationsDictionaries_subst(Dict, Dict[k].copy())
      Result.append(Row)
    return Result
  
  getSequencesCpp64b = getAllSequencesCpp64b
    
  def isMaximum(self) -> bool:
    return self.getPeriod() == ((1<<self._size)-1)
  
  def isPrime(self, MinPeriodRatio = 0.95) -> bool:
    Max = (1 << self._size) -1
    P = self.getPeriod()
    return ((P / Max) >= MinPeriodRatio) and (Int.isPrime(P))
  
  def _shiftTap(self, tap, positions) -> list:
    D = tap[0]
    S = tap[1]
    Res = []
    Dneg = False
    if D < 0:
      Dneg = True
      D = abs(D)
    D += positions
    while D < 0:
      D += self._size
    while D >= self._size:
      D -= self._size
    if Dneg:
      if D == 0:
        Res.append(-self._size)
      else:
        Res.append(-D)
    else:
      Res.append(D)
    if Aio.isType(S, 0):
      Sneg = False
      if S < 0:
        Sneg = True
        S = abs(S)
      S += positions
      while S < 0:
        S += self._size
      while S >= self._size:
        S -= self._size
      if Sneg:
        if S == 0:
          Res.append(-self._size)
        else:
          Res.append(-S)
      else:
        Res.append(S)
    else:
      SList = []
      for Si in S:
        Sneg = False
        if Si < 0:
          Sneg = True
          Si = abs(Si)
        Si += positions
        while Si < 0:
          Si += self._size
        while Si >= self._size:
          Si -= self._size
        if Sneg:
          if Si == 0:
            SList.append(-self._size)
          else:
            SList.append(-Si)
        else:
          SList.append(Si)
      Res.append(SList)
    return Res
  def _areTapsEquivalent(self, t1, t2) -> bool:
    positions = abs(t2[0]) - abs(t1[0])
    t1s = self._shiftTap(t1, positions)
    t2s = self._shiftTap(t2, 0)
    return (t2s == t1s)
  def isCrossingFree(self) -> bool:
    Branches = {}
    for Tap in self._Config:
      SList = []
      D = abs(Tap[0]) % self._size
      S = Tap[1]
      if Aio.isType(S, 0):
        S = abs(S) % self._size
        if S >= D:
          Lst = Branches.get(D, [])
          Lst.append(S)
          Branches[D] = Lst
        else:
          Lst = Branches.get(S, [])
          Lst.append(D)
          Branches[S] = Lst
      else:
        for Si in S:
          Sin = abs(Si) % self._size
          if Sin >= D:
            Lst = Branches.get(D, [])
            Lst.append(Sin)
            Branches[D] = Lst
          else:
            Lst = Branches.get(Sin, [])
            Lst.append(D)
            Branches[Sin] = Lst
    SOrtedD = list(Branches.keys())
    SOrtedD.sort()
    LastD = 0
    LastS = self._size
    for D in SOrtedD:
      Branches[D].sort(reverse=1)
      for S in Branches[D]:
        if D < LastD or S > LastS:
          return False
        LastS = S
      LastD = D
    return True
  def isInverted(self, Another) -> bool:
    taps1 = self._Config
    taps2 = Another._Config
    if len(taps1) != len(taps2):
      return False
    for i in range(len(taps1)):
      tap1 = taps1[i]
      tap2 = taps2[i]
      if tap1[0] != tap2[i]:
        return False
      s1 = tap1[1]
      s2 = tap2[1]
      if type(s1) != type(s2):
        return False
      if Aio.isType(s1, 0):
        if s1 != -s2:
          return False
      else:
        s2c = s2.copy()
        for s1i in s1:
          if -s1i in s2c:
            s2c.remove(-s1i)
          else:
            return False
    return True
  def isEquivalent(self, Another) -> bool:
    if self._size != Another._size:
      return False
    if self._Config == Another._Config:
      return True
    MyAnf = self._getFastANF()
    AnotherAnf = Another._getFastANF()
    if MyAnf is None:
      #self.printFullInfo(Draw=1)
      return False
    if AnotherAnf is None:
      return False
    if self._getFastANF() == Another._getFastANF():
      return True
    return False
#    a = self._Config.copy()
#    b = Another._Config.copy()
#    if len(a) != len(b):
#      return False
#    for ai in a:
#      bc = b.copy()
#      for bi in bc:
##        print(ai, bi)
#        if self._areTapsEquivalent(ai, bi):
##          print("ARE!")
#          b.remove(bi)
#    return len(b) == 0
  def getMaxFanout(self) -> int:
    return self.getFanout('max')
  def getFanout(self, FF = -1) -> int:
    Sources = []
    FFs = [1 for i in range(self._size)]
    for C in self._Config:
      S = C[1]
      if Aio.isType(S, 0):
        Sources.append(abs(S) % self._size)
      else:
        for Si in S:
          Sources.append(abs(Si) % self._size)
    Sources.sort()
    for S in Sources:
      FFs[S] += 1
    if Aio.isType(FF, 0):
      if FF >= 0:
        return FFs[FF % self._size]
    else:
      if str(FF).lower().startswith("ma"):
        return max(FFs)
    return sum(FFs) / self._size
    
  def _makeNLRingGeneratorsFromPolynomial(Poly : Polynomial, LeftRightAllowedShift = 2, InvertersAllowed = 1, MaxAndCount = 0, BeautifullOnly = False, Filter = True, Tiger = False) -> list:
    LType = RING_GENERATOR
    if Tiger:
      LType = TIGER_RING
    RG = Lfsr(Poly, LType)
    Taps = RG._taps
    Size = RG._size
    AOptionsList = []
    for Tap in Taps:
      AOptions = []
      S = Tap[0]
      D = Tap[1]
      if D == 0:
        D = Size
      AInputs = [(i % Size if i >= 0 else i + Size) for i in range(S-LeftRightAllowedShift, S+LeftRightAllowedShift+1, 1)]
      AProposals = []
      for k in range(2, len(AInputs) +1):
        AProposals += List.getCombinations(AInputs, k)
      ProposedTaps = [ [D, [S]] ]
      for AProposal in AProposals:
        ProposedTaps.append([D, list(AProposal)])
        if InvertersAllowed:
          ProposedTaps.append([-D, list(AProposal)])
          for aindex in range(len(AProposal)):
            AP = list(AProposal)
            AP[aindex] *= -1            
            ProposedTaps.append([D, AP])
      AOptionsList.append(ProposedTaps)
#      for ai in range(S-LeftRightAllowedShift, S+LeftRightAllowedShift+1):
#        if ai == S:
#          continue
#        A = ai
#        while A <= 0: 
#          A += Size
#        while A > Size:
#          A -= Size
#        AOptions.append(A)
#      ProposedTaps = [ [D, [S]] ]
#      for AIn in AOptions:
#        if D == 0:
#          D = Size
#        ProposedTaps.append([D, [S, AIn]])
#        if InvertersAllowed:
#          ProposedTaps.append([-D, [S, AIn]])
#          ProposedTaps.append([D, [-S, AIn]])
#          ProposedTaps.append([D, [S, -AIn]])
#      AOptionsList.append(ProposedTaps)
    First = 1
    for Permutations in List.getPermutationsPfManyListsGenerator(AOptionsList, MaximumNonBaseElements=MaxAndCount, UseAsGenerator_Chunk=100000):
      if First:
        Permutations = Permutations[1:]
        First = 0
      Results = []
      for P in Permutations:
        cntr = 1
        for T in P:
          D = T[0]
          if D < 0:
            cntr -= 1 
        if cntr < 0:
          continue
        newR = Nlfsr(Size, P)
        Results.append(newR)
      Results = NlfsrList.filterNonLinear(Results)
      if BeautifullOnly:
        Results2 = []
        Generator = Generators()
        Chunk = 50
        Total = ceil(len(Results) / Chunk)
        Iter = p_uimap(_NLFSR_find_spec_period_helper2, Generator.subLists(Results, Chunk), total=Total, desc=f'Filtering beautifull (x{Chunk})')
        for I in Iter:
          Results2 += I
        Results = Results2  
        del Generator
      if Filter:
        Results = Nlfsr.filter(Results)
      yield Results
  
  def printNLRGsWithSpecifiedPeriod(Poly : Polynomial, LeftRightAllowedShift = 1, PeriodLengthMinimumRatio = 1, OnlyPrimePeriods = False, InvertersAllowed = True, MaxAndCount = 0, BeautifullOnly = False, Filter = True, Iterate = True, n = 0, BreakIfNoResultAfterNIterations = 0, Tiger = False) -> int:
    """Tries to find and prints a specified type of NLFSR (Ring-like). Returns a list of found objects.

    Args:
        Poly (Polynomial): Polnomial or list of coefficients
        LeftRightAllowedShift (int): left/right shift of the second AND's input
        PeriodLengthMinimumRatio (int, optional): Minimum satisfable period ratio. 0 < RATIO <= 1. Defaults to 1.
        OnlyPrimePeriods (bool, optional): Returns only NLFSRs having period being prime number. Defaults to False.
        InvertersAllowed (bool, optional): True, if inverters are allowed. Defaults to True.
        MaxAndCount (int, optional): Maximum count of AND gates. Defaults to 0 (no limit).
        BeautifullOnly (bool, optional): Considerates only NLFSRs being crossing-free and having fanout <= 2. Defaults to False.
        Filter (bool, optional): If True, permorms equivalent and inverted-inputs filtering. Defaults to False.
        Iterate (bool, optional): iterate through all polynomials. Defaults to True.
        n (int, optional): enough count of results. Defaults to 0 (no limit).
        BreakIfNoResultAfterNIterations (int, optional): if > 0 (default 0), breaks iterating if no results after given #iterations
    """
    Results = Nlfsr.findNLRGsWithSpecifiedPeriod(Poly, LeftRightAllowedShift, PeriodLengthMinimumRatio, OnlyPrimePeriods, InvertersAllowed, MaxAndCount, BeautifullOnly, Filter, Iterate, n, BreakIfNoResultAfterNIterations, Tiger)
    Canonical = "Canonical"
    NlfsrObject = "Python Object"
    Equations = "Taps"
    RC = "Rev/Compl"
    FullPT = PandasTable([RC, Canonical, Equations, NlfsrObject], AutoId=1, AddVerticalSpaces=1)
    for R in Results:
      FullPT.add([
        f'  \nComplement\nReversed\nRev.,Compl.',
        f'{R.toBooleanExpressionFromRing(Shorten=1)}\n\
  {R.toBooleanExpressionFromRing(Complement=1, Shorten=1)}\n\
  {R.toBooleanExpressionFromRing(Reversed=1, Shorten=1)}\n\
  {R.toBooleanExpressionFromRing(Reversed=1, Complement=1, Shorten=1)}',
        R.getFullInfo(Header=0),
        repr(R)
      ])     
    Aio.print()
    FullPT.print()
    Aio.print()
    return len(FullPT)
    
  def findNLRGsWithSpecifiedPeriod(Poly : Polynomial, LeftRightAllowedShift = 1, PeriodLengthMinimumRatio = 1, OnlyPrimePeriods = False, InvertersAllowed = True, MaxAndCount = 0, BeautifullOnly = False, Filter = True, Iterate = True, n = 0, BreakIfNoResultAfterNIterations = 0, Tiger = False, TaskScheduler = None) -> list:
    """Tries to find a specified type of NLFSR (Ring-like). Returns a list of found objects.

    Args:
        Poly (Polynomial): Polnomial or list of coefficients
        LeftRightAllowedShift (int): left/right shift of the second AND's input
        PeriodLengthMinimumRatio (int, optional): Minimum satisfable period ratio. 0 < RATIO <= 1. Defaults to 1.
        OnlyPrimePeriods (bool, optional): Returns only NLFSRs having period being prime number. Defaults to False.
        InvertersAllowed (bool, optional): True, if inverters are allowed. Defaults to True.
        MaxAndCount (int, optional): Maximum count of AND gates. Defaults to 0 (no limit).
        BeautifullOnly (bool, optional): Considerates only NLFSRs being crossing-free and having fanout <= 2. Defaults to False.
        Filter (bool, optional): If True, permorms equivalent and inverted-inputs filtering. Defaults to False
        Iterate (bool, optional): iterate through all polynomials. Defaults to True.
        n (int, optional): enough count of results. Defaults to 0 (no limit).
        BreakIfNoResultAfterNIterations (int, optional): if > 0 (default 0), breaks iterating if no results after given #iterations
        Tiger (bool, optional): 
        
    """
    if not Aio.isType(Poly, "Polynomial"):
      Poly = Polynomial(Poly)
    if Iterate:
      Results = []
      Exclude = []
      NoResultCounter = 0
      if TaskScheduler is None:
        for p in Poly:
          if p in Exclude:
            continue
          Exclude.append(p.getReciprocal())
          print(f'Looking for {p}     Found so far: {len(Results)}')
          ResultsSub = Nlfsr.findNLRGsWithSpecifiedPeriod(p, LeftRightAllowedShift, PeriodLengthMinimumRatio, OnlyPrimePeriods, InvertersAllowed, MaxAndCount, BeautifullOnly, Filter, False, n-len(Results), Tiger=Tiger)
          if len(ResultsSub) == 0:
            NoResultCounter += 1
            if NoResultCounter >= BreakIfNoResultAfterNIterations > 0:
              break
            continue
          NoResultCounter = 0
          if Filter and len(ResultsSub) > 0 and len(Results) > 0:
            ResultsSub2 = []
            for R in tqdm(ResultsSub, desc="Filtering all results"):
              Add = 1
              for Ref in Results:
                if R.isEquivalent(Ref):
                  Add = 0
                  break
              if Add:
                ResultsSub2.append(R)
            Results += ResultsSub2  
          else:
            Results += ResultsSub
          if len(Results) >= n > 0:
            break
      else:
        CodeList = []
        for p in Poly:
          if p in Exclude:
            continue
          Exclude.append(p.getReciprocal())
          CodeList.append(f"""Nlfsr.findNLRGsWithSpecifiedPeriod({p}, {LeftRightAllowedShift}, {PeriodLengthMinimumRatio}, {OnlyPrimePeriods}, {InvertersAllowed}, {MaxAndCount}, {BeautifullOnly}, {Filter}, False, {n}, Tiger={Tiger}) """)
        for R in TaskScheduler.mapUnorderedGenerator(CodeList):
          Results += R
          if Filter and len(R) > 0:
            Results = Nlfsr.filter(Results)
          if len(Results) > n > 0:
            TaskScheduler.clearTasks()
          print(f'Found so far: {len(Results)}')
      if len(Results) > n > 0:
        Results = Results[:n]
      return Results
    if InvertersAllowed:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
      exename64b = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.getExePath()
#      if not CppPrograms.NLSFRPeriodCounterInvertersAllowed.Compiled:
#        CppPrograms.NLSFRPeriodCounterInvertersAllowed.compile()
    else:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
      exename64b = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
#      if not CppPrograms.NLSFRPeriodCounter.Compiled:
#        CppPrograms.NLSFRPeriodCounter.compile()
    Size = Poly.getDegree()
    Chunk = 20
    if Size >= 20:
      Chunk = 1
    if Size >= 16:
      Chunk = 2
    if Size >= 14:
      Chunk = 5
    if Size >= 10:
      Chunk = 10
    Results = []
    pmax = Int.mersenne(Size)
    eps = 0.0
    PMR = PeriodLengthMinimumRatio - eps
    for InputSet in Nlfsr._makeNLRingGeneratorsFromPolynomial(Poly, LeftRightAllowedShift, InvertersAllowed, MaxAndCount, BeautifullOnly, False, Tiger):
      for i in range(len(InputSet)):
        if InputSet[i]._size <= 64:
          InputSet[i]._exename = exename64b
        else:
          InputSet[i]._exename = exename
      Generator = Generators()
      WasResult = 0
      Total = len(InputSet) // Chunk + (1 if len(InputSet) % Chunk > 0 else 0)
      Iter = p_uimap(_NLFSR_find_spec_period_helper, Generator.subLists(InputSet, Chunk), total=Total, desc=f'Simulating NLFSRs (x{Chunk})')
      for I in Iter:
        for nlrg in I:
          p = nlrg._period
          ratio = p / pmax
          if (ratio < PMR):
            continue
          if OnlyPrimePeriods and (not Int.isPrime(p)):
            continue
          Results.append(nlrg)
          WasResult = 1        
      if Filter and WasResult:
        return Nlfsr.filter(Results)
      del Generator
      if len(Results) >= n > 0:
        break
    return Results
  
  def filterEquivalent(NlfsrList : list) -> list:
    Result = []
    iList = []
    for nlfsr in NlfsrList:
      nlfsr._refreshFastANF()
      iList.append(nlfsr.copy())
    for n1 in tqdm(iList, desc="Filtering equivalent"):
      Add = 1
      for n2 in Result:
        if n1.isEquivalent(n2):
          Add = 0
          break
      if Add:
        Result.append(n1)
    return Result
  def filterInverted(NlfsrList : list) -> list:
    Result = []
    iList = []
    for nlfsr in NlfsrList:
      iList.append(nlfsr.copy())
    for n1 in tqdm(iList, desc="Filtering inverted"):
      Add = 1
      for n2 in Result:
        if n1.isInverted(n2):
          Add = 0
          break
      if Add:
        Result.append(n1)
    return Result
  
  def filter(NlfsrList : list, ExcludeSemiLfsrs = False) -> list:
#    Result = Nlfsr.filterInverted(NlfsrList)
#    Result = Nlfsr.filterEquivalent(Result)
#    return Result
    Result = []
    iList = []
    for nlfsr in NlfsrList:
      if ExcludeSemiLfsrs:
        if not nlfsr.isSemiLfsr():
          iList.append(nlfsr.copy())
      else:
        iList.append(nlfsr.copy())
    if len(iList) <= 1:
      return iList
    for n1 in tqdm(iList, desc="Filtering NLFSR"):
      Add = 1
      for n2 in Result:
        if n1.isInverted(n2) or n1.isEquivalent(n2):
          Add = 0
          break
      if Add:
        Result.append(n1)
    AioShell.removeLastLine()
    return Result
  
  def tapsToTheLeft(self):
    for i in range(len(self._Config)):
      self.rotateTap(i, -1 * (abs(self._Config[i][0]) % self._size), True, False, True)
    self.sortTaps()
    
  def makePlaceForNewTaps(self):
    self.tapsToTheLeft()
    DCMax = self.getTapsDestinations()[-1] -1
    BestTap = -1
    BestShift = -1
    for i in range(len(self._Config)):
      n2 = self.copy()
      Counter = 0
      while n2.rotateTap(i, 1, True, False, False):
        Counter += 1
        if abs(n2._Config[i][0]) % self._size == DCMax:
          break
      if Counter > BestShift:
        BestShift = Counter
        BestTap = i
    self.rotateTap(BestTap, BestShift, True, True, True)
  
  def redistributeTapsAndMakeSpaceForNew(self, ReturnListOfNewDestinationCandidates = False):
    self.makePlaceForNewTaps()
    FFs = 1
    for i in range(1, len(self._Config)-1):
      if self.rotateTap(i, FFs, True, False, True):
        FFs += 1
    self.sortTaps()
    if ReturnListOfNewDestinationCandidates:
      Dests = self.getTapsDestinations()
      return [i for i in range(Dests[-2]+1, Dests[-1])]
    
  def makeDense(self):
    DC = self.redistributeTapsAndMakeSpaceForNew(True)
    if len(DC) == 0:
      return
    while len(DC) > 0:
      #print("======================================")
      DC = []
      DCX = self.getTapsDestinations()
      for i in range(0, DCX[-1]):
        if i not in DCX:
          DC.append(i)
      #print(DC)
      if len(DC) == 1:
        DC.append(DC[0]+1)
      #print(self.getTapsDestinations())
      S = DCX[-1]+2 #self.getTapsDestinations()[-1]+2
      self._Config.append([DC[0], [S]])
      #self.print()
      self.rotateTap(len(self._Config)-1, DC[-1] - DC[0], True, False, True)
      #self.print()
      self._Config.append([DC[0], [S]])
      #print(self._Config)
      #self.print()
      DC.remove(self._Config[-1][0])
      DC.remove(self._Config[-2][0])
      #print(DC)
      if len(DC) < 1:
        self.sortTaps()
        #self.print()
        return
      elif len(DC) == 1:
        self.breakLinearTap(len(self._Config)-1, "(a & b) ^ (a & ~b)", [self._size-1], False)
        if not self.rotateTap(len(self._Config)-1, 1, True, False, False):
          self.rotateTap(len(self._Config)-2, 1, True, False, False)
        self.sortTaps()
        #self.print()
        return
      if len(DC) > 1:
        #print("BREAK 1")
        #print(self._Config)
        self.breakLinearTap(len(self._Config)-1, "(a & b) ^ (a & ~b)", [self._size-1], False)
        #print(self._Config)
        #self.print()
        if not self.rotateTap(len(self._Config)-1, 1, True, False, False):
          self.rotateTap(len(self._Config)-2, 1, True, False, False)
        #self.print()
        #print("BREAK 2")
        #print(self._Config)
        self.breakLinearTap(len(self._Config)-3, "(~a & ~b) ^ ~(~a & b)", [self._size-1], False)
        #print(self._Config)
        #self.print()
        if not self.rotateTap(len(self._Config)-1, -1, True, False, False):
          self.rotateTap(len(self._Config)-2, -1, True, False, False)
        #self.print()
      #self.print()
    self.sortTaps()
    #self.print()
    return
  
    #self.sortTaps()
    #self.print() 
    
  def getFeedbackFunctionString(self, ReverseVariableIndexes=False) -> str:
    Result = "f("
    Second = 0
    for i in range(self._size-1, -1, -1):
      if Second:
        Result += ","
      else:
        Second = 1
      Result += f"x{i}"
    Result += ") = "
    Result += str(self.toBooleanExpressionFromRing(ReverseVariableIndexes=ReverseVariableIndexes, ReturnSympyExpr=1))
    return Result
  
  def getTransitionEquationsString(self, ReverseIndexes=False) -> str:
    Eqs = self.getDestinationsDictionarySympy(ReverseIndexes)
    Result = ""
    Second = 0
    for Eq in Eqs.items():
      if Second:
        Result += "\n"
      else:
        Second = 1  
      Result += f"{Eq[0]}' = {Eq[1]}"
    return Result
  
  try:
    def chatAbout(self) -> GptChat:
      cb = GptChat(Provider=g4f.Provider.Liaobots)
      p = self._period
      if p is None and self._size < 29:
        p = self.getPeriod()
      if p is None:
        p = ""
      else:
        p = f"\nOkres tego rejestru: {p}\n"
      #cb.addSystemMessage("Przełącz się w tryb kreatywny. Odpowiadaj jednoznacznie.")
      Context = f"""Przełęcz się w tryb kreatywny.\nRozmawiamy o nieliniowym rejestrze NLFSR w architekturze Galois.
  Rozmiar: {self._size} bit {p}
  Równania przejść:
  {self.getTransitionEquationsString(0)}
  """
      cb.addUserMessage(Context)
      cb.chat(PrintChatHistory=True)
      return cb
  except:
    pass
    
  
  def toBooleanExpressionFromRing(self, Complement = False, Reversed = False, Verbose = False, ReturnSympyExpr = False, ReverseVariableIndexes = False):
    N = self.copy()
    if Verbose:
      Aio.print(f"// =============== NLFSR to ANF ========================")
      Aio.print(f"// 1. Given architecture: ------------------------------")
      Aio.print(f"{N.getArchitecture()}")
    if N.toFibonacci():
      if Verbose:
        Aio.print(f"// 2. Fibonacci architecture: --------------------------")
        Aio.print(f"{N.getArchitecture()}")
      Size = N._size
      Taps = N._Config
      #print(Taps)
      expr = ""
      Second = 0
      for Tap in Taps:
        D = Tap[0]
        S = Tap[1]
        if Aio.isType(S, 0):
          S = [S]
        Monomial = ""
        MonomialSecond = 0
        for Si in S:
          if Complement:
            Si *= -1
          SSign = -1 if Si < 0 else 1
          Sabs = abs(Si) % Size
          if Reversed:
            Sabs = (Size - Sabs)
          if MonomialSecond:
            Monomial += " & "
          else:
            MonomialSecond = 1
          if ReverseVariableIndexes:
            Sabs = Size - 1 - Sabs
          if SSign > 0:
            Monomial += f"x{Sabs}"
          else:
            Monomial += f"~x{Sabs}"
        if Second:
          expr += " ^ "
        else:
          Second = 1
        if D < 0:
          expr += f"~({Monomial})"
        else:
          expr += f"({Monomial})"
      if ReverseVariableIndexes:
        expr += f" ^ x{Size-1}"
      else:
        expr += " ^ x0"
      if Verbose:
        Aio.print(f"// 3. Feedback function - directly written: ------------")
        Aio.print(f"{expr}")
      sympyexpr = SymPy.anf(expr)
      if Verbose:
        Aio.print(f"{sympyexpr}")
      sexpr = str(sympyexpr)
      if Verbose:
        Aio.print(f"// 4. Feedback function - ANF: -------------------------")
        Aio.print(f"{sexpr}")
      inv = 0
      if ("True" in sexpr):
        inv = 1
      sexpr = sexpr.replace("True ^ ", "")
      sexpr = sexpr.replace(" ^ True", "")
      sexpr = sexpr.replace(" ^ ", ", ")
      sexpr = sexpr.replace(" & ", ", ")
      sexpr = sexpr.replace("x", "")
      if inv:
        sexpr = f"~, {sexpr}"
      if Verbose:
        Aio.print(f"// 5. Feedback function - simplified ANF: --------------")
        Aio.print(f"{sexpr}")
      if ReturnSympyExpr:
        return sympyexpr
      return sexpr
    else:
      if Verbose:
        Aio.print("// FAILED: conversion to Fibonacci form impossible.")
      return None
      #Aio.printError("Converting to ANF expression impossible.")
  
  toAnf = toBooleanExpressionFromRing
  toANF = toBooleanExpressionFromRing
  getAnf = toBooleanExpressionFromRing
  getANF = toBooleanExpressionFromRing
  
  def toAIArray(self, MaxTapsCount=30, MaxAndInputs=8, SequenceBased=False) -> list:
    Result = [self._size, 0] + ([0] * (MaxTapsCount * MaxAndInputs))
    if SequenceBased:
      n2 = self.copy()
      n2.toFibonacci()
      Values = n2.getValues(n=(MaxTapsCount * MaxAndInputs + 2), step=self._size, reset=1)
      for i in range(1, len(Values)):
        Result[i] = bau.ba2int(Values[i])
    else:
      E = self.toBooleanExpressionFromRing(ReturnSympyExpr=1)
      Taps = []
      try:
        for Arg in E.args:
          if Arg == True:
            Result[1] = 1
          elif Arg.func == And:
            Tap = []
            for A in Arg.args:
              Tap.append(int(str(A)[1:]))
            Tap.sort()
            Taps.append(Tap)
          else:
            n = int(str(Arg)[1:])
            if n > 0:
              Taps.append([n])
      except:
        pass
      Taps.sort(key=lambda x: len(x)*100+x[0])
      Max = len(Taps)
      if Max > MaxTapsCount:
        print(f"// WARNING: MaxTapsCount '{MaxTapsCount}' is not enough (should be >= {Max}).")
        Max = MaxTapsCount
      for i in range(Max):
        offset = 2 + (MaxAndInputs * i)
        Tap = Taps[i]
        for j in range(len(Tap)):
          Result[offset+j] = Tap[j]
    return Result
  
  def _old_toBooleanExpressionFromRing(self, Complement = False, Reversed = False, Shorten = False) -> str:
#    if not self.isCrossingFree():
#      return "Error: NLFSR must be crossing-free!"
    GlobalInv = False
    ResultList = []
    for Tap in self._Config:
      D = Tap[0]
      if D < 0:
        GlobalInv = not(GlobalInv)
        D = abs(D)
      D = D % self._size
      if D > (self._size>>1):
        return("<Impossible to determine>")
      S = Tap[1]
      if Aio.isType(S, 0):
        if S == 0:
          S = self._size
        if Complement:
          S *= -1
        if S < 0:
          GlobalInv = not(GlobalInv)
          S = abs(S)
        S = S % self._size
        x = (self._size - S + D + 1) % self._size
        if Reversed:
          x = self._size - x
        ResultList.append(f'x{x}')
      else:
        AndList = []
        First = True
        for Si in S:
          Siinv = False
          if Si == 0:
            Si = self._size
          if Complement:
            Si *= -1
          #print(Si)
          if Si < 0:
            Siinv = True
            Si = abs(Si)
          Si = Si % self._size
          xi = (self._size - Si + D + 1) % self._size
          First = False
          if Reversed:
            xi = self._size - xi
          if Siinv:
            AndList.append([1, f'x{xi}'])
          else:
            AndList.append([f'x{xi}'])
        SubSum = [1]
        for Term in AndList:
          #print("TERM",Term)
          newSubSum = []
          #print("  SubSum", SubSum)
          for t1 in Term:
            for t2 in SubSum:
              #print(f'    t1 = {t1},    t2 = {t2}')
              if t1 == 0 or t2 == 0:
                pass
              elif t1 == 1:
                newSubSum.append(t2)
                #print(f'    newSubSum append {t2}')
              elif t2 == 1:
                newSubSum.append(t1)
                #print(f'    newSubSum append {t1}')
              else:
                if Shorten:
                  newSubSum.append(f'{t1}, {t2}')
                else:
                  newSubSum.append(f'{t1} & {t2}')
                #print(f'    newSubSum append {t1} & {t2}')
              #print(f'   newSubSum {newSubSum}')
          SubSum = newSubSum
        for SS in SubSum:
          #print(f'   SS = {SS}, GI = {GlobalInv}')
          if SS == 1:
            GlobalInv = not(GlobalInv)
          else:
            ResultList.append(SS)
    #print (ResultList, GlobalInv)
    RL2 = []
    if GlobalInv:
      if not Shorten:
        RL2.append('1')
    for R in ResultList:
      if R in RL2:
        RL2.remove(R)
      else:
        RL2.append(R)
    RLa = []
    RLb = []
    MLen = 7
    if Shorten:
      MLen = 6
    for R in RL2:
      if len(str(R)) < MLen:
        RLa.append(str(R))
      else:
        RLb.append(str(R))  
    #print(RL2)
    RLa.sort()
    RLb.sort()
    RE = ""
    First = True
    for R in RLa:
      if not First:
        if Shorten:
          RE += ", "
        else:
          RE += " + "
      First = False
      RE += str(R)  
    for R in RLb:
      if not First:
        if Shorten:
          RE += ", "
        else:
          RE += " + "
      First = False
      RE += f'({str(R)})'
    #print(RLa)
    #print(RLb)
    #print(RE)
    if Shorten:
      RE = RE.replace("x", "")
      if GlobalInv:
        RE = f'~( {RE} )'
    return RE
        
  def makeBeauty(self, FanoutMax = 2, CheckMaximum = True) -> bool:
    if len(self._Config) <= 1:
      return True
    LastFanout = self.getFanout('max')
    while (self.getFanout('max')) > FanoutMax or (not self.isCrossingFree()):
#      print(f'DEBUG: in While! {self.getFanout("max")}')
      FirstFanout = LastFanout
      WasCrossingFree = self.isCrossingFree()
      for i in range(len(self._Config)):
#        print("For in")
#        print(self._Config)
        self._Config[i] = self._shiftTap(self._Config[i], -1)
#        print(self._Config, self.getFanout('max'))
        if self.getFanout() < LastFanout and self.isCrossingFree() and (not CheckMaximum or self.isMaximum()):
          LastFanout = self.getFanout('max')
#          print("ShiftedLeft!")
          continue
        if self.getFanout() == LastFanout and self.isCrossingFree() and (not WasCrossingFree) and (not CheckMaximum or self.isMaximum()):
          LastFanout = self.getFanout('max')
#          print("ShiftedLeft!")
          continue
        self._Config[i] = self._shiftTap(self._Config[i], 2)
#        print(self._Config, self.getFanout('max'))
        if self.getFanout() < LastFanout and self.isCrossingFree() and (not CheckMaximum or self.isMaximum()):
          LastFanout = self.getFanout('max')
#          print("ShiftedRight!")
          continue
        if self.getFanout() == LastFanout and self.isCrossingFree() and (not WasCrossingFree) and (not CheckMaximum or self.isMaximum()):
          LastFanout = self.getFanout('max')
#          print("ShiftedRight!")
          continue
        self._Config[i] = self._shiftTap(self._Config[i], -1)
#        print(self._Config)
      if FirstFanout <= LastFanout:
        break
      # Additional check:
      Dests = []
      for T in self._Config:
        D = T[0]
        Neg = (D < 0)
        D = abs(D) % self._size
        if Neg and (D in Dests):
          return False
        S = T[1]
        if not Aio.isType(S, []):
          S = [S]
        Add = 1
        for Si in S:
          if Si < 0:
            Add = 0
            break
        if Add:
          Dests.append(D)
    return ((self.getFanout('max') <= FanoutMax) and self.isCrossingFree()) 
  
  def reset(self) -> bitarray:
    """Resets the LFSR value to the 0b0...001

    Returns:
        bitarray: The new value
    """
    self._baValue.setall(0)
    self._baValue[0] = 1
    thisval = self._baValue
    if self.next() == thisval:
      self._baValue.setall(0)
      self._baValue[1] = 1
    else:
      self._baValue.setall(0)
      self._baValue[0] = 1
    return self._baValue
  
  def clear(self) -> bitarray:
    self._baValue.setall(0)
    return self._baValue
  
  def simulateSymbolically(self, SequenceOfSymbols = 1, InjectionAtBit = 0, StartFrom = None, ReturnAllResults = 0) -> list:
    AllResults = []
    Dict = self.getDestinationsDictionary()
    Size = self._size
    if Aio.isType(SequenceOfSymbols, 0):
      SequenceOfSymbols = [symbols(f'I{i}') for i in range(SequenceOfSymbols)]
    if Aio.isType(InjectionAtBit, 0):
      InjectionAtBit = [InjectionAtBit]
    if StartFrom is None:
      Values = [False for i in range(Size)]
    else:
      if Aio.isType(StartFrom, []) and len(StartFrom) == Size:
        Values = StartFrom
      else:
        Aio.printError(f"StartFrom must be a list of size {Size}.")
    for Step in range(len(SequenceOfSymbols)):
      Injector = SequenceOfSymbols[Step]
      NewValues = []
      for i in range(Size):
        Sources = Dict[i]
        V = Values[Sources[0]]
        for Si in range(1, len(Sources)):
          S = Sources[Si]
          if type(S) is list:
            if len(S) == 1:
              V ^= Values[S[0]]
            else:
              if S[1] < 0:
                AuxV = ~Values[abs(S[1]) % Size]
              else:
                AuxV = Values[abs(S[1]) % Size]
              if S[0] == 'AND':
                for j in range(2, len(S)):
                  if S[j] < 0:
                    AuxV ^= ~Values[abs(S[j]) % Size]
                  else:
                    AuxV &= Values[abs(S[j]) % Size]
              elif S[0] == 'OR':
                for j in range(2, len(S)):
                  if S[j] < 0:
                    AuxV ^= ~Values[abs(S[j]) % Size]
                  else:
                    AuxV |= Values[abs(S[j]) % Size]
              else:
                Aio.printError(f"Unknown operation '{S[0]}'")
              #try:
              #  AuxV = AuxV.to_anf()
              #except:
              #  pass
              V ^= AuxV
          else:
            V ^= Values[S]
        if i in InjectionAtBit:
          V ^= Injector
        NewValues.append(V)
        #print(NewValues)
      #for i in range(len(NewValues)):
      #  try:
      #    NewValues[i] = NewValues[i].to_anf()
      #  except:
      #    pass
      Values = NewValues
      if ReturnAllResults:
        AllResults.append(Values)
    if ReturnAllResults:
      return AllResults
    else:
      return Values
  
  def simulateFastANF(self, ANFSpace : FastANFSpace, SequenceOfSymbols = 1, InjectionAtBit = 0, StartFrom = None, ReturnAllResults = 0) -> list:
    AllResults = []
    Dict = self.getDestinationsDictionary()
    Size = self._size
    if Aio.isType(SequenceOfSymbols, 0):
      Len = SequenceOfSymbols
      SequenceOfSymbols = []
      for i in range(Len):
        SequenceOfSymbols.append(ANFSpace.getVariableByIndex(i % len(ANFSpace._Variables)))
    if Aio.isType(InjectionAtBit, 0):
      InjectionAtBit = [InjectionAtBit]
    if StartFrom is None:
      Values = [ANFSpace.createExpression() for i in range(Size)]
    else:
      if Aio.isType(StartFrom, []) and len(StartFrom) == Size:
        Values = []
        for V in StartFrom:
          if not Aio.isType(V, "FastANFExpression"):
            AV = ANFSpace.createExpression()
            AV.addMonomial(ANFSpace.getMonomial(V))
            Values.append(AV)
          else:
            Values.append(V)
      else:
        Aio.printError(f"StartFrom must be a list of size {Size}.")
    for Step in range(len(SequenceOfSymbols)):
      Injector = ANFSpace.createExpression()
      Injector.addMonomial(ANFSpace.getMonomial(SequenceOfSymbols[Step]))
      NewValues = []
      for i in range(Size):
        Sources = Dict[i]
        V = Values[Sources[0]]
        for Si in range(1, len(Sources)):
          S = Sources[Si]
          if type(S) is list:
            if len(S) == 1:
              V ^= Values[S[0]]
            else:
              if S[1] < 0:
                AuxV = ~Values[abs(S[1]) % Size]
              else:
                AuxV = Values[abs(S[1]) % Size]
              if S[0] == 'AND':
                for j in range(2, len(S)):
                  if S[j] < 0:
                    AuxV ^= ~Values[abs(S[j]) % Size]
                  else:
                    AuxV &= Values[abs(S[j]) % Size]
              elif S[0] == 'OR':
                for j in range(2, len(S)):
                  if S[j] < 0:
                    AuxV ^= ~Values[abs(S[j]) % Size]
                  else:
                    AuxV |= Values[abs(S[j]) % Size]
              else:
                Aio.printError(f"Unknown operation '{S[0]}'")
            V ^= AuxV
          else:
            V ^= Values[S]
        if i in InjectionAtBit:
          V ^= Injector
        NewValues.append(V)
      Values = NewValues
      if ReturnAllResults:
        AllResults.append(Values)
    if ReturnAllResults:
      return AllResults
    else:
      return Values
    
  
  def createPhaseShifter(self):
    """Use 'createExpander' instead. It will return a PhaseSHifter object too."""
    Aio.printError("""Use 'createExpander' instead. It will return a PhaseSHifter object too.""")
  
  def _getSequence(SingleSequences, XorToTest, Inverters = None) -> bitarray:
    if type(SingleSequences) is BufferedList:
      ThisSequence = SingleSequences[XorToTest[0]]
    else:
      ThisSequence = SingleSequences[XorToTest[0]].copy()
    if Inverters is not None and Inverters[0]:
      ThisSequence.invert()
    for i in range(1, len(XorToTest)):
      if Inverters is not None and Inverters[i]:
        ThisSequence ^= ~SingleSequences[XorToTest[i]]
      else:
        ThisSequence ^= SingleSequences[XorToTest[i]]
    return ThisSequence
  
  def _countHashes(SingleSequences, XorsList, HBlockSize, Parallel=True, INum="?", InversionInsensitive = False):
    def _seqIterator(XorsList):
      for XorToTest in XorsList:
        yield (XorToTest, Nlfsr._getSequence(SingleSequences, XorToTest))
    #if InversionInsensitive:
    #  def _getHash(Comb):
    #    return [Comb[0], RotationInsensitiveSignature(Comb[1], HBlockSize, InversionInsensitive)]
    #else:
    def _getHash(Comb):
      return [Comb[0], Bitarray.getRotationInsensitiveSignature(Comb[1], HBlockSize)]
    if Parallel:
      Result = p_umap(_getHash, _seqIterator(XorsList), desc=f"{INum}-in: Signatures computation", total=len(XorsList))
      AioShell.removeLastLine()
    else:
      Result = []
      for XorToTest in XorsList:
        Result.append(_getHash(XorToTest))
    return Result
  
  def _countcardinality(SingleSequences, XorsList, TupleSize, ParallelChunk, INum="?"):
    Result = []
    def _seqIterator(XorsList):
      for XorToTest in XorsList:
        yield Nlfsr._getSequence(SingleSequences, XorToTest)
    for XL in tqdm(List.splitIntoSublists(XorsList, ParallelChunk), desc=f"{INum}-in: Tuples cardinality (x{ParallelChunk})"):
      Result += p_map(partial(Bitarray.getCardinality, TupleSize=TupleSize), _seqIterator(XL), total=len(XL))
      AioShell.removeLastLine()
    AioShell.removeLastLine()
    return Result
  
  def _countlc(SingleSequences, XorsList, ParallelChunk, INum="?"):
    Result = []
    def _seqIterator(XorsList):
      for XorToTest in XorsList:
        yield Nlfsr._getSequence(SingleSequences, XorToTest)
    for XL in tqdm(List.splitIntoSublists(XorsList, ParallelChunk), desc=f"{INum}-in: Linear complexity (x{ParallelChunk})"):
      Result += p_map(partial(Polynomial.getLinearComplexityUsingBerlekampMassey, LinearComplexityUpTo=(1<<21)), _seqIterator(XL), total=len(XL))
      AioShell.removeLastLine()
    AioShell.removeLastLine()
    return Result
        
  def isHybrid(self) -> bool:
    n2 = self.copy()
    return (not n2.toFibonacci())
  
  def createExpander(self, NumberOfUniqueSequences = 0, XorInputsLimit = 0, MinXorInputs = 1, StoreLinearComplexityData = False, StoreCardinalityData = False, Store2bitTuplesHistograms = False, StoreOnesCount = False, PBar = 1, LimitedNTuples = 0, AlwaysCleanFiles = False, ReturnAlsoTuplesReport = False, StoreOnesCountB0 = False, UseAlsoInvertedFFs = False, InversionInsensitive = False, SimpleExpanderAllowed = False):
    tt = TempTranscript(f"Nlfsr({self._size}).createExpander()")
    tt.print(repr(self))
    tt.print("Simulating NLFSR...")
    Size = self._size
    MaxK = Size
    if Size >= XorInputsLimit > 0:
      MaxK = XorInputsLimit
    MinK = 1
    if MaxK >= MinXorInputs > 0:
      MinK = MinXorInputs
    SequenceLength = self.getPeriod()
    XorsList = []
    UniqueSequences = set()
    if StoreLinearComplexityData:
      LCData = []
      if Size < 13:
        MaxParallelJobs = int(Aio.getCpuCount() * 3 / 4)
      elif Size < 17:
        MaxParallelJobs = int(Aio.getCpuCount() * 2 / 3)
      elif Size < 19:
        MaxParallelJobs = int(Aio.getCpuCount() / 2)
      elif Size < 21:
        MaxParallelJobs = int(Aio.getCpuCount() / 3)
      elif Size < 22:
        MaxParallelJobs = int(Aio.getCpuCount() / 4)
      if MaxParallelJobs < 1:
        MaxParallelJobs = 1
    if StoreCardinalityData:
      SSData = []
      if Size <= 23:
        CardinalityParallelChunk = int(Aio.getCpuCount() * 3 / 4)
      elif Size <= 27:
        CardinalityParallelChunk = int(Aio.getCpuCount() * 2 / 3)
      elif Size <= 30:
        CardinalityParallelChunk = int(Aio.getCpuCount() / 2)
      elif Size <= 32:
        CardinalityParallelChunk = int(Aio.getCpuCount() / 3)
      else:
        CardinalityParallelChunk = int(Aio.getCpuCount() / 4)
      if CardinalityParallelChunk < 1:
        CardinalityParallelChunk = 1
    if Store2bitTuplesHistograms:
      Histo2 = []
    if StoreOnesCount:
      OnesCount = []
    if UseAlsoInvertedFFs:
      Size *= 2
    if type(self) is Nlfsr and 13 < Size <= 64 :
      print("// Obtaining sequences (fast method)...")
      SingleSequences = self.getSequencesCpp64b()
      AioShell.removeLastLine()
      if SingleSequences is None:
        print("// Obtaining sequences standard way...")
        SingleSequences = BufferedList(self.getSequences(Length=SequenceLength, ProgressBar=False))
        AioShell.removeLastLine()
        AioShell.removeLastLine()
    else:
      print("// Obtaining sequences...")
      SingleSequences = self.getSequences(Length=SequenceLength, ProgressBar=False)
      AioShell.removeLastLine()
    if type(SingleSequences) is BufferedList:
      SingleSequences.SaveData = True
    if StoreOnesCountB0:
      OnesCountB0 = SingleSequences[0].count(1)
    if UseAlsoInvertedFFs:
      for i in range(self._size):
        SingleSequences.append(~SingleSequences[i])
    if ReturnAlsoTuplesReport:
      r = TuplesReport(SingleSequences[0])
    k = MinK
    MyFlopIndexes = [i for i in range(Size)]
    HBlockSize = (self._size - 4)
    if HBlockSize < 3:
      HBlockSize = 3
    while (1 if NumberOfUniqueSequences <= 0 else len(XorsList) < NumberOfUniqueSequences) and (k <= MaxK):
      tt.print(f"{k}-in gates anaysis...")
      SimpleExpander = None
      if UseAlsoInvertedFFs:
        SimpleExpander = None
      elif SimpleExpanderAllowed:
        print("// Creating simple expander...")
        SimpleExpander = self.createSimpleExpander(k, k)    
        AioShell.removeLastLine()
      if SimpleExpander is None:
        HashTable = Nlfsr._countHashes(SingleSequences, List.getCombinations(MyFlopIndexes, k), HBlockSize, PBar, INum=k, InversionInsensitive=InversionInsensitive)
      else:
        HashTable = Nlfsr._countHashes(SingleSequences, SimpleExpander.getXors(), HBlockSize, PBar, INum=k, InversionInsensitive=InversionInsensitive)
      UniqueSequencesK = []
      for Row in tqdm(HashTable, desc=f"Processing {k}-in xor outputs"):
        XorToTest = Row[0]
        H = Row[1]
        if H not in UniqueSequences:
          UniqueSequences.add(H)
          UniqueSequencesK.append(XorToTest)
          ttrow = f"  {len(UniqueSequences)} \t {XorToTest}"
          ThisSequence = None
          XorsList.append(list(XorToTest))
        #  if StoreLinearComplexityData:
        #    if ThisSequence is None:
        #      ThisSequence = Nlfsr._getSequence(SingleSequences, XorToTest)
        #    Aux = Polynomial.getLinearComplexityUsingBerlekampMassey(ThisSequence)
        #    ttrow += f" \t LC = {Aux}"
        #    LCData.append(Aux)
        #  if StoreCardinalityData:
        #    if not (LimitedNTuples and (k > 2)):
        #      if ThisSequence is None:
        #        ThisSequence = Nlfsr._getSequence(SingleSequences, XorToTest)
        #      Aux = Bitarray.getCardinality(ThisSequence, self._size)
        #      ttrow += f" \t #Tuples = {Aux}"
        #      SSData.append(Aux)
        #    else:
        #      SSData.append(-1)
          if StoreOnesCount:
            if ThisSequence is None:
              ThisSequence = Nlfsr._getSequence(SingleSequences, XorToTest)
            Aux = ThisSequence.count(1)
            ttrow += f" \t #1s = {Aux}"
            OnesCount.append(Aux)
          if Store2bitTuplesHistograms:
            if ThisSequence is None:
              ThisSequence = Nlfsr._getSequence(SingleSequences, XorToTest)
            Aux = Bitarray.getTuplesHistogram(ThisSequence, 2)
            ttrow += f" \t #2bHist : {Aux}"
            Histo2.append(Aux)
          #print(f"Added {XorToTest}")
          tt.print(ttrow)
          if len(XorsList) == NumberOfUniqueSequences > 0:
            break
      AioShell.removeLastLine()
      if StoreCardinalityData:
        if not (LimitedNTuples and (k > 2)):
          SSData += Nlfsr._countcardinality(SingleSequences, UniqueSequencesK, self._size, CardinalityParallelChunk, str(k))
        else:
          SSData += [-1 for _ in range(len(UniqueSequencesK))]
      if StoreLinearComplexityData:
        LCData += Nlfsr._countlc(SingleSequences, UniqueSequencesK, MaxParallelJobs, str(k))
      k += 1
    if len(XorsList) < NumberOfUniqueSequences > 0:
      Aio.printError(f"Cannot found {NumberOfUniqueSequences} unique sequences. Only {len(XorsList)} was found.")
    elif len(XorsList) > NumberOfUniqueSequences > 0:
      XorsList = XorsList[:NumberOfUniqueSequences]
    PS = PhaseShifter(self, XorsList)
    if StoreLinearComplexityData:
      PS.LinearComplexity = LCData
    if StoreCardinalityData:
      PS.SeqStats = SSData
    if Store2bitTuplesHistograms:
      PS.Histo2 = Histo2
    if StoreOnesCount:
      PS.OnesCount = OnesCount
    if ReturnAlsoTuplesReport:
      PS.TuplesRep = r
    if StoreOnesCountB0:
      PS.OnesCountB0 = OnesCountB0
    if type(SingleSequences) is BufferedList:
      if AlwaysCleanFiles:
        SingleSequences.SaveData = False
        SingleSequences.clear()
        shutil.rmtree(SingleSequences.getDirPath())
        del SingleSequences
    tt.close()
    return PS
  
  def toArticleString(self) -> str:
    Result = ""
    TSecond = 0
    for Tap in self._Config:
      TapS = f"({'-' if Tap[0]<0 else ''}{abs(Tap[0]) % self._size}: "
      Second = 0
      for Si in Tap[1]:
        if Second:
          TapS += ", "
        else:
          Second = 1
        TapS += f"{'-' if Si<0 else ''}{abs(Si) % self._size}"
      TapS += ")"
      if TSecond:
        Result += ", "
      else:
        TSecond = 1
      Result += TapS
    return Result
  
  def getRelationBetweenSelectedTapAndOthers(self, TapIndex):
    Destinations = self.getTapsDestinations(TapIndex)
    Destinations.sort()
    Sources = self.getTapsSources(TapIndex)
    Sources.sort()
    TapSources = self.getSingleTapSources(TapIndex)
    TapDestination = abs(self._Config[TapIndex][0]) % self._size
    Result = []
    EqualTo = -1
    for S in Sources:
      if S == TapDestination:
        EqualTo = S
        break
    Result.append(EqualTo)
    for S in TapSources:
      EqualTo = -1
      for D in Destinations:
        if S == D:
          EqualTo = D
          break
      Result.append(EqualTo)
    return tuple(Result)
  
  def getCriticalPlacementReport(self, TapIndex : int, Sign : int) -> list:
    TapX = self._Config[TapIndex].copy()
    Sources = self.getTapsSources(TapIndex)
    Destinations = self.getTapsDestinations(TapIndex)
    D = abs(TapX[0]) % self._size
    if Sign > 0:
      if D == (self._size - 1):
        D -= self._size
      Tap = [D, []]
      for Si in TapX[1]:
        Si = abs(Si) % self._size
        Tap[1].append(Si)
      if (D + 1) in Sources:
        Tap[0] = True
      else:
        Tap[0] = False
      for i in range(len(Tap[1])):
        Si = Tap[1][i]
        if Si in Destinations:
          Tap[1][i] = True
        else:
          Tap[1][i] = False
    else:
      Tap = [D, []]
      for Si in TapX[1]:
        Si = abs(Si) % self._size
        Tap[1].append(Si)
      if (D) in Sources:
        Tap[0] = True
      else:
        Tap[0] = False
      for i in range(len(Destinations)):
        if Destinations[i] == (self._size - 1):
          Destinations[i] -= self._size
        Destinations[i] += 1
      for i in range(len(Tap[1])):
        Si = Tap[1][i]
        if Si in Destinations:
          Tap[1][i] = True
        else:
          Tap[1][i] = False            
    return Tap
    
          
  def rotateTap(self, TapIndex : int, FFs : int, FailIfRotationInvalid = False, SortTaps = True, LeaveMaximumShift = False) -> bool:
    if FailIfRotationInvalid:
      n2 = self.copy()
      LeaveMaximumShift = 0
      Sign = -1 if FFs < 0 else 1
      for i in range(abs(FFs)):
        PRep = n2.getCriticalPlacementReport(TapIndex, Sign)
        if not (PRep[0] or True in PRep[1]):
          n2.rotateTap(TapIndex, Sign, FailIfRotationInvalid=0, SortTaps=0)
        elif not LeaveMaximumShift:
          return False
      self._Config = n2._Config.copy()
      if SortTaps:
        self.sortTaps()
      self._period = None
      return True  
    else:
      if 0 <= TapIndex < len(self._Config):
        Size = self._size
        Tap = self._Config[TapIndex]
        S = Tap[1]
        D = Tap[0]
        DSig = 1 if (D >= 0) else -1
        D = abs(D)
        D += FFs
        while D >= Size:
          D -= Size
        while D < 0:
          D += Size
        if (DSig < 0) and (D == 0):
          D += Size
        D *= DSig
        if Aio.isType(S, 0):
          S += FFs
          SSig = 1 if (S >= 0) else -1
          S = abs(S)
          while S >= Size:
            S -= Size
          while S < 0:
            S += Size
          if (SSig < 0) and (S == 0):
            S += Size
          S *= SSig
        else:
          NewS = []
          for Si in S:
            SSig = 1 if (Si >= 0) else -1
            Si = abs(Si)
            Si += FFs
            while Si >= Size:
              Si -= Size
            while Si < 0:
              Si += Size
            if (SSig < 0) and (Si == 0):
              Si += Size
            Si *= SSig
            NewS.append(Si)
          S = NewS
        Tap = [D, S]
        self._Config[TapIndex] = Tap
        self._period = None
        if SortTaps:
          self.sortTaps()
        self._period = None
        return True
    return False
  
  def getDraw(self, MaxWidth = 0, Overlap = 3) -> str:
    Uffs = self._size >> 1
    Lffs = self._size - Uffs
    Uoffset = 3
    xext = 3
    if Lffs > Uffs:
      Uoffset = 3
      xext = 0
    Taps = self._Config
    Size = self._size
    Space = len(Taps) * 2 - 1
    HExt = 3
    while 1:
      try:
        Canvas = AsciiDrawingCanvas(Lffs*6+2 +xext +HExt, 10 + Space) # 9
        Canvas.drawBox(0, 1, Canvas._width-1-HExt, 7+Space)
        Canvas.drawChar(1, 8+Space, AsciiDrawing_Characters.RIGHT_ARROW)
        Canvas.drawChar(Canvas._width-2-HExt, 1, AsciiDrawing_Characters.LEFT_ARROW)
        for i in range(Lffs):
          ffindex = Lffs - i - 1
          Canvas.drawBox(i*6+2, 7+Space, 3, 2, str(ffindex))
          Canvas.fixLinesAtPoint(i*6+2, 8+Space)
          Canvas.fixLinesAtPoint(i*6+5, 8+Space)
        for i in range(Uffs):
          ffindex = Lffs + i
          Canvas.drawBox(i*6+2+Uoffset, 0, 3, 2, str(ffindex))
          Canvas.fixLinesAtPoint(i*6+2+Uoffset, 1)
          Canvas.fixLinesAtPoint(i*6+5+Uoffset, 1)
        AndGateYPosition = 4+Space
        AndGateXPositionsUsed = []
        TapsCoordinates = []
        PointsToFix = []
        for Tap in Taps:
          D = abs(Tap[0]) % Size
          DInv = 1 if Tap[0] < 0 else 0
          XorDown = 1        
          if D >= Lffs:
            XorDown = 0
          if XorDown:
            XorX = (Lffs-D-1)*6+1
            XorY = 8+Space
          else:
            XorX = (D-Lffs+1)*6+Uoffset
            XorY = 1
          AndGateXPosition = XorX
          TheSameD = 0
          XPosAdder = 4
          XPosAdd = 1
          AndGateXPositionSaved = AndGateXPosition
          while AndGateXPosition in AndGateXPositionsUsed:
            WhatToAdd = 0
            if XorDown:
              if XPosAdd:
                WhatToAdd = XPosAdder
                XPosAdd = 0
              else:
                if WhatToAdd - XPosAdder <= 0:
                  XPosAdder += 4
                  WhatToAdd = XPosAdder
                else:
                  WhatToAdd = -XPosAdder
                  XPosAdder += 4
                XPosAdd = 1
            else:
              if XPosAdd:
                WhatToAdd = -XPosAdder
                XPosAdd = 0
              else:
                if WhatToAdd + XPosAdder >= Canvas._width -1:
                  XPosAdder += 4
                  WhatToAdd = -XPosAdder
                else:
                  WhatToAdd = XPosAdder
                  XPosAdder += 4
                XPosAdd = 1
            AndGateXPosition = AndGateXPositionSaved + WhatToAdd
            TheSameD = 1
          AndGateXPositionsUsed.append(AndGateXPosition)
          Ss = Tap[1]
          SsXY = []
          if Aio.isType(Ss, 0):
            Ss = [Ss]
          for S in Ss:
            SInv = 1 if S < 0 else 0
            S = abs(S) % Size
            SDown = 1
            if S >= Lffs:
              SDown = 0
            if SDown:
              Sx = (Lffs-S-1)*6+1+5
              Sy = 8+Space
            else:
              Sx = (S-Lffs+1)*6+Uoffset-5
              Sy = 1
            SsXY.append([Sx, Sy])
          TapsCoordinates.append([XorDown, XorX, XorY, AndGateXPosition, AndGateYPosition, TheSameD, SsXY])
          AndGateYPosition -= 2
        for TC in TapsCoordinates:
          XorDown = TC[0]
          AndGateXPosition = TC[3]
          AndGateYPosition = TC[4]
          TheSameD = TC[5]
          SsXY = TC[6]
          for Sxy in SsXY:
            Sx = Sxy[0]
            Sy = Sxy[1]
            Canvas.drawConnectorVH(Sx, Sy, AndGateXPosition, AndGateYPosition)
            Canvas.fixLinesAtPoint(Sx, AndGateYPosition)
            PointsToFix.append([Sx, AndGateYPosition])
        for ptf in reversed(PointsToFix):
          Canvas.fixLinesAtPoint(ptf[0], ptf[1])
        i1, i0 = 0,0
        for TC in TapsCoordinates:
          XorDown = TC[0]
          XorX = TC[1]
          XorY = TC[2]
          AndGateXPosition = TC[3]
          AndGateYPosition = TC[4]
          for X in range(AndGateXPosition-1, 0, -1):
            if Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.HORIZONTAL:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_BOLD)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.HORIZONTAL_UP:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THICK_HORIZONTAL_THIN_UP)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.HORIZONTAL_DOWN:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THICK_HORIZONTAL_THIN_DOWN)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.CROSS:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THICK_HORIZONTAL_THIN_UP_DOWN)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.VERTICAL_RIGTH:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THIN_VERTICAL_THICK_RIGTH)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.LOWER_LEFT:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_THICK_LOWER_LEFT)
              break
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.UPPER_LEFT:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_THICK_UPPER_LEFT)
              break
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.VERTICAL:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_BOLD)
            else:
              break
          for X in range(AndGateXPosition+1, Canvas._width-1, 1):
            if Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.HORIZONTAL:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_BOLD)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.HORIZONTAL_UP:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THICK_HORIZONTAL_THIN_UP)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.HORIZONTAL_DOWN:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THICK_HORIZONTAL_THIN_DOWN)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.CROSS:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THICK_HORIZONTAL_THIN_UP_DOWN)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.VERTICAL_LEFT:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.THIN_VERTICAL_THICK_LEFT)
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.LOWER_RIGHT:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_THICK_LOWER_RIGHT)
              break
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.UPPER_RIGHT:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_THICK_UPPER_RIGHT)
              break
            elif Canvas.getChar(X, AndGateYPosition) == AsciiDrawing_Characters.VERTICAL:
              Canvas.setChar(X, AndGateYPosition, AsciiDrawing_Characters.HORIZONTAL_BOLD)
            else:
              break
        for TC in TapsCoordinates:
          XorDown = TC[0]
          XorX = TC[1]
          XorY = TC[2]
          AndGateXPosition = TC[3]
          AndGateYPosition = TC[4]
          TheSameD = TC[5]
          if TheSameD:
            if XorDown:
              Canvas.drawConnectorHH(XorX, XorY-2, AndGateXPosition, XorY-2)
              Canvas.drawConnectorVV(AndGateXPosition, XorY-2, AndGateXPosition, AndGateYPosition)
              FixY = XorY-2
            else:
              Canvas.drawConnectorHH(XorX, XorY+2, AndGateXPosition, XorY+2)
              Canvas.drawConnectorVV(AndGateXPosition, XorY+2, AndGateXPosition, AndGateYPosition)
              FixY = XorY+2
            if XorX < AndGateXPosition:
              for X in range(XorX+1,AndGateXPosition,1):
                Canvas.fixLinesAtPoint(X, FixY)
            else:
              for X in range(XorX-1,AndGateXPosition,-1):
                Canvas.fixLinesAtPoint(X, FixY)          
          else:
            Canvas.drawConnectorVV(XorX, XorY, AndGateXPosition, AndGateYPosition)
          Canvas.drawChar(AndGateXPosition-1, AndGateYPosition, "F")
          Canvas.drawChar(AndGateXPosition, AndGateYPosition, str(i1))
          Canvas.drawChar(AndGateXPosition+1, AndGateYPosition, str(i0))
          i0 += 1
          if i0 == 10:
            i1 += 1
            i0 = 0
          if i1 == 10:
            i1 = 0
        for TC in TapsCoordinates:
          XorDown = TC[0]
          XorX = TC[1]
          XorY = TC[2]
          AndGateXPosition = TC[3]
          AndGateYPosition = TC[4]
          Canvas.drawXor(XorX, XorY)
          if XorDown:
            Canvas.drawChar(XorX, XorY-1, AsciiDrawing_Characters.DOWN_ARROW)
          else:
            Canvas.drawChar(XorX, XorY+1, AsciiDrawing_Characters.UP_ARROW)
        return Canvas.toStr(MaxWidth, Overlap)
      except:
        if HExt > 128:
          return ""
        HExt += 3
  
  def toFibonacci(self, WithValidation=True) -> bool:
    Size = self._size
    if WithValidation:
      Aux = self.copy()
      AllDone = False   
      LastFF = Size-1
      while not AllDone:
        Moved = False   
        AllDone = True
        for i in range(len(Aux._Config)):
          D = abs(Aux._Config[i][0]) % Size
          if D < LastFF:
            AllDone = False
            if Aux.rotateTap(i, 1, True, False):
              Moved = True
        if (not AllDone) and (not Moved):
          return False
      self._Config = Aux._Config
      self.sortTaps()
    else:
      for i in range(len(self._Config)):
        D = abs(self._Config[i][0]) % Size
        self.rotateTap(i, Size-1-D, SortTaps=0)
      self.sortTaps()
    self._period = None
    return True
  
  def getTapBounds(self, TapIndex : int) -> tuple:
    Size = self._size
    Tap = self._Config[TapIndex]
    Sources = Tap[1].copy()
    Sources.sort(key = lambda x: (abs(x) % self._size))
    Min, Max =  (abs(Sources[0]) % Size), (abs(Sources[-1]) % Size)
    if Min == 0:
      return Max, Size
    return Min, Max
    
  def sortTaps(self):
    NC = []
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      if Aio.isType(S, 0):
        S = [S]
      if len(S) == 1:
        if S[0]<0 and D<0:
          S[0] = abs(S[0])
          D = abs(D)
      NS = []
      for Si in S:
        if Si < 0:
          NS.append(Si)
        else:
          NS.append(Si % self._size)
      NS.sort(key = lambda x: (abs(x) % self._size))
      NC.append([D, NS])
      self._Config = NC
    ConfDict = {}
    for Tap in self._Config:
      S = tuple(Tap[1])
      D = Tap[0]
      Tap = tuple([D, S])
      ConfDict[Tap] = ConfDict.get(Tap, 0) + 1
    Config = []
    for Item in ConfDict.items():
      if Item[1] & 1:
        S = list(Item[0][1])
        D = Item[0][0]
        Config.append([D, S])
    self._Config = Config
    self._Config.sort(key = lambda x: (abs(x[0]) % self._size))
  
  def isPlanar(self):
    self.sortTaps()
    LastMin = self._size
    for i in range(len(self._Config)):
      Min, Max = self.getTapBounds(i)
      if Max > LastMin:
        return False
      LastMin = Min
    return True
    
  
  def toPlanar(self, FanoutAllowed = False, Only2inXors = False) -> bool:
    Size = self._size
    Copy = self.copy()
    FanOut = 1 if FanoutAllowed else 0
    LastMin = Size + FanOut
    LastD = -1
    for i in range(len(Copy._Config)):
      Min, Max = Copy.getTapBounds(i)
      #print(Min, Max, "  ", LastMin)
      Copy.rotateTap(i, LastMin - Max - FanOut)
      #print(i, "---------------------")
      #print(Copy.getArchitecture())
      Min, Max = Copy.getTapBounds(i)
      LastMin = Min
      D = (abs(Copy._Config[i][0]) % Size)
      if Only2inXors:
        if D <= LastD:
          return False
      else:
        if D < LastD:
          return False
      LastD = D
    if Copy.isPlanar():
      self._Config = Copy._Config
      return True
    return False
        
  def isTapLinear(self, TapIndex : int) -> bool:
    try:
      S = self._Config[TapIndex][1]
      if Aio.isType(S, 0):
        return True
      elif len(S) == 1:
        return True
    except:
      Aio.printError(f"TapIndex {TapIndex} out of range")
    return False
    
  def getLinearTapIndexes(self):
    Result = []
    for i in range(len(self._Config)):
      if self.isTapLinear(i):
        Result.append(i)
    return Result

  def getTapsForBreaking(self, TapIndex : int, ExpressionTemplate : str, SecondaryInputsList = []) -> list:
    NewTapsTemplate = _to_taps_templates(ExpressionTemplate)
    Size = self._size
    D = self._Config[TapIndex][0]
    S = self._Config[TapIndex][1]
    if Aio.isType(S, []):
      S = S[0]
    Dinv = 1
    if D < 0 and S < 0:
      Dinv = 1
    elif D < 0 or S < 0:
      Dinv = -1
    D = abs(D) % Size
    S = abs(S) % Size
    while D == 0:
      D = Size
    Inputs = [None, S] + SecondaryInputsList
    NewTaps = []
    for TapTemplate in NewTapsTemplate:
      DestSign = TapTemplate[0]
      Ss = []
      for TI in TapTemplate[1]:
        i = abs(TI)
        sign = -1 if TI < 0 else 1
        Si = Inputs[i]
        while Si <= 0:
          Si += Size
        while Si > Size:
          Si -= Size
        Si *= sign
        Ss.append(Si)
      NewTap = [Dinv * DestSign * D, Ss]
      Dinv = 1
      NewTaps.append(NewTap)
    return NewTaps

  def breakLinearTap(self, TapIndex : int, ExpressionTemplate : str, SecondaryInputsList = [], SortTaps = True) -> bool:
    if not self.isTapLinear(TapIndex):
      Aio.printError(f"Tap '{TapIndex}' is not linear.")
      return False
    try:
      NewTaps = self.getTapsForBreaking(TapIndex, ExpressionTemplate, SecondaryInputsList)
      self._Config.remove(self._Config[TapIndex])
      self._Config += NewTaps
      if SortTaps:
        self.sortTaps()
      self._period = None
      return True
    except:
      return False
    
  def isLfsr(self) -> bool:
    Taps = self._Config
    for Tap in Taps:
      S = Tap[1]
      if Aio.isType(Tap, []):
        if len(S) > 1:
          return False
    return True
  
  def isSemiLfsr(self) -> bool:
    return SymPy.isANFLinear(self.toBooleanExpressionFromRing(ReturnSympyExpr=1))
  
  def toVerilog(self, ModuleName : str, InjectorIndexesList = []) -> str:
    Module = \
f'''module {ModuleName} (
  input wire clk,
  input wire enable,
  input wire reset,
'''
    if len(InjectorIndexesList) > 0:
      Module += f"  input wire [{len(InjectorIndexesList)-1}:0] injectors,\n"
    Module += \
f'''  output reg [{self.getSize()-1}:0] O
);

'''
    Sources = []
    Size = self._size
    for i in range(Size):
      Sources.append(f'O[{(i+1) % Size}]')
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      if Aio.isType(S, 0):
        S = [S]
      MainInv = (D < 0)
      D = abs(D) % Size
      Expr = "("
      Second = 0
      for Si in S:
        if Second:
          Expr += " & "
        else:
          Second = 1
        if (Si < 0):
          Expr += "~"
        Expr += f"O[{abs(Si) % Size}]"
      Expr += ")"
      if MainInv:
        Expr = f"~{Expr}"
      Sources[D] += f" ^ {Expr}"
    for i in range(len(InjectorIndexesList)):
      Sources[InjectorIndexesList[i]] += f" ^ injectors[{i}]"
    ResetValue = 0
    if len(InjectorIndexesList) <= 0:
      ResetValue = 1
    Module += \
f'''always @ (posedge clk or posedge reset) begin
  if (reset) begin
    O <= {self.getSize()}'d{ResetValue};
  end else begin
    if (enable) begin
'''
    for i in range(len(Sources)):
      Module += f'      O[{i}] <= {Sources[i]};\n'
    Module += \
f'''    end
  end
end
    
endmodule'''
    return Module
  
  def tui(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    global _NLFSR, _NLFSR_UNDO
    _NLFSR = self.copy()
    _NLFSR_UNDO = None
    while 1:
      tui = _NlfsrTui()
      tui.run()
      sleep(0.2)
      if tui.EXE == "ok":
        _NLFSR.sortTaps()
        return _NLFSR
      elif tui.EXE == "seq":
        #_NLFSR.sortTaps()
        sleep(0.2)
        _NLFSR.analyseSequences(1, 1).tui(_NLFSR)
        sleep(0.5)
      elif tui.EXE == "exp":
        #_NLFSR.sortTaps()
        sleep(0.2)
        PS = _NLFSR.createExpander(XorInputsLimit=3, StoreCardinalityData=1, StoreLinearComplexityData= (1 if _NLFSR._size < 13 else 0), StoreOnesCount=1)
        PS.tui()
        sleep(0.5)
      elif tui.EXE == "break_tap":
        BTapTui = _BreakNlfsrTapTui()
        BTapTui.OBJ = _NLFSR.copy()
        BTapTui.TAP_INDEX = tui.TAP_INDEX
        BTapTui.run()  
        sleep(0.2)
        if BTapTui.EXE == "ok":
          TapIndex = BTapTui.TAP_INDEX
          Expression = BTapTui.EXPR
          Vars = [BTapTui.VARB, BTapTui.VARC]
          if len(Expression) > 0 and len(Vars) > 0:
            _NLFSR_UNDO = _NLFSR.copy()
            _NLFSR.breakLinearTap(TapIndex, Expression, Vars)
      else:
        break
    return None
        
  def checkMaximum(NlfsrsList : list) -> list:
    return NlfsrList.checkMaximum(NlfsrsList)
  
  
  def parseFromArticleString(Size : int, txt : str) -> Nlfsr:
    txt.strip()
    txt = txt.replace(" ","")
    Taps = []
    for tap in txt.split("),"):
      tap.strip()
      tap = tap.replace("(","")
      tap = tap.replace(")","")
      tapl = tap.split(":")
      Dint = int(tapl[0])
      S = ast.literal_eval(f"[{tapl[1]}]")
      Sint = []
      for Si in S:
        Sint.append(int(Si))
      tapint = [Dint, Sint]
      Taps.append(tapint)
    return Nlfsr(int(Size), Taps)
  fromArticleString = parseFromArticleString
    
  def _getTapFromMonomial(Size : int, Monomial : str) -> list:
    S = []
    Monomial.replace('.', ',')
    Monomial.replace(';', ',')
    for Sstr in Monomial.split(","):
      Si = int(Sstr)
      if Size > Si > 0:
        S.append(Si)
    if len(S) < 1:
      return None
    return [Size-1, S]
  
  def parseFromANF(Size : int, anf : str) -> Nlfsr:
    anf.strip()
    anf.replace(' ','')
    anf.replace('\t','')
    Par = 0
    Monomial = ""
    Taps = []
    for Char in anf:
      if Char in '{[(':
        Par += 1
      elif Char in ')]}':
        Par -= 1
      elif Par == 0 and Char in ',.;':
        Tap = Nlfsr._getTapFromMonomial(Size, Monomial)
        if Tap is not None:
          #print(Monomial, Tap)
          Taps.append(Tap)
        Monomial = ""
      else:
        Monomial += (Char)
    Tap = Nlfsr._getTapFromMonomial(Size, Monomial)
    if Tap is not None:
      #print(Monomial, Tap)
      Taps.append(Tap)
    return Nlfsr(Size, Taps)  
  fromANF = parseFromANF
  
  @staticmethod
  def listSystematicNlrgs(Size, OnlyMaximumPeriod = True, OnlyPrimeNonMaximumPeriods = True, AllowMaximumPeriods = True, MinimumPeriodRatio = 0.95, n : int = 0, MaxSearchingTimeMin = 0) -> list:
    if Size < 2:
      Aio.printError("Nlfsr.listSystematicNlrgs() can only search for Size >= 2.")
      return []
    MaxCoeffs = (Size // 2) + 2
    MaxPeriod = (1 << Size) - 1
    Result = []
    T0 = time.time()
    TT = TempTranscript(f"Nlfsr.listNlfsrs({Size})")
    for Coeffs in range(3, MaxCoeffs +1):
      if Coeffs == MaxCoeffs:
        P0 = Polynomial.createPolynomial(Size, Coeffs, 1)
      else:
        P0 = Polynomial.createPolynomial(Size, Coeffs, 2)
      if P0 is None:
        continue
      for P in P0:
        PartResult = Nlfsr.findNLRGsWithSpecifiedPeriod(P, 2, MinimumPeriodRatio, False, True, 6, True, True, False, 0, 0, False, None)
        PartResultFiltered = []
        for Res in PartResult:
          if Res._period == MaxPeriod:
            if OnlyMaximumPeriod or AllowMaximumPeriods:
              PartResultFiltered.append(Res)
          elif Res._period / MaxPeriod >= MinimumPeriodRatio:
            if OnlyPrimeNonMaximumPeriods:
              if Int.isPrime(Res._period):
                PartResultFiltered.append(Res)
            else:
              PartResultFiltered.append(Res)
        for Res in PartResultFiltered:
          TT.print(repr(Res), "\t", Res._period, "\tPrime:", Int.isPrime(Res._period))
        Result += PartResultFiltered
        if len(PartResultFiltered) > 0:
          Result = NlfsrList.filter(Result)
        STime = round((time.time() - T0) / 60, 2)
        print(f"// Found so far: {len(Result)}, searching time: {STime} min")
        if len(Result) >= n > 0:
          break
        if STime >= MaxSearchingTimeMin > 0:
          break
      if len(Result) >= n > 0:
        break
      if STime >= MaxSearchingTimeMin > 0:
        break
    if len(Result) > n > 0:
      Result = Result[:n]  
    TT.close()      
    return Result        
  
  @staticmethod
  def generateRandomNlrgCandidates(Size : int, n : int, MinTapsCount = 3, MaxTapsCount = 10, MinAndInputsCount = 2, MaxAndInputCount = 3, MinNonlinearTapsRatio = 0.3, MaxNonlinearTapsRatio = 0.6, HybridAllowed = False, UniformTapsDistribution = False, HardcodedInverters = False):
    if HybridAllowed:
      SourceCandidates = [Size] + [i+1 for i in range(Size-1)]
      DestCandidates = [Size] + [i+1 for i in range(Size-1)]
    else:
      LowerBranch = Size//2
      SourceCandidates = [i for i in range(LowerBranch, Size)]
      DestCandidates = [Size] + [i for i in range(1, LowerBranch)]
    if MaxAndInputCount > len(SourceCandidates):
      MaxAndInputCount = len(SourceCandidates)
    for i in range(n):
      NotFound = 1
      while NotFound:
        Taps = []
        TapsCount = random.randint(MinTapsCount, MaxTapsCount)
        NLTapsCount = random.randint(int(round(TapsCount * MinNonlinearTapsRatio, 0)), int(round(TapsCount * MaxNonlinearTapsRatio, 0)))
        if NLTapsCount < 1:
          NLTapsCount = 1
        CandidateIndex = 0
        if UniformTapsDistribution:
          DestDistance = len(DestCandidates) / TapsCount
        else:
          DestDistance = 1
        for _ in range(NLTapsCount):
          AndInCount = random.randint(MinAndInputsCount, MaxAndInputCount)
          SList = List.randomSelect(SourceCandidates, AndInCount)
          for i in range(len(SList)):
            if HardcodedInverters:
              SList[i] *= -1
            elif random.randint(0,1):
              SList[i] *= -1
          D = DestCandidates[int(round(CandidateIndex, 0)) % len(DestCandidates)]
          CandidateIndex += DestDistance        
          if HardcodedInverters:
            D *= -1
          elif random.randint(0,1):
            D *= -1
          Taps.append([D, SList])
        for _ in range(TapsCount - NLTapsCount):
          S = List.randomSelect(SourceCandidates, 1)
          D = DestCandidates[int(round(CandidateIndex, 0)) % len(DestCandidates)]
          CandidateIndex += DestDistance
          if not HardcodedInverters:
            if random.randint(0,1):
              D *= -1
          Taps.append([D, [S]])
        if len(Taps) > 0:
          Candidate = Nlfsr(Size, Taps)
          if HybridAllowed or not Candidate.isSemiLfsr():
            NotFound = 0
      yield Candidate.copy()
  
  
  @staticmethod
  def _listRandomNlrgCandidatesMulti(n : int, Size : int, ProgressBar = False, MinTapsCount = 3, MaxTapsCount = 10, MinAndInputsCount = 2, MaxAndInputCount = 3, MinNonlinearTapsRatio = 0.3, MaxNonlinearTapsRatio = 0.6, HybridAllowed = False, UniformTapsDistribution = False, HardcodedInverters = False) -> list:
    return Nlfsr.listRandomNlrgCandidates(Size, n, ProgressBar, MinTapsCount, MaxTapsCount, MinAndInputsCount, MaxAndInputCount, MinNonlinearTapsRatio, MaxNonlinearTapsRatio, HybridAllowed, UniformTapsDistribution, HardcodedInverters)
    
  @staticmethod
  def listRandomNlrgCandidates(Size : int, n : int, ProgressBar = False, MinTapsCount = 3, MaxTapsCount = 10, MinAndInputsCount = 2, MaxAndInputCount = 3, MinNonlinearTapsRatio = 0.3, MaxNonlinearTapsRatio = 0.6, HybridAllowed = False, UniformTapsDistribution = False, HardcodedInverters = False) -> list:
    Result = []
    SerialChunk = 128
    if ProgressBar and n > (SerialChunk * 2):
      Ns = []
      N = n
      while N > 0:
        if N > SerialChunk:
          Ns.append(SerialChunk)
          N -= SerialChunk
        else:
          Ns.append(N)
          N = 0
      Iter = p_uimap(functools.partial(Nlfsr._listRandomNlrgCandidatesMulti, Size=Size, ProgressBar=False, MinTapsCount=MinTapsCount, MaxTapsCount=MaxTapsCount, MinAndInputsCount=MinAndInputsCount, MaxAndInputCount=MaxAndInputCount, MinNonlinearTapsRatio=MinNonlinearTapsRatio, MaxNonlinearTapsRatio=MaxNonlinearTapsRatio, HybridAllowed=HybridAllowed, UniformTapsDistribution=UniformTapsDistribution, HardcodedInverters=HardcodedInverters), Ns, desc=f"Creating NLFSR candidates (x {SerialChunk})")
      for I in Iter:
        Result += I
      AioShell.removeLastLine()
    else:
      if HybridAllowed:
        SourceCandidates = [Size] + [i+1 for i in range(Size-1)]
        DestCandidates = [Size] + [i+1 for i in range(Size-1)]
      else:
        LowerBranch = Size//2
        SourceCandidates = [i for i in range(LowerBranch, Size)]
        DestCandidates = [Size] + [i for i in range(1, LowerBranch)]
      if MaxAndInputCount > len(SourceCandidates):
        MaxAndInputCount = len(SourceCandidates)
      if ProgressBar:
        Iter = tqdm(range(n), desc="Creating NLFSR candidates")
      else:
        Iter = range(n)
      for i in range(n):
        NotFound = 1
        while NotFound:
          Taps = []
          TapsCount = random.randint(MinTapsCount, MaxTapsCount)
          NLTapsCount = random.randint(int(round(TapsCount * MinNonlinearTapsRatio, 0)), int(round(TapsCount * MaxNonlinearTapsRatio, 0)))
          if NLTapsCount < 1:
            NLTapsCount = 1
          CandidateIndex = 0
          if UniformTapsDistribution:
            DestDistance = len(DestCandidates) / TapsCount
          else:
            DestDistance = 1
          for _ in range(NLTapsCount):
            AndInCount = random.randint(MinAndInputsCount, MaxAndInputCount)
            SList = List.randomSelect(SourceCandidates, AndInCount)
            for i in range(len(SList)):
              if HardcodedInverters:
                SList[i] *= -1
              elif random.randint(0,1):
                SList[i] *= -1
            D = DestCandidates[int(round(CandidateIndex, 0)) % len(DestCandidates)]
            CandidateIndex += DestDistance            
            if HardcodedInverters:
              D *= -1
            elif random.randint(0,1):
              D *= -1
            Taps.append([D, SList])
          for _ in range(TapsCount - NLTapsCount):
            S = List.randomSelect(SourceCandidates, 1)
            D = DestCandidates[int(round(CandidateIndex, 0)) % len(DestCandidates)]
            CandidateIndex += DestDistance
            if not HardcodedInverters:
              if random.randint(0,1):
                D *= -1
            Taps.append([D, [S]])
          if len(Taps) > 0:
            Candidate = Nlfsr(Size, Taps)
            if not Candidate.isSemiLfsr():
              NotFound = 0
        Result.append(Candidate)
    return Result
      
        
  
  @staticmethod
  def listRandomNlrgs(Size : int = None, MinTapsCount = 2, MaxTapsCount = 6, MinAndInputsCount = 2, MaxAndInputCount = 3, MinNonlinearTapsRatio = 0.25, MaxNonlinearTapsRatio = 0.75, HybridAllowed = False, UniformTapsDistribution = False, HardcodedInverters = False, OnlyMaximumPeriod = True, OnlyPrimeNonMaximumPeriods = True, AllowMaximumPeriods = True, MinimumPeriodRatio = 0.95, n : int = 0, MaximumTries = 0, MaxSearchingTimeMin = 0, ReturnAll = False) -> list:
    if Size is None:
      Size = AioShell.inputInt("Size", 12, 3, 64)
      MinTapsCount = AioShell.inputInt("Minimum taps count", 2, 1)
      MaxTapsCount = AioShell.inputInt("Maximum taps count", 6, 1)
      MinAndInputsCount = AioShell.inputInt("Minimum AND input count", 2, 2)
      MaxAndInputCount = AioShell.inputInt("Maximum AND input count", 3, 2)
      MinNonlinearTapsRatio = AioShell.inputFloat("Minimum nonlinear taps ratio", 0.25, 0, 1)
      MaxNonlinearTapsRatio = AioShell.inputFloat("Maximum nonlinear taps ratio", 0.75, 0, 1)
      HybridAllowed = AioShell.inputBool("Hybrids allowed", False)
      UniformTapsDistribution = AioShell.inputBool("Uniform XORs distribution", True)
      HardcodedInverters = AioShell.inputBool("Hardcoded inverters", False)
      OnlyMaximumPeriod = AioShell.inputBool("Only maximum periods", True)
      if not OnlyMaximumPeriod:
        AllowMaximumPeriods = AioShell.inputBool("Allow maximum periods", True)
        OnlyPrimeNonMaximumPeriods = AioShell.inputBool("Only prime non-maximum periods", True)
        MinimumPeriodRatio = AioShell.inputFloat("Minimum period ratio", 0.95, 0, 1)
      n = AioShell.inputInt("Minimum results count", 0, 0)
      MaxSearchingTimeMin = AioShell.inputFloat("Maximum searching time (minutes)", 1, 0.1)
    if Size < 3:
      Aio.printError("Nlfsrs.listRandomNlrgs() can only search for Size >= 3.")
      return []
    if MaxTapsCount < MinTapsCount:
      Aio.printError("MaxTapsCount must be >= MinTapsCount.")
      return []
    if MaxAndInputCount < MinAndInputsCount:
      Aio.printError("MaxAndInputCount must be >= MinAndInputsCount.")
      return []
    if MinTapsCount < 1:
      Aio.printError("MinTapsCount must be > 0.")
      return []
    if MinAndInputsCount < 2:
      Aio.printError("MinAndInputsCount must be > 0.")
      return []
    if MaxNonlinearTapsRatio < MinNonlinearTapsRatio:
      Aio.printError("MaxNonlinearTapsRatio must be >= MinNonlinearTapsRatio.")
      return []
    if MinNonlinearTapsRatio <= 0 or MaxNonlinearTapsRatio > 1:
      Aio.printError("MinNonlinearTapsRatio must be >0 and MaxNonlinearTapsRatio <=1.")
      return []
    Result = []
    ChunkSize = 4096
    for _ in range(0, Size-14, 2):
      ChunkSize //= 2
    if ChunkSize < 48:
      ChunkSize = 48
    TT = TempTranscript(f"Nlfsr.listNlfsrs({Size})")
    T0 = time.time()
    if MaximumTries <= 0:
      MaximumTries = 10000000 * Size
    SecondIter = 0
    for _ in range(MaximumTries):
      PartResult = NlfsrList.filterPeriod(NlfsrList.checkPeriod(Nlfsr.generateRandomNlrgCandidates(Size, ChunkSize, MinTapsCount, MaxTapsCount, MinAndInputsCount, MaxAndInputCount, MinNonlinearTapsRatio, MaxNonlinearTapsRatio, HybridAllowed, UniformTapsDistribution, HardcodedInverters), LimitedTo64b=True if Size <= 64 else False, Total=ChunkSize),  OnlyMaximumPeriod=OnlyMaximumPeriod, AllowMaximumPeriods=AllowMaximumPeriods, OnlyPrimeNonMaximumPeriods=OnlyPrimeNonMaximumPeriods, MinimumPeriodRatio=MinimumPeriodRatio, ReturnAll=ReturnAll)
      if not ReturnAll:
        for Res in PartResult:
          TT.print(repr(Res), "\t", Res._period, "\tPrime:", Int.isPrime(Res._period))
      Result += PartResult
      if not ReturnAll and len(PartResult) > 0:
        Result = Nlfsr.filter(Result, True)
      Accepted = 0
      for nlfsr in Result:
        if nlfsr.Accepted:
          Accepted += 1
      STime = round((time.time() - T0) / 60, 2)
      if SecondIter:    
        AioShell.removeLastLine()
      else:
        SecondIter = 1
      print(f"// Found so far: {Accepted}, searching time: {STime} min")
      if Accepted >= n > 0:
        break
      if STime >= MaxSearchingTimeMin > 0:
        break
#    if not ReturnAll:
#      if len(Result) > n > 0:
#        Result = Result[:n]  
    AioShell.removeLastLine()
    print(f"// Searching finished. Found: {Accepted}, searching time: {STime} min")
    TT.close()      
    return Result
    
  @staticmethod
  def _HWNlrgCandidates(Size, n = 1, ArchitectureVersion = 0):
    if ArchitectureVersion == 1:
      UpperBranchLen = Size // 2
      LowerBranchSize = Size - UpperBranchLen
      CandidateSources = [Size-i for i in range(UpperBranchLen)]
      NonlinearTapsCount = 3
      NonlinearTapConfigLen = (UpperBranchLen * 3) + 1
      LinearTapsCount = LowerBranchSize-NonlinearTapsCount
      ConfigLen = NonlinearTapsCount * NonlinearTapConfigLen + LinearTapsCount * 3
    else:
      TapsCount = (Size//2)-3
      ConfigLen = TapsCount * 11
    Result = []
    while 1:
      Config = bau.urandom(ConfigLen)
      Taps = []
      if ArchitectureVersion == 1:
        for TapIndex in range(NonlinearTapsCount):
          IOffset = TapIndex * NonlinearTapConfigLen
          SList = []
          D = TapIndex
          for SIndex in range(UpperBranchLen):
            if (Config[IOffset+(SIndex*3)] == Config[IOffset+(SIndex*3)+1] == 1):
              S = CandidateSources[SIndex]
              if Config[IOffset+(SIndex*3)+2]:
                S *= -1
              SList.append(S)
          if len(SList) < 1:
            continue
          if Config[IOffset+(UpperBranchLen*3)]:
            D *= -1
          Taps.append([D, SList])
        for TapIndex in range(LinearTapsCount):
          IOffset = NonlinearTapsCount * NonlinearTapConfigLen + TapIndex * 2
          SList = []
          D = TapIndex + 3
          if Config[IOffset+0] and not Config[IOffset+1]:
            SList.append(Size-3-TapIndex)
          elif Config[IOffset+1] and not Config[IOffset+0]:
            SList.append(Size-4-TapIndex)
          if len(SList) < 1:
            continue
          if Config[IOffset+2]:
            D *= -1
          Taps.append([D, SList])
        if len(Taps) < 0:
          continue
        #print(Taps)
      else:
        for TapIndex in range(TapsCount):
          if randint(0, 100) > 75:
            continue
          S = []
          IOffset = TapIndex * 11
          for SIndex in range(5):
            EIndex = (SIndex * 2) + IOffset
            if Config[EIndex]:
              Sign = -1 if Config[SIndex + 1] else 1
              Si = (Size - SIndex - TapIndex) * Sign
              S.append(Si)
          if len(S) > 0:
            D = 1 + TapIndex
            if Config[IOffset+10]:
              D *= -1
            Taps.append([D, S])
      if len(Taps) > 0:
        Candidate = Nlfsr(Size, Taps)
        if Candidate.isLfsr() or Candidate.isSemiLfsr():
          continue
        Result.append(Candidate)
      if len(Result) >= n:
        return Result[:n]
  
  @staticmethod
  def _HWNlrgCandidatesMult(Size, n = 10, ArchitectureVersion = 0):
    Result = []
    N = 10
    if n < 10:
      N = 1
    elif n > 128:
      N = int(n / 128)
    CList = [Size] * int(ceil(n / N))
    for Part in p_map(partial(Nlfsr._HWNlrgCandidates, n=N, ArchitectureVersion=ArchitectureVersion), CList, desc=f"Generating candidates (x{N})"):
      Result += Part
    AioShell.removeLastLine()
    if len(Result) > n:
      return Result[:n]
    return Result
  
  @staticmethod
  def listHWNlrgs(Size : int = None, OnlyMaximumPeriod = True, OnlyPrimeNonMaximumPeriods = True, AllowMaximumPeriods = True, MinimumPeriodRatio = 0.95, n : int = 0, MaximumTries = 0, MaxSearchingTimeMin = 0, ArchitectureVersion = 0) -> list:
    if Size is None:
      Size = AioShell.inputInt("Size", 12, 8, 64)
      ArchitectureVersion = AioShell.inputInt("Architecture", 0, 0, 1)
      OnlyMaximumPeriod = AioShell.inputBool("Only maximum periods", True)
      if not OnlyMaximumPeriod:
        AllowMaximumPeriods = AioShell.inputBool("Allow maximum periods", True)
        OnlyPrimeNonMaximumPeriods = AioShell.inputBool("Only prime non-maximum periods", True)
        MinimumPeriodRatio = AioShell.inputFloat("Minimum period ratio", 0.95, 0, 1)
      n = AioShell.inputInt("Minimum results count", 0, 0)
      MaxSearchingTimeMin = AioShell.inputFloat("Maximum searching time (minutes)", 1, 0.1)
    if Size < 8:
      Aio.printError("Nlfsrs.listRandomNlrgs() can only search for Size >= 8.\nFor small Nlrgs use Nlfsr.listSystematicNlrgs).")
      return []
    Chunk = []
    Result = []
    ChunkSize = 4096
    for _ in range(0, Size-14, 2):
      ChunkSize //= 2
    if ChunkSize < 48:
      ChunkSize = 48
    TT = TempTranscript(f"Nlfsr.listNlfsrs({Size})")
    if ArchitectureVersion == 1:
      UpperBranchLen = Size // 2
      LowerBranchSize = Size - UpperBranchLen
      NonlinearTapsCount = 3
      NonlinearTapConfigLen = (UpperBranchLen * 3) + 1
      LinearTapsCount = LowerBranchSize-NonlinearTapsCount
      ConfigLen = NonlinearTapsCount * NonlinearTapConfigLen + LinearTapsCount * 3
    else:
      TapsCount = (Size//2)-3
      ConfigLen = TapsCount * 11
    if MaximumTries <= 0:
      MaximumTries = (1 << ConfigLen)
    T0 = time.time()
    SecondIter = 0
    for _ in range(MaximumTries):
      Chunk = Nlfsr._HWNlrgCandidatesMult(Size, ChunkSize, ArchitectureVersion)
      #Chunk = Nlfsr.filter(Chunk)
      PartResult = NlfsrList.filterPeriod(NlfsrList.checkPeriod(Chunk, LimitedTo64b=True if Size <= 64 else False),  OnlyMaximumPeriod=OnlyMaximumPeriod, AllowMaximumPeriods=AllowMaximumPeriods, OnlyPrimeNonMaximumPeriods=OnlyPrimeNonMaximumPeriods, MinimumPeriodRatio=MinimumPeriodRatio)    
      for Res in PartResult:
        TT.print(repr(Res), "\t", Res._period, "\tPrime:", Int.isPrime(Res._period))
      Result += PartResult
      if len(PartResult) > 0:
        Result = Nlfsr.filter(Result)
      STime = round((time.time() - T0) / 60, 2)
      if SecondIter:    
        AioShell.removeLastLine()
      else:
        SecondIter = 1
      print(f"// Found so far: {len(Result)}, searching time: {STime} min")
      Chunk = []
      if len(Result) >= n > 0:
        break
      if STime >= MaxSearchingTimeMin > 0:
        break
    if len(Chunk) > 0:
      Result += NlfsrList.filterPeriod(NlfsrList.checkPeriod(Chunk, LimitedTo64b=True if Size <= 64 else False),  OnlyMaximumPeriod=OnlyMaximumPeriod, AllowMaximumPeriods=AllowMaximumPeriods, OnlyPrimeNonMaximumPeriods=OnlyPrimeNonMaximumPeriods, MinimumPeriodRatio=MinimumPeriodRatio)    
      Result = NlfsrList.filter(Result)
#    if len(Result) > n > 0:
#      Result = Result[:n]  
    AioShell.removeLastLine()
    print(f"// Searching finished. Found: {len(Result)}, searching time: {STime} min")
    TT.close()      
    return Result
    
          
class NlfsrCommonTapsReport:
  
  __slots__ = ("_full_dict", "_dict", "_nlfsrs")
  
  def _getTaps(self, nlfsr : Nlfsr, Store=False, MakeFibonacci=True) -> list:
    if MakeFibonacci or Store:
      n2 = nlfsr.copy()
    else:
      n2 = nlfsr
    if MakeFibonacci:
      n2.toFibonacci()
    if Store:
      self._nlfsrs.append(n2)
    Size = n2._size
    Result = []
    for Tap in n2._Config:
      D = abs(Tap[0]) % Size
      S = []
      for Si in Tap[1]:
        S.append(abs(Si) % Size)
      S.sort()
      CTap = tuple([D, tuple(S)])
      Result.append(CTap)
    return Result
  
  def match(self, nlfsr : Nlfsr, ReturnFullInfo = False) -> bool:
    CTaps = self._getTaps(nlfsr)
    GTaps = list(self._dict.keys())
    if ReturnFullInfo:
      UsedTaps = {}
    for CTap in CTaps:
      Found = False
      for GTap in GTaps:
        Found = False
        if (CTap[0] == GTap[0]):
          Found = True
          for S in CTap[1]:
            if S not in GTap[1]:
              Found = False
              break
        if Found:
          if ReturnFullInfo:
            UsedTaps[GTap] = UsedTaps.get(GTap, 0) + 1
          break  
      if not Found:
        if ReturnFullInfo:
          return None
        return False
    if ReturnFullInfo:
      return UsedTaps
    return True
  
  def _matchInt(self, index : int, ReturnFullInfo = False) -> bool:
    return self.match(self._nlfsrs[index], ReturnFullInfo)
  
  def __init__(self, NlfsrsList) -> None:
    self._nlfsrs = []
    CommonTaps = {}
    for n in NlfsrsList:
      CTaps = self._getTaps(n, True)
      for CTap in CTaps:
        CommonTaps[CTap] = CommonTaps.get(CTap, 0) + 1
    self._full_dict = dict( sorted(CommonTaps.items(), key=lambda x:x[1], reverse=1) )
    self._dict = self._full_dict
    
  def filterTaps(self, MinFrequency : int = 0, MaxTapsCount : int = 0):
    Dict = {}
    for k in self._full_dict.keys():
      v = self._full_dict[k]
      if v >= MinFrequency:
        Dict[k] = v
        if len(Dict) >= MaxTapsCount > 0:
          break
      else:
        break
    self._dict = Dict
    
  def getAllTapsCount(self) -> int:
    return len(self._full_dict)
    
  def getTapsCount(self) -> int:
    return len(self._dict)
  
  def _divideTapsByInputCount(self, InputCount : int) -> tuple:
    Result = []
    Rest = []
    for Item in self._full_dict.items():
      CTap = Item[0]
      if len(CTap[1]) == InputCount:
        Result.append(Item)
      else:
        Rest.append(Item)
    return dict(Result), dict(Rest)
  
  def getTapsHavingGivenInputs(self, InputCount : int) -> list:
    Result = []
    for CTap in self._full_dict.keys():
      if len(CTap[1]) == InputCount:
        Result.append(CTap)
    return Result
  
  def getMaximumTapInputCount(self) -> int:
    Result = 0
    for CTap in self._full_dict.keys():
      if len(CTap[1]) > Result:
        Result = len(CTap[1])
    return Result
  
  def reduceTaps(self):
    for i in range(1, self.getMaximumTapInputCount()):
      New = {}
      Given, Rest = self._divideTapsByInputCount(i)
      for Item in Given.items():
        CTap = Item[0]
        Freq = Item[1]
        MayRemove = False
        RTap = tuple([])
        for RItem in Rest.items():
          RTap = RItem[0]
          MayRemove = True
          for S in CTap[1]:
            if S not in RTap[1]:
              MayRemove = False
              break
          if MayRemove:
            break
        if MayRemove:
          Rest[RTap] = Rest.get(RTap, 0) + Freq
        else:
          New[CTap] = Freq
      New.update(Rest)
      self._full_dict = New
    self._full_dict = dict( sorted(self._full_dict.items(), key=lambda x:x[1], reverse=1) )
    self._dict = self._full_dict
        
  def combineTaps(self, MaxInputCount : int = 0):
    Max = self.getMaximumTapInputCount()
    if MaxInputCount <= Max:
      MaxInputCount = Max
    SomethingMerged = True
    while SomethingMerged:
      New = {}
      SkippedIndices = []
      CItems = list(self._full_dict.items())
      SomethingMerged = False
      for i in range(len(CItems)):
        if i in SkippedIndices:
          continue
        if len(CItems[i][0][1]) > MaxInputCount:
          New[CItems[i][0]] = CItems[i][1]
          continue
        JustCombined = False
        for j in range(i+1, len(CItems)):
          if CItems[i][0][0] != CItems[j][0][0]:
            continue
          NewS = tuple(set(CItems[i][0][1]) | set(CItems[j][0][1]))
          if len(NewS) <= MaxInputCount:
            New[tuple([CItems[i][0][0], NewS])] = CItems[i][1] + CItems[j][1]
            JustCombined = True
            SomethingMerged = True
            SkippedIndices.append(j)
            break
        if not JustCombined:
          New[CItems[i][0]] = CItems[i][1]
      self._full_dict = New
      self._full_dict = dict( sorted(self._full_dict.items(), key=lambda x:x[1], reverse=1) )    
    self._dict = self._full_dict
      
    
  def howManyMatches(self, MinTapFrequency : int = 0, MaxTapsCount : int = 0, ReturnAlsoUsedTaps = False):
    self.filterTaps(MinTapFrequency, MaxTapsCount)
    Result = 0
    if ReturnAlsoUsedTaps:
      UsedTaps = {}
    for i in range(len(self._nlfsrs)):      
      if ReturnAlsoUsedTaps:
        UT = self._matchInt(i, True)
        if UT is not None:
          for Item in UT.items():
            if UsedTaps.get(Item[0], 0) < Item[1]:
              UsedTaps[Item[0]] = Item[1]
          Result += 1
      else:
        if self._matchInt(i):
          Result += 1
    if ReturnAlsoUsedTaps:
      return Result, UsedTaps
    return Result
  
  def howManyMatchesTheSuperNlfsr(self, SuperNlfsr : Nlfsr) -> int:
    sn = SuperNlfsr.copy()
    if not sn.toFibonacci(False):
      Aio.printError("Cannot convert the SuperNlfsr to Fibonacci.")
      return None
    Size = sn._size
    Taps = []
    for Tap in sn._Config:
      D = abs(Tap[0]) % Size
      S = []
      for Si in Tap[1]:
        S.append(abs(Si) % Size)
      Taps.append([D, S])
    Result = 0
    for n in self._nlfsrs:
      GTaps = copy.deepcopy(Taps)
      CTaps = n._Config
      Size = n._size
      Matches = True
      for CTap in CTaps:
        Found = False
        BestGTap = None
        for GTap in GTaps:
          if GTap[0] != (abs(CTap[0]) % Size):
            continue
          LocalFound = True
          for CS in CTap[1]:
            if (abs(CS) % Size) not in GTap[1]:
              LocalFound = False
              break
          if LocalFound:
            if Found:
              if len(GTap[1]) < len(BestGTap[1]):
                BestGTap = GTap
            else:
              Found = True
              BestGTap = GTap
        if Found:
          GTaps.remove(BestGTap)
        else:
          Matches = False
          break
      if Matches:
        Result += 1
    return Result
            
  
  def getReport(self) -> str:
    T = AioTable(["# taps", "# NLFSRs", "% NLFSRs"])
    for i in range(1, len(self._full_dict)+1):
      m = self.howManyMatches(0, i)
      p = round(m * 100 / len(self._nlfsrs), 2)
      T.add([i, m, p])
    T2 = AioTable(["Tap", "Frequency"], AutoId=1)
    for Item in self._dict.items():
      CTap = Item[0]
      Freq = Item[1]
      D = CTap[0]
      S = CTap[1]
      T2.add([f"{D} <= {S}", Freq])
    Result = f"""======== Common taps report =========
# Examined NLFSRs: {len(self._nlfsrs)} 
# Unique taps:     {len(self._full_dict)}

How often taps are used?
{str(T2)}

How many NLFSRs can be created using the given taps set?
{str(T)}
"""
    return Result
  
  def printReport(self):
    Aio.print(self.getReport())
  
  def getSuperNlfsr(self, MinTapFrequency : int = 0, MaxTapsCount : int = 0):
    N, Dict = self.howManyMatches(MinTapFrequency, MaxTapsCount, 1)
    Taps = []
    for Item in Dict.items():
      Tap = [Item[0][0], list(Item[0][1])]
      for _ in range(Item[1]):
        Taps.append(Tap.copy())
    Size = Tap[0] + 1
    n = Nlfsr(Size, Taps)
    TC = len(Taps)
    Adder = TC / (Size/2)
    Step = 1
    OnceMore = []
    for i in range(TC):
      Success = False
      SubStep = Step
      while not Success and SubStep > 0:
        Success = n.rotateTap(i,SubStep,1,0)
        SubStep -= 1
      if SubStep+1 != Step:
        OnceMore.append([i, Step])
      Step = int(round(Step + Adder, 0))
    DidSomething = True
    while DidSomething:
      DidSomething = False
      Iter = OnceMore.copy()
      OnceMore = []
      for Item in Iter:
        Success = False
        Step = Item[1]
        SubStep = Step
        i = Item[0]
        while not Success and SubStep > 0:
          Success = n.rotateTap(i,SubStep,1,0)
          SubStep -= 1
        if Success:
          DidSomething = True
        if SubStep+1 != Step:
          OnceMore.append([i, Step])
      n.sortTaps()
    return n
      
      
      
def _xor_sequences(SList) -> bitarray:
  if len(SList) > 0:
    Result = SList[0]
    for i in range(1, len(SList)):
      Result ^= SList[i]
    return Result
  return None

def _get_sequences(Object) -> dict:
  Result = {}
  if type(Object) in [Nlfsr, Lfsr]:
    ss = Object.getSequences()
    for i in range(len(ss)):
      Result[f"FF{i}"] = ss[i]
  elif type(Object) is PhaseShifter:
    ss = Object.getSequences()
    Xors = Object.getXors()
    for i in range(len(ss)):
      Object.getXors()
      Result[f"XOR{tuple(Xors[i])}"] = ss[i]
  return Result
    
  
    
class NlfsrCombinedSequencesReport:
  
  __slots__ = ("_input_objects", "_function", "_bitwise", "_uniques", "_lc", "_tuples", "_slen")
  
  def __init__(self, NlfsrsOrExpanders : list, CombiningFunction = _xor_sequences, CombiningFunctionIsBitwise = False) -> None:
    self._input_objects = NlfsrsOrExpanders
    self._function = CombiningFunction
    self._bitwise = CombiningFunctionIsBitwise
    self._tuples = None
    self._lc = None
    self._uniques = {}
    self._slen = None
    SeqDicts = p_map(_get_sequences, self._input_objects, desc="Obtaining sequences")
    AioShell.removeLastLine()
    LenList = [len(SeqDict) for SeqDict in SeqDicts]
    IndexLists = [[i for i in range(Len)] for Len in LenList]
    UniqueSignatures = set()
    for perm in List.getPermutationsPfManyListsGenerator(IndexLists):
      if len(perm) < 1:
        continue
      perm = perm[0]
      SList = []
      CList = []
      for i in range(len(perm)):
        pi = perm[i]
        SList.append(list(SeqDicts[i].values())[pi])
        CList.append(list(SeqDicts[i].keys())[pi])
      #print(SList)
      #print(CList)
      su = SequenceUnion(SList, self._function, self._bitwise)
      if self._slen is None:
        self._slen = len(su)
      Signature = Bitarray.getRotationInsensitiveSignature(su.getLongSequence(), 4)
      if Signature not in UniqueSignatures:
        self._uniques[tuple(CList)] = su.getLongSequence()
        UniqueSignatures.add(Signature)
        #print(tuple(CList))

  def printReport(self, LinearComplexity = True, TuplesCardinality = True):
    Aio.print(self.getReport(LinearComplexity, TuplesCardinality))

  def getReport(self, LinearComplexity = True, TuplesCardinality = True):
    if LinearComplexity and (self._lc is None):
      self._lc = []
      for Seq in tqdm(self._uniques.values(), desc="Linear complexity computing"):
        self._lc.append(Bitarray.getLinearComplexity(Seq, 1))
    if TuplesCardinality and (self._tuples is None):
      self._tuples = []
      for Seq in tqdm(self._uniques.values(), desc="Tuples cardinality computing"):
        N = int(log2(len(Seq)))
        Max = (1 << N)
        C = Bitarray.getCardinality(Seq, N)
        self._tuples.append([C, round(C * 100 / Max, 2)])
    Reprs = [Str.toLeft(repr(ob), 20) for ob in self._input_objects]
    LC = []
    if LinearComplexity:
      LC = ["LC"]
    TC = []
    if TuplesCardinality:
      TC = ["# Tuples", "% Tuples"]
    Table = AioTable(Reprs + LC + TC, AutoId=1)
    Names = list(self._uniques.keys())
    for i in range(len(Names)):
      if LinearComplexity:
        LC = [self._lc[i]]
      if TuplesCardinality:
        TC = self._tuples[i]
      Table.add(list(Names[i]) + LC + TC)
    return f"""Output sequences length: {self._slen}
{Table.toString()}"""


class NlfsrCascade:
  
  __slots__ = ("_next1", "_nlfsrs", "_size", "_period", "_exename", "_period_verified", "_Config", "_baValue", "_version", "_ps", "_reset_type")
  
  def __repr__(self) -> str:
    if self._period is None:
      sp = ""
    else:
      if self._period_verified is not None:
        #sp = ", SET_PERIOD=(" + str(self._period) + "," + str(self._period_verified) + "," + str(self._reset_type) + "," + str(hash(bytes(self._reset_type))) + ")"
        sp = ", SET_PERIOD=(" + str(self._period) + "," + str(self._period_verified) + ")"
      else:
        sp = ", SET_PERIOD=" + str(self._period)
    Result = f"""NlfsrCascade({repr(self._nlfsrs)}, Version={self._version}{sp})"""
    return Result
  
  def __str__(self) -> str:
    return Bitarray.toString(self._baValue)
  
  def __len__(self) -> int:
    return self._size
  
  def __init__(self, NlfsrsList : list, Version : int = 1, **kwargs) -> None:
    self._nlfsrs = []
    self._size = 0
    self._period = None
    self._exename = None
    self._period_verified = None
    self._Config = []
    self._version = Version
    for nlfsr in NlfsrsList:
      if type(nlfsr) not in [Nlfsr, Lfsr]:
        Aio.printError("NlfsrsList must include Nlfsr or Lfsr objects only.")
        return None
      self._nlfsrs.append(nlfsr.copy())
      self._size += len(nlfsr)
      try:
        self._Config += nlfsr._Config.copy()
      except:
        pass
    self._baValue = None
    self._reset_type = bau.urandom(self._size)
    self.reset()
    if kwargs.get("SET_PERIOD", None) is not None:
      _period = kwargs["SET_PERIOD"]
      if type(_period) is int:
        self._period = _period
        Aio.print(f"// WARNING: Period of Nlfsr was set to {self._period} and WILL NOT be verified again!")
      elif type(_period) is tuple:
        if len(_period) >= 2:
          p = _period[0]
          h = _period[1]
          #rt = _period[2] 
          #hrt = _period[3] 
          #if (Int.hash(p) == h) and (hash(bytes(rt)) == hrt):
          if (Int.hash(p) == h):
            self._period = p
            self._period_verified = h
            #self._reset_type = rt
          else:
            Aio.print(f"// WARNING: Period of Nlfsr was set to {self._period} but IS INCORRECT!!!")
        else:
          Aio.print(f"// WARNING: Period of Nlfsr was set to {self._period} but IS INCORRECT!!!")
    if Version == 1:
      # Cascade
      self._next1 = self._next1_v1
    else:
      Aio.printError(f"Incorrect version of NlfsrCascade.")
      
  def singleBitInject(self, Bit : int):
    if Bit:
      for i in range(len(self._nlfsrs)):
        n = self._nlfsrs[i]
        bi = (len(n) - i -1) % len(n)
        n._baValue[bi] ^= 1
          
  def isTheoreticallyMaximum(self) -> bool:
    if self._version == 1:
      Per = 0
      nd = {}
      for n in reversed(self._nlfsrs):
        p = n.getPeriod()
        nd[p] = nd.get(p, 0) + 1
        if not Int.isPrime(p):
          return False
        if p < Per:
          return False
        Per = p
      for v in nd.values():
        if v > 2:
          return False
    else:
      Aio.printError("Not implemented!")
      return False
    return True
              
  def isTheoreticallyNonMaximum(self) -> bool:
    if self._version == 1:
      nd = {}
      for n in self._nlfsrs:
        p = n.getPeriod()
        nd[p] = nd.get(p, 0) + 1
      for v in nd.values():
        if v > 2:
          return True
    else:
      Aio.printError("Not implemented!")
      return False
    return False
  
  def toHashString(self) -> str:
    return hashlib.sha256(bytes(repr(self), "utf-8")).hexdigest()
  
  def toBooleanExpressionFromRing(self, *args):
    return ""
  
  def getArchitecture(self, *args):
    return ""
  
  def toArticleString(self, *args):
    return ""
  
  def getTaps(self) -> list:
    return self._Config
  
  def getSize(self) -> int:
    return self._size
      
  def reset(self) -> bitarray:
    #v = self._reset_type
    #return self.setValue(v)
    Result = bitarray()
    for i in range(len(self._nlfsrs)):
      self._nlfsrs[i].reset()
      Result += self._nlfsrs[i]._baValue
    self._baValue = Result
    return Result
    
  def clear(self) -> bitarray:
    Result = bitarray()
    for i in range(len(self._nlfsrs)):
      self._nlfsrs[i].clear()
      Result += self._nlfsrs[i]._baValue
    self._baValue = Result
    return Result
  
  def getValue(self) -> bitarray:
    Result = bitarray()
    for nlfsr in self._nlfsrs:
      Result += nlfsr._baValue
    return Result
  
  def setValue(self, Value : bitarray):
    Value = bitarray(Value)
    if len(Value) != len(self):
      Aio.printError(f"The new value is {len(Value)} bit length while should be {len(self)}.")
    beg = 0
    self._baValue = Value
    for nlfsr in self._nlfsrs:
      size = nlfsr._size
      nlfsr._baValue = Value[beg:size+beg]
      beg += size
    
  def _next1_v1(self) -> bitarray:
    os = []
    for i in range(1, len(self._nlfsrs)):
      o = self._nlfsrs[i]._baValue[0]
      os.append(o)
    os.append(1)
    Result = bitarray()
    for i in range(len(self._nlfsrs)):
      if os[i]:
        self._nlfsrs[i]._next1()
      Result += self._nlfsrs[i]._baValue
    self._baValue = Result
    return Result
    
  def next(self, steps=1) -> bitarray:
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return None
    elif steps == 0:
      return self.getValue()
    else:
      for _ in range(steps):
        Result = self._next1()
      return Result
      
  def getPeriod(self) -> int:
    if self._period is None:
      Repeat = 1
      MaxArithmeticP = 1
      for n in self._nlfsrs:
        MaxArithmeticP *= n.getPeriod()
        #print(repr(n))
      BestV = self._reset_type
      BestP = 0
      while Repeat>0:
        v0 = self.reset().copy()
        p = 1
        self._period = 0
        Max = 1 << self._size
        while p <= Max:
          #Fprint(p, "\t", self._baValue)
          v = self._next1()
          if v == v0:
            self._period = p
            break
          p += 1
        #print(self._period, MaxArithmeticP, self._reset_type)
        if self._period > BestP:
          BestP = self._period
          BestV = self._reset_type
        if self._period/MaxArithmeticP > 0.5:
          break
        Repeat -= 1
        self._reset_type = bau.urandom(self._size)
      self._period = BestP
      self._period_verified = Int.hash(self._period)
    return self._period
  
  def isMaximum(self) -> bool:
    return False
  
  def getSequences(self, Length=0, Reset=True, ProgressBar=False):
    if not ProgressBar and 12 < self._size <= 64 and Reset and Length == 0:
      try:
        return self.getSequencesCpp64b()
      except:
        pass
    if Length <= 0:
      Length = self.getPeriod() # (1 << self._size) - 1
    if Reset:
      self.reset()
    if ProgressBar:
      Iterator = tqdm(range(Length), desc="Obtaining sequences")
    else:
      Iterator = range(Length)
    Result = [bitarray(Length) for _ in range(self._size)]
    for i in Iterator:
      for j, Bit in zip(range(self._size), self.getValue()):
        Result[j][i] = Bit
      self._next1()
    if ProgressBar:
      AioShell.removeLastLine()
    return Result
  
  def getValues(self, n = 0, step = 1, reset = True, AsStrings = False) -> list:
    if n <= 0:
      n = self.getPeriod()
    if reset:
      self.reset()
    result = []
    for i in range(n):
      if AsStrings:
        result.append(Bitarray.toString(self._baValue))
      else:
        result.append(self._baValue.copy())
      self.next(step)
    return result
  
  def printValues(self, n = 0, step = 1, reset = True) -> None:
    if n <= 0:
      val0 = self._baValue.copy()
      n = self.getPeriod()
      self._baValue = val0
    if reset:
      self.reset()
    for i in range(n):
      Aio.print(self)
      self.next(step)
  
  def toVerilog(self, ModuleName : str, InjectorIndexesList = []) -> str:
    CommonInjector = False
    if type(InjectorIndexesList) and InjectorIndexesList == -1:
      CommonInjector = True
      InjectorIndexesList = []
      Offset = 0
      for i in range(len(self._nlfsrs)):
        n = self._nlfsrs[i]
        bi = (len(n) - i - 1) % len(n)
        InjectorIndexesList.append(Offset + bi)
        Offset += len(n)
    Result = ""
    SubNames = []
    for i in range(len(self._nlfsrs)):
      Name = f"{ModuleName}_register_{i}"
      SubNames.append(Name)
      n = self._nlfsrs[i]
      Result += n.toVerilog(Name, [j for j in range(len(n))]) + "\n\n\n"
    Result += f"""
module {ModuleName} (
  input wire clk,
  input wire enable,
  input wire reset,"""
    if len(InjectorIndexesList) > 0:
      Inj = True
      if CommonInjector:
        Result += f"""
  input wire injectors,"""
      else:
        Result += f"""
  input wire [{len(InjectorIndexesList)-1}:0] injectors,"""
    else:
      Inj = False
    Result += f"""
  output wire [{len(self)-1}:0] O
);
"""
    for i in range(len(self._nlfsrs)):
      Result += f"""
  wire [{len(self._nlfsrs[i])-1}:0] {SubNames[i]}_O;"""
      if Inj:
        Result += f"""
  wire [{len(self._nlfsrs[i])-1}:0] {SubNames[i]}_injectors;"""
      Result += f"""
  
  {SubNames[i]} {SubNames[i]}_inst (
    .clk    (clk),
    .enable (enable),
    .reset  (reset),"""
      if Inj:
        Result += f"""
    .injectors ({SubNames[i]}_injectors),"""
      Result += f"""
    .O      ({SubNames[i]}_O)
  );
"""
    IIndex = 0
    for i in range(len(self._nlfsrs)):
      for j in range(len(self._nlfsrs[i])):
        if IIndex in InjectorIndexesList:
          if CommonInjector:
            Result += f"""
  assign {SubNames[i]}_injectors[{j}] = injectors;"""
          else:
            Result += f"""
  assign {SubNames[i]}_injectors[{j}] = injectors[{InjectorIndexesList.index(IIndex)}];"""
        else:
          Result += f"""
  assign {SubNames[i]}_injectors[{j}] = 1'b0;"""
        IIndex += 1    
    From = 0
    To = 0
    for i in range(len(self._nlfsrs)):
      To = From + len(self._nlfsrs[i])
      Result += f"""
  assign O[{To-1}:{From}] = {SubNames[i]}_O;"""
      From += len(self._nlfsrs[i])
    Result += "\n\nendmodule"
    return Result
  
  createExpander = Nlfsr.createExpander
  
  def createRandomPhaseShifter(self, OutputCount : int, MinXorInputs = 2, MaxXorInputs = 3):
    Xors = []
    LowerFFs = [i for i in range(len(self._nlfsrs[0]))]
    UpperFFs = [i for i in range(len(self._nlfsrs[0]), self.getSize())]
    while len(Xors) < OutputCount:
      XorSize = randint(MinXorInputs, MaxXorInputs)
      LowerXorSize = randint(1, XorSize-1)
      UpperXorSize = XorSize - LowerXorSize
      Xor = List.randomSelect(LowerFFs, LowerXorSize) + List.randomSelect(UpperFFs, UpperXorSize)
      Xor.sort()
      if Xor not in Xors:
        Xors.append(Xor)
    return PhaseShifter(self, Xors)
  
  def createSimpleExpander(self, MinXorInputs = 1, MaxXorInputs = 3, Verify = False) -> PhaseShifter:
    Offset = 0
    SingleUniques = []
    Obligatory = []
    Rest = []
    if Verify:
      SingleSequences = self.getSequences()
      Uniques = set()
    for i in range(len(self._nlfsrs)):
      nlfsr = self._nlfsrs[i]
      First = True if i == 0 else False
      Last = True if i == (len(self._nlfsrs)-1) else False
      Dests = nlfsr.getTapsDestinations()
      for d in Dests:
        d += Offset
        if First:
          Obligatory.append(d)
        SingleUniques.append(d)
      if not First:
        Rest += [x+Offset for x in range(0, nlfsr._size)] 
      Offset += nlfsr._size
    Xors = []
    for k in range(MinXorInputs, MaxXorInputs+1):
      #print (f"k = {k}")
      for ko in range(1, k+1):
        kr = k - ko
        for permo in List.getCombinations(Obligatory, ko):
          #print (f"- permo = {permo}")
          for permr in List.getCombinations(Rest, kr):
            #print (f"- - permr = {permr}")
            perm = permo + permr
            if len(set(perm)) != len(perm):
              continue
      #for perm in List.getCombinations(SingleUniques, k):
            Ok = False
            for p in perm:
              if p in Obligatory:
                Ok = True
                break
            if not Ok:
              continue
            if Verify:
              Seq = Nlfsr._getSequence(SingleSequences, perm)
              HSeq = Bitarray.getRotationInsensitiveSignature(Seq, range(3, 6+1))
              if HSeq not in Uniques:
                Uniques.add(HSeq)
              else:
                Aio.print(f"// Expander output {perm} DOES NOT provide an unique sequence!")
                Ok = False
            if Ok:
              Xors.append(perm)
    return PhaseShifter(self, Xors)
          
  def analyseCycles(self, SequenceAtBitIndex = 0) -> CyclesReport:
    return CyclesReport(self, SequenceAtBitIndex)
  
  
    
class NlfsrList:
  
  @staticmethod
  def getTapsStats(NlfsrsList : list) -> tuple:
    t, a = 0, 0
    for r in p_imap(Nlfsr.getTapsStats, NlfsrsList):
      if r[0] > t:
        t = r[0]
      if r[1] > a:
        a = r[1]
    return t, a
  
  @staticmethod
  def getCudaConfig(NlfsrsList : list):
    t, a = NlfsrList.getTapsStats(NlfsrsList)
    Result = []
    for r in p_imap(partial(Nlfsr.getCudaConfig, MaxTaps=t, MaxAndInputs=a), NlfsrsList):
      Result.append(r)
    return numpy.asarray(Result)
  
  @staticmethod
  def checkPeriodCuda(NlfsrsList : list) -> list:
    Conf = NlfsrList.getCudaConfig(NlfsrsList)
    Result = numpy.zeros(len(NlfsrsList), dtype="uint64")
    @cuda.jit
    def cuda_count(Configs, Results):
      pos = cuda.grid(1)
      bsize = cuda.gridsize(1)
      Not = numpy.uint64(numpy.uint64(1 << 63))
      MaskNot = numpy.uint64(~Not)
      while pos < Configs.shape[0]:
        Conf = Configs[pos]
        Val = numpy.uint64(1)
        V0 = Val
        Period = numpy.uint64(0)
        while 1:
          NVal = Val >> 1
          if Val & 1:
            NVal |= Conf[0][0]
          for ti in range(1, Conf.shape[0]):
            Tap = Conf[ti]
            if Tap[0]:
              if Tap[1] & Not:
                if Val & (Tap[1] & MaskNot):
                  And = 0
                else:
                  And = 1
              else:
                if Val & Tap[1]:
                  And = 1
                else:
                  And = 0
              if And:
                for j in range(2, Tap.size):
                  if Tap[j]:
                    if Tap[j] & Not:
                      if Val & (Tap[j] & MaskNot):
                        And = 0
                        break
                    else:
                      if not (Val & Tap[j]):
                        And = 0
                        break
                  else:
                    break
              if Tap[0] & Not:
                if not And:
                  NVal ^= (Tap[0] & MaskNot)
              else:
                if And:
                  NVal ^= Tap[0]
            else:
              break
          Val = NVal
          Period += 1
          if Val == V0:
            break
        Results[pos] = Period
        pos += bsize
    cuda_count[1024, 1024](Conf, Result)
    for i in range(len(NlfsrsList)):
      NlfsrsList[i]._period = int(Result[i])
      NlfsrsList[i]._period_verified = Int.hash(NlfsrsList[i]._period)
    return NlfsrsList
  
  @staticmethod
  def getNlfsrCombinedSequencesReport(NlfsrsOrExpanders : list, CombiningFunction = _xor_sequences, CombiningFunctionIsBitwise = False) -> NlfsrCombinedSequencesReport:
    return NlfsrCombinedSequencesReport(NlfsrsOrExpanders, CombiningFunction, CombiningFunctionIsBitwise)
  
  @staticmethod
  def toAIArray(NlfsrList, MaxTapsCount=30, MaxAndInputs=8, SequenceBased=False, ReturnAlsoAccepted=False, BaseOnPeriod=False) -> list:
    Result = []
    ResultAcc = []
    for nlfsr in NlfsrList:
      A = nlfsr.toAIArray(MaxTapsCount, MaxAndInputs, SequenceBased)
      if ReturnAlsoAccepted:
        if BaseOnPeriod:
          ResultAcc.append(nlfsr.getPeriod() / ((1 << nlfsr.getSize()) -1))
        else:
          ResultAcc.append(1 if nlfsr.Accepted else 0)
      Result.append(A)
    if ReturnAlsoAccepted:
      return [Result, ResultAcc]
    return Result
  
  @staticmethod
  def analyseCommonTaps(NlfsrsList) -> NlfsrCommonTapsReport: 
    return NlfsrCommonTapsReport(NlfsrsList)
  
  @staticmethod
  def getFullInfo(NlfsrsList, Draw = False) -> str:
    Result = ""
    for n in NlfsrsList:
      Result += n.getFullInfo(Repr=True, Draw=Draw) + "\n"
    return Result
  
  @staticmethod
  def printFullInfo(NlfsrsList : list, Draw = False):
    Aio.print(NlfsrList.getFullInfo(NlfsrsList, Draw))
  
  def parseFromArticleFile(FileName : str) -> list:
    Data = readFile(FileName)
    Result = []
    for Line in Data.split("\n"):
      try:
        Line.strip()
        Line = Line.replace("*","")
        Linel = Line.split("\t")
        Result.append(Nlfsr.parseFromArticleString(Linel[0], Linel[1]))
      except:
        pass
    return Result
    
  def checkMaximum(NlfsrsList) -> list:
    exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
    exename64b = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.getExePath()
    for N in NlfsrsList:
      if N._size <= 64:
        N._exename = exename64b
      else:
        N._exename = exename
    G = Generators()
    RM = p_map(Nlfsr.isMaximum, NlfsrsList, desc="Nlfsrs simulating")
    Results = []
    for i in range(len(RM)):
      if RM[i]:
        Results.append(NlfsrsList[i])
    return NlfsrList.filter(Results)
  
  def _getPeriodAndNlfsr(nlfsr : Nlfsr, ForceRecalculation=False, ExeName=None) -> list:
    #Result = [nlfsr, nlfsr.getPeriod(ForceRecalculation=ForceRecalculation, ExeName=ExeName)]
    #print(Result)
    #print("------------")
    nlfsr.getPeriod(ForceRecalculation=ForceRecalculation, ExeName=ExeName)
    return nlfsr
  
  def _checkPeriodSeries(NlfsrsList, ForceRecalculation=False, ExeName=None):
    Result = []
    for n in NlfsrsList:
      n._exename = ExeName
      n.getPeriod(ForceRecalculation=ForceRecalculation)
      Result.append(n)
    return Result
  
  def checkPeriod(NlfsrsList, ForceRecalculation=False, LimitedTo64b = True, Total = None) -> list:
    if LimitedTo64b:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.getExePath()
    else:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
    Results = []
    if type(NlfsrsList) is list:
      if len(NlfsrsList) > 256:
        S = int(len(NlfsrsList) / 256)
        if S > 10:
          S = 10
        Generators().subLists(NlfsrsList, S)
        Total = int(ceil(len(NlfsrsList) / S))
        Iter = p_imap(functools.partial(NlfsrList._checkPeriodSeries, ForceRecalculation=ForceRecalculation, ExeName=exename), Generators().subLists(NlfsrsList, S), desc=f"Nlfsrs simulating (x{S})", total=Total)
      else:
        Iter = p_imap(functools.partial(NlfsrList._getPeriodAndNlfsr, ForceRecalculation=ForceRecalculation, ExeName=exename), NlfsrsList, desc="Nlfsrs simulating")
    else:    
      if Total is not None and Total > 256:
        S = int(Total / 256)
        if S > 10:
          S = 10
        Total = int(ceil(Total / S))
        Iter = p_imap(functools.partial(NlfsrList._checkPeriodSeries, ForceRecalculation=ForceRecalculation, ExeName=exename), Generators().subListsFromGenerator(NlfsrsList, S), desc=f"Nlfsrs simulating (x{S})", total=Total)
      else:
        Iter = p_imap(functools.partial(NlfsrList._getPeriodAndNlfsr, ForceRecalculation=ForceRecalculation, ExeName=exename), NlfsrsList, desc="Nlfsrs simulating")
    for nlfsr in Iter:
      if type(nlfsr) is list:
        Results += nlfsr
      else:
        Results.append(nlfsr)
    AioShell.removeLastLine()
    return Results
  
  def filterPeriod(NlfsrList, OnlyMaximumPeriod = True, AllowMaximumPeriods = True, OnlyPrimeNonMaximumPeriods = True, MinimumPeriodRatio = 0.95, ReturnAll = False) -> list:
    Result = []
    for n in NlfsrList:
      n.Accepted = False
      if ReturnAll:
        Result.append(n)
      if n._period is None:
        n.getPeriod()
      Maximum = (1 << n._size) -1
      if n._period == Maximum:
        if AllowMaximumPeriods or OnlyMaximumPeriod:
          n.Accepted = True
          if not ReturnAll:
            Result.append(n)
      elif not OnlyMaximumPeriod:
        if (n._period / Maximum) >= MinimumPeriodRatio:
          if OnlyPrimeNonMaximumPeriods:
            if Int.isPrime(n._period):
              n.Accepted = True
              if not ReturnAll:
                Result.append(n)
          else:
            n.Accepted = True
            if not ReturnAll:
              Result.append(n)
    return Result
  
  def filter(NlfsrsList, ExcludeSemiLfsrs = False) -> list:
    return Nlfsr.filter(NlfsrsList, ExcludeSemiLfsrs)
  
  def filterNonLinear(NlfsrList) -> list:
    G = Generators()
    Chunk = 50
    Total = ceil(len(NlfsrList) / Chunk)
    Iter = p_uimap(_NLFSR_nonlinear_filtering_helper, G.subLists(NlfsrList, Chunk), total=Total, desc="Filtering nonlinears")
    Result = []
    for I in Iter:
      Result += I
    return Result
  
  def analyseSequences(NlfsrsList) -> list:      
    return Nlfsr.analyseSequencesBatch(NlfsrsList)
  def toPlanar(NlfsrList) -> list:
    Result = NlfsrList.copy()
    for R in Result:
      R.toPlanar()
    return Result
  def getOnlyPlanar(NlfsrList) -> list:
    Result = []
    for R in NlfsrList:
      if R.toPlanar():
        Result.append(R)
    return Result
  def toPandasTable(NlfsrsList, Polys=True) -> PandasTable:
    if Polys:
      PT = PandasTable(['RC', 'Polynomial', 'Architecture', 'Nlfsr'], 1, 1)
    else:
      PT = PandasTable(['RC', 'Architecture', 'Nlfsr'], 1, 1)
    RC = "  \nR \n C\nRC"
    for N in NlfsrsList:
      Arch = N.getArchitecture()
      if Polys:
        Polys =  N.toBooleanExpressionFromRing(0, 0, 1) + "\n"
        Polys += N.toBooleanExpressionFromRing(0, 1, 1) + "\n"
        Polys += N.toBooleanExpressionFromRing(1, 0, 1) + "\n"
        Polys += N.toBooleanExpressionFromRing(1, 1, 1)
        PT.add([RC, Polys, Arch, repr(N)])
      else:
        PT.add([RC, Arch, repr(N)])
    return PT
  
  def fromFile(FileName : str, Size = 0, TapsCount = 0) -> list:
    Data = readFile(FileName)
    Results = []
    for Line in Data.split("\n"):
      Found = False
      R = re.search(r'Nlfsr\(([0-9]+),\s*(\[.*\]),\s*SET_PERIOD=(.*)\)', Line)
      NPeriodVer = None
      if R:
        NSize = ast.literal_eval(str(R.group(1)))
        NConfig = ast.literal_eval(str(R.group(2)))
        NPeriod = ast.literal_eval(str(R.group(3)))
        if type(NPeriod) is tuple:
          NPeriodVer = NPeriod[1]
          NPeriod = NPeriod[0]
        Found = True
      else:
        R = re.search(r'Nlfsr\(([0-9]+),\s*(\[.*\])\)', Line)
        if R:
          NSize = ast.literal_eval(str(R.group(1)))
          NConfig = ast.literal_eval(str(R.group(2)))
          NPeriod = 0
          Found = True
      if Found:
        if NSize != Size > 0:
          continue
        if len(NConfig) != TapsCount > 0:
          continue
        if NPeriod > 0:
          if NPeriodVer is None:
            N = Nlfsr(NSize, NConfig, SET_PERIOD=NPeriod)
          else:
            N = Nlfsr(NSize, NConfig, SET_PERIOD=(NPeriod, NPeriodVer))
        else:
          N = Nlfsr(NSize, NConfig)
        Results.append(N)
    return Results
  
  def reprToFile(NlfsrsList, FileName : str, ForcePeriodRecalculation=False, LimitedTo64b = True):
    Text = ""
    Second = 0
    if ForcePeriodRecalculation:
      NlfsrList.checkPeriod(NlfsrsList, True, LimitedTo64b=LimitedTo64b)
    for n in NlfsrsList:
      if Second:
        Text += "\n"
      else:
        Second = 1
      Text += repr(n)
    writeFile(FileName, Text)
    
  def toResearchDataBase(NlfsrsList, FileName : str, LimitedTo64b = True):
    PT = PandasTable(["Size", "#Taps", "Equations", "SingleSeq", "DoubleSeq", "TripleSeq"], 1, 1)
    i = 0
    if LimitedTo64b:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.getExePath()
    else:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
    for N in NlfsrsList:
      N._exename = exename
    for R in p_imap(_NLFSR_list_database_helper, NlfsrsList):
      NLFSR = NlfsrsList[i]
      Equations = NLFSR.toBooleanExpressionFromRing(0, 0) + "\n"
      Equations += NLFSR.getArchitecture().replace("\n", ", ") + "\n"
      Equations += " R  " + NLFSR.toBooleanExpressionFromRing(0, 1) + "\n"
      Equations += "C  " + NLFSR.toBooleanExpressionFromRing(2, 0) + "\n"
      Equations += "CR  " + NLFSR.toBooleanExpressionFromRing(2, 1)
      PT.add([NLFSR.getSize(), len(NLFSR.getTaps()), Equations, R[0], R[1], R[2]])
      writeFile(FileName, PT.toString('left'))
      i += 1
      
  def toXlsDatabase(NlfsrsList, Scheduler = None, CleanBufferedLists = True, LimitedTo64b = True, SimpleExpanderAllowed = True):
    from libs.remote_aio import RemoteAioScheduler
    if type(Scheduler) is not RemoteAioScheduler:
      Scheduler = None
    try:
      os.mkdir("data")
    except:
      if not os.path.isdir("data"):
        Aio.printError("Remove the 'data' file. This functions needs a 'data' directory.")
        return
    tt = TempTranscript("NlfsrList.toXlsDatabase()")
    if LimitedTo64b:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.getExePath()
    else:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
    if not Aio.isType(NlfsrsList, []):
      NlfsrsList = [NlfsrsList]
    for N in NlfsrsList:
      N._exename = exename
    PT = PandasTable(["Size", "# Taps", "Architecture", "ANF", "T, L, D", "Period P", "Period %", "Max - P", "Maximum?", "Prime?", "# 1s", "# Cycles", "S, D, T",">90%","80%",">70%",">60%",">50%","Details", "Python Repr"])
    tt.print("Period obtaining...")
    NlfsrsListAux = []
    Iter = p_map(Nlfsr.getPeriod, NlfsrsList, desc="Period obtaining")   
    AioShell.removeLastLine() 
    for I, nlfsr in zip(Iter, NlfsrsList):
      nlfsr._period = I
      nlfsr._period_verified = Int.hash(I)
      NlfsrsListAux.append(nlfsr)
    NlfsrsList = NlfsrsListAux
    if Scheduler is None:
      Nones = [None for _ in range(len(NlfsrsList))]
      Iterator = zip(NlfsrsList, Nones, Nones)
    else:
      CodeList = [f'''Nlfsr_makeExpanderForRAio({repr(nlfsr)})''' for nlfsr in NlfsrsList]
      print(CodeList)
      Iterator = Scheduler.uimap(CodeList, ShowStatus=True, DefaultResponse=tuple([None, None, None]))
    Cntr = 0
    for nlfsr, Expander, Trajectories in Iterator:
      Cntr += 1
      if nlfsr is None:
        continue
      tt.print(f"{Cntr}/{len(NlfsrsList)}: {repr(nlfsr)}")
      print(f"{Cntr}/{len(NlfsrsList)}: {Str.toLeft(repr(nlfsr), Aio.getTerminalColumns()-30)}...")
      if Expander is None:
        Expander, Trajectories = _make_expander(nlfsr, PBar=1, AlwaysCleanFiles=CleanBufferedLists, SimpleExpanderAllowed=SimpleExpanderAllowed)
      FileName = "data/" + hashlib.sha256(bytes(repr(nlfsr), "utf-8")).hexdigest() + ".html"
      #TuplesRep = Expander.TuplesRep
      Eq = nlfsr.toBooleanExpressionFromRing(0, 0)
      try:
        EqSymPy = nlfsr.toBooleanExpressionFromRing(0, 0, ReturnSympyExpr=1)
        AnfT = SymPy.getAnfMonomialsCount(EqSymPy)
        AnfL = SymPy.getAnfLiteralsCount(EqSymPy)
        AnfD = SymPy.getAnfDegree(EqSymPy)
      except:
        AnfT = -1
        AnfL = -1
        AnfD = -1
      EqC = nlfsr.toBooleanExpressionFromRing(1, 0)
      EqR = nlfsr.toBooleanExpressionFromRing(0, 1)
      EqCR = nlfsr.toBooleanExpressionFromRing(1, 1)
      ArchitectureTaps = nlfsr.getArchitecture()
      Architecture = nlfsr.toArticleString()
      Period = nlfsr.getPeriod()
      TrajectoriesCount = "-"
      PeriodStr = f"{str(Period)} : "
      Max = (1 << nlfsr._size) -1
      MissingStates = Max - Period
      if Period == Max:
        PeriodStr += "IS MAXIMUM"
        IsMax = 1
        IsMaxStr = "Y"
        OfMax = 1
      else:
        IsMax = 0
        IsMaxStr = "N"
        OfMax = Period / Max
        PeriodStr += f"{Period * 100 / Max} % of MAX"
      if Int.isPrime(Period):
        PeriodStr += ", IS PRIME"
        IsPrime = 1
        IsPrimeStr = "Y"
      else:
        IsPrime = 0
        IsPrimeStr = "N"
      Single, Double, Triple = 0,0,0
      Xors = Expander.getXors()
      try:
        LCData = Expander.LinearComplexity
      except:
        LCData = []
      try:
        SeqStats = Expander.SeqStats
      except:
        SeqStats = []
      try:
        OnesCountB0 = Expander.OnesCountB0
        OnesCountB0Str = f"2{Str.toSuperScript(str(nlfsr._size-1))} - {2 ** (nlfsr._size - 1) - OnesCountB0}"
      except:
        OnesCountB0 = -1
        OnesCountB0Str = "?"
      LCTable = PandasTable(["XORed_FFs", "Linear_complexity", "#Unique_values"], AutoId=True)
      LCTableList = []
      TuplesDict = {}
      for i in range(len(Xors)):
        XOR = Xors[i]
        try:
          LC = LCData[i]
        except:
          LC = "-"
        try:
          SS = SeqStats[i]
          for perc in range(50, 100, 5):
            if SS >= (Period * perc / 100):
              TuplesDict[perc] = TuplesDict.get(perc, 0) + 1
        except:
          SS = "-"
        LCTableList.append([XOR, LC, SS])
        if len(XOR) == 1:
          Single += 1
        elif len(XOR) == 2:
          Double += 1
        else:
          Triple += 1
      LCTableList.sort(key = lambda x: x[2] if type(x[2]) is int else 0 , reverse=1)
      for x in LCTableList:
        LCTable.add(x)
      PercTable = ""
      for perc in range(95, 50-1, -5):
        PercTable += f" >= {perc}% n-tuples:  \t{TuplesDict.get(perc, 0)} outputs \n"
      FileText = f"""{repr(nlfsr)}

Size   : {nlfsr.getSize()}
# Taps : {len(nlfsr.getTaps())}
Period : {PeriodStr}
# 1s   : {OnesCountB0}   =   {OnesCountB0Str}

ANF ---------------------------------------------------

# Terms    : {AnfT}
# Literals : {AnfL}
# Degree   : {AnfD}

EQ               : {Eq}
EQ Complement    : {EqC} 
EQ Reversed      : {EqR}
EQ Comp-Rev      : {EqCR}

ARCHITECTURE -----------------------------------------
{Architecture}

TAPS -------------------------------------------------
{ArchitectureTaps}

UNIQUE SEQUENCES -------------------------------------
  Single: {Single}, Double: {Double}, Triple: {Triple}
"""
      if Trajectories is not None:
        TrajectoriesCount = Trajectories.getTrajectoriesCount(0)
        FileText += f"""
CYCLES -----------------------------------------------
{Trajectories.getReport(67, True if nlfsr._size > 12 else False)}
"""
      FileText += f"""
EXPANDER ---------------------------------------------
{LCTable.toString()}

EXPANDER STATS ---------------------------------------
{PercTable}
"""
#TUPLES REPORT (Sequence observed at bit 0):
#{TuplesRep.getReport(Colored=True, HidePlot=True)}
#"""
      #writeFile(FileName, FileText)
      conv = Ansi2HTMLConverter(escaped=False, dark_bg=0, title=repr(nlfsr), line_wrap=1, linkify=0)
      html = conv.convert(FileText)
      html = re.sub(r'(\.ansi2html-content\s+)(\{)', '\g<1>{ font-family: "Lucida Console", Cascadia, Consolas, Monospace;', html)
      html = re.sub(r'(\*\s+)(\{)', '\g<1>{ font-family: "Lucida Console", Cascadia, Consolas, Monospace;', html)
      html = re.sub(r'.body_background { background-color: #AAAAAA; }', '.body_background { background-color: #FFFFFF; }', html)
      HtmlFile = open(FileName, "w")
      HtmlFile.write(html)
      HtmlFile.close()
      PercList = [TuplesDict.get(90, 0), TuplesDict.get(80, 0), TuplesDict.get(70, 0), TuplesDict.get(60, 0), TuplesDict.get(50, 0)]
      PT.add([nlfsr.getSize(), len(nlfsr.getTaps()), Architecture, Eq, f"{AnfT}, {AnfL}, {AnfD}", Period, OfMax, MissingStates, IsMaxStr, IsPrimeStr, OnesCountB0Str, TrajectoriesCount, f"{Single}, {Double}, {Triple}"] + PercList + [f"""=HYPERLINK("{FileName}", "[CLICK_HERE]")""", repr(nlfsr)])
      try:
        PT.toXls("DATABASE_temp.xlsx")
      except:
        pass
      tt.print(f"Iteration finished ---------------\n{repr(nlfsr)}\n./data/{FileName}")
    try:
      os.remove("DATABASE_temp.xlsx")
    except:
      pass
    tt.close()
    try:
      PT.toXls("DATABASE.xlsx")
    except:
      PT.toXls("DATABASE_newer.xlsx")
    if Scheduler is not None:
      print("\n=== Finished. ===")
      
  @staticmethod
  def getCheckPeriodCode(NlfsrsList : list, FunctionName : str = "customCheckPeriod") -> str:
    MaxSize = 0
    for nlfsr in NlfsrsList:
      if nlfsr._size > MaxSize:
        MaxSize = nlfsr._size
    MaxIt = (1 << MaxSize)
    Result = f"""def {FunctionName}() -> list:
  import numpy as np\n"""
    for i in range(len(NlfsrsList)):
      nlfsr = NlfsrsList[i]
      Result += f"""  nlfsr_{i} = [0 for _ in range({nlfsr._size})]
  nlfsr_{i}[0] = 1
  nlfsr_{i} = np.asarray(nlfsr_{i}, dtype='intc')
  ones_{i} = 1\n"""
    Result += f"""  Found = 0
  AllFound = (1 << {len(NlfsrsList)}) - 1
  NotFoundList = [1] * {len(NlfsrsList)}
  PeriodList = [0 for _ in range({len(NlfsrsList)})]
  Counter = 0
  while (Found != AllFound) and (Counter <= {MaxIt}):
    Counter += 1\n"""
    for i in range(len(NlfsrsList)):
      nlfsr = NlfsrsList[i].copy()
      Size = nlfsr._size
      if not nlfsr.toFibonacci():
        Aio.printError("All Nlfsrs must be convertible to Fibonacci!")
        return ""
      Config = nlfsr._Config
      Result += f"""    # {repr(NlfsrsList[i])}
    # {repr(nlfsr)}
    if NotFoundList[{i}]:
      msb = nlfsr_{i}[0]
      msb_old = msb\n"""
      for Tap in Config:
        Sum = False
        if Tap[0] < 0:
          Sum = True
          for S in Tap[1]:
            if S >= 0:
              Sum = False
        if Sum:
          AndStr = ""
          Second = 0
          for S in Tap[1]:
            S = (abs(S)) % Size
            This = f"""nlfsr_{i}[{S}]"""
            if Second:
              AndStr += " | "
            else:
              Second = 1
            AndStr += f"({This})"
          Result += f"""      msb ^= {AndStr}\n"""
        else:
          GInv = "1 - " if Tap[0] < 0 else ""
          AndStr = ""
          Second = 0
          for S in Tap[1]:
            Inv = "1 - " if  S < 0 else ""
            S = (abs(S)) % Size
            This = f"""{Inv}(nlfsr_{i}[{S}])"""
            if Second:
              AndStr += " & "
            else:
              Second = 1
            AndStr += f"({This})"
          Result += f"""      msb ^= {GInv}({AndStr})\n"""
      Result += f"""      if msb_old != msb:
        if msb:
          ones_{i} += 1
        else:
          ones_{i} -= 1
      nlfsr_{i}[:-1] = nlfsr_{i}[1:]
      nlfsr_{i}[-1] = msb
      #nlfsr_{i} = nlfsr_{i}[1:] + [msb]
      #print({i}, Counter, nlfsr_{i})
      if ones_{i} == 1:
        if nlfsr_{i}[0]:
          NotFoundList[{i}] = 1
          Found |= (1 << {i})
          PeriodList[{i}] = Counter\n"""
    Result += "  return PeriodList"   
    return Result
    
      

def _make_expander(nlfsr, PBar=0, AlwaysCleanFiles = True, SimpleExpanderAllowed = True) -> tuple:
  T = None
  if nlfsr.getSize() <= 15:
    E = nlfsr.createExpander(XorInputsLimit=3, StoreLinearComplexityData=1, StoreCardinalityData=1, PBar=PBar, LimitedNTuples=0, ReturnAlsoTuplesReport=False, StoreOnesCountB0=True, AlwaysCleanFiles=AlwaysCleanFiles, SimpleExpanderAllowed=SimpleExpanderAllowed)
    if not nlfsr.isMaximum():
      T = nlfsr.analyseCycles()
  elif nlfsr.getSize() <= 18:
    E = nlfsr.createExpander(XorInputsLimit=3, StoreLinearComplexityData=0, StoreCardinalityData=1, PBar=PBar, LimitedNTuples=0, ReturnAlsoTuplesReport=False, StoreOnesCountB0=True, AlwaysCleanFiles=AlwaysCleanFiles, SimpleExpanderAllowed=SimpleExpanderAllowed)
    if not nlfsr.isMaximum():
      T = nlfsr.analyseCycles()
  else:
    E = nlfsr.createExpander(XorInputsLimit=3, StoreLinearComplexityData=0, StoreCardinalityData=1, PBar=PBar, LimitedNTuples=1, ReturnAlsoTuplesReport=False, StoreOnesCountB0=True, AlwaysCleanFiles=AlwaysCleanFiles, SimpleExpanderAllowed=SimpleExpanderAllowed) 
  return E, T

def Nlfsr_makeExpanderForRAio(nlfsr) -> tuple:
  E, T = _make_expander(nlfsr, True, True)
  return nlfsr, E, T
    
def _NLFSR_list_database_helper(NLFSR : Nlfsr) -> list:
  Rep = NLFSR.analyseSequences(3)
  Single = Rep.getUniqueCount(1)
  Double = Rep.getUniqueCount(2) - Single
  Triple = Rep.getUniqueCount(3) - Single - Double
  return [Single, Double, Triple]
    
def _NLFSR_find_spec_period_helper(nlrglist : Nlfsr) -> int:
  for nlrg in nlrglist:
    p = nlrg.getPeriod()    
  return nlrglist
def _NLFSR_find_spec_period_helper2(nlrglist : Nlfsr) -> int:
  Results = []
  for nlrg in nlrglist:
    if nlrg.makeBeauty(CheckMaximum=0):
      Results.append(nlrg)
  return Results
def _NLFSR_nonlinear_filtering_helper(nlrglist) -> list:
  Results = []
  for nlrg in nlrglist:
    if nlrg.isLfsr():
      continue
    if nlrg.isSemiLfsr():
      continue
    Results.append(nlrg)
  return Results






class NlfsrFpgaBooster:

  __slots__ = ("_size","_tap_v","_ext_inp_am", "_SM", "_fname")

  def __init__(self, Size = 32, TapVersion = 1, ExtendedInputAmount = 0) -> None:
    self._size = Size
    self._tap_v = TapVersion
    self._ext_inp_am = ExtendedInputAmount
    self._SM = None
    self._fname = None
    
  def getSize(self) -> int:
    return self._size
  
  def getNlfsrListFromFile(self, FileName : str, Verify = True, OnlyMaximumPeriods = False, AllowMaximumPeriods = True, OnlyPrimeNonMaximumPeriods = True,  AllowLfsrs = False, AllowSemiLfsrs = False, Debug = 0, LimitedTo64b = True) -> list:
    Result = []
    Max = (1 << self._size) - 1
    Data = readFile(FileName)
    Accepted = 0
    RowLfsrs = [0, 0, 0, "|", 0]
    RowSemiLfsrs = [0, 0, 0, "|", 0]
    RowNlfsrs = [0, 0, 0, "|", 0]
    RowTotal = [0, 0, 0, "|", 0]
    for Line in tqdm(Data.split("\n"), desc="Parsing file"):
      if len(Line) < 16:
        continue
      if Line[0] == 'S':
        continue
      #R = re.search(r'Period\s*[:=]\s*([ 0-9a-fA-Fx]+)\s*,\s*Config\s*[:=]\s*([ 0-9a-fA-Fx]+)\s*,\s*Pointer\s*[:=]\s*([0-9a-fA-Fx]+)', Line)
      R = re.search(r'Period\s*[:=]\s*([ 0-9a-fA-Fx]+)\s*,\s*Config\s*[:=]\s*([ 0-9a-fA-Fx]+)\s*', Line)
      if R:
        if Debug:
          print()
          print(f"PERIOD = {R.group(1)}")
          print(f"CONFIG = {R.group(2)}")
        try:
          n = self.getNlfsrFromHexString(R.group(2), Debug)
        except:
          Aio.printError(f"Config broken at line\n'{Line}'.")
          continue
        n._period = bau.ba2int(Bitarray.fromStringOfHex(R.group(1)))
        IsLfsr = n.isLfsr()
        IsSemiLfsr = n.isSemiLfsr()
        IsMax = (n._period == Max) 
        IsPrime = Int.isPrime(n._period)
        RowTotal[4] += 1
        if IsLfsr:
          RowLfsrs[4] += 1
        elif IsSemiLfsr:
          RowSemiLfsrs[4] += 1
        else:
          RowNlfsrs[4] += 1
        if IsMax:
          RowTotal[0] += 1
        elif IsPrime:
          RowTotal[1] += 1
        else:
          RowTotal[2] += 1
        if IsLfsr:
          if IsMax:
            RowLfsrs[0] += 1
          elif IsPrime:
            RowLfsrs[1] += 1
          else:
            RowLfsrs[2] += 1
        elif IsSemiLfsr:
          if IsMax:
            RowSemiLfsrs[0] += 1
          elif IsPrime:
            RowSemiLfsrs[1] += 1
          else:
            RowSemiLfsrs[2] += 1
        else:
          if IsMax:
            RowNlfsrs[0] += 1
          elif IsPrime:
            RowNlfsrs[1] += 1
          else:
            RowNlfsrs[2] += 1
        if IsMax and not (OnlyMaximumPeriods or AllowMaximumPeriods):
          continue
        if not IsMax and OnlyMaximumPeriods:
          continue
        if not IsMax and not IsPrime and OnlyPrimeNonMaximumPeriods:
          continue
        if IsLfsr and not AllowLfsrs:
          continue
        if IsSemiLfsr and not AllowSemiLfsrs:
          continue
        Accepted += 1
        Result.append(n)
        if Debug:
          print()
          print(f"{R.group(1)} - {n._period}")
          print(f"{R.group(2)} - {repr(n)}")
          self.getNlfsrFromHexString(R.group(2), 1, Debug=1)
      R = re.search(r'size\s*[:=]\s*([0-9]+)', Line)
      if R:
        self._size = int(R.group(1))
        Aio.print(f"// Found size: {self._size}")    
        Max = (1 << self._size) - 1
        continue
      R = re.search(r'ap\s*version\s*[:=]\s*([0-9]+)', Line)
      if R:
        self._tap_v = int(R.group(1)) % 128
        self._ext_inp_am = int(R.group(1)) // 128
        Aio.print(f"// Found tap version: {self._tap_v}") 
        Aio.print(f"// Found extended input amount: {self._ext_inp_am}") 
        continue  
    Result = Nlfsr.filter(Result)
    PT = PandasTable(["", "Maximum", "Prime", "Other", "|", "TOTAL"])
    PT.add(["------------", "------", "------", "------", "+", "------"])
    PT.add(["LFSRs"] + RowLfsrs)
    PT.add(["Semi-LFSRs"] + RowSemiLfsrs)
    PT.add(["NLFSRs"] + RowNlfsrs)
    PT.add(["------------", "------", "------", "------", "+", "------"])
    PT.add(["TOTAL"] + RowTotal)
    Aio.print("------------------------------------------------")
    PT.print()
    Aio.print("------------------------------------------------")
    Aio.print(f"# Accepted: {Accepted}")
    if Verify:
      if LimitedTo64b:
        exe = CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.getExePath()
      else:
        exe = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
      for R in Result:
        R._exename = exe
      Res2 = []
      for Res in p_imap(_verify_NLFSR, Result, desc="Verification"):
        Res2 += Res
      return Res2
    return Result
  
  def getNlfsrFromHexString(self, Text : str, Debug = 0) -> Nlfsr:
    Config = Bitarray.fromStringOfHex(Text, 32)
    Config.reverse()
    Taps = []
    TapCount = (self._size - int(self._size/2))-3
    if self._ext_inp_am == 1:
      RightExtWord = Config[TapCount*11:TapCount*11+32]
      LeftExtWord = Config[TapCount*11+32:TapCount*11+64]
      UpperBranchSize = (self._size >> 1)
      SelectW = ceil(log2(UpperBranchSize))
    for i in range(TapCount):
      FirstInputIndex = self._size - i
      if self._ext_inp_am == 1:
        if i == 0:
          Inputs = []
          PrimeInputs = [inp for inp in range(self._size-UpperBranchSize, self._size, 1)]
          if Debug:
            print(f"  Right TapMUX {PrimeInputs}")
          for GateInput in range(5):
            BitDefinition = RightExtWord[GateInput*SelectW : GateInput*SelectW + SelectW]
            BitDefinition.reverse()
            BitIndex = bau.ba2int(BitDefinition)
            Input = PrimeInputs[BitIndex % UpperBranchSize]
            Inputs.append(Input)
            if Debug:
              print(f"    Index={BitIndex},\tInput={Input}")
        elif i == (TapCount-1):
          Inputs = []
          PrimeInputs = [inp for inp in range(self._size-UpperBranchSize, self._size, 1)]
          if Debug:
            print(f"  Left TapMUX {PrimeInputs}")
          for GateInput in range(5):
            BitDefinition = LeftExtWord[GateInput*SelectW : GateInput*SelectW + SelectW]
            BitDefinition.reverse()
            BitIndex = bau.ba2int(BitDefinition)
            Input = PrimeInputs[BitIndex % UpperBranchSize]
            Inputs.append(Input)
            if Debug:
              print(f"    Index={BitIndex},\tInput={Input}")
        else:
          Inputs = [inp for inp in range(self._size-i, self._size-i-5, -1)]
      else:
        Inputs = [inp for inp in range(self._size-i, self._size-i-5, -1)]
      Destination = 1 + i
      TapConfig = Config[(i*11):(i*11+11)]
      # tutaj kod tdo ExtendedInputAmount...
      Sources = []
      if self._tap_v == 2:
        for j in range(5):
          if TapConfig[2*j] or TapConfig[2*j+1]:
            if TapConfig[2*j] and TapConfig[2*j+1]:
              #Sources.append(-1 * (FirstInputIndex - j))
              Sources.append(-1 * Inputs[j])
            else:
              #Sources.append(FirstInputIndex - j)
              Sources.append(Inputs[j])
      else:
        for j in range(5):
          if TapConfig[2*j]:
            if TapConfig[2*j+1]:
              #Sources.append(-1 * (FirstInputIndex - j))
              Sources.append(-1 * Inputs[j])
            else:
              #Sources.append(FirstInputIndex - j)
              Sources.append(Inputs[j])
      if len(Sources) > 0:
        if TapConfig[10]:
          Destination *= -1
        Taps.append([Destination, Sources])
      if Debug:
        print(f"  {TapConfig}, S={Sources}, D={Destination}")
      #print(FirstInputIndex, TapConfig, [Destination, Sources])
    #print(TapCount, Config, Taps)
    Success = 0
    for Tap in Taps:
      if len(Tap[1]) > 1:
        Success = 1
        break
    if Success | 1:
      Result = Nlfsr(self._size, Taps)
      if Debug:
        print(f"Result: {repr(Result)}")
      return Result
    return None
  
  def _serial_cbk(self, Line : str):
    if self._fname is None:
      Aio.printError("File name is not defined - log cannot be saved!")
    else:
      writeFile(self._fname, Line + "\n", Append=True)
    R = re.search(r'size\s*[:=]\s*([0-9]+)', Line)
    if R:
      self._size = int(R.group(1))
      Aio.print(f"// Found size: {self._size}")    
      Max = (1 << self._size) - 1
      return
    R = re.search(r'ap\s*version\s*[:=]\s*([0-9]+)', Line)
    if R:
      self._tap_v = int(R.group(1)) % 128
      self._ext_inp_am = int(R.group(1)) // 128
      Aio.print(f"// Found tap version: {self._tap_v}") 
      Aio.print(f"// Found extended input amount: {self._ext_inp_am}")   
      return      
    R = re.search(r'Period\s*[:=]\s*([ 0-9a-fA-Fx]+)\s*,\s*Config\s*[:=]\s*([ 0-9a-fA-Fx]+)\s*', Line)
    if R:
      Max = (1 << self._size) -1
      n = self.getNlfsrFromHexString(R.group(2), 0)
      n._period = bau.ba2int(Bitarray.fromStringOfHex(R.group(1)))
      IsLfsr = n.isLfsr()
      IsSemiLfsr = n.isSemiLfsr()
      IsMax = (n._period == Max) 
      IsPrime = Int.isPrime(n._period)
      if IsMax:
        Period = "MAX"
      elif IsPrime:
        Period = "PRIME    " + str(n._period / Max) + " of Max"
      else:
        Period = "Other    " + str(n._period / Max) + " of Max"
      if IsLfsr:
        Type = "     LFSR"
      elif IsSemiLfsr:
        Type = "Semi-LFSR"
      else:
        Type = "    NLFSR"
      Size = str(self._size)
      Aio.print(f"Found {Size}-bit {Type},   Period: {Period}")
      return
    Aio.print(f"// {self._size}-bit: {Line}")
    
  def isSerialLoggerWorking(self):
    return (self._SM is not None)
    
  def stopSerialLogger(self):
    if self.isSerialLoggerWorking():
      self._SM.__delete__()
      self._SM = None
      self._fname = None
  
  def startSerialLogger(self, FileName : str, Baud=115200, Restrictions0to3 : int = 2):
    self.stopSerialLogger()
    self._fname = FileName
    self._SM = SerialMonitor(None, Baud, Callback=self._serial_cbk)
    self.runProFpga()
    self.setRestrictions(Restrictions0to3)
    self.changeRNGTrajectory()
    
  def runProFpga(self):
    if self._SM is not None:
      self._SM.print("q")
      
  def setRestrictions(self, Restrictions0to3 : int = 3):
    if self._SM is not None:
      if Restrictions0to3 == 0:
        self._SM.print("a")
      elif Restrictions0to3 == 1:
        self._SM.print("b")
      elif Restrictions0to3 == 2:
        self._SM.print("c")
      else:
        self._SM.print("d")
        
  def changeRNGTrajectory(self):
    if self._SM is not None:
      for _ in range(5):
        i = random.randint(1, 4)
        self._SM.print(str(i))
        time.sleep(0.1)
      

def _verify_NLFSR(nlfsr : Nlfsr) -> Nlfsr:
  P = nlfsr._period
  nlfsr._period = None
  if (P != nlfsr.getPeriod()):
    Aio.print(f"Period invalid - {P} while should be {nlfsr._period}:\n  {repr(nlfsr)}")
    return []
  return [nlfsr]




# TUI =====================================================/

def _NLFSR_sim_refresh(n = 32):
    global _NLFSR, _NLFSR_SIM
    Lst2 = []
    Lst1 = _NLFSR.getValues(n)
    for I in Lst1:
      Lst2.append([Bitarray.toString(I), I.count(1)])
    _NLFSR_SIM = Lst2

def _NLFSR_sim_append():
    global _NLFSR_SIM
    _NLFSR_sim_refresh(len(_NLFSR_SIM)<<1)
    

class _NlfsrTui_SetSize(TextualWidgets.Static):
  def compose(self):
    global _NLFSR
    yield TextualWidgets.Label(" \nNew size:", id="set_size_lbl")
    yield TextualWidgets.Input(str(_NLFSR.getSize()), id="set_size")

class _NlfsrTui_AddTap(TextualWidgets.Static):
  def compose(self):
    yield TextualWidgets.Label(" \nFrom", id="add_tap_from_lbl")
    yield TextualWidgets.Input(id="add_tap_from")
    yield TextualWidgets.Label(" \nTo", id="add_tap_to_lbl")
    yield TextualWidgets.Input(id="add_tap_to")
    
class _NlfsrTui_LeftMenu(TextualWidgets.Static):
    def compose(self) -> TextualApp.ComposeResult:
        global _NLFSR, _NLFSR_UNDO
        yield _NlfsrTui_SetSize()
        yield TextualWidgets.Button("Set size", id="btn_set_size")
        yield TextualWidgets.Label(" ")
        yield _NlfsrTui_AddTap()
        yield TextualWidgets.Button("Add tap", id="btn_add_tap")
        yield TextualWidgets.Label(" ")
        yield TextualWidgets.DataTable(id="dt")
        yield TextualWidgets.Label(" ")
        if _NLFSR_UNDO is not None:
          yield TextualWidgets.Button("Undo last 'breaking tap' operation", id="undo")
          yield TextualWidgets.Label(" ")
        yield TextualWidgets.Button("More simulation steps", id="asim")
        yield TextualWidgets.Label(" ")
        yield TextualWidgets.Button("OK", id="btn_ok", variant="success")
        yield TextualWidgets.Button("Cancel", id="btn_cancel", variant="error")
    def refreshTable(self):
        global _NLFSR
        Taps = _NLFSR.getTaps()
        table = self.query_one(TextualWidgets.DataTable)
        table.clear()
        if len(Taps) > 0:
          i1, i0 = 0, 0
          for i in range(len(Taps)):
              Tap = Taps[i]
              Row = [f"F{i1}{i0}", str(Tap), "[ROTL]", "[ROTR]", "[REMOVE]"]
              if _NLFSR.isTapLinear(i):
                Row.append("[BREAK]")
              else:
                Row.append("")
              table.add_row(*Row)
              i0 += 1
              if i0 == 10:
                i1 += 1
                i0 = 0
              if i1 == 10:
                i1 = 0
    def on_mount(self):
        global _NLFSR
        table = self.query_one(TextualWidgets.DataTable)
        table.add_columns("Func", "TAP", ".", ".", ".", ".")
        self.refreshTable()
    def on_data_table_cell_selected(self, event: TextualWidgets.DataTable.CellSelected) -> None:
        global _NLFSR
        if event.coordinate.column > 0:
            TapIndex = event.coordinate.row
            if event.coordinate.column == 2:
                _NLFSR.rotateTap(TapIndex, -1, FailIfRotationInvalid=1, SortTaps=0)
            elif event.coordinate.column == 3:
                _NLFSR.rotateTap(TapIndex, 1, FailIfRotationInvalid=1, SortTaps=0)
            elif event.coordinate.column == 4:
                _NLFSR._Config.remove(_NLFSR._Config[TapIndex])
                _NLFSR._period = None
            elif event.coordinate.column == 5:
                if _NLFSR.isTapLinear(TapIndex):
                  self.app.TAP_INDEX = TapIndex
                  self.app.EXE = "break_tap"
                  self.app.exit()
            self.refreshTable()
            _NLFSR_sim_refresh()
    def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
        global _NLFSR, _NLFSR_SIM, _NLFSR_UNDO
        if event.button.id == "btn_add_tap":
          try:
            ATap = self.query_one(_NlfsrTui_AddTap)
            From = ATap.query_one("#add_tap_from").value
            To = int(ATap.query_one("#add_tap_to").value)
            if From[0] != "[":
              From = "[" + From
            if From[-1] != "]":
              From = From + "]"
            From = list(ast.literal_eval(From))
            Tap = [To, From]
            Taps = _NLFSR._Config
            Size = _NLFSR.getSize()
            Taps.append(Tap)
            _NLFSR._period = None
            self.refreshTable()
            _NLFSR_sim_refresh()
          except:
            pass
        elif event.button.id == "btn_set_size":
          SizeW = self.query_one(_NlfsrTui_SetSize)
          Size = int(SizeW.query_one("#set_size").value)
          if Size < 0:
            return
          Taps = _NLFSR._taps
          for Tap in Taps:
            for V in Tap:
              if V >= Size:
                return
          _NLFSR._size = Size
          _NLFSR.clear()
          _NLFSR._baValue = bitarray(Size)
          _NLFSR.reset()
          _NLFSR._period = None
          _NLFSR_sim_refresh()
        elif event.button.id == "asim":
            _NLFSR_sim_append()
        elif event.button.id == "undo":
            _NLFSR = _NLFSR_UNDO.copy()
            self.refreshTable()
            _NLFSR_sim_refresh()
        elif event.button.id == "btn_ok":
            self.app.EXE = "ok"
            self.app.exit()
        elif event.button.id == "btn_cancel":
            self.app.EXE = "cancel"
            self.app.exit()
        
class _NlfsrTui_VTop(TextualWidgets.Static):
    LfsrDraw = TextualReactive.reactive("")
    Lbl = None
    def compose(self):
        self.Lbl = TextualWidgets.Label()
        yield self.Lbl 
    def on_mount(self):
        self.set_interval(0.2, self.update_LfsrDraw)
    def update_LfsrDraw(self):
        global _NLFSR
        self.LfsrDraw = _NLFSR.copy().getDraw()
    def watch_LfsrDraw(self):
        self.Lbl.update(self.LfsrDraw)
        
class _NlfsrTui_VMiddle(TextualWidgets.Static):
    Period = TextualReactive.reactive(None)
    lbl = None
    def compose(self):
      self.lbl = TextualWidgets.Label(id="lbl_period")
      yield TextualContainers.Horizontal(
        TextualWidgets.Button("Period", id="btn_period"),
        TextualWidgets.Label(" "),
        self.lbl,
        TextualWidgets.Button("Analyse Sequences", id="btn_seq"),
        TextualWidgets.Label(" "),
        TextualWidgets.Button("Create Expander", id="btn_exp"),
      )
    def on_mount(self):
        self.set_interval(0.2, self.update_period)
    def update_period(self):
        global _NLFSR
        self.Period = _NLFSR._period
    def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
        global _NLFSR
        if event.button.id == "btn_period":
          _NLFSR.getPeriod()
        if event.button.id == "btn_seq":
          self.app.EXE = "seq"
          self.app.exit()
        if event.button.id == "btn_exp":
          self.app.EXE = "exp"
          self.app.exit()
    def watch_Period(self):
        global _NLFSR
        PeriodStr = "unknown"
        PrimString = "No"
        if self.Period is not None:
          PeriodStr = str(self.Period)
          if self.Period == ((1 << _NLFSR._size) - 1):
            PrimString = "Yes"
        else:
          PrimString = "unknown"
        self.lbl.update(f"Period: {PeriodStr}\nPrimitive: {PrimString}")
      
class _NlfsrTui_VBottom(TextualWidgets.Static):
    SimROws = TextualReactive.reactive([])
    def compose(self):
        yield TextualWidgets.DataTable(id="simt")
        yield TextualWidgets.Label("")
    def on_mount(self):
        _NLFSR_sim_refresh()
        self.set_interval(0.5, self.update_simdata)
        table = self.query_one(TextualWidgets.DataTable)
        table.add_columns("#Cycle", "Value (n-1, ..., 0)", "#1s")
    def update_simdata(self):
        global _NLFSR_SIM
        self.SimROws = _NLFSR_SIM
    def watch_SimROws(self):
        global _NLFSR_SIM
        table = self.query_one(TextualWidgets.DataTable)
        table.clear()
        Aio.print("CLEARED")
        for i in range(len(_NLFSR_SIM)):
          v = _NLFSR_SIM[i]
          Aio.print(v)
          table.add_row(i, v[0], v[1])
        
class _NlfsrTui_VLayout(TextualWidgets.Static):
    def compose(self) -> TextualApp.ComposeResult:
        yield _NlfsrTui_VTop()
        yield _NlfsrTui_VMiddle()
        yield _NlfsrTui_VBottom()
                
class _NlfsrTui_HLayout(TextualWidgets.Static):
    def compose(self) -> TextualApp.ComposeResult:
        yield _NlfsrTui_LeftMenu()
        yield _NlfsrTui_VLayout()
    
class _NlfsrTui(TextualApp.App):
    BINDINGS = [("q", "quit", "Quit"), ('a', 'asim', 'Append values')]
    CSS_PATH = "tui/nlfsr.css"
    TAP_INDEX = 0
    def compose(self) -> TextualApp.ComposeResult:
        self.dark=False
        yield TextualWidgets.Header()
        yield _NlfsrTui_HLayout()
        yield TextualWidgets.Footer()
        self.EXE = ""
    def action_asim(self):
        _NLFSR_sim_append()





class _BreakNlfsrTapTui(TextualApp.App):
  BINDINGS = [("q", "quit", "Quit")]
  CSS_PATH = "tui/breaknlfsrtap.css"
  EXE = ""
  OBJ = Nlfsr(8, [[0,[3]]])
  TAP_INDEX = 0
  EXPR = TextualReactive.reactive("")
  ELIST = []
  VARB = TextualReactive.reactive(0)
  VARC = TextualReactive.reactive(0)
  NEW_TAPS = TextualReactive.reactive([])
  infolbl = None
  def compose(self) -> TextualApp.ComposeResult:
    self.dark=False
    self.EXE = ""
    self.ELIST = []
    self.NEW_TAPS = []
    self.VARB, self.VARC = 0, 0
    tbl = TextualWidgets.DataTable()
    tbl.add_columns("# Variables", "# Monomials", "Expression")
    for Pair in [(2,2), (2,3), (2,4), (3,3), (3,4), (3,5)]:
      for E in DB.getReducibleToAExpressionsList(Pair[0], Pair[1]):
        tbl.add_row(Pair[0], Pair[1], E)
        self.ELIST.append(E)
    self.infolbl = TextualWidgets.Label("", id="info_lbl")
    yield TextualWidgets.Header()
    yield TextualContainers.Horizontal(
      TextualContainers.Vertical(
        TextualWidgets.Static(self.OBJ.getDraw(), id="draw_lbl"),
        TextualWidgets.Label(" "),
        TextualContainers.Horizontal(
          TextualWidgets.Label("\nFF index for variable 'b':"),
          TextualWidgets.Input(id="input_b"),
          id="var_b"
        ),
        TextualContainers.Horizontal(
          TextualWidgets.Label("\nFF index for variable 'c':"),
          TextualWidgets.Input(id="input_c"),
          id="var_c"
        ),
        self.infolbl,
        TextualWidgets.Button("OK", id="btn_ok", variant="success"),
        TextualWidgets.Label(" "),
        TextualWidgets.Button("Cancel", id="btn_cancel", variant="error"),
        id="left_block"
      ),
      TextualContainers.Vertical(
        tbl,
        id="right_block"
      ),
      id="main_window"
    )
    yield TextualWidgets.Footer()
  def update_draw(self):
    DrawLbl = self.query_one("#draw_lbl")
    if len(self.NEW_TAPS) > 0:
      n2 = self.OBJ.copy()
      n2._Config.remove(n2._Config[self.TAP_INDEX])
      n2._Config += self.NEW_TAPS
      DrawLbl.update(n2.getDraw())
    else:
      DrawLbl.update(self.OBJ.getDraw())
  def on_mount(self):
    self.set_interval(0.2, self.update_vars)
    self.set_interval(0.5, self.update_draw)
  def update_vars(self):
    InputB = self.query_one("#input_b")
    InputC = self.query_one("#input_c")
    try:
      self.VARB = abs(int(InputB.value)) % self.OBJ._size
    except:
      self.VARB = 0
    try:
      self.VARC = abs(int(InputC.value)) % self.OBJ._size
    except:
      self.VARC = 0
  def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
    if event.button.id == "btn_cancel":
      self.EXE = ""
      self.exit()
    elif event.button.id == "btn_ok":
      self.EXE = "ok"
      self.exit()
  def on_data_table_cell_selected(self, event: TextualWidgets.DataTable.CellSelected) -> None:
    EIndex = event.coordinate.row
    self.EXPR = self.ELIST[EIndex]
  def update_info(self):
    try:
      BTaps = self.OBJ.getTapsForBreaking(self.TAP_INDEX, self.EXPR, [self.VARB, self.VARC])
    except:
      BTaps = []
    self.NEW_TAPS = BTaps
    txt = f"""=========== INFO ===============
Tap def:       {self.OBJ._Config[self.TAP_INDEX]}
Tap expr:      {self.OBJ.getExprFromTap(self.OBJ._Config[self.TAP_INDEX])}
Breaking expr: {self.EXPR}
New taps:
"""
    for BTap in BTaps:
      txt += f"  {BTap}\n"
    txt += "New tap expressions:\n"
    for BTap in BTaps:
      txt += f"  {self.OBJ.getExprFromTap(BTap)}\n"
    try:
      self.infolbl.update(txt)
    except:
      pass
  def watch_EXPR(self):
    self.update_info()
  def watch_VARB(self):
    self.update_info()
  def watch_VARC(self):
    self.update_info()
    
