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
#from tqdm.contrib.concurrent import process_map




class MSequencesReport:
  """This class is used to hold the result of MSequence analysis.
  """
  _xor2 = False
  _xor3 = False
  _dict = {}
  _title = ""
  SourceObject = None
  def __str__(self) -> str:
    return self.getReport() 
  
  def _psmaxlevel(self) -> int:
    if self._xor3:
      return 3
    elif self._xor2:
      return 2
    return 2
  
  def getTitle(self) -> str:
    """Returns a string containing the report's title.
    """
    return self._title
  
  def getUniqueCount(self, PhaseShifterGatesInputs = 0) -> int:
    """get the number ofunique sequences.

    Args:
        PhaseShifterGatesInputs (int, optional): maximum count of inputs of phase shifter's XORs.. Defaults to 0 (no limit).
    """
    if PhaseShifterGatesInputs <= 0 or PhaseShifterGatesInputs > 3:
      PhaseShifterGatesInputs = self._psmaxlevel()
    return self._dict[PhaseShifterGatesInputs]["unique_count"]
  
  def getReport(self, PhaseShifterGatesInputs = 0) -> str:
    """returns a string containing the full report of MSequence analysis.

    Args:
        PhaseShifterGatesInputs (int, optional): maximum count of inputs of phase shifter's XORs.. Defaults to 0 (no limit).
    """
    Lines = ""
    if PhaseShifterGatesInputs <= 0 or PhaseShifterGatesInputs > 3:
      PhaseShifterGatesInputs = self._psmaxlevel()
    SDict = self._dict[PhaseShifterGatesInputs]
    keys = list(SDict.keys())
    keys.sort()
    Lines += f'UNIQUE SEQUENCES: {SDict["unique_count"]}'
    for key in keys:
      if key == "unique_count":
        continue
      Lines += (f'\n{key}{" " * (18 - len(key))}=>  {SDict[key]}')
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
  _coefficients_list = []
  _balancing = 0    
  _bmin = 1
  _positions = False
  _ctemp = True
  _mindist = 0
  _lf = False
  _notes = ""
  _CoefficientList = []
  _CoeffsCount = []
  _DontTouchBounds = 1
  _OddOnly = 1
  
  def _getAllPrimitivesHavingSpecifiedCoeffsHelper(self, FromTo : list):
    Polys = self._getAllHavingSpecifiedCoeffsHelper(FromTo)
    return Polynomial.checkPrimitives(Polys)
  
  def _getAllHavingSpecifiedCoeffsHelper(self, FromTo : list):
    CList = self._CoefficientList.copy()
    CList.sort()
    CCList = self._CoeffsCount.copy()
    DontTouchBounds = self._DontTouchBounds
    OddOnly = self._OddOnly
#    if DontTouchBounds and ((1<<(len(CList)-1)) & FromTo[1]) == 0:
#      return []
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
        #print("Bad length")
        continue
