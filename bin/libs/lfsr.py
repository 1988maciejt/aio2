from lib2to3.pgen2.tokenize import TokenError
from libs.utils_bitarray import *
from libs.binstr import *
from libs.aio import *
from libs.database import *
from libs.utils_array import *
from libs.utils_int import *
from libs.cache import *
from libs.asci_drawing import *
from libs.phaseshifter import *
import math
from tqdm import *
import multiprocess
from p_tqdm import *
from libs.generators import *
import copy
import gc
from bitarray import *
import bitarray.util as bau
from libs.programmable_lfsr_config import *
from sympy import *
from sympy.logic import *
from libs.fast_anf_algebra import *
from libs.pandas_table import *
#from tqdm.contrib.concurrent import process_map

# TUI =====================================================

import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive

_LFSR = None
_LFSR_SIM = []



class MSequencesReport:
  """This class is used to hold the result of MSequence analysis.
  """
  _rep = {}
  _uniques = {}
  _max = 0
  _title = ""
  SourceObject = None
  
  def __str__(self) -> str:
    return self.getReport() 
  
  def getTitle(self) -> str:
    """Returns a string containing the report's title.
    """
    return self._title
  
  def getUniqueCount(self, PhaseShifterGatesInputs = 0) -> int:
    """get the number ofunique sequences.

    Args:
        PhaseShifterGatesInputs (int, optional): maximum count of inputs of phase shifter's XORs.. Defaults to 0 (no limit).
    """
    if PhaseShifterGatesInputs <= 0 or PhaseShifterGatesInputs > self._max:
      PhaseShifterGatesInputs = self._max
    Sum = 0
    for i in range(1, PhaseShifterGatesInputs+1):
      Sum += self._uniques[i]
    return Sum
  
  def printReport(self, PhaseShifterGatesInputs = 0) -> str:
    Aio.print(self.getReport(PhaseShifterGatesInputs))
    
  def getReport(self, PhaseShifterGatesInputs = 0) -> str:
    """returns a string containing the full report of MSequence analysis.

    Args:
        PhaseShifterGatesInputs (int, optional): maximum count of inputs of phase shifter's XORs.. Defaults to 0 (no limit).
    """
    Lines = ""
    if PhaseShifterGatesInputs <= 0 or PhaseShifterGatesInputs > self._max:
      PhaseShifterGatesInputs = self._max
    Lines += f'\nUNIQUE SEQUENCES: {self.getUniqueCount(PhaseShifterGatesInputs)}'
    PT = PandasTable(["XOR size", "XORed signals", "Sequence"])
    for i in range(1, PhaseShifterGatesInputs+1):
      SDict = self._rep[i]
      for key in SDict.keys():
        PT.add([i, key, SDict[key]])
    Lines += "\n\n" + PT.toString()  
    return Lines
  
  def printReport(self, PhaseShifterGatesInputs = 0):
    """Prints the full report of MSequence analysis.

    Args:
        PhaseShifterGatesInputs (int, optional): maximum count of inputs of phase shifter's XORs.. Defaults to 0 (no limit).
    """
    Aio.print(self.getReport(PhaseShifterGatesInputs))




# POLYNOMIAL CLASS ================

class Polynomial:
  pass
class Polynomial:
  """This object represents Polynomials in GF(2)."""
  __slots__ = ("_coefficients_list",
               "_sign_list",
               "_balancing",
               "_bmin",
               "_bmax",
               "_positions",
               "_mindist",
               "_lf",
               "_notes",
               "_CoefficientList",
               "_CoeffsCount",
               "_DontTouchBounds",
               "_OddOnly",
               "_IterationStartingPoint",
               "_mnext",
               "_first")
  
  def _getAllPrimitivesHavingSpecifiedCoeffsHelper(self, FromTo : list):
    Polys = self._getAllHavingSpecifiedCoeffsHelper(FromTo)
    return Polynomial.checkPrimitives(Polys)
  
  def _getAllHavingSpecifiedCoeffsHelper(self, FromTo : list):
    CList = self._CoefficientList.copy()
    CList.sort()
    CCList = self._CoeffsCount.copy()
    DontTouchBounds = self._DontTouchBounds
    Result = []
    Step = 1
    if DontTouchBounds:
      Step = 2
    for n in range(FromTo[0], FromTo[1]+1, Step):
      PT = []
      bsn = BinString(len(CList), n)
      i = 0
      for b in bsn:
        if b: 
          PT.append(CList[i])
        i += 1
      #print(n, bsn, PT)
      if not (len(PT) in CCList):
        continue
      Result.append(Polynomial(PT.copy()))
    return Result
  
  def _check(p):
    if p.isPrimitive():
      return p
    return None
        
  def copy(self) -> Polynomial:
    """returns a full copy of the Polynomial object.
    """
    return Polynomial(self)
  
  def getSigns(self) -> list:
    return self._sign_list.copy()
  
  def getSignedCoefficients(self) -> list:
    Result = []
    for i in range(len(self._coefficients_list)):
      Result.append(self._sign_list[i] * self._coefficients_list[i])
    return Result
  
  def setStartingPointForIterator(self, StartingPolynomial = None) -> bool:
    """This proc allows to set starting polynomial for iterating purposes.

    Args:
        StartingPolynomial (None, list, Polynomial): starting polynomial 'None' means 'automatic'. Defaults to None.

    Returns:
        bool: False, it the given StartingPolynomial does not pass validation.
    """
    if StartingPolynomial is None:
      self._IterationStartingPoint = None
    else:
      NewPoly = Polynomial(StartingPolynomial)
      NewDegree = NewPoly.getDegree()
      SelfDegree = self.getDegree()
      if NewDegree != SelfDegree:
        Aio.printError(f"The starting polynomial '{StartingPolynomial}' has degree = '{NewDegree}', while it should be '{SelfDegree}'.")
        return False
      NewCoeffsCount = NewPoly.getCoefficientsCount()
      SelfCoeffsCount = self.getCoefficientsCount()
      if NewCoeffsCount != SelfCoeffsCount:
        Aio.printError(f"The starting polynomial '{StartingPolynomial}' has '{NewCoeffsCount}' coefficients, while it should have '{SelfCoeffsCount}'.")
        return False
      NewBalancing = NewPoly.getBalancing()
      if NewBalancing > self._balancing > 0:
        Aio.printError(f"The starting polynomial '{StartingPolynomial}' has balancing '{NewBalancing}' which is greater than allowed '{self._balancing}'.")
        return False
      NewMinDistance = NewPoly.getMinDistance()
      if NewMinDistance > self._mindist > 0:
        Aio.printError(f"The starting polynomial '{StartingPolynomial}' has minimum distance '{NewMinDistance}' which is greater than allowed '{self._mindist}'.")
        return False
      NewLF = NewPoly.isLayoutFriendly()
      if self._lf and (not NewLF):
        Aio.printError(f"The starting polynomial '{StartingPolynomial}' is not layout-friendly, while it should be.")
        return False
      self._IterationStartingPoint = NewPoly._coefficients_list
    return True

  def __init__(self, PolynomialCoefficientList : list, PolynomialBalancing = 0):
    """ Polynomial (Polynomial, PolynomialBalancing=0)
Polynomial (PolynomialCoefficientList, PolynomialBalancing=0)
Polynomial (int, PolynomialBalancing=0)
Polynomial (hex_string, PolynomialBalancing=0)
Polynomial ("size,HexNumber", PolynomialBalancing=0)
    """
    self._coefficients_list = []         # Polynomial sorted oefficients list
    self._balancing = 0    
    self._bmin = 1 
    self._bmax = 2
    self._positions = False
    self._mindist = 0
    self._lf = False
    self._notes = ""
    self._CoefficientList = []
    self._CoeffsCount = []
    self._DontTouchBounds = 1
    self._OddOnly = 1
    self._sign_list = []
    self._IterationStartingPoint = None
    if "Polynomial" in str(type(PolynomialCoefficientList)):
      self._coefficients_list = PolynomialCoefficientList._coefficients_list.copy()
      self._sign_list = PolynomialCoefficientList._sign_list.copy()
      self._balancing = PolynomialCoefficientList._balancing + 0
      self._bmin = PolynomialCoefficientList._bmin
      self._bmax = PolynomialCoefficientList._bmax
      if Aio.isType(PolynomialCoefficientList._positions, []):
        self._positions = PolynomialCoefficientList._positions.copy()
      else:
        self._positions = PolynomialCoefficientList._positions
      self._lf = PolynomialCoefficientList._lf
      self._notes = PolynomialCoefficientList._notes
      self._mindist = PolynomialCoefficientList._mindist
      self._IterationStartingPoint = PolynomialCoefficientList._IterationStartingPoint
    elif "int" in str(type(PolynomialCoefficientList)):
      cntr = 0
      self._coefficients_list = []
      while PolynomialCoefficientList > 0:
        if PolynomialCoefficientList & 1 == 1:
          self._coefficients_list.append(cntr)
        cntr += 1
        PolynomialCoefficientList >>= 1
      self._coefficients_list.sort(reverse=True)
      self._sign_list = [1 for _ in range(len(self._coefficients_list))]
      self._balancing = PolynomialBalancing
      self._bmax = self._coefficients_list[0] 
      self._IterationStartingPoint = None
    elif "str" in str(type(PolynomialCoefficientList)):
      lst = PolynomialCoefficientList.split(",")
      num = lst[0]
      deg = 0
      if len(lst) > 1:
        deg = 2**(int(lst[0]))
        num = lst[1]
      num = Int.fromString(num, 16) | deg
      cntr = 0
      self._coefficients_list = []
      while num > 0:
        if num & 1 == 1:
          self._coefficients_list.append(cntr)
        cntr += 1
        num >>= 1
      self._coefficients_list.sort(reverse=True)
      self._sign_list = [1 for _ in range(len(self._coefficients_list))]
      self._balancing = PolynomialBalancing   
      self._bmax = self._coefficients_list[0]   
      self._IterationStartingPoint = None
    else:
      lst = []
      for c in PolynomialCoefficientList:
        lst.append(c)
      lst.sort(reverse=True, key=lambda x: abs(x))
      self._coefficients_list = lst
      self._sign_list = [1 for _ in range(len(self._coefficients_list))]
      for i in range(len(lst)):
        if lst[i] < 0:
          lst[i] = abs(lst[i])
          self._sign_list[i] = -1
      self._coefficients_list = lst
      self._balancing = PolynomialBalancing
      self._bmax = self._coefficients_list[0]
      self._IterationStartingPoint = None
    
  def __hash__(self) -> int:
    return self.toInt()
      
  def __iter__(self):
    if self._IterationStartingPoint is None:
      self._coefficients_list = Polynomial.createPolynomial(self.getDegree(), self.getCoefficientsCount(), self._balancing, self._lf, self._mindist)._coefficients_list
    else:
      self._coefficients_list = self._IterationStartingPoint
    self._mnext = True
    self._first = True
    if self._balancing > 0:
      if self.getBalancing() > self._balancing:
        self._mnext = False
    if self._lf:
      if not self.isLayoutFriendly():
        self._mnext = False
    return self
  
  def __next__(self):
    if self._mnext:  
      if self._first:
        self._first = False
        return self.copy()
      else:
        self._mnext = self.makeNext()
        if self._mnext:
          return self.copy()
    if self._IterationStartingPoint is None:
      self._coefficients_list = Polynomial.createPolynomial(self.getDegree(), self.getCoefficientsCount(), self._balancing, self._lf, self._mindist)._coefficients_list
    else:
      self._coefficients_list = self._IterationStartingPoint
    raise StopIteration  
  
  def __str__(self) -> str:
    Second = 0
    Result = "["
    for i in range(len(self._coefficients_list)):
      if Second:
        Result += ", "
      else:
        Second = 1
      Result += str(self._sign_list[i] * self._coefficients_list[i])
    Result += "]"
    return Result
  
  @staticmethod
  def iterate(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, ExcludeReciprocals = False):
    poly0 = Polynomial.createPolynomial(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance)
    if poly0 is None:
      return
    Used = []
    for p in poly0:
      if ExcludeReciprocals:
        if p in Used:
          continue
        Used.append(p.getReciprocal())
      yield p.copy()
      
  def iterateThroughSigns(self):
    poly = self.copy()
    signs = poly._sign_list
    intmax = (1 << (len(signs)-2)) - 1
    for i in range(1, intmax):
      for index in range(1, len(signs)-1):
        if i & 1:
          signs [index] = -1
        else: 
          signs [index] = 1
        i >>= 1
      yield poly
  
  def getDifferentTapCount(self, AnotherPolynomial) -> int:
    Second = Polynomial(AnotherPolynomial)
    MyTaps = self._coefficients_list[1:-1]
    SecondTaps = Second._coefficients_list[1:-1]
    Result = 0
    for Tap in MyTaps:
      if Tap not in SecondTaps:
        Result += 1
    return Result
  
  def getDifferentTaps(self, AnotherPolynomial) -> list:
    Second = Polynomial(AnotherPolynomial)
    MyTaps = self._coefficients_list[1:-1]
    SecondTaps = Second._coefficients_list[1:-1]
    Result = []
    for Tap in MyTaps:
      if Tap not in SecondTaps:
        Result.append(Tap)
    return Result
  
  @staticmethod
  def printAllPrimitivesHavingSpecifiedCoeffs(CoefficientList : list, CoeffsCount = 0, DontTouchBounds = 1, OddOnly = 1):
    """Prints all primitive polynomials having coefficients included in a given list.

    Args:
        CoefficientList (list): list of all possible coefficients
        CoeffsCount (int, optional): specifies coefficients count of the candidate polynomials Defaults to 0 (no limit).
        DontTouchBounds (int, optional): If True, highest and lowest coefficients are not touched. Defaults to 1.
        OddOnly (int, optional): If True, lists only polys having odd coefficients count. Defaults to 1.
    """
    Results = Polynomial.listAllPrimitivesHavingSpecifiedCoeffs(CoefficientList, CoeffsCount, DontTouchBounds, OddOnly)
    for R in Results:
      Aio.print(R._coefficients_list)
    
  @staticmethod
  def listAllPrimitivesHavingSpecifiedCoeffs(CoefficientList : list, CoeffsCount = 0, DontTouchBounds = 1, OddOnly = 1) -> list:
    """Returns a list containing all primitive polynomials having coefficients included in a given list.

    Args:
        CoefficientList (list): list of all possible coefficients
        CoeffsCount (int, optional): specifies coefficients count of the candidate polynomials Defaults to 0 (no limit).
        DontTouchBounds (int, optional): If True, highest and lowest coefficients are not touched. Defaults to 1.
        OddOnly (int, optional): If True, lists only polys having odd coefficients count. Defaults to 1.
    """
    CList = CoefficientList.copy()
    CList.sort()
    CMax = CList[-1]
    if Aio.isType(CoeffsCount, 0):
      if CoeffsCount <= 0:
        CCList = [i for i in range(3, len(CList)+1)]
      else:
        CCList = [CoeffsCount]
    else:
      CCList = [i for i in CoeffsCount]
    if len(CCList) > 1 and OddOnly:
      CCList = list(filter(lambda x: x&1==1, CCList))
    nMax = 1 << len(CList)
    nMin = 1
    Step = 1
    if DontTouchBounds:
      Step = 2
      nMin = (nMax >> 1) | 1
    Results = []
    FromToList = []
    Step =  100000
    From = nMin
    To = From + Step-1
    Break = 0
    if To >= nMax:
      To = nMax-1
      Break = 1
    while 1:
      FromToList.append([From, To])
      if Break:
        break
      From += Step
      To += Step
      if To >= nMax:
        To = nMax-1
        Break = 1
      if To < From:
        break
    px = Polynomial([0])
    px._CoefficientList = CList
    px._CoeffsCount = CCList
    px._DontTouchBounds = DontTouchBounds
    px._OddOnly = OddOnly
    for FT in FromToList:
      print(f'Generating polynomials basing on integer counter from {FT[0]} to {FT[1]}...')
      Results += px._getAllPrimitivesHavingSpecifiedCoeffsHelper(FT)
    return Results
  
  @staticmethod
  def getAllHavingSpecifiedCoeffs(CoefficientList : list, CoeffsCount = 0, DontTouchBounds = 1, OddOnly = 1):
    """Returns a list containing all  polynomials having coefficients included in a given list.

    Args:
        CoefficientList (list): list of all possible coefficients
        CoeffsCount (int, optional): specifies coefficients count of the candidate polynomials Defaults to 0 (no limit).
        DontTouchBounds (int, optional): If True, highest and lowest coefficients are not touched. Defaults to 1.
        OddOnly (int, optional): If True, lists only polys having odd coefficients count. Defaults to 1.
    """
    CList = CoefficientList.copy()
    CList.sort()
    if Aio.isType(CoeffsCount, 0):
      if CoeffsCount <= 0:
        CCList = [i for i in range(3, len(CList)+1)]
      else:
        CCList = [CoeffsCount]
    else:
      CCList = [i for i in CoeffsCount]
    if len(CCList) > 1 and OddOnly:
      CCList = list(filter(lambda x: x&1==1, CCList))
    nMax = 1 << len(CList)
    nMin = 1
    Result = []
    Step = 1
    if DontTouchBounds:
      Step = 2
      nMin = (nMax >> 1) | 1
    if (nMax-nMin) > 110000:
      FromToList = []
      Step =  100000
      From = nMin
      To = From + Step-1
      Break = 0
      if To >= nMax:
        To = nMax-1
        Break = 1
      while 1:
        FromToList.append([From, To])
        if Break:
          break
        From += Step
        To += Step
        if To >= nMax:
          To = nMax-1
          Break = 1
        if To < From:
          break
      px = Polynomial([0])
      px._CoefficientList = CList
      px._CoeffsCount = CCList
      px._DontTouchBounds = DontTouchBounds
      px._OddOnly = OddOnly
      #, desc="Polynomials creating")
      R = p_map(px._getAllHavingSpecifiedCoeffsHelper, FromToList)
      for Ri in R:
        #print(len(Ri))
        Result += Ri
    else:
      for n in range(nMin, nMax, Step):
        PT = []
        bsn = BinString(len(CList), n)
        i = 0
        for b in bsn:
          if b: 
            PT.append(CList[i])
          i += 1
        #print(n, bsn, PT)
        if not (len(PT) in CCList):
          #print("Bad length")
          continue
