from ast import BitOr
from libs.logic import Logic
from libs.aio import *
from libs.database import *
from libs.utils_array import *
from libs.utils_int import *
from libs.cache import *
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
  _cont = True
  _n = 0
  _bmin = 1
  def _check(p):
    if Polynomial._cont:
      Aio.printTemp("Checking " + str(p))
      if p.isPrimitive():
        Polynomial._result.append(p)
        if Polynomial._n > 0 and len(Polynomial._result) >= Polynomial._n:
          Polynomial._cont = False
        if not Polynomial._quiet:
          print("Found " + str(p) + " " * 30)
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
    else:
      self._coefficients_list = coefficients_list
      self._coefficients_list.sort(reverse=True)
      self._balancing = balancing
  def __iter__(self):
    p = Polynomial.createPolynomial(self.getDegree(), self.getCoefficientsCount(), self.getBalancing())
    self._coefficients_list = p._coefficients_list
    return self
  def __next__(self):
    if self.makeNext():
      return Polynomial(self)
    raise StopIteration  
  def __str__(self) -> str:
    return str(self._coefficients_list)
  def __repr__(self) -> str:
    return "Polynomial(" + str(self._coefficients_list) + ")"
  def __eq__(self, other : Polynomial) -> bool:
    return self._coefficients_list == other._coefficients_list
  def __ne__(self, other : Polynomial) -> bool:
    return self._coefficients_list != other._coefficients_list
  def getCoefficients(self) -> list:
    """Returns list of coefficients.
    """
    return self._coefficients_list
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
    minsub = self._bmin
    ccount = len(self._coefficients_list)
    degree = self._coefficients_list[0]
    lastmax = degree-minsub
    for i in range(1, ccount-1):
      this = self._coefficients_list[i]
      if this < lastmax:
        self._coefficients_list[i] = this+1
        return True
      else:
        if (i == (ccount-2)):
          return False
        if self._coefficients_list[i+1] + 1 + minsub <= self._coefficients_list[i]:
          self._coefficients_list[i] = self._coefficients_list[i+1] + 1 + minsub
          self._coefficients_list[i+1] = self._coefficients_list[i+1] + 1
          return True      
      lastmax = this-minsub
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
    cached = Cache.recall(self.toInt())
    if cached != None:
      return cached
    cached = Cache.recall(self.getReversed().toInt())
    if cached != None:
      return cached
    l = Lfsr(self, LfsrType.Galois)
    result = l.isMaximum()
    l.clear()
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
  def createPolynomial(degree : int, coeffs_count : int, balancing = 0) -> Polynomial:
    """Returns a polynomial, usefull for LFSRs.

    Args:
        degree (int): polynomial degree (i.e. size of LFSR)
        coeffs_count (int): coefficients count (i.e. LFSRs taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking).
    """
    if coeffs_count < 1:
      Aio.printError ("'oefficients_count' must be >= 1")
      return Polynomial([])
    if degree < (coeffs_count-1):
      Aio.printError ("'coefficients_count - 1' must be <= 'degree'")
      return Polynomial([])  
    result = [degree]
    bmin = 1
    if balancing > 0 and balancing < degree:
      avg = float(degree) / float(coeffs_count - 1)
      halfbal = float(balancing) / 2.0
      bmin = avg - halfbal
      bmax = avg + halfbal
      result.insert(0,0);
      if bmin < 1.0:
        bmin = 1.0
        bmax = float(balancing + 1)
      c = 0.0
      for i in range(3, coeffs_count):
        c += bmin
        result.insert(0, int(round(c)))
      max_c = int(round(float(degree) - bmax))
      while max_c in result:
        max_c += 1
      result.insert(0, max_c)
    else:
      for i in range(coeffs_count-1):
        result.insert(0,i)
    p = Polynomial(result, balancing)
    p._bmin = int(bmin)
    return p
  def listPrimitives(degree : int, coeffs_count : int, balancing = 0, n = 0, quiet = False) -> list:
    """Returns a list of primitive polynomials (over GF(2)).

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)
        n (int, optional): stop searching if n polynomials is found. Defaults to 0 (don't stop)
        quiet (bool, optional): if False (default) print to the sdtout every time a new prim poly is found

    Returns:
        list: list of polynomial objects
    """
    Aio.printTemp("Preparing...")
    manager = multiprocessing.Manager()
    Polynomial._result = manager.list()
    Polynomial._n = n
    Polynomial._quiet = quiet
    Polynomial._cont = True
    poly = Polynomial.createPolynomial(degree, coeffs_count, balancing)
    pool = multiprocessing.Pool()
    pr = pool.map_async(Polynomial._check, poly)
    while not pr.ready():
       time.sleep(0.1)
    pool.close()
    r = list(Polynomial._result)
    if n > 0 and len(r) > n:
      r = r[0:n]
    Aio.printTemp(" " * Aio.getTerminalColumns())
    gc.collect()
    return r
  def firstPrimitive(degree : int, coeffs_count : int, balancing = 0, quiet=False) -> list:
    """Returns a first found primitive (over GF(2)) polynomial.

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)

    Returns:
        list: _description_
    """
    p = Polynomial.createPolynomial(degree, coeffs_count, balancing)
    if p.isPrimitive():
      return p
    elif p.nextPrimitive(quiet):
      return p
    return None
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