#      if DontTouchBounds:
#        if (not (CList[0] in PT)) or (not (CList[-1] in PT)):
#          print("Bad coeff", CList, PT)
#          continue     
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
  
  def __init__(self, coefficients_list : list, balancing = 0):
    """ Polynomial (Polynomial, balancing=0)
Polynomial (coefficients_list, balancing=0)
Polynomial (int, balancing=0)
Polynomial (hex_string, balancing=0)
Polynomial ("size,HexNumber", balancing=0)
    """
    if "Polynomial" in str(type(coefficients_list)):
      self._coefficients_list = coefficients_list._coefficients_list.copy()
      self._balancing = coefficients_list._balancing + 0
      self._bmin = coefficients_list._bmin
      self._bmax = coefficients_list._bmax
      if Aio.isType(coefficients_list._positions, []):
        self._positions = coefficients_list._positions.copy()
      else:
        self._positions = coefficients_list._positions
      self._lf = coefficients_list._lf
      self._notes = coefficients_list._notes
      self._mindist = coefficients_list._mindist
    elif "int" in str(type(coefficients_list)):
      cntr = 0
      self._coefficients_list = []
      while coefficients_list > 0:
        if coefficients_list & 1 == 1:
          self._coefficients_list.append(cntr)
        cntr += 1
        coefficients_list >>= 1
      self._coefficients_list.sort(reverse=True)
      self._balancing = balancing
      self._bmax = self._coefficients_list[0] 
    elif "str" in str(type(coefficients_list)):
      lst = coefficients_list.split(",")
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
      self._balancing = balancing   
      self._bmax = self._coefficients_list[0]   
    else:
      lst = []
      for c in coefficients_list:
        lst.append(abs(c))
      self._coefficients_list = lst
      self._coefficients_list.sort(reverse=True)
      self._balancing = balancing
      self._bmax = self._coefficients_list[0]
      
  def __hash__(self) -> int:
    return self.toInt()
      
  def __iter__(self):
    self = Polynomial.createPolynomial(self.getDegree(), self.getCoefficientsCount(), self._balancing, self._lf, self._mindist)
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
    raise StopIteration  
  
  def __str__(self) -> str:
    return str(self._coefficients_list)
  
  
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
    return "Polynomial(" + str(self._coefficients_list) + ")"
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
      result.append(deg - self._coefficients_list[i])
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
  
  def getMinimumDistance(self) -> int:
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
#  def createBasingOnCoeffsList(CoeffsList : list) -> Polynomial:
#    pass 
  def createPolynomial(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, MinimumDistance = 0) -> Polynomial:
    """Returns a polynomial, usefull for LFSRs.

    Args:
        degree (int): polynomial degree (i.e. size of LFSR)
        coeffs_count (int): coefficients count (i.e. LFSRs taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking).
        MinimumDistance (int, optional): minimum distance between successive coefficients. Defaults to 0 (no matters)
        LayoutFriendly (bool, optional): only layout-friendly poly.
    """
    if coeffs_count < 1:
      Aio.printError ("'oefficients_count' must be >= 1")
      return Polynomial([])
    if degree < (coeffs_count-1):
      Aio.printError ("'coefficients_count - 1' must be <= 'degree'")
      return Polynomial([])  
    result = [degree]
    bmin = 1
    bmax = degree-1
    if balancing > 0 and balancing < degree:
      avg = float(degree) / float(coeffs_count - 1)
      halfbal = float(balancing) / 2.0
      bmin = int(avg - halfbal)
      if bmin < 1:
        bmin = 1
      if MinimumDistance > bmin > 0:
        bmin = MinimumDistance
      if bmin < 2 and LayoutFriendly:
        bmin = 2
      bmax = bmin + balancing
      if bmax > degree-1:
        bmax = degree-1
      result = [0]
      rest = degree
      actual = bmin
      restcoeffs = coeffs_count-2
      diff = bmin
      diffmax = bmax
      diffmin = diff
      for i in range(2, coeffs_count):
        while (diffmin + ((restcoeffs-1) * diffmax)) < (rest-diff):
          diffmin += 1
        coeff = actual
        result.append(coeff)
        rest -= diffmin
        restcoeffs -= 1
        actual += diffmin
      result.append(degree)
    elif MinimumDistance > 0:
      bmin = MinimumDistance
      result = [0]
      c = MinimumDistance
      for i in range(2, coeffs_count):
        result.append(c)
        c += MinimumDistance
      result.append(degree)
    else:
      for i in range(coeffs_count-1):
        result.append(i)
    p = Polynomial(result, balancing)
    q = p.getReversed()
    pos = {}
    cp = p._coefficients_list.copy()
    cq = q._coefficients_list.copy()
    for i in range(1, coeffs_count-1):
      pos[i] = [cp[i], cq[i]]
    p._positions = pos
    p._bmin = bmin
    p._bmax = bmax
    p._lf = LayoutFriendly
    p._mindist = MinimumDistance