#        if DontTouchBounds:
#          if (not (CList[0] in PT)) or (not (CList[-1] in PT)):
#            print("Bad coeff")
#            continue     
        Result.append(Polynomial(PT.copy()))
        #print(n, bsn, PT)
    return Result
  
  def toKassabStr(self) -> str:
    """Returns a string containing polynomial dexription consistent with Mark Kassab's C++ code.
    """
    result = "add_polynomial("
    first = True
    for c in self._coefficients_list:
      if first:
        first = False
      else:
        result += ", "
      result += str(c)
    return result + ");"
  def __repr__(self) -> str:
    return "Polynomial(" + str(self) + ")"
  def __eq__(self, other : Polynomial) -> bool:
    return self._coefficients_list == other._coefficients_list
  def __ne__(self, other : Polynomial) -> bool:
    return self._coefficients_list != other._coefficients_list
  
  def printFullInfo(self):
    """Prints full information about the polynomial.
    """
    title = "Polynomial  deg=" + str(self.getDegree()) + ", bal=" + str(self.getBalancing())
    Aio.transcriptSubsectionBegin(title)
    Aio.print("Degree            : ", self.getDegree())
    Aio.print("Coefficients count: ", self.getCoefficientsCount())
    Aio.print("Hex with degree   : ", self.toHexString())
    Aio.print("Hex without degree: ", self.toHexString(False))
    Aio.print("Balancing         : ", self.getBalancing())
    Aio.print("Is layout-friendly: ", self.isLayoutFriendly())
    Aio.print("Coefficients      : ", self.getCoefficients())
    Aio.transcriptSubsectionEnd()
    
  def toHexString(self, IncludeDegree=True, shorten=True) -> str:
    """Returns a string containing polynomial description in hexadecimal convention.
    
    Args:
        IncludeDegree (bool, optional): if 1, the highest coefficients is included. Defaults to 1.
        shorten (bool, optional): if 1, then uses such convention: 222 -> 2^3. Defaults to 1.
    """
    ival = self.toInt()
    deg = self.getDegree()
    if not IncludeDegree:
      msk = (1 << (deg)) - 1
      ival &= msk
    bs = BinString(deg+1, ival)
    return bs.toHexString(shorten)
  
  def toBinString(self, IncludeDegree=True):
    ival = self.toInt()
    deg = self.getDegree()
    if not IncludeDegree:
      msk = (1 << (deg)) - 1
      ival &= msk
    return BinString(deg+1, ival)
  
  def getCoefficients(self) -> list:
    """Returns list of coefficients.
    """
    return self._coefficients_list.copy()
  
  def getCoefficientsCount(self) -> int:
    """Returns coefficients count.
    """
    return len(self._coefficients_list)
  
  def getReciprocal(self) -> Polynomial:
    """Gets reciprocal version of polynomial.
    
    For example:
    Polynomial([6,4,3,1,0]).getReversed() 
    >> Polynomial([6,5,3,2,0])
    """
    clen = len(self._coefficients_list)
    deg = self._coefficients_list[0]
    result = [deg, self._coefficients_list[clen-1]]
    for i in range(1, clen-1):
      result.append((deg - self._coefficients_list[i]) * self._sign_list[i])
    return Polynomial(result)
  
  def getReversed(self) -> Polynomial:
    """alias for getReciprocal to keep backward compatibility.
    """
    return self.getReciprocal()
  
  def getDegree(self) -> int:
    """Returns polynomials degree.
    """
    return self._coefficients_list[0]
  
  def makeNext(self) -> bool:
    """Moves the middle coefficients to obtain a next polynomial
    giving an LFSR having the sam count of taps.

    Returns:
        bool: True if successfull, Ffalse if no next polynomial.
    """
    while self._makeNext():
      s = True
      if self._balancing > 0:
        if self.getBalancing() > self._balancing:
          s = False
      if s:
        return True
    return False
  
  def _makeNext(self) -> bool:
    ccount = len(self._coefficients_list)
    degree = self._coefficients_list[0]
    left = degree
    pos = {}
    step = self._bmin
    stepmax = self._bmax
    if self._positions != False:
      pos = self._positions
    for i in range(1, ccount-1):
      posi = pos.get(i, [0, self._coefficients_list[0]])
      vmax = posi[1]
      vmin = posi[0]
      this = self._coefficients_list[i]
      right = self._coefficients_list[i+1]
      if vmax > (left-step):
        vmax = left-step
      if vmax > (right+stepmax):
        vmax = right+stepmax
      if vmin < (right+step):
        vmin = right+step
      if this < vmax:
        self._coefficients_list[i] += 1
        return True
      if this > vmin+1:
        self._coefficients_list[i] = vmin+1    
        left = vmin+1 
    return False  
  
  def getTapsCount(self) -> int:
    """Returns LFSR taps count in case of a LFSR created basing on this polynomial 
    """
    return len(self._coefficients_list)-2
  
  def getPolynomialsCount(self) -> int:
    """Returns a count of polynomials having the same parameters (obtained using .makeNext())  
    """
    return math.comb(self.getDegree()-1, self.getTaps())
  
  def getMinDistance(self) -> int:
    """Calculates and returns the minimum distance between successive coefficients.
    """
    Result = self._coefficients_list[0]
    for i in range(1, len(self._coefficients_list)):
      d = self._coefficients_list[i-1] - self._coefficients_list[i]
      if d < Result:
        Result = d
    return Result
  
  def getBalancing(self) -> int:
    """Calculates and returns the balaning factor of the polynomial.
    """
    bmin = self._coefficients_list[0]
    bmax = 0
    for i in range(1, len(self._coefficients_list)):
      d = self._coefficients_list[i-1] - self._coefficients_list[i]
      if d < bmin:
        bmin = d
      if d > bmax:
        bmax = d
    return (bmax - bmin)
  
  def toInt (self) -> int:
    """Returns an integer representing the given polynomial.
    
    For example:
    >>> bin(Polynomial([3,1,0]).toInt())
    >>> 0b1011
    """
    clist = self._coefficients_list
    result = int(0)
    for coeff in clist:
      result += (1 << coeff)
    return result
  
  def toBitarray(self):
    clist = self._coefficients_list
    result = bitarray(self.getDegree()+1)
    result.setall(0)
    for coeff in clist:
      result[coeff] = 1
    return result
  def isPrimitive(self) -> bool:
    """Check if the polynomial is primitive over GF(2).
    
    That's considered by simulating an LFSR based on the polynomial.

    Returns:
        bool: True if is the poly is primitive, otherwise False
    """
    if len(self._coefficients_list) % 2 == 0: 
      return False
    Degree = self.getDegree()
    if len(self._coefficients_list) == 3 and Degree % 8 == 0: 
      return False
    l = Lfsr(self.copy(), LfsrType.Galois)
    result = l.isMaximum()
    return result
  
  def nextPrimitive(self, Silent=False) -> bool:
    """Looks for the next primitive polynomial.

    Returns:
        bool: True if primitive found, otherwise False.
    """
    while True:
      if not self.makeNext():
        return False
      if not Silent:
        Aio.printTemp("Testing",self)
      if self.isPrimitive():
        if not Silent:
          Aio.printTemp(str(" ")*100)
        return True
      
  def isLayoutFriendly(self) -> bool:
    for i in range(len(self._coefficients_list)-1):
      this = self._coefficients_list[i]
      right = self._coefficients_list[i+1]
      if (this-right) <= 1:
        return False
    return True

  @staticmethod
  def createPolynomial(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0) -> Polynomial:
    """Returns a polynomial, usefull for LFSRs.

    Args:
        PolynomialDegree (int): polynomial degree (i.e. size of LFSR)
        PolynomialCoefficientsCount (int): coefficients count (i.e. LFSRs taps count + 2)
        PolynomialBalancing (int, optional): balancing factor. Defaults to 0 (no balance checking).
        MinDistance (int, optional): minimum distance between successive coefficients. Defaults to 0 (no matters)
        LayoutFriendly (bool, optional): only layout-friendly poly.
    """
    if PolynomialCoefficientsCount < 1:
      Aio.printError ("'oefficients_count' must be >= 1")
      return Polynomial([])
    if PolynomialDegree < (PolynomialCoefficientsCount-1):
      Aio.printError ("'coefficients_count - 1' must be <= 'degree'")
      return Polynomial([])  
    result = [PolynomialDegree]
    bmin = 1
    bmax = PolynomialDegree-1
    if 0 < PolynomialBalancing < PolynomialDegree:
      avg = float(PolynomialDegree) / float(PolynomialCoefficientsCount - 1)
      halfbal = float(PolynomialBalancing) / 2.0
      bmin = int(avg - halfbal)
      if bmin < 1:
        bmin = 1
      if MinDistance > bmin > 0:
        bmin = MinDistance
      if bmin < 2 and LayoutFriendly:
        bmin = 2
      bmax = bmin + PolynomialBalancing
      if bmax > PolynomialDegree-1:
        bmax = PolynomialDegree-1
      result = [0]
      rest = PolynomialDegree
      actual = bmin
      restcoeffs = PolynomialCoefficientsCount-2
      diff = bmin
      diffmax = bmax
      diffmin = diff
      for i in range(2, PolynomialCoefficientsCount):
        while (diffmin + ((restcoeffs-1) * diffmax)) < (rest-diff):
          diffmin += 1
        coeff = actual
        result.append(coeff)
        rest -= diffmin
        restcoeffs -= 1
        actual += diffmin
      result.append(PolynomialDegree)
    elif (MinDistance > 0) or LayoutFriendly:
      bmin = MinDistance
      if bmin < 2 and LayoutFriendly:
        bmin = 2
      result = [0]
      c = bmin
      for i in range(2, PolynomialCoefficientsCount):
        result.append(c)
        c += bmin
      result.append(PolynomialDegree)
    else:
      for i in range(PolynomialCoefficientsCount-1):
        result.append(i)
    p = Polynomial(result, PolynomialBalancing)
    q = p.getReversed()
    pos = {}
    cp = p._coefficients_list.copy()
    cq = q._coefficients_list.copy()
    for i in range(1, PolynomialCoefficientsCount-1):
      pos[i] = [cp[i], cq[i]]
    p._positions = pos
    p._bmin = bmin
    p._bmax = bmax
    p._lf = LayoutFriendly
    p._mindist = MinDistance
