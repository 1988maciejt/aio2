from numpy import polysub
from sympy import Poly
from libs.binstr import *
from libs.logic import Logic
from libs.aio import *
from libs.database import *
from libs.utils_array import *
from libs.utils_int import *
from libs.cache import *
from libs.asci_drawing import *
import math
from tqdm import *
import multiprocessing
import time
import copy
import gc
import zlib


# POLYNOMIAL CLASS ================

class Polynomial:
  pass
class Polynomial:
  _coefficients_list = []
  _balancing = 0    
  _result = None
  _n = 0
  _bmin = 1
  _positions = False
  _ctemp = True
  _lf = False
  def _check(p):
    if (Polynomial._n > 0) and  (len(Polynomial._result) >= Polynomial._n):
      return
    Aio.printTemp("Checking " + str(p))
    if p.isPrimitive():
      Polynomial._result.append(p)
      if not Polynomial._quiet:
        print("Found " + str(p) + " " * 30)
  def __del__(self):
    if self._positions != False:
      self._positions.clear()
    self._coefficients_list.clear()
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
      self._positions = coefficients_list._positions
      self._lf = coefficients_list._lf
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
      self._coefficients_list = coefficients_list
      self._coefficients_list.sort(reverse=True)
      self._balancing = balancing
      self._bmax = self._coefficients_list[0]
  def __iter__(self):
    self = Polynomial.createPolynomial(self.getDegree(), self.getCoefficientsCount(), self._balancing, self._lf)
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
        return self
      else:
        self._mnext = self.makeNext()
        if self._mnext:
          return self
    raise StopIteration  
  def __str__(self) -> str:
    return str(self._coefficients_list)
  def toKassabStr(self) -> str:
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
  def toHexString(self, IncludeDegree=True, shorten=True):
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
  def getReversed(self) -> Polynomial:
    """Gets 'reversed' version of polynomial.
    
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
      if self._lf:
        if not self.isLayoutFriendly():
          s = False
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
  def getTaps(self) -> int:
    """Returns LFSR taps count in case of a LFSR created basing on this polynomial 
    """
    return len(self._coefficients_list)-2
  def getPolynomialsCount(self) -> int:
    """Returns a count of polynomials having the same parameters (obtained using .makeNext())  
    """
    return math.comb(self.getDegree()-1, self.getTaps())
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
    degree = int(clist[0])
    result = int(0)
    for i in range(len(clist)):
      coeff = clist[i]
      result += (1 << coeff)
    return result
  def isPrimitive(self) -> bool:
    """Check if the polynomial is primitive over GF(2).
    
    That's considered by simulating an LFSR based on the polynomial.

    Returns:
        bool: True if is the poly is primitive, otherwise False
    """
    if len(self._coefficients_list) % 2 == 0: 
      return False
#    cached = PersistentCache.recall(self)
    cached = Cache.recall(self.toInt())
    if cached != None:
      return cached
#    cached = PersistentCache.recall(self.getReversed())
    cached = Cache.recall(self.getReversed().toInt())
    if cached != None:
      return cached
    l = Lfsr(self.copy(), LfsrType.Galois)
    result = l.isMaximum()
    del l
#    PersistentCache.store(self, result)
    Cache.store(self.toInt(), result)
    return result
  def nextPrimitive(self, quiet=False) -> bool:
    """Looks for the next primitive polynomial.

    Returns:
        bool: True if primitive found, otherwise False.
    """
    while True:
      if not self.makeNext():
        return False
      if not quiet:
        Aio.printTemp("Testing",self)
      if self.isPrimitive():
        if not quiet:
          Aio.printTemp(str(" ")*100)
        return True
  def copy(self):
    return Polynomial(self)
  def isLayoutFriendly(self) -> bool:
    for i in range(len(self._coefficients_list)-1):
      this = self._coefficients_list[i]
      right = self._coefficients_list[i+1]
      if (this-right) <= 1:
        return False
    return True
  def createPolynomial(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False) -> Polynomial:
    """Returns a polynomial, usefull for LFSRs.

    Args:
        degree (int): polynomial degree (i.e. size of LFSR)
        coeffs_count (int): coefficients count (i.e. LFSRs taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking).
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
      bmin = avg - halfbal
      bmax = avg + halfbal
      result.insert(0,0);
      if bmin < 1.0:
        bmin = 1.0
        bmax = float(balancing + 1)
      if bmin < 2 and LayoutFriendly:
        bmin = 2
      result = [0]
      rest = degree-1
      actual = bmin
      restcoeffs = coeffs_count-2
      diff = round(bmin,0)
      for i in range(2, coeffs_count):
        coeff = int(round(actual, 0))
        result.append(coeff)
        rest -= diff
        restcoeffs -= 1
        actual += diff
        if diff < bmax:
          try:
            if rest / restcoeffs >= bmax:
              diff = bmax
          except:
            pass
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
    p._bmin = int(round(bmin,0))
    p._bmax = int(round(bmax,0))
    p._lf = LayoutFriendly
