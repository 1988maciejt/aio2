from libs.cpp_program import *
from libs.lfsr import *
from libs.utils_list import *
from libs.utils_bitarray import *
from libs.asci_drawing import *
from libs.pandas_table import *
from pyeda.inter import *
from p_tqdm import *
from bitarray import *
from libs.generators import *

  
class Nlfsr(Lfsr):
  _baValue = None
  _size = 0
  _Config = []
  _points = []
  _start = bitarray()
  _offset = 0
  _exename = ""
  _period = 0
  def clear(self):
    pass
  def copy(self):
    return Nlfsr(self)
  def __del__(self):
    pass
  def printFullInfo(self, Simplified = False):
    Aio.print(self.getFullInfo(Simplified))
  def getFullInfo(self, Simplified = False, Header = True):
    Result = ""
    if Header:
      Result = f'{self._size}-bit NLFSRs taps list:\n'
    if not Simplified:
      for C in self._Config:
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
    else:
      EqDict = {}
      for C in self._Config:
        D = C[0]
        Slist = C[1]
        DInv = False
        if D < 0:
          DInv = True      
        D = abs(D) % self._size
        dest_str = f'Q[{D}]'
        expr_line = ''
        if DInv:
          expr_line += "~("
        if Aio.isType(Slist, 0):
          expr_line += " "
          if Slist < 0:
            expr_line += "~"
          Slist = abs(Slist) % self._size
          expr_line += f'Q[{Slist}]'
        else:
          First = True
          for S in Slist:
            if not First:
              expr_line += " &"
            First = False
            expr_line += " "
            if S < 0:
              expr_line += "~"
            S = abs(S) % self._size
            expr_line += f'Q[{S}]'
        if DInv:
          expr_line += " )"
        if dest_str in EqDict:
          EqDict[dest_str] = f'({EqDict[dest_str]}) ^ ({expr_line})'
        else:
          EqDict[dest_str] = expr_line
      for key in EqDict.keys():
        Result += f' {key} <= {espresso_exprs(expr(EqDict[key]).to_dnf())[0]}\n'
#        EqDict[key] = espresso_exprs(expr(EqDict[key]).to_dnf())[0]
      Result = Result.replace('Q[', '')
      Result = Result.replace(']', '')
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
      self._Config = []
      for C in Config:
        D = C[0]
        S = C[1]
        if Aio.isType(S, []):
          S.sort()
        self._Config.append([D, S])
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
    NewVal = Bitarray.rotl(self._baValue)
    for Tap in self._Config:
      D = Tap[0]
      S = Tap[1]
      DIndex = (abs(D) % self._size)
      AndResult = 1
      if Aio.isType(S, 0):
        SIndex = (abs(S) % self._size)
        Bit = self._baValue[SIndex]
        if S < 0:
          Bit = 1 - Bit
        AndResult = Bit
      else:
        for Si in S:
          SIndex = (abs(Si) % self._size)
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
    a = self._Config.copy()
    b = Another._Config.copy()
    if len(a) != len(b):
      return False
    for ai in a:
      bc = b.copy()
      for bi in bc:
#        print(ai, bi)
        if self._areTapsEquivalent(ai, bi):
#          print("ARE!")
          b.remove(bi)
    return len(b) == 0
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
    
  def _makeNLRingGeneratorsFromPolynomial(Poly : Polynomial, LeftRightAllowedShift = 2, InvertersAllowed = 1, MaxAndCount = 0, BeautifullOnly = False, Filter = True) -> list:
    RG = Lfsr(Poly, RING_GENERATOR)
    Taps = RG._taps
    Size = RG._size
    AOptionsList = []
    for Tap in Taps:
      AOptions = []
      S = Tap[0]
      D = Tap[1]
      for ai in range(S-LeftRightAllowedShift, S+LeftRightAllowedShift+1):
        if ai == S:
          continue
        A = ai
        while A <= 0: 
          A += Size
        while A > Size:
          A -= Size
        AOptions.append(A)
      ProposedTaps = [ [D, [S]] ]
      for AIn in AOptions:
        if D == 0:
          D = Size
        ProposedTaps.append([D, [S, AIn]])
        if InvertersAllowed:
          ProposedTaps.append([-D, [S, AIn]])
          ProposedTaps.append([D, [-S, AIn]])
          ProposedTaps.append([D, [S, -AIn]])