#    print(Aio.format(pos))
    if p.getMinDistance() < p._mindist > 0:
      return None
    if p.getBalancing() > p._balancing > 0:
      while p.getBalancing() > p._balancing:
        if not p._makeNext():
          return None
    return p
  
  @staticmethod
  def checkPrimitives(Candidates : list, n = 0, Silent = True) -> list:
    """Returns a list of primitive polynomials (over GF(2)) found on a given list.

    Args:
        PList (list): list of candidate polynomials 
        m (int, optional): stop checking if n polynomials is found. Defaults to 0 (don't stop)
        Silent (bool, optional): if False (default) print to the sdtout every time a new prim poly is found

    Returns:
        list: list of polynomial objects
    """    
    if len(Candidates) < 1:
      return []
    PList = []
    for p in Candidates:
      PList.append(Polynomial(p))
    Generator = Generators()
    Results = []
    Iter = p_uimap(Polynomial._check, Generator.wrapper(PList), total=len(PList))
    for I in Iter:
      if I is not None:
        Results.append(I)
        if not Silent:
          print(f'Found {str(I)}')
      if len(Results) >= n > 0:
        Generator.disable()
    del Generator    
    if len(Results) > n > 0:
      Results = Results[:n]
    return Results
  def toTigerStr(self) -> str:
    Coeffs = self._coefficients_list
    Line = ""      
    Minus = ""
    for i in range(len(Coeffs)-1, 0 , -1):
      c = Coeffs[i]
      Line = ", " + Minus + str(c) + Line
      Minus = "-" if Minus == "" else ""
    Line = "[" + str(Coeffs[0]) + Line + "]"
    return Line
  
  @staticmethod
  def firstTigerPrimitive(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, NoResultsSkippingIteration = 0, StartingPolynomial = None, MinNotMatchingTapsCount = 0):
    Polys = Polynomial.listTigerPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance, 1, NoResultsSkippingIteration, StartingPolynomial, MinNotMatchingTapsCount)
    if len(Polys) >= 1:
      return Polys[0]
    return None
      
  @staticmethod
  def printTigerPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, n = 0, NoResultsSkippingIteration = 0, StartingPolynomial = None, MinNotMatchingTapsCount = 0):
    Polys = Polynomial.listTigerPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance, n, NoResultsSkippingIteration, StartingPolynomial, MinNotMatchingTapsCount)
    for p in Polys:
      Aio.print(p.toTigerStr())
      
  @staticmethod
  def listTigerPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, n = 0, NoResultsSkippingIteration = 0, StartingPolynomial = None, MinNotMatchingTapsCount = 0) -> list:
    Poly0 = Polynomial.createPolynomial(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance)
    Signs = Poly0._sign_list
    for i in range(len(Signs)-2, 0, -2):
      Signs[i] = -1
    if Poly0 is None:
      return []
    if not Poly0.setStartingPointForIterator(StartingPolynomial):
      return []
    SerialChunkSize = 20
    if PolynomialDegree >= 512:
      SerialChunkSize = 1
    elif PolynomialDegree >= 256:
      SerialChunkSize = 5
    elif PolynomialDegree >= 128:
      SerialChunkSize = 10 
    aux = 100000 // PolynomialDegree
    if aux < 100:
      aux = 100
    ParallelChunk = aux * SerialChunkSize
    lfsrs = []
    SkippingCounter = NoResultsSkippingIteration
    Polys = []
    SkipFirst = 0
    SkipPolysCOunterMax = 1000000
    SkipPolysCOunter = SkipPolysCOunterMax
    SkipAll = 0
    if MinNotMatchingTapsCount > 0:
      ParallelChunk >>= 4
      PRefList = Polynomial.listTigerPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance, 1, NoResultsSkippingIteration, StartingPolynomial, 0)
      if len(PRefList) > 0:
        PRef = PRefList[0]
        Polys.append(PRef)
        Polynomial.setStartingPointForIterator(PRef)
        SkipFirst = 1
      else:
        SkipAll = 1
    if (n <= 0) or (len(Polys) < n > 0) and not SkipAll:
      for p in Poly0:
        WasFound = 0
        if SkipFirst:
          SkipFirst = 0
          continue
        if MinNotMatchingTapsCount > 0:
          MinDiffTapsOk = 1
          for R in Polys:
            if p.getDifferentTapCount(R) < MinNotMatchingTapsCount:
              MinDiffTapsOk = 0
              break
          if not MinDiffTapsOk:
            SkipPolysCOunter -= 1
            if SkipPolysCOunter <= 0:
              break
            continue
          SkipPolysCOunter = SkipPolysCOunterMax
        lfsrs.append(Lfsr(p, TIGER_RING))
        if len(lfsrs) >= ParallelChunk:
          AuxComb = Lfsr.checkMaximum(lfsrs, n-len(Polys), SerialChunkSize, 1)
          Aux = AuxComb[0]
          lfsrs = AuxComb[1]
          if MinNotMatchingTapsCount > 0:
            MinDiffTapsOk = 1
            for l in Aux:
              lpol = Polynomial(l._my_poly.copy())
              for R in Polys:
                if lpol.getDifferentTapCount(R) < MinNotMatchingTapsCount:
                  MinDiffTapsOk = 0
                  break
              if MinDiffTapsOk:
                Polys.append(lpol)
                WasFound = 1
          else:
            if len(Aux) > 0:
              WasFound = 1
              for l in Aux:
                Polys.append(Polynomial(l._my_poly.copy()))
          print(f'Found so far: {len(Polys)}')
          if len(Polys) >= n > 0:
            break
          if NoResultsSkippingIteration > 0:
            if WasFound:
              SkippingCounter = NoResultsSkippingIteration
            else:
              SkippingCounter -= 1
            if SkippingCounter <= 0:
              break
    while len(lfsrs) > 0 and (len(Polys) < n or n <= 0) and not SkipAll:
      if NoResultsSkippingIteration > 0 and SkippingCounter <= 0:
        break
      AuxComb = Lfsr.checkMaximum(lfsrs, n-len(Polys), SerialChunkSize, 1)
      Aux = AuxComb[0]
      lfsrs = AuxComb[1]
      if MinNotMatchingTapsCount > 0:
        MinDiffTapsOk = 1
        for l in Aux:
          lpol = Polynomial(l._my_poly.copy())
          for R in Polys:
            if lpol.getDifferentTapCount(R) < MinNotMatchingTapsCount:
              MinDiffTapsOk = 0
              break
          if MinDiffTapsOk:
            Polys.append(lpol)
      else:
        for l in Aux:
          lpol = Polynomial(l._my_poly.copy())
          Polys.append(Polynomial(lpol))      
      print(f'Found so far: {len(Polys)}')
    for P in Polys:      
      P._sign_list = Signs
    return Polys
            

  @staticmethod
  def printHybridPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, n = 0, NoResultsSkippingIteration = 0, StartingPolynomial = None, MinNotMatchingTapsCount = 0):
    Polys = Polynomial.listHybridPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance, n, NoResultsSkippingIteration, StartingPolynomial, MinNotMatchingTapsCount)
    for p in Polys:
      Aio.print(p)
      
  @staticmethod
  def listHybridPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, n = 0, NoResultsSkippingIteration = 0, StartingPolynomial = None, MinNotMatchingTapsCount = 0) -> list:
    Poly0 = Polynomial.createPolynomial(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance)
    if Poly0 is None:
      return []
    if not Poly0.setStartingPointForIterator(StartingPolynomial):
      return []
    SerialChunkSize = 20
    if PolynomialDegree >= 512:
      SerialChunkSize = 1
    elif PolynomialDegree >= 256:
      SerialChunkSize = 5
    elif PolynomialDegree >= 128:
      SerialChunkSize = 10 
    aux = 100000 // PolynomialDegree
    if aux < 100:
      aux = 100
    ParallelChunk = aux * SerialChunkSize
    lfsrs = []
    SkippingCounter = NoResultsSkippingIteration
    Polys = []
    SkipFirst = 0
    SkipPolysCOunterMax = 1000000
    SkipPolysCOunter = SkipPolysCOunterMax
    SkipAll = 0
    if MinNotMatchingTapsCount > 0:
      ParallelChunk >>= 4
      PRefList = Polynomial.listHybridPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance, 1, NoResultsSkippingIteration, StartingPolynomial, 0)
      if len(PRefList) > 0:
        PRef = PRefList[0]
        Polys.append(PRef)
        Polynomial.setStartingPointForIterator(PRef)
        SkipFirst = 1
      else:
        SkipAll = 1
    if (n <= 0) or (len(Polys) < n > 0) and not SkipAll:
      for ph in Poly0:
        for p in ph.iterateThroughSigns():
          WasFound = 0
          if SkipFirst:
            SkipFirst = 0
            continue
          if MinNotMatchingTapsCount > 0:
            MinDiffTapsOk = 1
            for R in Polys:
              if p.getDifferentTapCount(R) < MinNotMatchingTapsCount:
                MinDiffTapsOk = 0
                break
            if not MinDiffTapsOk:
              SkipPolysCOunter -= 1
              if SkipPolysCOunter <= 0:
                break
              continue
            SkipPolysCOunter = SkipPolysCOunterMax
          lfsrs.append(Lfsr(p, HYBRID_RING))
          if len(lfsrs) >= ParallelChunk:
            AuxComb = Lfsr.checkMaximum(lfsrs, n-len(Polys), SerialChunkSize, 1)
            Aux = AuxComb[0]
            lfsrs = AuxComb[1]
            if MinNotMatchingTapsCount > 0:
              MinDiffTapsOk = 1
              for l in Aux:
                lpol = Polynomial(l._my_poly.copy())
                lpol._sign_list = l._my_signs.copy()
                for R in Polys:
                  if lpol.getDifferentTapCount(R) < MinNotMatchingTapsCount:
                    MinDiffTapsOk = 0
                    break
                if MinDiffTapsOk:
                  Polys.append(lpol)
                  WasFound = 1
            else:
              if len(Aux) > 0:
                WasFound = 1
                for l in Aux:
                  lpol = Polynomial(l._my_poly.copy())
                  lpol._sign_list = l._my_signs.copy()
                  Polys.append(Polynomial(lpol))     
            print(f'Found so far: {len(Polys)}')
            if len(Polys) >= n > 0:
              break
            if NoResultsSkippingIteration > 0:
              if WasFound:
                SkippingCounter = NoResultsSkippingIteration
              else:
                SkippingCounter -= 1
              if SkippingCounter <= 0:
                break         
        if len(Polys) >= n > 0:
          break   
    while len(lfsrs) > 0 and (len(Polys) < n or n <= 0) and not SkipAll:
      if NoResultsSkippingIteration > 0 and SkippingCounter <= 0:
        break
      AuxComb = Lfsr.checkMaximum(lfsrs, n-len(Polys), SerialChunkSize, 1)
      Aux = AuxComb[0]
      lfsrs = AuxComb[1]
      if MinNotMatchingTapsCount > 0:
        MinDiffTapsOk = 1
        for l in Aux:
          lpol = Polynomial(l._my_poly.copy())
          lpol._sign_list = l._my_signs.copy()
          for R in Polys:
            if lpol.getDifferentTapCount(R) < MinNotMatchingTapsCount:
              MinDiffTapsOk = 0
              break
          if MinDiffTapsOk:
            Polys.append(lpol)
      else:
        for l in Aux:
          lpol = Polynomial(l._my_poly.copy())
          lpol._sign_list = l._my_signs.copy()
          Polys.append(Polynomial(lpol))      
      print(f'Found so far: {len(Polys)}')
    return Polys
  
  @staticmethod
  def printPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, n = 0, Silent = True, MaxSetSize=10000, ExcludeList = [], FilteringCallback = None, NoResultsSkippingIteration = 0, StartingPolynomial = None) -> None:
    """Prints a list of primitive polynomials (over GF(2)).

    Args:
        PolynomialDegree (int): polynomial degree (i.e. LFSR size)
        PolynomialCoefficientsCount (int): coefficients count (i.e. LFSR taps count + 2)
        PolynomialBalancing (int, optional): balancing factor. Defaults to 0 (no balance checking)
        MinDistance (int, optional): Minimum distance between consecutive coefficients. Default: 0 (no restriction)
        LayoutFriendly (bool, optional): like MinDistance=2. Defaults to False.
        n (int, optional): stop searching if n polynomials is found. Defaults to 0 (don't stop)
        Silent (bool, optional): if False (default) print to the sdtout every time a new prim poly is found
        ExcludeList (list, optional): list of polynomials excluded from checking
        FilteringCallback (procedure, optional): if specified, then will be used to filter acceptable polynomials (must return bool value: True means acceptable).
    """
    for p in Polynomial.listPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance, n, Silent, MaxSetSize, ExcludeList, 0, FilteringCallback, NoResultsSkippingIteration, StartingPolynomial):
      Aio.print(p.getCoefficients())
      
  @staticmethod
  def listPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, MinDistance = 0, n = 0, Silent = True, MaxSetSize=10000, ExcludeList = [], ReturnAlsoAllCandidaes = False, FilteringCallback = None, NoResultsSkippingIteration = 0, StartingPolynomial = None) -> list:
    """Returns a list of primitive polynomials (over GF(2)).

    Args:
        PolynomialDegree (int): polynomial degree (i.e. LFSR size)
        PolynomialCoefficientsCount (int): coefficients count (i.e. LFSR taps count + 2)
        PolynomialBalancing (int, optional): balancing factor. Defaults to 0 (no balance checking)
        MinDistance (int, optional): Minimum distance between consecutive coefficients. Default: 0 (no restriction)
        LayoutFriendly (bool, optional): like MinDistance=2. Defaults to False.
        n (int, optional): stop searching if n polynomials is found. Defaults to 0 (don't stop)
        Silent (bool, optional): if False (default) print to the sdtout every time a new prim poly is found
        ExcludeList (list, optional): list of polynomials excluded from checking
        ReturnAlsoAllCandidaes (bool, optional): if true, then it returns list: [polynomials_found, all_tested_polynomials]
        FilteringCallback (procedure, optional): if specified, then will be used to filter acceptable polynomials (must return bool value: True means acceptable).

    Returns:
        list: list of polynomial objects
    """
    polys = Polynomial.createPolynomial(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, MinDistance)
    if type(polys) == type(None):
      Aio.printError("No candidate polynomials found. Consider relaxing the requirements.")
      if ReturnAlsoAllCandidaes:
        return [[], []]
      return []
    if not polys.setStartingPointForIterator(StartingPolynomial):
      return []
    result = []
    candidates = []
    AllCandidates = []
    cntr = 0
    SkippingCounter = NoResultsSkippingIteration
    for p in polys:
      if p in ExcludeList:
        continue
      if not (FilteringCallback is None):
        if not FilteringCallback(p):
          continue 
      candidates.append(p.copy())
      if ReturnAlsoAllCandidaes:
        AllCandidates.append(p.copy())
      cntr += 1
      if (cntr >= MaxSetSize):
        Aux = Polynomial.checkPrimitives(candidates, n, Silent)
        result += Aux
        print("Found so far:", len(result))
        candidates.clear()
        cntr = 0
        if len(result) >= n > 0:
          break    
        if NoResultsSkippingIteration > 0:
          if len(Aux) > 0:
            SkippingCounter = NoResultsSkippingIteration
          else:
            SkippingCounter -= 1
          if SkippingCounter <= 0:
            break
    if (cntr > 0):
      result += Polynomial.checkPrimitives(candidates, n, Silent)
      candidates.clear()
    if cntr != 0:
        result += Polynomial.checkPrimitives(candidates, n, Silent)
        candidates.clear()      
    if n > 0 and len(result) > n:
      result = result[0:n]
    Aio.printTemp()
    gc.collect()
    if ReturnAlsoAllCandidaes:
      return [result, AllCandidates]
    return result
  
  @staticmethod
  def firstPrimitive(PolynomialDegree : int, PolynomialCoefficientsCount : int, PolynomialBalancing = 0, LayoutFriendly = False, Silent=True, StartingPolynomial = None) -> Polynomial:
    """Returns a first found primitive (over GF(2)) polynomial.

    Args:
        PolynomialDegree (int): polynomial degree (i.e. LFSR size)
        PolynomialCoefficientsCount (int): coefficients count (i.e. LFSR taps count + 2)
        PolynomialBalancing (int, optional): balancing factor. Defaults to 0 (no balance checking)

    Returns:
        list: _description_
    """
    lp = Polynomial.listPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, LayoutFriendly, 0, 1, Silent, StartingPolynomial = StartingPolynomial)
    if len(lp) > 0:
      return lp[0]
    return None
  
  @staticmethod
  def firstMostBalancedPrimitive(PolynomialDegree : int, PolynomialCoefficientsCount : int, StartBalancing=1, EndBalancing=10, LayoutFriendly = False, Silent = True) -> Polynomial:
    bal = EndBalancing
    if bal > (PolynomialDegree-PolynomialCoefficientsCount):
      bal = (PolynomialDegree-PolynomialCoefficientsCount)
    for b in range(StartBalancing, bal):
      fp = Polynomial.firstPrimitive(PolynomialDegree, PolynomialCoefficientsCount, b, LayoutFriendly, Silent)
      if type(fp) != type(None):
        return fp
    return None
  
  @staticmethod
  def firstEveryNTapsPrimitive(PolynomialDegree : int, EveryN : int, Silent = True, StartingPolynomial = None) -> Polynomial:
    result = Polynomial.listEveryNTapsPrimitives(PolynomialDegree, EveryN, 1, Silent, StartingPolynomial)
    if len(result) > 0:
      return result[0]
    return None
  
  @staticmethod
  def printEveryNTapsPrimitives(PolynomialDegree : int, EveryN : int, n = 0, Silent = True, StartingPolynomial = None) -> None:
    for p in Polynomial.listEveryNTapsPrimitives(PolynomialDegree, EveryN, n, Silent, StartingPolynomial):
      Aio.print(p.getCoefficients())
      
  @staticmethod
  def listEveryNTapsPrimitives(PolynomialDegree : int, EveryN : int, n = 0, Silent = True, StartingPolynomial = None) -> list:
    ccount = int(round(PolynomialDegree / EveryN, 0)) | 1
    if ccount < 3: ccount = 3
    results = []
    exclude = []
    for b in range(1, EveryN):
      resultsAux = Polynomial.listPrimitives(PolynomialDegree, ccount, b, True, 0, n, Silent, ExcludeList=exclude, ReturnAlsoAllCandidaes=True, StartingPolynomial=StartingPolynomial)
      exclude += resultsAux[1]
      for pol in resultsAux[0]:
        results.append(pol.copy())
      if n > 0:
        if len(results) >= n:
          break
    if n > 0:
      if len(results) > n:
        results = results[0:n]
    return results
  
  @staticmethod
  def firstDensePrimitive(PolynomialDegree : int, Silent = True, StartingPolynomial = None) -> Polynomial:
    r = Polynomial.listDensePrimitives(PolynomialDegree, 1, Silent, StartingPolynomial)
    if len(r) > 0:
      return r[0]
    return None
  
  @staticmethod
  def printDensePrimitives(PolynomialDegree, n=0, Silent = True, StartingPolynomial = None) -> None:
    for p in Polynomial.listDensePrimitives(PolynomialDegree, n, Silent, StartingPolynomial):
      Aio.print(p.getCoefficients())
      
  @staticmethod
  def listDensePrimitives(PolynomialDegree, n=0, Silent = True, StartingPolynomial = None) -> list:
    Half = int(PolynomialDegree / 2) | 1
    c = Half - 2
    result = []
    exclude = []
    if n < 0:
      n = 0
    n2 = n
    minc = Half * 0.65
    #print("c", c, "minc", minc)
    while (c >= 3) & (c >= minc):
      print (f'Found so far: {len(result)}. Looking for {c} coefficients')
      resultAux = Polynomial.listPrimitives(PolynomialDegree, c, 2, True, 0, n2, Silent, ExcludeList=exclude, ReturnAlsoAllCandidaes=True, StartingPolynomial=StartingPolynomial)
      result += resultAux[0]
      exclude += resultAux[1]
      if n > 0:
        if len(result) >= n:
          break
        n2 = n - len(result)
      c -= 2
    if len(result) > n > 0:
      result = result[0:n-1]   
    return result
  
  @staticmethod
  def printStarPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing=0, n=0) -> None:
    for p in Polynomial.listStarPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, n):
      Aio.print(p)
  
  @staticmethod
  def listStarPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing=0, n=0) -> list:
    Results = []
    Candidates = []
    ChunkSize = 10000
    SerialChunkSize = 5
    for p in Polynomial.iterate(PolynomialDegree>>1, PolynomialCoefficientsCount, PolynomialBalancing):
      p._coefficients_list[0] = PolynomialDegree
      Candidates.append(Lfsr(p, STAR_RING))
      if len(Candidates) >= ChunkSize:
        N = 0 if n <= 0 else n - len(Results)
        Results += Lfsr.checkMaximum(Candidates, N, SerialChunkSize)
        Candidates = []
        print(f'Found so far: {len(Results)}')
      if len(Results) >= n > 0:
        break
    if(len(Candidates) > 0) and not (len(Results) >= n > 0):
      N = 0 if n <= 0 else n - len(Results)
      Results += Lfsr.checkMaximum(Candidates, N, SerialChunkSize)  
    if len(Results) > n > 0:
      Results = Results[0:n-1]   
    Polys = []
    for L in Results:
      Polys.append(Polynomial(L._my_poly))
    return Polys
  
  @staticmethod
  def printStarTigerPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing=0, n=0) -> None:
    for p in Polynomial.listStarTigerPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing, n):
      Aio.print(p.toTigerStr())
      
  @staticmethod
  def listStarTigerPrimitives(PolynomialDegree, PolynomialCoefficientsCount, PolynomialBalancing=0, n=0) -> list:
    Results = []
    Candidates = []
    ChunkSize = 10000
    SerialChunkSize = 5
    for p in Polynomial.iterate(PolynomialDegree>>1, PolynomialCoefficientsCount, PolynomialBalancing):
      p._coefficients_list[0] = PolynomialDegree
      Candidates.append(Lfsr(p, STAR_TIGER_RING))
      if len(Candidates) >= ChunkSize:
        N = 0 if n <= 0 else n - len(Results)
        Results += Lfsr.checkMaximum(Candidates, N, SerialChunkSize)
        Candidates = []
        print(f'Found so far: {len(Results)}')
      if len(Results) >= n > 0:
        break
    if(len(Candidates) > 0) and not (len(Results) >= n > 0):
      N = 0 if n <= 0 else n - len(Results)
      Results += Lfsr.checkMaximum(Candidates, N, SerialChunkSize)  
    if len(Results) > n > 0:
      Results = Results[0:n-1]   
    Polys = []
    for L in Results:
      Polys.append(Polynomial(L._my_poly))
    return Polys
  
  @staticmethod
  def printTapsFromTheLeftPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, MaxDistance = 3, n=0, Silent = True) -> None:
    for p in Polynomial.listTapsFromTheLeftPrimitives(PolynomialDegree, PolynomialCoefficientsCount, MaxDistance, n, Silent):
      Aio.print(p.getCoefficients())
      
  @staticmethod
  def listTapsFromTheLeftPrimitives(PolynomialDegree : int, PolynomialCoefficientsCount : int, MaxDistance = 3, n=0, Silent = True) -> list:
    clist = [PolynomialDegree]
    davg = PolynomialDegree // PolynomialCoefficientsCount
    distance = MaxDistance
    if davg < distance:
      distance = davg
    num = PolynomialDegree
    for _ in range(1, PolynomialCoefficientsCount-1):
      num -= distance
      clist.append(num)
    clist.append(0)
    poly = Polynomial(clist)
    plist = [poly.copy()]
    while poly.makeNext():
      plist.append(poly.copy())
    return Polynomial.checkPrimitives(plist, n, Silent)
  
  @staticmethod
  def firstTapsFromTheLeftPrimitive(PolynomialDegree : int, PolynomialCoefficientsCount : int, MaxDistance = 3, Silent = True) -> list:
    lst = Polynomial.listTapsFromTheLeftPrimitives(PolynomialDegree, PolynomialCoefficientsCount, MaxDistance, Silent)
    if len(lst) > 0:
      return lst[0]
    return None
  
  @staticmethod
  def decodeUsingBerlekampMassey(Sequence) -> Polynomial:
    if Aio.isType(Sequence, "Lfsr"):
      Seq2 = Sequence.getSequence(Length=Sequence._size<<1+2)
    else:
      Seq2 = Sequence
    seq = []
    for S in Seq2:
      if int(S):
        seq.append(1)
      else:
        seq.append(0)
    return _BerlekampMassey(seq).getPolynomial().getReversed()
  
  def derivativeGF2(self) -> Polynomial:
    result = self.copy();
    coeffs = result._coefficients_list
    coeffs.sort()
    new_coeffs = []
    for i in range(1,len(coeffs)):
      if coeffs[i] & 1 == 1:
        new_coeffs.append(coeffs[i]-1)
    new_coeffs.sort(reverse=True)
    result._coefficients_list = new_coeffs
    return result