#    print(Aio.format(pos))
    if p.getMinimumDistance() < p._mindist > 0:
      return None
    if p.getBalancing() > p._balancing > 0:
      while p.getBalancing() > p._balancing:
        if not p._makeNext():
          return None
    return p
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
  def printTigerPrimitives(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, MinimumDistance = 0, n = 0, NoResultsSkippingIteration = 0) -> list:
    Polys = Polynomial.listTigerPrimitives(degree, coeffs_count, balancing, LayoutFriendly, MinimumDistance, n, NoResultsSkippingIteration)
    for p in Polys:
      Aio.print(p.toTigerStr())
  def listTigerPrimitives(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, MinimumDistance = 0, n = 0, NoResultsSkippingIteration = 0) -> list:
    Poly0 = Polynomial.createPolynomial(degree, coeffs_count, balancing, LayoutFriendly, MinimumDistance)
    if Poly0 is None:
      return []
    SerialChunkSize = 20
    if degree >= 512:
      SerialChunkSize = 1
    elif degree >= 256:
      SerialChunkSize = 5
    elif degree >= 128:
      SerialChunkSize = 10 
    aux = 100000 // degree
    if aux < 100:
      aux = 100
    ParallelChunk = aux * SerialChunkSize
    lfsrs = []
    Results = []
    SkippingCounter = NoResultsSkippingIteration
    for p in Poly0:
      lfsrs.append(Lfsr(p, TIGER_RING))
      Aux = []
      if len(lfsrs) >= ParallelChunk:
        Aux = Lfsr.checkMaximum(lfsrs, n-len(Results), SerialChunkSize)
        Results += Aux
        print(f'Found so far: {len(Results)}')
        lfsrs = []
        if len(Results) >= n > 0:
          break
        if NoResultsSkippingIteration > 0:
          if len(Aux) > 0:
            SkippingCounter = NoResultsSkippingIteration
          else:
            SkippingCounter -= 1
          if SkippingCounter <= 0:
            break
    if len(lfsrs) > 0 and (len(Results) < n or n <= 0):
      Results += Lfsr.checkMaximum(lfsrs, n-len(Results), SerialChunkSize)
    Polys = []
    for l in Results:
      Polys.append(Polynomial(l._my_poly.copy()))
    return Polys
  def printPrimitives(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, MinimumDistance = 0, n = 0, Silent = True, MaxSetSize=10000, ExcludeList = [], FilteringCallback = None, NoResultsSkippingIteration = 0) -> None:
    """Prints a list of primitive polynomials (over GF(2)).

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)
        MinimumDistance (int, optional): Minimum distance between consecutive coefficients. Default: 0 (no restriction)
        LayoutFriendly (bool, optional): like MinimumDistance=2. Defaults to False.
        n (int, optional): stop searching if n polynomials is found. Defaults to 0 (don't stop)
        Silent (bool, optional): if False (default) print to the sdtout every time a new prim poly is found
        ExcludeList (list, optional): list of polynomials excluded from checking
        FilteringCallback (procedure, optional): if specified, then will be used to filter acceptable polynomials (must return bool value: True means acceptable).
    """
    for p in Polynomial.listPrimitives(degree, coeffs_count, balancing, LayoutFriendly, MinimumDistance, n, Silent, MaxSetSize, ExcludeList, 0, FilteringCallback, NoResultsSkippingIteration):
      Aio.print(p.getCoefficients())
  def listPrimitives(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, MinimumDistance = 0, n = 0, Silent = True, MaxSetSize=10000, ExcludeList = [], ReturnAlsoAllCandidaes = False, FilteringCallback = None, NoResultsSkippingIteration = 0) -> list:
    """Returns a list of primitive polynomials (over GF(2)).

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)
        MinimumDistance (int, optional): Minimum distance between consecutive coefficients. Default: 0 (no restriction)
        LayoutFriendly (bool, optional): like MinimumDistance=2. Defaults to False.
        n (int, optional): stop searching if n polynomials is found. Defaults to 0 (don't stop)
        Silent (bool, optional): if False (default) print to the sdtout every time a new prim poly is found
        ExcludeList (list, optional): list of polynomials excluded from checking
        ReturnAlsoAllCandidaes (bool, optional): if true, then it returns list: [polynomials_found, all_tested_polynomials]
        FilteringCallback (procedure, optional): if specified, then will be used to filter acceptable polynomials (must return bool value: True means acceptable).

    Returns:
        list: list of polynomial objects
    """
    polys = Polynomial.createPolynomial(degree, coeffs_count, balancing, LayoutFriendly, MinimumDistance)
    if type(polys) == type(None):
      if ReturnAlsoAllCandidaes:
        return [[], []]
      return []
    result = []
    candidates = []
    AllCandidates = []
    cntr = 0
    Polynomial._ctemp = False
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
    Polynomial._ctemp = True
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
  def firstPrimitive(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, Silent=True) -> Polynomial:
    """Returns a first found primitive (over GF(2)) polynomial.

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)

    Returns:
        list: _description_
    """
    lp = Polynomial.listPrimitives(degree, coeffs_count, balancing, LayoutFriendly, 0, 1, Silent)
    if len(lp) > 0:
      return lp[0]
