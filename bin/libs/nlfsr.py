from libs.cpp_program import *
from libs.lfsr import *
from libs.utils_list import *
from libs.utils_bitarray import *
from libs.asci_drawing import *
from bitarray import *
import multiprocessing
from random import uniform
from tqdm.contrib.concurrent import process_map


class Nlfsr(Lfsr):
  _baValue = None
  _size = 0
  _Config = []
  _points = []
  _start = bitarray()
  _offset = 0
  _exename = ""
  def clear(self):
    pass
  def copy(self):
    return Nlfsr(self)
  def __del__(self):
    pass
  def printFullInfo(self):
    Aio.print(self.getFullInfo())
  def getFullInfo(self):
    Result = f'{self._size}-bit NLFSRs taps list:\n'
    for C in self._Config:
      D = C[0]
      Slist = C[1]
      DInv = False
      if D < 0:
        DInv = True      
      D = D % self._size
      Result += f' {D} {AsciiDrawing_Characters.LEFT_ARROW} '
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
            Result += " AND"
          First = False
          Result += " "
          if S < 0:
            Result += "~"
          S = abs(S) % self._size
          Result += f'{S}'
      if DInv:
        Result += " )"
      Result += "\n"
    return Result[:-1]
  def __init__(self, Size : int, Config = []) -> None:
    if Aio.isType(Size, "Nlfsr"):
      self._size = Size._size      
      self._Config = Size._Config.copy()
      self._baValue = Size._baValue.copy()
      self._points = Size._points
      self._exename = Size._exename
    else:  
      self._size = Size
      self._Config = Config
      def msortf(e):
        return abs(e[0])%Size
      self._Config.sort(key=msortf)
      self._baValue = bitarray(self._size)
      self._exename = ""
      self.reset()
  def __repr__(self) -> str:
    result = "Nlfsr(" + str(self._size) + ", " + str(self._Config) + ")"
    return result
  def _next1(self):
    NewVal = Bitarray.rotr(self._baValue)
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      DIndex = -(abs(D) % self._size)-1
      AndResult = 1
      if Aio.isType(S, 0):
        SIndex = -(abs(S) % self._size)-1
        Bit = self._baValue[SIndex]
        if S < 0:
          Bit = 1 - Bit
        AndResult = Bit
      else:
        for Si in S:
          SIndex = -(abs(Si) % self._size)-1
          Bit = self._baValue[SIndex]
          if Si < 0:
            Bit = 1 - Bit
          AndResult &= Bit
      if D < 0:
        AndResult = 1 - AndResult
      NewVal[DIndex] ^= AndResult
    self._baValue = NewVal
    return self._baValue
  def next(self, steps=1):
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return 0
    else:
      for _ in range(steps):
        self._next1()
    return self._baValue
  def getPeriod(self):
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
    if len(self._exename) > 0:
      Res = Aio.shellExecute(self._exename + " " + ArgStr)   
    else:
      if WithInverters:
        Res = CppPrograms.NLSFRPeriodCounterInvertersAllowed.run(ArgStr)
      else:
        Res = CppPrograms.NLSFRPeriodCounter.run(ArgStr)
    try:
      return int(Res)
    except:
      return 0
  def isMaximum(self):
    return self.getPeriod() == ((1<<self._size)-1)
  
  def makeNLRingGeneratorsFromPolynomial(Poly : Polynomial, InvertersAllowed = False) -> list:
    RG = Lfsr(Poly, RING_GENERATOR)
    Taps = RG._taps
    Size = RG._size
    Bounds = []
    for Tap in Taps:
      Bounds.append(Tap[0])
      Bounds.append(Tap[1])
    Bounds += [Size>>1, (Size>>1), 1, 2, 0]
    AOptionsList = []
    for Tap in Taps:
      AOptions = []
      S = Tap[0]
      D = Tap[1]
      A = (S-1)%Size
      while 1:
        AOptions.append(A)
        if A in Bounds:
          break
        A = (A-1)%Size
      A = (S+1)%Size
      while 1:
        AOptions.append(A)
        if A in Bounds:
          break
        A = (A+1)%Size
      ProposedTaps = [ [D, [S]] ]
      for AIn in AOptions:
        if D == 0:
          D = Size
        for DS in range(1, -2 if InvertersAllowed else 0, -2):
          ProposedTaps.append([DS * D, [S, AIn]])
          if InvertersAllowed:
            ProposedTaps.append([DS * D, [-S, AIn]])
            ProposedTaps.append([DS * D, [S, -AIn]])
            ProposedTaps.append([DS * D, [-S, -AIn]])
      AOptionsList.append(ProposedTaps)
    Permutations = List.getPermutationsPfManyLists(*AOptionsList)[1:]
    Results = []
    for P in Permutations:
      Results.append(Nlfsr(Size, P))
    return Results
  def findNLRGsWithSpecifiedPeriod(Poly : Polynomial, PeriodLengthMinimumRatio = 1, OnlyPrimePeriods = False, InvertersAllowed = False):
    #Pool = multiprocessing.Pool()
    if InvertersAllowed:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
#      if not CppPrograms.NLSFRPeriodCounterInvertersAllowed.Compiled:
#        CppPrograms.NLSFRPeriodCounterInvertersAllowed.compile()
    else:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
#      if not CppPrograms.NLSFRPeriodCounter.Compiled:
#        CppPrograms.NLSFRPeriodCounter.compile()
    InputSet = Nlfsr.makeNLRingGeneratorsFromPolynomial(Poly, InvertersAllowed)
    for i in range(len(InputSet)):
      InputSet[i]._exename = exename
    Periods = process_map(_nlfsr_find_spec_period_helper, InputSet, chunksize=10)
    #Periods = Pool.map(_nlfsr_find_spec_period_helper, InputSet)
    #Pool.close()
    #Pool.join()
    Results = []
    eps = 0.0
    PMR = PeriodLengthMinimumRatio - eps
    for i in range(len(InputSet)):
      p, nlrg = Periods[i], InputSet[i]
      pmax = Int.mersenne(nlrg._size)
      ratio = p / pmax
      if (ratio < PMR):
        continue
      if OnlyPrimePeriods and (not Int.isPrime(p)):
        continue
      Results.append([nlrg, p, ratio])
#      print([nlrg, p, ratio])
    return Results
    
    
def _nlfsr_find_spec_period_helper(nlrg : Nlfsr) -> int:
  p = nlrg.getPeriod()
#  print(repr(nlrg), "\t", p)
  return p