# POLYNOMIAL END ==================


# LFSR TYPE ENUM ==================

class LfsrType:
  """Enumerator used to determine an LFSR type. 
  """
  Galois = 1
  Fibonacci = 2
  RingGenerator = 3
  RingWithSpecifiedTaps = 4
  TigerRing = 5
  HybridRing = 6
  StarRing = 7
  StarTigerRing = 8
  StarHybridRing = 9

# Constants
FIBONACCI = LfsrType.Fibonacci
GALOIS = LfsrType.Galois
RING_GENERATOR = LfsrType.RingGenerator
RING_WITH_SPECIFIED_TAPS = LfsrType.RingWithSpecifiedTaps
TIGER_RING = LfsrType.TigerRing
HYBRID_RING = LfsrType.HybridRing
STAR_RING = LfsrType.StarRing
STAR_TIGER_RING = LfsrType.StarTigerRing
STAR_HYBRID_RING = LfsrType.StarHybridRing


# LFSR BEGIN ======================
class Lfsr:
  pass
class Lfsr:
  """An LFSR object. Used for all 3 LFSR implementations, like 
  Galois, Fibonacci (default), RingGenerator.
  """
  _my_poly = []
  _my_signs = []
  _type = LfsrType.Galois
  _hval = 0
  _size = 0
  _ba_fast_sim_array = None
  _taps = []
  _baValue = bitarray(0)
  _bamask = bitarray(0)
  _notes = ""
  def __del__(self):
    self.clear()
    self._taps.clear()
    self._my_poly.clear()    
    
  def tui(self) -> Lfsr:
    global _LFSR
    _LFSR = self.copy()
    tui = _LfsrTui()
    tui.run()
    if tui.EXE == "ok":
      return _LFSR
    return None
    
  def getDestinationsDictionary(self) -> dict:
    DestDict = {}
    Size = self._size
    for i in range(Size):
      DestDict[i] = [(i + 1) % Size]
    if self._type == LfsrType.RingGenerator or self._type == LfsrType.RingWithSpecifiedTaps:
      Taps = self.getTaps()
      for Tap in Taps:
        S = Tap[0]
        D = Tap[1]
        Aux = DestDict[D]
        Aux.append(S)
        DestDict[D] = Aux    
    elif self._type == LfsrType.Fibonacci:
      Poly = self._my_poly
      Aux = DestDict[Size-1]
      for i in range(1, len(Poly)-1):
        Aux.append(Poly[i])
      DestDict[Size-1] = Aux
    elif self._type == LfsrType.Galois:
      Poly = self._my_poly
      for i in range(1, len(Poly)-1):
        Aux = DestDict[i-1]
        Aux.append(0)
        DestDict[i-1] = Aux
    else:
      Aio.printError("Not implemented")
    return DestDict
    
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
          V ^= Values[S]
        if i in InjectionAtBit:
          V ^= Injector
        NewValues.append(V)
        #print(NewValues)
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
    
  def clear(self):
    """Clears the fast-simulation array
    """
    if self._ba_fast_sim_array is not None:
      #self._ba_fast_sim_array.clear()
      del self._ba_fast_sim_array
      self._ba_fast_sim_array = None
  def __iter__(self):
    self.reset()
    self._v0 = self._baValue.copy()
    self._next_iteration = False
    return self
  def __next__(self):
    val = self._baValue.copy()
    if self._next_iteration:    
      if val == self._v0:
        raise StopIteration
    else:
      self._next_iteration = True
    self.next()
    return val
  def copy(self):
    return Lfsr(self)
  def __init__(self, polynomial, lfsr_type = LfsrType.Fibonacci, manual_taps = []):
    poly = polynomial
    if "Lfsr" in str(type(polynomial)):
        self._my_poly = polynomial._my_poly.copy()
        self._my_signs = polynomial._my_signs.copy()
        self._type = polynomial._type
        self._hval = copy.deepcopy(polynomial._hval)
        self._size = polynomial._size
        self._baValue = polynomial._baValue.copy()
        self._bamask = polynomial._bamask.copy()
        try:
          self._ba_fast_sim_array = polynomial._ba_fast_sim_array.copy()
        except:
          self._ba_fast_sim_array = polynomial._ba_fast_sim_array
        self._taps = polynomial._taps.copy()
        self._notes = copy.deepcopy(polynomial._notes)
        return
    if type(Polynomial([0])) != type(polynomial):
      if lfsr_type == LfsrType.RingWithSpecifiedTaps:
        poly = Polynomial([int(polynomial),0])
      else:
        poly = Polynomial(polynomial)
    self._ba_fast_sim_array = None
    self._my_poly = poly.getCoefficients()
    self._my_signs = poly.getSigns()
    self._type = lfsr_type
    self._size = poly.getDegree()
    self._baValue = bitarray(self._size)
    if lfsr_type == LfsrType.RingWithSpecifiedTaps:
      self._taps = manual_taps
    elif lfsr_type == LfsrType.Galois:
      self._bamask = (poly.toBitarray() << 1)[:-1]
    elif lfsr_type == LfsrType.Fibonacci:
      self._bamask = poly.toBitarray()[:-1]
    elif lfsr_type in {LfsrType.RingGenerator, LfsrType.TigerRing, LfsrType.HybridRing}:
      self._rg_table = []
      flist = self._my_poly
      flist_incr = flist.copy()
      flist_incr.sort()
      bitcount = flist[0]
      taps_count = len(flist) - 2
      sum = 0
      active_upper = True
      From = 0
      To = bitcount-1
      taps = []
      for i in range(taps_count):
        factor = flist_incr[i+1]
        while sum < factor:
          sum += 1
          if active_upper:
            active_upper = False
            if From <= 0:
              From = bitcount-1
            else:
              From -= 1
          else:
            active_upper = True
            if To >= bitcount-1:
              To = 0
            else:          
              To += 1
        taps.append([From, To])
      self._taps = taps
      if lfsr_type == LfsrType.TigerRing:
        for i in range(0, len(taps), 2):
          self.reverseTap(i)
        self._type = LfsrType.RingWithSpecifiedTaps
      elif lfsr_type == LfsrType.HybridRing:
        signs = self._my_signs
        for i in range(1, len(signs)-1):
          if signs[i] < 0:
            self.reverseTap(taps_count - i)
        self._type = LfsrType.RingWithSpecifiedTaps
    elif lfsr_type in [LfsrType.StarRing, LfsrType.StarTigerRing, LfsrType.StarHybridRing]:
      taps = []
      flist = self._my_poly
      signs = self._my_signs
      deg = flist[0]
      deg_div2 = (deg >> 1)
      for i in range(1, len(flist)):
        S = flist[i]
        D = ((S - 1 + deg_div2) % deg)
        taps.append([S, D])
      self._taps = taps
      for i in range(1, len(signs)-1):
        if signs[i] < 0:
          self.reverseTap(taps_count - i)
      if lfsr_type == LfsrType.StarTigerRing:
        for i in range(0, len(taps), 2):
          self.reverseTap(i)
      elif lfsr_type == LfsrType.StarHybridRing:
        signs = self._my_signs
        for i in range(1, len(signs)-1):
          if signs[i] < 0:
            self.reverseTap(taps_count - i)
      self._type = LfsrType.RingWithSpecifiedTaps
    else:
      Aio.printError("Unrecognised lfsr type '" + str(lfsr_type) + "'")
    self.reset()
    self._hval = 1 << (poly.getDegree()-1)
    
  def getReciprocal(self):
    if self._type == LfsrType.RingWithSpecifiedTaps:
      L = self.copy()
      H = (L._size + 1) >> 1
      for i in range(len(L._taps)):
        S = L._taps[i][0]
        D = L._taps[i][1]
        if S < H:
          S = H - S
        else:
          S = H + (L._size - S) 
        if D < H:
          D = H - D - 2
        else:
          D = H + (L._size - D) - 2
        L._taps[i] = [S, D]
      return L
    if self._type == LfsrType.RingGenerator:
      Poly = Polynomial(self._my_poly)
      return Lfsr(Poly.getReciprocal(), LfsrType.RingGenerator)
    if self._type == LfsrType.Fibonacci:
      Poly = Polynomial(self._my_poly)
      return Lfsr(Poly.getReciprocal(), LfsrType.Fibonacci)
    if self._type == LfsrType.Galois:
      Poly = Polynomial(self._my_poly)
      return Lfsr(Poly.getReciprocal(), LfsrType.Galois)
    else:
      Aio.printError("'getReciprocal' is available only for Lfsrs of type RING_WITH_SPECIFIED_TAPS")
      return None
  def toBinString(self):
    return BinString(str(self))
  def __str__(self) -> str:
    return Bitarray.toString(self._baValue)
  def __repr__(self) -> str:
    result = "Lfsr("
    if self._type == LfsrType.Galois:
      result += str(self._my_poly) + ", LfsrType.Galois"
    if self._type == LfsrType.Fibonacci:
      result += str(self._my_poly) + ", LfsrType.Fibonacci" 
    if self._type == LfsrType.RingGenerator:
      result += str(self._my_poly) + ", LfsrType.RingGenerator" 
    if self._type == LfsrType.RingWithSpecifiedTaps:
      result += str(self._size) + ", LfsrType.RingWithSpecifiedTaps, " + str(self._taps)
    result += ")"
    return result
  def __eq__(self, other) -> bool:
    if self._type != other._type:
      return False
    if self._bamask != other._bamask:
      return False
    if self._taps != other._taps:
      return False
    return True
  def __ne__(self, other) -> bool:
    return not (self == other)
  def _buildFastSimArray(self):
    oldVal = self._baValue
    size = self._size
    FSA = create2DArray(size, size, None)
    value0 = bitarray(size)
    value0.setall(0)
    value0[0] = 1
    for i in range(size):
      self._baValue = value0.copy()
      self.next()
      FSA[0][i] = self._baValue.copy()
      value0 >>= 1 
    zeros = bitarray(size)
    zeros.setall(0)
    for r in range(1,size):
      rowm1 = FSA[r-1]
      for c in range(size):
        res = zeros.copy()
        for index in rowm1[c].search(1):
          res ^= rowm1[index]
        FSA[r][c] = res
    self._ba_fast_sim_array = FSA
    self._baValue = oldVal
  def rotateTap(self, TapIndex : int, FFs : int) -> bool:
    if 0 <= TapIndex < len(self._taps):
      Size = self._size
      Tap = self._taps[TapIndex]
      S = Tap[0]
      D = Tap[1]
      S += FFs
      D += FFs
      while S >= Size:
        S -= Size
      while D >= Size:
        D -= Size
      while S < 0:
        S += Size
      while D < 0:
        D += Size
      Tap = [S, D]
      self._taps[TapIndex] = Tap
      self._type = LfsrType.RingWithSpecifiedTaps
      return True
    return False
  def reverseTap(self, TapIndex : int) -> bool:
    if 0 <= TapIndex < len(self._taps):
      Size = self._size
      Tap = self._taps[TapIndex]
      S = Tap[0]
      D = Tap[1]
      D2 = S - 1
      while D2 < 0: 
          D2 += Size
      S2 = D + 1
      while S2 >= Size: 
          S2 -= Size
      self._taps[TapIndex] = [S2, D2]
      self._type = LfsrType.RingWithSpecifiedTaps
      return True
    return False
  def getDual(self):
    if self._type == LfsrType.Fibonacci:
      return Lfsr(self._my_poly.copy(), LfsrType.Galois)
    if self._type == LfsrType.Galois:
      return Lfsr(self._my_poly.copy(), LfsrType.Fibonacci)
    else:
      Result = self.copy()
      for i in range(len(Result._taps)):
        Result.reverseTap(i)
      Result._type = LfsrType.RingWithSpecifiedTaps
      return Result
    
  def getTaps(self):
    return self._taps.copy()
  
  def getPhaseShiftIndexes(self, ListOfXoredOutputs : list, DelayedBy : int) -> list:
    Dual = self.getDual()
    Dual._baValue.setall(0)
    if Aio.isType(ListOfXoredOutputs, 0):
      ListOfXoredOutputs = [ListOfXoredOutputs]
    if DelayedBy == 0:
      return ListOfXoredOutputs.copy()
    Max = Int.mersenne(self._size)
    while DelayedBy < 0:
      DelayedBy += Max
    while DelayedBy > Max:
      DelayedBy -= Max
    for i in ListOfXoredOutputs:
      Dual._baValue[i] = 1
    Dual.next(DelayedBy)
    return Dual._baValue.search(1)
  def createPhaseShifter(self, OutputCount : int, MinimumSeparation = 100, MaxXorInputs = 3, MinXorInputs = 1, FirstXor = None) -> PhaseShifter:
    if 0 < MinXorInputs <= MaxXorInputs:
      if FirstXor is None:
        FirstXor = [i for i in range(MinXorInputs)]
      XorList = []
      ActualXor = FirstXor
      XorList.append(ActualXor.copy())
      for i in range(OutputCount-1):
        ActualXor = self.getPhaseShiftIndexes(ActualXor, MinimumSeparation)
        while len(ActualXor) < MinXorInputs or len(ActualXor) > MaxXorInputs:
          ActualXor = self.getPhaseShiftIndexes(ActualXor, 1)
        XorList.append(ActualXor.copy())
      PS = PhaseShifter(self, XorList)
      return PS
    return None
  def getValue(self) -> bitarray:
    """Returns current value of the LFSR
    """
    return self._baValue
  def setValue(self, Value : bitarray):
    Value = bitarray(Value)
    if len(Value) != len(self._baValue):
      Aio.printError(f"The new value is {len(Value)} bit length while should be {len(self._baValue)}.")
    self._baValue = Value
  def getSize(self) -> int:
    """Returns size of the LFSR
    """
    return (self._size)
  def next(self, steps=1) -> bitarray:
    """Performs a shift of the LFSR. If more than 1 step is specified, 
    the fast-simulation method is used.

    Args:
        steps (int, optional): How many steps to simulate. Defaults to 1.

    Returns:
        bitarray: new LFSR value
    """
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return 0
    elif steps == 0:
      return self._baValue
    elif steps == 1:
      if self._type == LfsrType.Fibonacci:
        ParityBit = bau.count_and(self._baValue, self._bamask) & 1
        self._baValue <<= 1
        if ParityBit:
          self._baValue[-1] = 1
        return self._baValue
      elif self._type == LfsrType.Galois:
        lbit = self._baValue[0]
        self._baValue <<= 1
        if lbit:
          self._baValue ^= self._bamask
        return self._baValue
      elif self._type == LfsrType.RingGenerator or self._type == LfsrType.RingWithSpecifiedTaps:
        nval = Bitarray.rotl(self._baValue)
        for tap in self._taps:
          nval[tap[1]] ^= self._baValue[tap[0]]
        self._baValue = nval
        return self._baValue
      return bitarray(self._size).setall(0)
    else:
      if self._ba_fast_sim_array is None:
        self._buildFastSimArray()
      size = self._size
      RowIndex = 0
      baresult = bitarray(size)
      while steps > 0: 
        if steps & 1:
          baresult.setall(0)
          for index in self._baValue.search(1):
            baresult ^= self._ba_fast_sim_array[RowIndex][index]
          self._baValue = baresult.copy()
        steps >>= 1
        RowIndex += 1
      return self._baValue    
  def getPeriod(self) -> int:
    """Simulates the LFSR to obtain its period (count of states in trajectory).

    Returns:
        int: result. If the result is == (1<<size) it means a subtrajectory was reached
              and it cannot determine the period.
    """
    MaxResult = Int.mersenne(self._size) + 1
    if self.isMaximum():
      return MaxResult
    self.reset()
    value0 = self._baValue.copy()
    valuebefore = self._baValue.copy()
    valuex = self.next().copy()
    for i in range(MaxResult+1):
      if valuex == value0:
        return i+1
      elif valuex == valuebefore:
        return 1
      valuebefore = valuex
      valuex = self.next().copy()  
    return -1      
  def _isMaximumAndClean(self) -> bool:
    Result = self.isMaximum()
    self.clear()
    return Result
  def _isMaximumList(List : list) -> list:
    Results = []
    for L in List:
      if L.isMaximum():
        Results.append(L)
    return Results
  def _isMaximumAsync(self) -> bool:
    if self.isMaximum():
      return self
    return None
  def isMaximum(self) -> bool:
    """Uses the fast-simulation method to determine if the LFSR's trajectory
    includes all possible (but 0) states. 

    Returns:
        bool: True if is maximum, otherwise False.
    """
    index = self._size
    self.reset()
    value0 = self._baValue.copy()
    if self.next(Int.mersenne(index)) != value0:
      return False
    lst = DB.getPrimitiveTestingCyclesList(index)
    for num in lst:
      self.reset()
      if self.next(num) == value0:
        return False
    return True
  def reset(self) -> bitarray:
    """Resets the LFSR value to the 0b0...001

    Returns:
        bitarray: The new value
    """
    self._baValue.setall(0)
    self._baValue[0] = 1
    return self._baValue
  
  def getValuesIterator(self, n = 0, step = 1, reset = True, AsStrings = False):
    if n <= 0:
      n = self.getPeriod()
    if reset:
      self.reset()
    for i in range(n):
      if AsStrings:
        yield Bitarray.toString(self._baValue)
      else:
        yield self._baValue.copy()
      self.next(step)
  
  def getValues(self, n = 0, step = 1, reset = True, AsStrings = False) -> list:
    """Returns a list containing consecutive values of the LFSR.

    Args:
        n (int, optional): How many steps to simulate for. If M= 0 then maximum period is obtained. Defaults to 0.
        step (int, optional): steps (clock pulses) per iteration. Defaults to 1.
        reset (bool, optional): If True, then the LFSR is resetted to the 0x1 value before simulation. Defaults to True.

    Returns:
        list of bitarrays.
    """
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
    """Prints the consecutive binary values of the LFSR.

    Args:
        n (int, optional): How many steps to simulate for. If M= 0 then maximum period is obtained. Defaults to 0.
        step (int, optional): steps (clock pulses) per iteration. Defaults to 1.
        reset (bool, optional): If True, then the LFSR is resetted to the 0x1 value before simulation. Defaults to True.
    """
    if n <= 0:
      val0 = self._baValue.copy()
      n = self.getPeriod()
      self._baValue = val0
    if reset:
      self.reset()
    for i in range(n):
      Aio.print(self)
      self.next(step)
  def getMSequence(self, BitIndex = 0, Reset = True):
    return self.getSequence(BitIndex, Reset, 0)
  def getSequence(self, BitIndex = 0, Reset = True, Length = 0) -> bitarray:
    """Returns a bitarray containing the Sequence of the LFSR.

    Args:
        bitIndex (int, optional): At this bit the sequence is observed. Defaults to 0.
        reset (bool, optional): If True, then the LFSR is resetted to the 0x1 value before simulation. Defaults to True.
        length (int, optional): returns specified count of bits of sequence
    Returns:
        str: M-Sequence
    """
    result = bitarray()
    if Reset:
      self.reset()
    n = Length
    if n <= 0:
      n = self.getPeriod()
    for i in range(n):
      result.append(self._baValue[BitIndex])
      self.next()
    return result
  def printFastSimArray(self):
    """Prints the fast-simulation array.
    """
    if self._ba_fast_sim_array is None:
      self._buildFastSimArray()
    for r in self._ba_fast_sim_array:
      line = ""
      for c in r:
        line += Bitarray.toString(c) + "\t"
      Aio.print(line)
  def _simplySim(self, sequence):
    rm = Lfsr(self)
    res = rm.simulateForDataString(sequence, self._IBit, self._Start)
    self._C.append(0)