#    print(Aio.format(pos))
    if p._balancing > 0:
      if p.getBalancing() > p._balancing:
        return None
    if p._lf:
      while not p.isLayoutFriendly():
        if not p.makeNext():
          return None
    return p
  def checkPrimitives(Candidates : list, n = 0, quiet = False) -> list:
    """Returns a list of primitive polynomials (over GF(2)) found on a given list.

    Args:
        PList (list): list of candidate polynomials 
        m (int, optional): stop checking if n polynomials is found. Defaults to 0 (don't stop)
        quiet (bool, optional): if False (default) print to the sdtout every time a new prim poly is found

    Returns:
        list: list of polynomial objects
    """    
    if len(Candidates) < 1:
      return []
    PList = []
    for p in Candidates:
      PList.append(Polynomial(p))
#    print("CHECK_PRIMITIVES:")
#    print(Aio.format(PList))
    manager = multiprocessing.Manager()
    Polynomial._result = manager.list()
    Polynomial._n = n
    Polynomial._quiet = quiet
    pool = multiprocessing.Pool()   
    pool.map_async(Polynomial._check, PList)
    pool.close()
    pool.join()
    r = list(Polynomial._result)
    if n > 0 and len(r) > n:
      r = r[0:n]
    Aio.printTemp(" " * (Aio.getTerminalColumns()-1))
    return r
  def listPrimitives(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, n = 0, quiet = False, MaxSetSize=1024, ExcludeList = [], ReturnAlsoAllCandidaes = False) -> list:
    """Returns a list of primitive polynomials (over GF(2)).

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)
        n (int, optional): stop searching if n polynomials is found. Defaults to 0 (don't stop)
        quiet (bool, optional): if False (default) print to the sdtout every time a new prim poly is found
        ExcludeList (list, optional): list of polynomials excluded from checking
        ReturnAlsoAllCandidaes (bool, optional): if true, then it returns list: [polynomials_found, all_tested_polynomials]

    Returns:
        list: list of polynomial objects
    """
    polys = Polynomial.createPolynomial(degree, coeffs_count, balancing, LayoutFriendly)
    if type(polys) == type(None):
      if ReturnAlsoAllCandidaes:
        return [[], []]
      return []
    result = []
    candidates = []
    AllCandidates = []
    cntr = 0
    Polynomial._ctemp = False
    for p in polys:
      if p in ExcludeList:
        continue
      candidates.append(p.copy())
      if ReturnAlsoAllCandidaes:
        AllCandidates.append(p.copy())
      cntr += 1
      if (cntr >= MaxSetSize):
        result += Polynomial.checkPrimitives(candidates, n, quiet)
        candidates.clear()
        cntr = 0
        if len(result) >= n > 0:
          break    
    if (cntr > 0):
      result += Polynomial.checkPrimitives(candidates, n, quiet)
      candidates.clear()
    Polynomial._ctemp = True
    if cntr != 0:
        result += Polynomial.checkPrimitives(candidates, n, quiet)
        candidates.clear()      
    if n > 0 and len(result) > n:
      result = result[0:n]
    Aio.printTemp()
    gc.collect()
    if ReturnAlsoAllCandidaes:
      return [result, AllCandidates]
    return result
  def firstPrimitive(degree : int, coeffs_count : int, balancing = 0, LayoutFriendly = False, quiet=True) -> Polynomial:
    """Returns a first found primitive (over GF(2)) polynomial.

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)

    Returns:
        list: _description_
    """
    lp = Polynomial.listPrimitives(degree, coeffs_count, balancing, LayoutFriendly, 1, quiet)
    if len(lp) > 0:
      return lp[0]