#    p = Polynomial.createPolynomial(degree, coeffs_count, balancing)
#    if p.isPrimitive():
#      return p
#    elif p.nextPrimitive(Silent):
#      return p
    return None
  def firstMostBalancedPrimitive(degree : int, coeffs_count : int, StartBalancing=1, EndBalancing=10, LayoutFriendly = False, Silent = True) -> Polynomial:
    bal = EndBalancing
    if bal > (degree-coeffs_count):
      bal = (degree-coeffs_count)
    for b in range(StartBalancing, bal):
      fp = Polynomial.firstPrimitive(degree, coeffs_count, b, LayoutFriendly, Silent)
      if type(fp) != type(None):
        return fp
    return None
  def firstEveryNTapsPrimitive(Degree : int, EveryN : int, Silent = True) -> Polynomial:
    result = Polynomial.listEveryNTapsPrimitives(Degree, EveryN, 1, Silent)
    if len(result) > 0:
      return result[0]
    return None
  def printEveryNTapsPrimitives(Degree : int, EveryN : int, n = 0, Silent = True) -> None:
    for p in Polynomial.listEveryNTapsPrimitives(Degree, EveryN, n, Silent):
      Aio.print(p.getCoefficients())
  def listEveryNTapsPrimitives(Degree : int, EveryN : int, n = 0, Silent = True) -> list:
    ccount = int(round(Degree / EveryN, 0)) | 1
    if ccount < 3: ccount = 3
    results = []
    exclude = []
    for b in range(1, EveryN):
      resultsAux = Polynomial.listPrimitives(Degree, ccount, b, True, 0, n, Silent, ExcludeList=exclude, ReturnAlsoAllCandidaes=True)
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
  def firstDensePrimitive(Degree : int, Silent = True) -> Polynomial:
    r = Polynomial.listDensePrimitives(Degree, 1, Silent)
    if len(r) > 0:
      return r[0]
    return None
  def printDensePrimitives(Degree, n=0, Silent = True) -> None:
    for p in Polynomial.listDensePrimitives(Degree, n, Silent):
      Aio.print(p.getCoefficients())
  def listDensePrimitives(Degree, n=0, Silent = True) -> list:
    Half = int(Degree / 2) | 1
    c = Half - 4
    result = []
    exclude = []
    if n < 0:
      n = 0
    n2 = n
    minc = Half * 0.7
    while (c >= 3) & (c >= minc):
      print (f'Found so far: {len(result)}. Looking for {c} coefficients')
      resultAux = Polynomial.listPrimitives(Degree, c, 2, True, 0, n2, Silent, ExcludeList=exclude, ReturnAlsoAllCandidaes=True)
      result += resultAux[0]
      exclude += resultAux[1]
      if n > 0:
        if len(result) >= n:
          break
        n2 = n - len(result)
      c -= 2
    if len(result) > n > 0:
      result = result[0:n-1]   
    print (f'Found: {len(result)}')   
    return result
  def printTapsFromTheLeftPrimitives(degree : int, coeffs_count : int, max_distance = 3, n=0, Silent = True) -> None:
    for p in Polynomial.listTapsFromTheLeftPrimitives(degree, coeffs_count, max_distance, n, Silent):
      Aio.print(p.getCoefficients())
  def listTapsFromTheLeftPrimitives(degree : int, coeffs_count : int, max_distance = 3, n=0, Silent = True) -> list:
    clist = [degree]
    davg = degree // coeffs_count
    distance = max_distance
    if davg < distance:
      distance = davg
    num = degree
    for _ in range(1, coeffs_count-1):
      num -= distance
      clist.append(num)
    clist.append(0)
    poly = Polynomial(clist)
    plist = [poly.copy()]
    while poly.makeNext():
      plist.append(poly.copy())
    return Polynomial.checkPrimitives(plist, n, Silent)
  def firstTapsFromTheLeftPrimitive(degree : int, coeffs_count : int, max_distance = 3, Silent = True) -> list:
    lst = Polynomial.listTapsFromTheLeftPrimitives(degree, coeffs_count, max_distance, Silent)
    if len(lst) > 0:
      return lst[0]
    return None
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
  
  Available types:
  .Galois
  .Fibonacci
  .RingGenerator
  """
  Galois = 1
  Fibonacci = 2
  RingGenerator = 3
  RingWithSpecifiedTaps = 4
  TigerRing = 5

# Constants
FIBONACCI = LfsrType.Fibonacci
GALOIS = LfsrType.Galois
RING_GENERATOR = LfsrType.RingGenerator
RING_WITH_SPECIFIED_TAPS = LfsrType.RingWithSpecifiedTaps
TIGER_RING = LfsrType.TigerRing

# LFSR BEGIN ======================
class Lfsr:
  """An LFSR object. Used for all 3 LFSR implementations, like 
  Galois, Fibonacci (default), RingGenerator.
  """
  _maxfound = 0
  _maxFoundN = 0
  _my_poly = []
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
        self._my_poly = copy.deepcopy(polynomial._my_poly)
        self._type = copy.deepcopy(polynomial._type)
        self._hval = copy.deepcopy(polynomial._hval)
        self._size = copy.deepcopy(polynomial._size)
        self._baValue = copy.deepcopy(polynomial._baValue)
        self._bamask = copy.deepcopy(polynomial._bamask)
        self._ba_fast_sim_array = copy.deepcopy(polynomial._ba_fast_sim_array)
        self._taps = copy.deepcopy(polynomial._taps)
        self._notes = copy.deepcopy(polynomial._notes)
        return
    if type(Polynomial([0])) != type(polynomial):
      if lfsr_type == LfsrType.RingWithSpecifiedTaps:
        poly = Polynomial([int(polynomial),0])
      else:
        poly = Polynomial(polynomial)
    self._ba_fast_sim_array = None
    self._my_poly = poly.getCoefficients()
    self._type = lfsr_type
    self._size = poly.getDegree()
    self._baValue = bitarray(self._size)
    if lfsr_type == LfsrType.RingWithSpecifiedTaps:
      self._taps = manual_taps
    elif lfsr_type == LfsrType.Galois:
      self._bamask = (poly.toBitarray() << 1)[:-1]
    elif lfsr_type == LfsrType.Fibonacci:
      self._bamask = poly.toBitarray()[:-1]
    elif lfsr_type == LfsrType.RingGenerator or lfsr_type == LfsrType.TigerRing:
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
    else:
      Aio.printError("Unrecognised lfsr type '" + str(lfsr_type) + "'")
    self.reset()
    self._hval = 1 << (poly.getDegree()-1)
  def getReciprocal(self):
    Aio.print("NOT FINISHED!!!!")
    if self._type == LfsrType.RingWithSpecifiedTaps:
      L = self.copy()
      
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
      return Result
  def getTaps(self):
    return self._taps
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
  def getValues(self, n = 0, step = 1, reset = True) -> list:
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
      val0 = self._baValue.copy()
      n = self.getPeriod()
      self._baValue = val0
    result = []
    for i in range(n):
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
  def simulateForDataString(self, Sequence, InjectionAtBit = 0, StartValue = None) -> int:
    if "list" in str(type(Sequence)):
      self._N = len(Sequence)
      self._IBit = InjectionAtBit
      self._Start = StartValue
      man = multiprocess.Manager()
      self._C = man.list()
      #results = pool.map(self._simplySim, Sequence)
      results = p_map(self._simplySim, Sequence)
      Aio.printTemp("                                    ")
      del self._C
      return results
    if not Aio.isType(StartValue, None):
      self._baValue = StartValue
    Index = InjectionAtBit
    for Bit in Sequence:
      self.next()
      if Bit:
        self._baValue[Index] ^= 1
    return self._baValue
  def toVerilog(self, ModuleName : str, SingleInjector = False, CorrectionInput = False) -> str:
    Module = \
f'''module {ModuleName} (
  input wire clk,
  input wire enable,
  input wire reset,
'''
    if CorrectionInput:
      Module += "  input wire correction_in,\n"
      Module += "  input wire correction_time,\n"
    if SingleInjector:
      Module += "  input wire injector,\n"
    Module += \
f'''  output reg [{self.getSize()-1}:0] O
);

'''
    if self._type == LfsrType.Fibonacci:
      Module += "wire xor_gate;\n\n"
    if CorrectionInput:
      if self._type == LfsrType.Galois or self._type == LfsrType.RingGenerator or self._type == LfsrType.RingWithSpecifiedTaps:
        if SingleInjector:
          Module += "wire corrector_mux = correction_time ? correction_in : O[0] ^ injector;\n\n"
        else:
          Module += "wire corrector_mux = correction_time ? correction_in : O[0];\n\n"
    Module += \
f'''always @ (posedge clk or posedge reset) begin
  if (reset) begin
    O <= {self.getSize()}'d0;
  end else begin
    if (enable) begin
'''
    if self._type == LfsrType.Fibonacci:
      for i in range(0, self.getSize()-1):
        Module += f'      O[{i}] <= O[{i+1}];\n'
      Module += f'      O[{self.getSize()-1}] <= xor_gate;'
    elif self._type == LfsrType.Galois:
      for i in range(0, self.getSize()-1):
        if (i+1) in self._my_poly:
          Module += f'      O[{i}] <= O[{i+1}] ^ O[0];\n'
        else:
          Module += f'      O[{i}] <= O[{i+1}];\n'
      Module += f'      O[{self.getSize()-1}] <= O[0]'
      if SingleInjector and not CorrectionInput:
        Module += f' ^ injector;\n'
      else:
        Module += f';\n'
    elif self._type == LfsrType.RingGenerator or self._type == LfsrType.RingWithSpecifiedTaps:
      f = []
      t = []
      for tap in self._taps:
        f.append(tap[0])
        t.append(tap[1])
      for i in range(0, self.getSize()-1):
        if i in t:
          Module += f'      O[{i}] <= O[{i+1}] ^ O[{f[t.index(i)]}];\n'
        else:
          Module += f'      O[{i}] <= O[{i+1}];\n'
      if CorrectionInput:
        Module += f'      O[{self.getSize()-1}] <= corrector_mux;\n'
      else:      
        if SingleInjector:
          Module += f'      O[{self.getSize()-1}] <= O[0] ^ injector;\n'
        else:
          Module += f'      O[{self.getSize()-1}] <= O[0];\n'
    Module += "    end\n"
    if self._type == LfsrType.Fibonacci:
      Module += f'\nassign xor_gate = '
      for i in range(1, len(self._my_poly)):
        Module += f'O[{self._my_poly[i]}] ^ '
      if SingleInjector:
        Module += f'injector;\n'
      else:
        Module += f'1\'b0;\n'
    Module += \
f'''  end
end
    
endmodule'''
    return Module
  def draw(self, JT = False, Shorten = True, Crop = True):
    if self._type == LfsrType.RingGenerator:
      FFs = []
      InputNodes = []
      OutputNodes = []
      OutputNodesPrim = []
      OutputNodesPrim2 = []
      InputNodesPrim = []
      XorUsage = []
      HorizontalWires = []
      FFSize = 3
      if self._size > 9:
        FFSize = 4
      if self._size > 99:
        FFSize = 5
      UpperSize = self._size // 2
      LowerSize = self._size - UpperSize
      WireTxt = " " * (FFSize + 1)
      for i in range(self._size):
        if JT:
          FFs.append(AsciiDrawing_HorizontalFF(self.getJTIndex(i), FFSize))
        else:
          FFs.append(AsciiDrawing_HorizontalFF(i, FFSize))
        InputNodes.append(AsciiDrawing_WiringNode(AD_DIRECTION_LEFT + AD_DIRECTION_RIGHT))
        OutputNodes.append(AsciiDrawing_WiringNode(AD_DIRECTION_LEFT + AD_DIRECTION_RIGHT))
        OutputNodesPrim.append(AsciiDrawing_WiringNode())
        OutputNodesPrim2.append(AsciiDrawing_WiringNode())
        InputNodesPrim.append(AsciiDrawing_WiringNode())
        HorizontalWires.append(WireTxt)
        XorUsage.append(0)
      Lines = ["" for _ in range(9)]
      # taps
      empties = []
      lastIndex = self._size-1
      for tap in self._taps:
        if tap[0] < lastIndex:
          empties += [i  for i in range(tap[0]+2, lastIndex)]
          lastIndex = tap[0]-1
        OutputNodes[tap[0]].addDirection(AD_DIRECTION_DOWN)
        OutputNodesPrim[tap[0]].addDirection(AD_DIRECTION_UP+AD_DIRECTION_DOWN)
        OutputNodesPrim2[tap[0]].addDirection(AD_DIRECTION_UP)
        ForLeftTesting = (self._size - tap[0])
        ForRightTesting = ((self._size-2 - tap[0])) % self._size
        if tap[0] == tap[1]:
          XorUsage[tap[0]] += 1  
        if (self._size-1 - tap[0]) == tap[1]:
          OutputNodesPrim2[tap[0]].addDirection(AD_DIRECTION_DOWN)
          InputNodes[tap[1]].addDirection(AD_DIRECTION_SPECIAL_XOR)
          InputNodesPrim[tap[1]].addDirection(AD_DIRECTION_UP+AD_DIRECTION_DOWN)
          XorUsage[tap[1]] += 1
        elif ForLeftTesting == tap[1]:
          ### Not yet supported!
          OutputNodesPrim2[tap[0]].addDirection(AD_DIRECTION_LEFT)
        elif ForRightTesting == tap[1]:
          OutputNodesPrim2[tap[0]].addDirection(AD_DIRECTION_RIGHT)
          if XorUsage[tap[1]] == 0:
            OutputNodesPrim2[(tap[0]+1) % self._size].addDirection(AD_DIRECTION_LEFT+AD_DIRECTION_DOWN)
            HorizontalWires[tap[0]] = AsciiDrawing_Characters.HORIZONTAL * (FFSize+1)
            InputNodes[tap[1]].addDirection(AD_DIRECTION_SPECIAL_XOR)
            InputNodesPrim[tap[1]].addDirection(AD_DIRECTION_UP+AD_DIRECTION_DOWN)
          else:
            HorizontalWires[tap[0]] = AsciiDrawing_Characters.HORIZONTAL * (FFSize) + AsciiDrawing_Characters.UPPER_RIGHT    
          XorUsage[(tap[1] + 1) % self._size] += 1
          if XorUsage[tap[1]] > 0:        
            OutputNodes[(tap[1]+1) % self._size].addDirection(AD_DIRECTION_SPECIAL_XOR)
            OutputNodesPrim[(tap[1]+1) % self._size].addDirection(AD_DIRECTION_UP+AD_DIRECTION_DOWN)           
      if not Shorten:
        empties = []
      if LowerSize < lastIndex:
        empties += [i  for i in range(LowerSize+1, lastIndex)]
      el = []
      for e in empties:
        el.append(self._size-1 - e)
      empties += el
      # upper
      Lines[0] += "  "
      Lines[1] += AsciiDrawing_Characters.UPPER_LEFT + AsciiDrawing_Characters.LEFT_ARROW
      Lines[2] += AsciiDrawing_Characters.VERTICAL + " "
      if UpperSize < LowerSize:
        Lines[0] += " " * (FFSize + 2)
        Lines[1] += AsciiDrawing_Characters.HORIZONTAL * (FFSize + 2)
        Lines[2] += " " * (FFSize + 2)
      DashesAdded = False
      for i in range(UpperSize):
        index = LowerSize + i
        if index in empties:       
          if not DashesAdded:
            Lines[0] += "  "
            Lines[1] += "\U0000254C\U0000254C"
            Lines[2] += "  "
            DashesAdded = True
          continue
        DashesAdded = False
        Lines[0] += " "
        Lines[1] += str(OutputNodes[index])
        Lines[2] += str(OutputNodesPrim[index])
        Lines[0] += FFs[index].toString(0)
        Lines[1] += FFs[index].toString(1)
        Lines[2] += FFs[index].toString(2)
        Lines[0] += " "
        Lines[1] += str(InputNodes[index])
        Lines[2] += " "
      Lines[0] += "  "
      Lines[1] += AsciiDrawing_Characters.LEFT_ARROW + AsciiDrawing_Characters.UPPER_RIGHT
      Lines[2] += " " + AsciiDrawing_Characters.VERTICAL
      # wires
      Lines[3] += AsciiDrawing_Characters.VERTICAL + " "
      if UpperSize < LowerSize:
        Lines[3] += " " * (FFSize + 2)
      DashesAdded = False
      for i in range(UpperSize):
        index = LowerSize + i
        if index in empties:       
          if not DashesAdded:
            Lines[3] += "  "
            DashesAdded = True
          continue
        DashesAdded = False
        Lines[3] += str(OutputNodesPrim2[index]) + HorizontalWires[index]
      Lines[3] += " " + AsciiDrawing_Characters.VERTICAL
      # lower
      Lines[6] += AsciiDrawing_Characters.VERTICAL + " "
      Lines[7] += AsciiDrawing_Characters.LOWER_LEFT + AsciiDrawing_Characters.RIGHT_ARROW
      Lines[8] += "  "
      DashesAdded = False
      for i in range(LowerSize):
        index = LowerSize-1 - i
        if index in empties:       
          if not DashesAdded:
            Lines[6] += "  "
            Lines[7] += "\U0000254C\U0000254C"
            Lines[8] += "  "
            DashesAdded = True
          continue
        DashesAdded = False
        Lines[6] += str(InputNodesPrim[index])
        Lines[7] += str(InputNodes[index])
        Lines[8] += " "
        Lines[6] += FFs[index].toString(0)
        Lines[7] += FFs[index].toString(1)
        Lines[8] += FFs[index].toString(2)
        Lines[6] += str(OutputNodesPrim[index])
        Lines[7] += str(OutputNodes[index])
        Lines[8] += " "
      Lines[6] += " " + AsciiDrawing_Characters.VERTICAL
      Lines[7] += AsciiDrawing_Characters.RIGHT_ARROW + AsciiDrawing_Characters.LOWER_RIGHT
      Lines[8] += "  "
      # print
      Result = ""
      Cols = Aio.getTerminalColumns()-1
      for i in range(9):
        if 4 <= i <= 5:
          continue
        if Crop:
          Result += (Lines[i][0:Cols] + '\n')
        else:
          Result += (Lines[i] + '\n')
    else:
      Result = Aio.print("<This type of LFSR is not yet supported.>")
    return Result
  def print(self, JT = False, Shorten = True, Crop = True):
    Aio.print(self.draw(JT, Shorten, Crop))
  def getJTIndex(self, index):
    if self._type == LfsrType.RingGenerator:
      UpperSize = self._size // 2
      LowerSize = self._size - UpperSize
      if index >= LowerSize:
        return index - LowerSize
      return index + LowerSize
    return index
  def analyseSequencesBatch(ListOfObjects) -> list:
    #return process_map(_analyseSequences_helper, ListOfObjects, chunkside=2, desc="Sequences analysis")
    R = p_map(_analyseSequences_helper, ListOfObjects)
    return R
  def analyseSequences(self, Reset = True, WithXor2 = True, WithXor3 = True) -> MSequencesReport:
    Values = self.getValues(reset=Reset)
    Sequences = [bitarray() for i in range(self._size)]
    for word_index in range(len(Values)):
      Word = Values[word_index]
      for flop_index in range(self._size):
        Sequences[flop_index].append(Word[flop_index])
    Results = {}
    BaseDict = {}
    BaseUniques = {}
    FlopIndex = 0
    for Sequence in Sequences:
      Found = 0
      for key in BaseUniques.keys():
        Shift = Bitarray.getShiftBetweenSequences(BaseUniques[key], Sequence)
        if Shift is not None:
          BaseDict[f'Q{FlopIndex}'] = f'{key}{" " * (18-len(key))}delayed by {Shift}'
          Found = 1
        else:
          NotShift = Bitarray.getShiftBetweenSequences(~BaseUniques[key], Sequence)
          if NotShift is not None:
            BaseDict[f'Q{FlopIndex}'] = f'~{key}{" " * (17-len(key))}delayed by {NotShift}'
            Found = 1
      if not Found:        
        BaseDict[f'Q{FlopIndex}'] = "Unique"
        BaseUniques[f'Q{FlopIndex}'] = Sequence
      FlopIndex += 1      
    BaseDict["unique_count"] = len(BaseUniques)
    Results[1] = BaseDict.copy()
    Xor2Sequences = {}
    Xor3Sequences = {}
    if WithXor2 or WithXor3:
      for q1 in range(self._size-1):
        for q2 in range(1, self._size):
          if q1 < q2:
            q1r = self._size - q1 - 1
            q2r = self._size - q2 - 1
            Name2 = f'Q{q1}+Q{q2}'
            Sequence2 = Sequences[q1r] ^ Sequences[q2r]
            Xor2Sequences[Name2] = Sequence2
            if WithXor3:
              for q3 in range(2, self._size):
                if q2 < q3:
                  q3r = self._size - q3 - 1
                  Name3 = f'Q{q1}+Q{q2}+Q{q3}'
                  Sequence3 = Sequence2 ^ Sequences[q3r]
                  Xor3Sequences[Name3] = Sequence3
    if WithXor2:
      for SequenceName in Xor2Sequences.keys():
        Sequence = Xor2Sequences[SequenceName]
        Found = 0
        for key in BaseUniques.keys():
          Shift = Bitarray.getShiftBetweenSequences(BaseUniques[key], Sequence)
          if Shift is not None:
            BaseDict[SequenceName] = f'{key}{" " * (18-len(key))}delayed by {Shift}'
            Found = 1
          else:
            NotShift = Bitarray.getShiftBetweenSequences(~BaseUniques[key], Sequence)
            if NotShift is not None:
              BaseDict[SequenceName] = f'~({key}){" " * (15-len(key))}delayed by {NotShift}'
              Found = 1
        if not Found:        
          BaseDict[SequenceName] = "Unique"
          BaseUniques[SequenceName] = Sequence
      BaseDict["unique_count"] = len(BaseUniques)
      Results[2] = BaseDict.copy()
    if WithXor3:
      for SequenceName in Xor3Sequences.keys():
        Sequence = Xor3Sequences[SequenceName]
        Found = 0
        for key in BaseUniques.keys():
          Shift = Bitarray.getShiftBetweenSequences(BaseUniques[key], Sequence)
          if Shift is not None:
            BaseDict[SequenceName] = f'{key}{" " * (18-len(key))}delayed by {Shift}'
            Found = 1
          else:
            NotShift = Bitarray.getShiftBetweenSequences(~BaseUniques[key], Sequence)
            if NotShift is not None:
              BaseDict[SequenceName] = f'~({key}{" " * (15-len(key))}) delayed by {NotShift}'
              Found = 1
        if not Found:        
          BaseDict[SequenceName] = "Unique"
          BaseUniques[SequenceName] = Sequence
      BaseDict["unique_count"] = len(BaseUniques)
      Results[3] = BaseDict.copy()
    Report = MSequencesReport()
    Report._xor2 = WithXor2
    Report._xor3 = WithXor3
    Report._dict = Results
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
      
  def _checkMaximumSerial(LfsrsList : list) -> list:
    if Lfsr._maxfound >= Lfsr._maxFoundN > 0:
      return []
    Results = []
    for lfsr in LfsrsList:
      if lfsr._isMaximumAndClean():
        Results.append(lfsr)
        if Lfsr._maxfound+len(Results) >= Lfsr._maxFoundN > 0:
          break
    Lfsr._maxfound += len(Results)
    return Results
  def checkMaximum(LfsrsList : list, n = 0, SerialChunkSize = 20) -> list:
    Lfsr._maxfound = 0
    Lfsr._maxFoundN = n
    Candidates = List.splitIntoSublists(LfsrsList, SerialChunkSize)
    Results = []
    Generator = Generators()
    Iter = p_uimap(Lfsr._checkMaximumSerial, Generator.wrapper(Candidates), total=len(Candidates), desc = f'x{SerialChunkSize}')
    for RL in Iter:
      Results += RL
      if len(Results) >= n > 0:
        Generator.disable()
    del Generator
    if len(Results) > n > 0:
      Results = Results[:n]
    return Results
    
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
  


  