#    cnt = len(self._C)
#    if cnt % 100 == 0:
#      perc = round(cnt * 100 / self._N, 1)
#      Aio.printTemp("  Lfsr sim ", perc , "%             ")  
    return res
  def simulateForDataString(self, Sequence, InjectionAtBit = 0, StartValue = 0) -> bitarray:
    if Aio.isType(Sequence, []):
      self._IBit = InjectionAtBit
      self._Start = StartValue
      man = multiprocess.Manager()
      self._C = man.list()
      #results = pool.map(self._simplySim, Sequence)
      results = p_map(self._simplySim, Sequence)
      Aio.printTemp("                                    ")
      del self._C
      return results
    if Aio.isType(StartValue, 0):
      self._baValue = bau.int2ba(StartValue, length=self._size, endian='little')
    if Aio.isType(StartValue, "bitarray"):
      self._baValue = StartValue
    if Aio.isType(Sequence, ""):
      Sequence = bitarray(Sequence)
    Mask = self._baValue.copy()
    Mask.setall(0)
    if Aio.isType(InjectionAtBit, 0):
      Mask[InjectionAtBit] = 1
    else:
      for I in InjectionAtBit:
        Mask[I] = 1   
    for Bit in Sequence:
      self.next()
      if Bit:
        self._baValue ^= Mask
    return self._baValue
  
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
    if self._type == LfsrType.Fibonacci:
      for j in range(1, len(self._my_poly)-1):
        Sources[Size-1] += f" ^ O[{j}]"
    elif self._type == LfsrType.Galois:
      for j in range(1, len(self._my_poly)-1):
        Sources[j-1] += f" ^ O[0]"
    else:
      for Tap in self._taps:
        Sources[Tap[1]] += f" ^ O[{Tap[0]}]"
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
  
  def getDraw(self, MaxWidth = 0, Overlap = 3) -> str:
    if self._type == LfsrType.Fibonacci:
      Canvas = AsciiDrawingCanvas(self._size*5+3, 5)
      Canvas.drawBox(0, 0, Canvas._width-1, 3)
      for i in range(self._size):
        ffindex = self._size - i - 1
        Canvas.drawBox(i*5+2, 2, 3, 2, str(ffindex))
        Canvas.fixLinesAtPoint(i*5+2, 3)
        Canvas.fixLinesAtPoint(i*5+5, 3)
        if ffindex != 0 and ffindex in self._my_poly:
          Canvas.drawConnectorVV(i*5+6, 3, i*5+6, 0)
          Canvas.drawXor(i*5+6, 0)
          Canvas.drawChar(i*5+5, 0, AsciiDrawing_Characters.LEFT_ARROW)
    elif self._type == LfsrType.Galois:
      Canvas = AsciiDrawingCanvas(self._size*5+3, 5)
      Canvas.drawBox(0, 0, Canvas._width-1, 3)
      for i in range(self._size):
        ffindex = self._size - i - 1
        Canvas.drawBox(i*5+2, 2, 3, 2, str(ffindex))
        Canvas.fixLinesAtPoint(i*5+2, 3)
        Canvas.fixLinesAtPoint(i*5+5, 3)
        if ffindex != 0 and ffindex in self._my_poly:
          Canvas.drawConnectorVV(i*5+6, 3, i*5+6, 0)
          Canvas.drawXor(i*5+6, 3)
      Canvas.drawChar(1, 3, AsciiDrawing_Characters.RIGHT_ARROW)
    else:
      Uffs = self._size >> 1
      Lffs = self._size - Uffs
      Uoffset = 0
      if Lffs > Uffs:
        Uoffset = 6
      Canvas = AsciiDrawingCanvas(Lffs*6+2, 9)
      Canvas.drawBox(0, 1, Canvas._width-1, 6)
      Canvas.drawChar(1, 7, AsciiDrawing_Characters.RIGHT_ARROW)
      Canvas.drawChar(Canvas._width-2, 1, AsciiDrawing_Characters.LEFT_ARROW)
      for i in range(Lffs):
        ffindex = Lffs - i - 1
        Canvas.drawBox(i*6+2, 6, 3, 2, str(ffindex))
        Canvas.fixLinesAtPoint(i*6+2, 7)
        Canvas.fixLinesAtPoint(i*6+5, 7)
      for i in range(Uffs):
        ffindex = Lffs + i
        Canvas.drawBox(i*6+2+Uoffset, 0, 3, 2, str(ffindex))
        Canvas.fixLinesAtPoint(i*6+2+Uoffset, 1)
        Canvas.fixLinesAtPoint(i*6+5+Uoffset, 1)
      for tap in self._taps:
        BU = 1
        ED = 1
        S = tap[0]
        D = tap[1]
        if S < Lffs:
          BU = 0
        if D >= Lffs:
          ED = 0
        if BU:
          Bx = (S-Lffs)*6+1+Uoffset
        else:
          Bx = (Lffs-S)*6
        if ED:
          Ex = (Lffs-D-1)*6+1
        else:
          Ex = (D-Lffs+1)*6+Uoffset
        if BU and ED:
          Canvas.drawConnectorVV(Bx, 1, Ex, 7)
          Canvas.drawXor(Ex, 7)
          Canvas.fixLinesAtPoint(Bx, 4)
        elif BU and not ED:
          Canvas.drawConnectorVDV(Bx, 1, Ex, 1, 2)
          Canvas.drawXor(Ex, 1)
        elif not BU and ED:
          Canvas.drawConnectorVUV(Bx, 7, Ex, 7, 2)
          Canvas.drawXor(Ex, 7)
        elif not BU and not ED:
          Canvas.drawConnectorVV(Bx, 7, Ex, 1)
          Canvas.drawXor(Ex, 1)
          Canvas.fixLinesAtPoint(Bx, 4)      
    return Canvas.toStr(MaxWidth, Overlap)
  def print(self):
    Aio.print(self.getDraw())
  def getJTIndex(self, index):
    if self._type == LfsrType.RingGenerator:
      One = self._size & 1
      UpperSize = self._size >> 1
      LowerSize = self._size - UpperSize
      if index >= LowerSize:
        return index - LowerSize 
      return index + LowerSize - One
    return index
  def analyseSequencesBatch(ListOfObjects) -> list:
    #return process_map(_analyseSequences_helper, ListOfObjects, chunkside=2, desc="Sequences analysis")
    R = p_map(_analyseSequences_helper, ListOfObjects)
    return R
  def _sumstr(self,Sum) -> str:
    Second = 0
    Result = ""
    for S in Sum:
      if Second:
        Result += "+"
      else:
        Second = 1
      Result += f"Q{S}"
    return Result
  def analyseSequences(self, XorInputsLimit = 0) -> MSequencesReport:
    MaxK = self._size
    if self._size >= XorInputsLimit > 0:
      MaxK = XorInputsLimit
    Values = self.getValues(reset=1)
    SequenceLength = len(Values)
    SingleSequences = [bitarray() for i in range(self._size)]
    UniqueSequences = {}
    ResultDict = {}
    ResultUDict = {}
    for word_index in range(SequenceLength):
      Word = Values[word_index]
      for flop_index in range(self._size):
        SingleSequences[flop_index].append(Word[flop_index])
    k = 1
    MyFlopIndexes = [i for i in range(self._size)]
    while (k <= MaxK):
      Uniques = 0
      ResultDict[k] = {}
      for XorToTest in List.getCombinations(MyFlopIndexes, k):
        XorToTestStr = self._sumstr(XorToTest)
        ThisSequence = bau.zeros(SequenceLength)
        for i in XorToTest:
          ThisSequence ^= SingleSequences[i]
        IsUnique = 1
        for ReferenceKey in UniqueSequences.keys():
          Reference = UniqueSequences[ReferenceKey]
          Shift = Bitarray.getShiftBetweenSequences(ThisSequence, Reference)
          if Shift is not None:
            IsUnique = 0
            ResultDict[k][self._sumstr(XorToTest)] = f"{ReferenceKey} delayed by {Shift}"
            break
        if IsUnique:
          UniqueSequences[XorToTestStr] = ThisSequence
          ResultDict[k][XorToTestStr] = f"Unique"
          Uniques += 1
        ResultUDict[k] = Uniques
      k += 1
    Report = MSequencesReport()
    Report._rep = ResultDict
    Report._max = MaxK
    Report._uniques = ResultUDict
    Report._title = repr(self)
    Report.SourceObject = self
    return Report
  def listMaximumLfsrsHavingSpecifiedTaps(SizeOrProgrammableLfsrConfiguration : int, TapsList = [], CountOnly = False, GetTapsOnly = False) -> list:
    """list Lfsrs of type RING_WITH_SPECIFIED_TAPS satisfying the given criteria.

    Args:
        Size (int): Size of the LFSRs
        TapsList (list): list of taps. Each tap must be defined in dict struct, like a MUX. 
        CountOnly (bool, optional): if True, counts results and returns the int. Defaults to 0.
        
    Examples of taps:
    
    mandatory tap from 5 to 2:      { 0: [5,2] }
    on/off from 3 to 6:             { 0: [3,6], 1: None }  // None means "off"
    demux from 3 to 5 or 6:         { 0: {3,5], 1: [3,6] }}
    ...the same with "off" option:  { 0: {3,5], 1: [3,6] }, 2: None }
    """
    if Aio.isType(SizeOrProgrammableLfsrConfiguration, "ProgrammableLfsrConfiguration"):
      Size = SizeOrProgrammableLfsrConfiguration.getSize()
      TapsList = SizeOrProgrammableLfsrConfiguration.getTaps()
    else:
      Size = int(SizeOrProgrammableLfsrConfiguration)
    MainCounter = []
    Count = 0
    ToReturn = []
    for Tap in TapsList:
      MainCounter.append(list(Tap.keys()))
    ChunkSize = 100000
    SerialChunkSize = 100
    PermCount = List.getPermutationsPfManyListsCount(MainCounter)
    SetCount = PermCount // ChunkSize + 1
    SetCntr = 0
    for Permutations in List.getPermutationsPfManyListsGenerator(MainCounter, UseAsGenerator_Chunk=ChunkSize):
      Candidates = []
      SetCntr += 1
      for P in Permutations:
        iTaps = []
        for i in range(len(TapsList)):
          Tap = TapsList[i][P[i]]
          if Tap is not None:
            iTaps.append(Tap)
        if len(iTaps) > 0:
          C = Lfsr(Size, LfsrType.RingWithSpecifiedTaps, iTaps)
          if not CountOnly:
            C.MuxConfig = P
          Candidates.append(C)
      if len(Permutations) < SerialChunkSize:
        CandidatesSplitted = List.splitIntoSublists(Candidates, 5)
      else:
        CandidatesSplitted = List.splitIntoSublists(Candidates, SerialChunkSize)
      ResultsIterator = p_uimap(Lfsr._isMaximumList, CandidatesSplitted, desc=f'{SetCntr}/{SetCount}')
      for Results in ResultsIterator:
        for Result in Results:
          if Result is not None:
            if CountOnly:
              Count += 1
            elif GetTapsOnly:
              ToReturn.append(Result.getTaps().copy())  
            else:
              ToReturn.append(Result)  
      gc.collect()
    if CountOnly:
      return Count
    return ToReturn
  
  def getSequences(self, Length=0):
    Values = self.getValues(n = Length)
    if len(Values) < 1:
      return []
    SequenceLength = len(Values)
    Result = [bitarray() for i in range(self._size)]
    for word_index in range(SequenceLength):
      Word = Values[word_index]
      for flop_index in range(self._size):
        Result[flop_index].append(Word[flop_index])
    return Result
      
  def _checkMaximumSerial(LfsrsList : list) -> list:
    Results = []
    for lfsr in LfsrsList:
      if lfsr._isMaximumAndClean():
        Results.append(lfsr)
    return Results
  
  def checkMaximum(LfsrsList : list, n = 0, SerialChunkSize = 20, ReturnAlsoNotTested = 0) -> list:
    Candidates = List.splitIntoSublists(LfsrsList, SerialChunkSize)
    Results = []
    Generator = Generators()
    Iter = p_uimap(Lfsr._checkMaximumSerial, Generator.wrapper(Candidates), total=len(Candidates), desc = f'x{SerialChunkSize}')
    ItCounter = 0
    for RL in Iter:
      Results += RL
      ItCounter += 1
      if len(Results) >= n > 0:
        Generator.disable()
    del Generator
    if len(Results) > n > 0:
      Results = Results[:n]
    if ReturnAlsoNotTested:
      NotTested = []
      for i in range(ItCounter, len(Candidates)):
        NotTested += Candidates[i]
      return [ Results, NotTested ]
    else:
      return Results
  
  @staticmethod
  def tuiCreateRing(Size = 32) -> Lfsr:
    return Lfsr(int(Size), LfsrType.RingWithSpecifiedTaps, []).tui()
    
  @staticmethod
  def tuiCreateFibonacci(Size = 32) -> Lfsr:
    return Lfsr([int(Size), 0], LfsrType.Fibonacci).tui()
    
  @staticmethod
  def tuiCreateGalois(Size = 32) -> Lfsr:
    return Lfsr([int(Size), 0], LfsrType.Galois).tui()
        