#    p = Polynomial.createPolynomial(degree, coeffs_count, balancing)
#    if p.isPrimitive():
#      return p
#    elif p.nextPrimitive(quiet):
#      return p
    return None
  def firstMostBalancedPrimitive(degree : int, coeffs_count : int, StartBalancing=1, EndBalancing=10, LayoutFriendly = False, quiet = True) -> Polynomial:
    bal = EndBalancing
    if bal > (degree-coeffs_count):
      bal = (degree-coeffs_count)
    for b in range(StartBalancing, bal):
      fp = Polynomial.firstPrimitive(degree, coeffs_count, b, LayoutFriendly, quiet)
      if type(fp) != type(None):
        return fp
    return None
  def firstEveryNTaps(Degree : int, EveryN : int, quiet = True) -> Polynomial:
    result = Polynomial.listEveryNTaps(Degree, EveryN, 1, quiet)
    if len(result) > 0:
      return result[0]
    return None
  def listEveryNTaps(Degree : int, EveryN : int, n = 0, quiet = False) -> list:
    ccount = int(round(Degree / EveryN, 0)) | 1
    if ccount < 3: ccount = 3
    results = []
    exclude = []
    for b in range(1, EveryN):
      resultsAux = Polynomial.listPrimitives(Degree, ccount, b, True, n, quiet, ExcludeList=exclude, ReturnAlsoAllCandidaes=True)
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
  def firstDense(Degree : int, quiet = True) -> Polynomial:
    r = Polynomial.listDense(Degree, 1, quiet)
    if len(r) > 0:
      return r[0]
    return None
  def listDense(Degree, n=0, quiet = False) -> list:
    Half = int(Degree / 2) | 1
    c = Half
    result = []
    exclude = []
    n2 = n
    Cont = True
    minc = Half * 0.8
    while (c >= 3) & Cont & (c >= minc):
      resultAux = Polynomial.listPrimitives(Degree, c, 1, False, n2, quiet, ExcludeList=exclude, ReturnAlsoAllCandidaes=True)
      result += resultAux[0]
      exclude += resultAux[1]
      if n > 0:
        n2 -= len(result)
        if n2 <= 0:
          break
      else:
        if len(result) > 0:
          Cont = False
      c -= 2
    if len(result) == 0:
      c = Half-2
      Cont = True
      while (c >= 3) & Cont & (c >= minc):
        resultAux = Polynomial.listPrimitives(Degree, c, 2, True, n2, quiet, ExcludeList=exclude, ReturnAlsoAllCandidaes=True)
        result += resultAux[0]
        exclude += resultAux[1]
        if n > 0:
          n2 -= len(result)
          if n2 <= 0:
            break
        else:
          if len(result) > 0:
            Cont = False
        c -= 2
    if len(result) == 0:
      c = Half-4
      Cont = True
      while (c >= 3) & Cont & (c >= minc):
        resultAux = Polynomial.listPrimitives(Degree, c, 3, True, n2, quiet, ExcludeList=exclude, ReturnAlsoAllCandidaes=True)
        result += resultAux[0]
        exclude += resultAux[1]
        if n > 0:
          n2 -= len(result)
          if n2 <= 0:
            break
        else:
          if len(result) > 0:
            Cont = False
        c -= 2
    if len(result) > n > 0:
      return result[0:n-1]      
    return result
  def listTapsFromTheLeft(degree : int, coeffs_count : int, max_distance = 3, n=0, quiet = False) -> list:
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
    return Polynomial.checkPrimitives(plist, n, quiet)
  def firstTapsFromTheLeft(degree : int, coeffs_count : int, max_distance = 3, quiet = False) -> list:
    lst = Polynomial.listTapsFromTheLeft(degree, coeffs_count, max_distance, quiet)
    if len(lst) > 0:
      return lst[0]
    return None
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

# Constants
FIBONACCI = LfsrType.Fibonacci
GALOIS = LfsrType.Galois
RING_GENERATOR = LfsrType.RingGenerator
RING_WITH_SPECIFIED_TAPS = LfsrType.RingWithSpecifiedTaps