#        for DS in range(1, -2 if InvertersAllowed else 0, -2):
#          ProposedTaps.append([DS * D, [S, AIn]])
#          if InvertersAllowed:
#            ProposedTaps.append([DS * D, [-S, AIn]])
#            ProposedTaps.append([DS * D, [S, -AIn]])
#            ProposedTaps.append([DS * D, [-S, -AIn]])
      AOptionsList.append(ProposedTaps)
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
      if BeautifullOnly:
        Results2 = []
        Generator = Generators()
        Chunk = 50
        Total = len(Results) // Chunk +  + (1 if len(Results) % Chunk > 0 else 0)
        Iter = p_uimap(_nlfsr_find_spec_period_helper2, Generator.subLists(Results, Chunk), total=Total, desc=f'Filtering beautifull (x{Chunk})')
        for I in Iter:
          Results2 += I
        Results = Results2  
        del Generator
      if Filter:
        Results = Nlfsr.filter(Results)
      yield Results
  
  def printNLRGsWithSpecifiedPeriod(Poly : Polynomial, LeftRightAllowedShift = 1, PeriodLengthMinimumRatio = 1, OnlyPrimePeriods = False, InvertersAllowed = True, MaxAndCount = 0, BeautifullOnly = False, Filter = True, Iterate = True, n = 0, BreakIfNoResultAfterNIterations = 0) -> int:
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
    Results = Nlfsr.findNLRGsWithSpecifiedPeriod(Poly, LeftRightAllowedShift, PeriodLengthMinimumRatio, OnlyPrimePeriods, InvertersAllowed, MaxAndCount, BeautifullOnly, Filter, Iterate, n, BreakIfNoResultAfterNIterations)
    Canonical = "Canonical"
    NlfsrObject = "Python Object"
    Equations = "Taps"
    RC = "Rev/Compl"
    FullPT = PandasTable([RC, Canonical, Equations, NlfsrObject], AutoId=1, AddVerticalSpaces=1)
    for R in Results:
      FullPT.add([
        f'  \nComplement\nReversed\nRev.,Compl.',
        f'{R.toBooleanExpressionFromRing(Shorten=1)}\n\
  {R.toBooleanExpressionFromRing(Complementary=1, Shorten=1)}\n\
  {R.toBooleanExpressionFromRing(Reversed=1, Shorten=1)}\n\
  {R.toBooleanExpressionFromRing(Reversed=1, Complementary=1, Shorten=1)}',
        R.getFullInfo(Header=0),
        repr(R)
      ])     
    Aio.print()
    FullPT.print()
    Aio.print()
    return len(FullPT)
    
  def findNLRGsWithSpecifiedPeriod(Poly : Polynomial, LeftRightAllowedShift = 1, PeriodLengthMinimumRatio = 1, OnlyPrimePeriods = False, InvertersAllowed = True, MaxAndCount = 0, BeautifullOnly = False, Filter = True, Iterate = True, n = 0, BreakIfNoResultAfterNIterations = 0) -> list:
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
    """
    if Iterate and Aio.isType(Poly, "Polynomial"):
      Results = []
      Exclude = []
      NoResultCounter = 0
      for p in Poly:
        if p in Exclude:
          continue
        Exclude.append(p.getReciprocal())
        print(f'Looking for {p}     Found so far: {len(Results)}')
        ResultsSub = Nlfsr.findNLRGsWithSpecifiedPeriod(p, LeftRightAllowedShift, PeriodLengthMinimumRatio, OnlyPrimePeriods, InvertersAllowed, MaxAndCount, BeautifullOnly, Filter, False, n-len(Results))
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
        LastLen = len(Results)
      if len(Results) > n > 0:
        Results = Results[:n]
      return Results
    if InvertersAllowed:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
#      if not CppPrograms.NLSFRPeriodCounterInvertersAllowed.Compiled:
#        CppPrograms.NLSFRPeriodCounterInvertersAllowed.compile()
    else:
      exename = CppPrograms.NLSFRPeriodCounterInvertersAllowed.getExePath()
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
    for InputSet in Nlfsr._makeNLRingGeneratorsFromPolynomial(Poly, LeftRightAllowedShift, InvertersAllowed, MaxAndCount, BeautifullOnly, False):
      for i in range(len(InputSet)):
        InputSet[i]._exename = exename
      Generator = Generators()
      WasResult = 0
      Total = len(InputSet) // Chunk + (1 if len(InputSet) % Chunk > 0 else 0)
      Iter = p_uimap(_nlfsr_find_spec_period_helper, Generator.subLists(InputSet, Chunk), total=Total, desc=f'Simulating NLFSRs (x{Chunk})')
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
    Manager = multiprocessing.Manager()
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
  
  def filter(NlfsrList : list) -> list:
#    Result = Nlfsr.filterInverted(NlfsrList)
#    Result = Nlfsr.filterEquivalent(Result)
#    return Result
    Result = []
    iList = []
    for nlfsr in NlfsrList:
      iList.append(nlfsr.copy())
    for n1 in tqdm(iList, desc="Filtering NLFSRs"):
      Add = 1
      for n2 in Result:
        if n1.isInverted(n2) or n1.isEquivalent(n2):
          Add = 0
          break
      if Add:
        Result.append(n1)
    return Result
  def toBooleanExpressionFromRing(self, Complementary = False, Reversed = False, Shorten = False) -> str:
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
      S = Tap[1]
      if Aio.isType(S, 0):
        if S == 0:
          S = self._size
        if Complementary:
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
          if Complementary:
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
        RE = f'NOT ( {RE} )'
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
        
        

    
class NlfsrList:
  def analyseSequences(NlfsrsList) -> list:      
    return Nlfsr.analyseSequencesBatch(NlfsrsList)
        
      
    
    
def _nlfsr_find_spec_period_helper(nlrglist : Nlfsr) -> int:
  for nlrg in nlrglist:
    p = nlrg.getPeriod()
    nlrg._period = p
  return nlrglist
def _nlfsr_find_spec_period_helper2(nlrglist : Nlfsr) -> int:
  Results = []
  for nlrg in nlrglist:
    if nlrg.makeBeauty(CheckMaximum=0):
      Results.append(nlrg)
  return Results


  