def _analyseSequences_helper(lfsr) -> MSequencesReport:
  return lfsr.analyseSequences()
    
    
class LfsrList:
  def analyseSequences(LfsrsList) -> list:      
    return Lfsr.analyseSequencesBatch(LfsrsList)
  


# LFSR END ========================
  

  
class _BerlekampMassey:
    def __init__(self, sequence):
        n = len(sequence)
        s = sequence.copy()

        k = 0
        for k in range(n):
            if s[k] == 1:
                break
        self._f = {k + 1, 0}
        self._l = k + 1

        g = {0}
        a = k
        b = 0

        for n in range(k + 1, n):
            d = 0
            for item in self._f:
                d ^= s[item + n - self._l]

            if d == 0:
                b += 1
            else:
                if 2 * self._l > n:
                    self._f ^= set([a - b + item for item in g])
                    b += 1
                else:
                    temp = self._f.copy()
                    self._f = set([b - a + item for item in self._f]) ^ g
                    self._l = n + 1 - self._l
                    g = temp
                    a = b
                    b = n - self._l + 1

    def _get_polynomial_string(self):
        result = ''
        lis = sorted(self._f, reverse=True)
        for i in lis:
            if i == 0:
                result += '1'
            else:
                result += 'x^%s' % str(i)

            if i != lis[-1]:
                result += ' + '
        return result

    def getPolynomial(self):
        return Polynomial(list(self._f))

    def getDegree(self):
        return self._l

    def __str__(self):
        return self._get_polynomial_string()

    def __repr__(self):
        return "<%s polynomial=%s>" % (self.__class__.__name__, self._get_polynomial_string())
  


  