# LFSR BEGIN ======================
class Lfsr:
  """An LFSR object. Used for all 3 LFSR implementations, like 
  Galois, Fibonacci (default), RingGenerator.
  """
  _my_poly = []
  _mask = 0
  Value = 0
  _type = LfsrType.Galois
  _hval = 0
  _size = 0
  _fast_sim_array = False
  _taps = []
  def __del__(self):
    self.clear()
    self._taps.clear()
    self._my_poly.clear()    
  def clear(self):
    """Clears the fast-simulation array
    """
    #self._fast_sim_array.clear()
    if self._fast_sim_array != False:
      self._fast_sim_array.clear()
      del self._fast_sim_array
      self._fast_sim_array = False
  def __iter__(self):
    self.Value = 1
    self._next_iteration = False
    return self
  def __next__(self):
    val = self.getValue()
    self.next()
    if self._next_iteration:    
      if val == 1:
        raise StopIteration
    else:
      self._next_iteration = True
    return val
  def __init__(self, polynomial, lfsr_type = LfsrType.Fibonacci, manual_taps = []):
    poly = polynomial
    if "Lfsr" in str(type(polynomial)):
        self._my_poly = copy.deepcopy(polynomial._my_poly)
        self._mask = copy.deepcopy(polynomial._mask)
        self.Value = copy.deepcopy(polynomial.Value)
        self._type = copy.deepcopy(polynomial._type)
        self._hval = copy.deepcopy(polynomial._hval)
        self._size = copy.deepcopy(polynomial._size)
        self._fast_sim_array = copy.deepcopy(polynomial._fast_sim_array)
        self._taps = copy.deepcopy(polynomial._taps)
        return
    if type(Polynomial([0])) != type(polynomial):
      if lfsr_type == LfsrType.RingWithSpecifiedTaps:
        poly = Polynomial([int(polynomial),0])
      else:
        poly = Polynomial(polynomial)
    self._my_poly = poly.getCoefficients()
    self._type = lfsr_type
    self._size = poly.getDegree()
    if lfsr_type == LfsrType.RingWithSpecifiedTaps:
      self._taps = manual_taps
    elif lfsr_type == LfsrType.Galois:
      self._mask = poly.toInt() >> 1
    elif lfsr_type == LfsrType.Fibonacci:
      self._mask = poly.toInt()
    elif lfsr_type == LfsrType.RingGenerator:
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
    else:
      Aio.printError("Unrecognised lfsr type '" + str(lfsr_type) + "'")
    self.Value = 1
    self._hval = 1 << (poly.getDegree()-1)
  def toBinString(self):
    return BinString(self._size, self.Value)
  def __str__(self) -> str:
    return str(self.toBinString())
  def __repr__(self) -> str:
    result = "Lfsr(" + str(self._my_poly) + ", "
    if self._type == LfsrType.Galois:
      result += "Galois"
    if self._type == LfsrType.Fibonacci:
      result += "Fibonacci" 
    if self._type == LfsrType.RingGenerator:
      result += "RingGenerator" 
    if self._type == LfsrType.RingWithSpecifiedTaps:
      result += "RingWithSpecifiedTaps" 
    result += ")"
    return result
  def _buildFastSimArray(self):
    oldVal = self.Value
    size = self._size
    self._fast_sim_array = create2DArray(size, size)
    value0 = 1
    for i in range(size):
      self.Value = value0
      self._fast_sim_array[0][i] = self.next()
      value0 <<= 1
    for r in range(1,size):
      for c in range(size):
        result = 0
        PrevValue = self._fast_sim_array[r-1][c]
        for b in range(size):
          if PrevValue & 1 == 1:
            result ^= self._fast_sim_array[r-1][b]
          PrevValue >>= 1
        self._fast_sim_array[r][c] = result
    self.Value = oldVal
  def getValue(self) -> int:
    """Returns current value of the LFSR
    """
    return self.Value
  def getSize(self) -> int:
    """Returns size of the LFSR
    """
    return (self._size)
  def next(self, steps=1) -> int:
    """Performs a shift of the LFSR. If more than 1 step is specified, 
    the fast-simulation method is used.

    Args:
        steps (int, optional): How many steps to simulate. Defaults to 1.

    Returns:
        int: new LFSR value
    """
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return 0
    if steps == 0:
      return self.Value
    if steps == 1:
      if self._type == LfsrType.Fibonacci:
        hbit = Int.parityOf(self._mask & self.Value)
        self.Value >>= 1
        if hbit == 1:
          self.Value |= self._hval
        return self.Value
      elif self._type == LfsrType.Galois:
        lbit = self.Value & 0x1
        self.Value >>= 1
        if lbit == 1:
          self.Value ^= self._mask
        return self.Value
      elif self._type == LfsrType.RingGenerator or self._type == LfsrType.RingWithSpecifiedTaps:
        Value2 = Int.rotateRight(self.Value, self._size, 1)
        for tap in self._taps:
          From = tap[0]
          To = tap[1]
          frombit = Int.getBit(self.Value, From)
          Value2 ^= (frombit << To)
        self.Value = Value2
        return self.Value
      return 0
    else:
      if self._fast_sim_array == False:
        self._buildFastSimArray()
      size = self._size
      RowIndex = 0
      #steps = copy.deepcopy(steps)
      while steps > 0: 
        value0 = self.Value
        if steps & 1 == 1:
          result = 0
          for b in range(size):
            if value0 & 1 == 1:
              result ^= self._fast_sim_array[RowIndex][b]
            value0 >>= 1
          self.Value = result
        steps >>= 1
        RowIndex += 1
      return self.Value    
  def getPeriod(self) -> int:
    """Simulates the LFSR to obtain its period (count of states in trajectory).

    Returns:
        int: result. If the result is == (1<<size) it means a subtrajectory was reached
              and it cannot determine the period.
    """
    MaxResult = Int.mersenne(self._size) + 1
    self.Value = 1
    value0 = self.Value
    result = 1
    valuex = self.next()
    while valuex != value0 and result <= MaxResult:
      valuex = self.next()  
      result += 1
    return result
  def isMaximum(self) -> bool:
    """Uses the fast-simulation method to determine if the LFSR's trajectory
    includes all possible (but 0) states. 

    Returns:
        bool: True if is maximum, otherwise False.
    """
    index = self._size
    self.Value = 1
    if self.next(Int.mersenne(index)) != 1:
      return False
    lst = DB.getPrimitiveTestingCyclesList(index)
    for num in lst:
      self.Value = 1
      if self.next(num) == 1:
        return False
    return True
  def reset(self, NewValue = 1) -> int:
    """Resets the LFSR value 

    Args:
        NewValue (int, optional): new value. Defaults to 1.

    Returns:
        int: The new value
    """
    self.Value = NewValue
    return NewValue
  def getValues(self, n = 0, step = 1, reset = True) -> list:
    """Returns a list containing consecutive values of the LFSR.

    Args:
        n (int, optional): How many steps to simulate for. If M= 0 then maximum period is obtained. Defaults to 0.
        step (int, optional): steps (clock pulses) per iteration. Defaults to 1.
        reset (bool, optional): If True, then the LFSR is resetted to the 0x1 value before simulation. Defaults to True.

    Returns:
        list of integers.
    """
    if n <= 0:
      n = self.getPeriod()
    if reset:
      self.reset()
    result = []
    for i in range(n):
      result.append(self.Value)
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
      n = self.getPeriod()
    if reset:
      self.reset()
    for i in range(n):
      Aio.print(self.toBinString())
      self.next(step)
  def getMSequence(self, bitIndex = 0, reset = True) -> str:
    """Returns a string containing the M-Sequence of the LFSR.

    Args:
        bitIndex (int, optional): At this bit the sequence is observed. Defaults to 0.
        reset (bool, optional): If True, then the LFSR is resetted to the 0x1 value before simulation. Defaults to True.

    Returns:
        str: M-Sequence
    """
    result = ""
    if reset:
      self.reset()
    n = self.getPeriod()
    for i in range(n):
      result += str(Int.getBit(self.Value, bitIndex))
      self.next()
    return result
  def printFastSimArray(self):
    """Prints the fast-simulation array.
    """
    if self._fast_sim_array == False:
      self._buildFastSimArray()
    for r in self._fast_sim_array:
      line = ""
      for c in r:
        line += str(bin(c)) + "\t"
      Aio.print(line)
  def _simplySim(self, sequence : BinString):
    rm = Lfsr(self)
    res = rm.simulateForDataString(sequence, self._IBit, self._Start)
    self._C.append(0)
    cnt = len(self._C)
    if cnt % 100 == 0:
      perc = round(cnt * 100 / self._N, 1)
      Aio.printTemp("  Lfsr sim ", perc , "%             ")  
    return res
  def simulateForDataString(self, Sequence : BinString, InjectionAtBit = 0, StartValue = 0, quiet=False) -> int:
    if "list" in str(type(Sequence)):
      pool = multiprocessing.Pool()
      self._N = len(Sequence)
      self._IBit = InjectionAtBit
      self._Start = StartValue
      man = multiprocessing.Manager()
      self._C = man.list()
      results = pool.map(self._simplySim, Sequence)
      pool.close()
      pool.join()
      Aio.printTemp("                                    ")
      del self._C
      return results
    self.Value = StartValue
    imask = 1 << InjectionAtBit
    for Bit in Sequence:
      self.next()
      if Bit == 1:
        self.Value ^= imask
    return self.Value
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
    
# LFSR END ========================
  

  