# LFSR BEGIN ======================
class Lfsr:
  """An LFSR object. Used for all 3 LFSR implementations, like 
  Galois, Fibonacci (default), RingGenerator.
  """
  _my_poly = []
  _mask = []
  Value = 0
  _type = LfsrType.Galois
  _hval = 0
  _size = 0
  _fast_sim_array = False
  _taps = []
  def clear(self):
    """Clears the fast-simulation array
    """
    #self._fast_sim_array.clear()
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
  def __init__(self, polynomial, lfsr_type = LfsrType.Fibonacci):
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
    if type(Polynomial([])) != type(polynomial):
      poly = Polynomial(polynomial)
    self._my_poly = poly.getCoefficients()
    self._type = lfsr_type
    self._size = poly.getDegree()
    if lfsr_type == LfsrType.Galois:
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
  def __str__(self) -> str:
    return str(bin(self.Value))
  def __repr__(self) -> str:
    result = "Lfsr(" + str(self._my_poly) + ", "
    if self._type == LfsrType.Galois:
      result += "Galois"
    if self._type == LfsrType.Fibonacci:
      result += "Fibonacci" 
    if self._type == LfsrType.RingGenerator:
      result += "RingGenerator" 
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
      elif self._type == LfsrType.RingGenerator:
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
      Aio.print(bin(self.Value))
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
  def _append_results(r):
    global _results
    _results.append(r)
    cnt = len(_results)
    if cnt % 100 == 0:
      perc = round(cnt * 100 / Lfsr._N, 1)
      Aio.printTemp("  Lfsr sim ", perc , "%             ")
  def simulateForDataString(self, BinString : str, InjectionAtBit = 0, StartValue = 0, CompressedData=False) -> int:
    if "list" in str(type(BinString)):
      global _results
      _results = []
      pool = multiprocessing.Pool()
      lfsrs = []
      Lfsr._N = len(BinString)
      for BS in BinString:
        rn = Lfsr(self)
        lfsrs.append(rn)
        pool.apply_async(rn.simulateForDataString, args=(BS, InjectionAtBit, StartValue, CompressedData), callback=Lfsr._append_results)
      pool.close()
      pool.join()
      for rn in lfsrs:
        del rn
      gc.collect()
      Aio.printTemp("                                    ")
      return _results
    self.Value = StartValue
    imask = 1 << InjectionAtBit
    if CompressedData:
      BitArray = zlib.decompress(BinString)
      for Bit in BitArray:
        self.next()
        if Bit == 49:
          self.Value ^= imask
      return [BinString ,self.Value]
    else:  
      for Bit in BinString:
        self.next()
        if Bit == "1":
          self.Value ^= imask
      return [BinString ,self.Value]
      
    
# LFSR END ========================
  

  