# TUI =====================================================/

def _lfsr_sim_refresh(n = 32):
    global _LFSR, _LFSR_SIM
    Lst2 = []
    Lst1 = _LFSR.getValues(n)
    for I in Lst1:
      Lst2.append([Bitarray.toString(I), I.count(1)])
    _LFSR_SIM = Lst2

def _lfsr_sim_append():
    global _LFSR_SIM
    _lfsr_sim_refresh(len(_LFSR_SIM)<<1)
    
class _SetSize(TextualWidgets.Static):
  def compose(self):
    global _LFSR
    yield TextualWidgets.Label(" \nNew size:", id="set_size_lbl")
    yield TextualWidgets.Input(str(_LFSR.getSize()), id="set_size")

class _AddTap(TextualWidgets.Static):
  def compose(self):
    yield TextualWidgets.Label(" \nFrom", id="add_tap_from_lbl")
    yield TextualWidgets.Input(id="add_tap_from")
    yield TextualWidgets.Label(" \nTo", id="add_tap_to_lbl")
    yield TextualWidgets.Input(id="add_tap_to")
    
class _LeftMenu(TextualWidgets.Static):
    def compose(self) -> TextualApp.ComposeResult:
        global _LFSR
        self.IsRing = (_LFSR._type == LfsrType.RingGenerator) or (_LFSR._type == LfsrType.RingWithSpecifiedTaps)
        if self.IsRing:
          yield _SetSize()
          yield TextualWidgets.Button("Set size", id="btn_set_size")
          yield TextualWidgets.Label(" ")
          yield _AddTap()
          yield TextualWidgets.Button("Add tap", id="btn_add_tap")
          yield TextualWidgets.Label(" ")
        else:
          yield TextualWidgets.Label("\n  POLYNOMIAL:")
          yield TextualWidgets.Input(str(_LFSR._my_poly), id="left_menu_polynomial")
        yield TextualWidgets.DataTable(id="dt")
        yield TextualWidgets.Label(" ")
        yield TextualWidgets.Button("DUAL", id="dual")
        yield TextualWidgets.Button("RECIPROCAL", id="reci")
        yield TextualWidgets.Label(" ")
        yield TextualWidgets.Button("More simulation steps", id="asim")
        yield TextualWidgets.Label(" ")
        yield TextualWidgets.Button("OK", id="btn_ok", variant="success")
        yield TextualWidgets.Button("Cancel", id="btn_cancel", variant="error")
    def refreshTable(self):
        global _LFSR
        Taps = _LFSR.getTaps()
        table = self.query_one(TextualWidgets.DataTable)
        table.clear()
        if len(Taps) > 0:
          for Tap in Taps:
              table.add_row(str(Tap), "[ROTL]", "[INV]", "[ROTR]", "[REMOVE]")
    def on_mount(self):
        global _LFSR
        if self.IsRing:
          table = self.query_one(TextualWidgets.DataTable)
          table.add_columns("TAP", ".", ".", ".", ".")
          self.refreshTable()
        else:
          self.set_interval(0.2, self.on_my_interval)
    def refreshPolynomial(self, Poly : Polynomial):
      if not self.IsRing:
        self.query_one("#left_menu_polynomial").value = str(Poly)
    def on_my_interval(self):
      global _LFSR
      try:
        p = Polynomial(list(ast.literal_eval(self.query_one("#left_menu_polynomial").value)))
        _LFSR.__init__(p, _LFSR._type)
        _lfsr_sim_refresh()
      except:
        pass
    def on_data_table_cell_selected(self, event: TextualWidgets.DataTable.CellSelected) -> None:
        global _LFSR
        if event.coordinate.column > 0:
            TapIndex = event.coordinate.row
            if event.coordinate.column == 1:
                _LFSR.rotateTap(TapIndex, -1)
            elif event.coordinate.column == 3:
                _LFSR.rotateTap(TapIndex, 1)
            elif event.coordinate.column == 2:
                _LFSR.reverseTap(TapIndex)
            elif event.coordinate.column == 4:
                _LFSR._taps.remove(_LFSR._taps[TapIndex])
            _LFSR._type = LfsrType.RingWithSpecifiedTaps
            self.refreshTable()
            _lfsr_sim_refresh()
    def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
        global _LFSR, _LFSR_SIM
        if event.button.id == "dual":
            _LFSR = _LFSR.getDual()
            self.refreshTable()
            _lfsr_sim_refresh()
        elif event.button.id == "reci":
            _LFSR = _LFSR.getReciprocal()
            if not self.IsRing:
              self.refreshPolynomial(_LFSR._my_poly)
            self.refreshTable()
            _lfsr_sim_refresh()
        elif event.button.id == "btn_add_tap":
          ATap = self.query_one(_AddTap)
          From = int(ATap.query_one("#add_tap_from").value)
          To = int(ATap.query_one("#add_tap_to").value)
          Tap = [From, To]
          Taps = _LFSR._taps
          Size = _LFSR.getSize()
          if (0 <= From < Size) and (0 <= To < Size):
            if Tap not in Taps:
              Taps.append(Tap)
              self.refreshTable()
              _lfsr_sim_refresh()
        elif event.button.id == "btn_set_size":
          SizeW = self.query_one(_SetSize)
          Size = int(SizeW.query_one("#set_size").value)
          if Size < 0:
            return
          Taps = _LFSR._taps
          for Tap in Taps:
            for V in Tap:
              if V >= Size:
                return
          _LFSR._size = Size
          _LFSR.clear()
          _LFSR._baValue = bitarray(Size)
          _LFSR.reset()
          _LFSR._type = LfsrType.RingWithSpecifiedTaps
          _lfsr_sim_refresh()
        elif event.button.id == "asim":
            _lfsr_sim_append()
        elif event.button.id == "btn_ok":
            self.app.EXE = "ok"
            self.app.exit()
        elif event.button.id == "btn_cancel":
            self.app.EXE = "cancel"
            self.app.exit()
        
class _VTop(TextualWidgets.Static):
    LfsrDraw = TextualReactive.reactive("")
    Lbl = None
    def compose(self):
        self.Lbl = TextualWidgets.Label()
        yield self.Lbl 
    def on_mount(self):
        self.set_interval(0.2, self.update_LfsrDraw)
    def update_LfsrDraw(self):
        global _LFSR
        self.LfsrDraw = _LFSR.copy().getDraw()
    def watch_LfsrDraw(self):
        self.Lbl.update(self.LfsrDraw)
        
class _VMiddle(TextualWidgets.Static):
    LfsrPoly = TextualReactive.reactive(Polynomial([1,0]))
    def on_mount(self):
        self.set_interval(0.2, self.update_LfsrPoly)
    def update_LfsrPoly(self):
        global _LFSR, _WATCH
        self.LfsrPoly = Polynomial.decodeUsingBerlekampMassey(_LFSR)
    def watch_LfsrPoly(self):
        global _LFSR
        l = _LFSR.copy()
        Max = "IS MAXIMUM" if l.isMaximum() else "is NOT maximum"
        Prim = "IS PRIMITIVE" if self.LfsrPoly.isPrimitive() else "Is NOT primitive"
        self.update(f"This LFSR {Max}.\nCharacteristic polynomial {Prim}: {self.LfsrPoly}")
        
class _VBottom(TextualWidgets.Static):
    SimROws = TextualReactive.reactive([])
    def compose(self):
        self.Data = TextualWidgets.DataTable()
        yield TextualWidgets.DataTable()
        yield TextualWidgets.Label("")
    def on_mount(self):
        _lfsr_sim_refresh()
        self.set_interval(0.5, self.update_simdata)
        table = self.query_one(TextualWidgets.DataTable)
        table.add_columns("#Cycle", "Value (n-1, ..., 0)", "#1s")
    def update_simdata(self):
        global _LFSR_SIM
        self.SimROws = _LFSR_SIM
    def watch_SimROws(self):
        global _LFSR_SIM
        table = self.query_one(TextualWidgets.DataTable)
        table.clear()
        for i in range(len(_LFSR_SIM)):
          v = _LFSR_SIM[i]
          table.add_row(i, v[0], v[1])
        
class _HRight(TextualWidgets.Static):
    def compose(self) -> TextualApp.ComposeResult:
        yield _VTop()
        yield _VMiddle()
        yield _VBottom()
                
class _HLayout(TextualWidgets.Static):
    def compose(self) -> TextualApp.ComposeResult:
        yield _LeftMenu()
        yield _HRight()
    
class _LfsrTui(TextualApp.App):
    BINDINGS = [("q", "quit", "Quit"), ('a', 'asim', 'Append values')]
    CSS_PATH = "tui/lfsr.css"
    def compose(self) -> TextualApp.ComposeResult:
        self.dark=False
        yield TextualWidgets.Header()
        yield _HLayout()
        yield TextualWidgets.Footer()
        self.EXE = ""
    def action_asim(self):
        _lfsr_sim_append()
      

