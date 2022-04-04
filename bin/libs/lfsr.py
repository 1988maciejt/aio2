from libs.aio import *
from libs.database import *
from libs.utils_array import *
from libs.utils_int import *
from libs.cache import *
import math


# POLYNOMIAL CLASS ================

class Polynomial:
  pass
class Polynomial:
  _coefficients_list = []
  _balancing = 0
  def __init__(self, coefficients_list : list, balancing = 0):
    if "Polynomial" in str(type(coefficients_list)):
      self._coefficients_list = coefficients_list._coefficients_list.copy()
      self._balancing = coefficients_list._balancing + 0
    else:
      self._coefficients_list = coefficients_list
      self._coefficients_list.sort(reverse=True)
      self._balancing = balancing
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
  def makeNext(self, balancing = -1) -> bool:
    """Moves the middle coefficients to obtain next polynomial
    giving an LFSR having the sam count of taps.

    Args:
        balancing (int, optional): balancing factor.
          -1 : auto (default)
           0 : no balancechecking
          >0 : balancing factor

    Returns:
        bool: True if successfull, Ffalse if no next polynomial.
    """
    if balancing < 0:
      balancing = self._balancing
    if balancing > 0:
      while True:
        if not self.makeNext(0):
          return False
        if self.getBalancing() <= balancing:
          return True
    ccount = len(self._coefficients_list)
    degree = self._coefficients_list[0]
    last = degree
    for i in range(1, ccount-1):
      this = self._coefficients_list[i]
      if this+1 < last:
        self._coefficients_list[i] = this+1
        for j in range(i-1, 0,-1):
          self._coefficients_list[j] = self._coefficients_list[j+1] + 1
        return True
      last = this
    return False  
  def getTaps(self) -> int:
    return len(self._coefficients_list)-2
  def getPolynomialsCount(self) -> int:
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
    >>> Polynomial([3,1,0]).toInt()
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
  def nextPrimitive(self) -> bool:
    """Looks for the next primitive polynomial.

    Returns:
        bool: True if primitive found, otherwise False.
    """
    while True:
      if not self.makeNext():
        return False
      Aio.printTemp("Testing",self)
      if self.isPrimitive():
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
    return Polynomial(result, balancing)
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
    result = []
    poly = Polynomial.createPolynomial(degree, coeffs_count, balancing)
    if poly.isPrimitive():
      poly2 = Polynomial(poly)
      result.insert(0,poly2)
      if not quiet:
        print("Found prim. poly:", poly.getCoefficients())
      if n == 1:
        return result
    while poly.nextPrimitive():
      poly2 = Polynomial(poly)
      result.insert(0,poly2)
      if not quiet:
        print("Found prim. poly:", poly.getCoefficients())
      if n > 0:
        if len(result) >= n:
          break
    return result
  def firstPrimitive(degree : int, coeffs_count : int, balancing = 0) -> list:
    """Returns a first found primitive (over GF(2)) polynomial.

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)

    Returns:
        list: _description_
    """
    result = Polynomial.listPrimitives(degree,coeffs_count,balancing,1,True)
    if len(result) > 0:
      return result[0]
    return None
# POLYNOMIAL END ==================


# LFSR TYPE ENUM ==================
class LfsrType:
  Galois = 1
  Fibonacci = 2


# LFSR BEGIN ======================
class Lfsr:
  _my_poly = []
  _mask = []
  _value = 0
  _type = LfsrType.Galois
  _hval = 0
  _size = 0
  _fast_sim_array = False
  def clear(self):
    self._fast_sim_array.clear()
    self._fast_sim_array = False
  def __iter__(self):
    self._value = 1
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
    if type(Polynomial([])) != type(polynomial):
      poly = Polynomial(polynomial)
    self._my_poly = poly.getCoefficients()
    self._type = lfsr_type
    self._size = poly.getDegree()
    if lfsr_type == LfsrType.Galois:
      self._mask = poly.toInt() >> 1
    else:
      self._mask = poly.toInt()
    self._value = 1
    self._hval = 1 << (poly.getDegree()-1)
  def __str__(self) -> str:
    return str(bin(self._value))
  def __repr__(self) -> str:
    result = "Lfsr(" + str(self._my_poly) + ", "
    if self._type == LfsrType.Galois:
      result += "Galois"
    if self._type == LfsrType.Fibonacci:
      result += "Fibonacci" 
    result += ")"
    return result
  def _buildFastSimArray(self):
    oldVal = self._value
    size = self._size
    self._fast_sim_array = create2DArray(size, size)
    value0 = 1
    for i in range(size):
      self._value = value0
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
    self._value = oldVal
  def getValue(self) -> int:
    """Returns current value of the LFSR
    """
    return self._value
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
      return self._value
    if steps == 1:
      if self._type == LfsrType.Fibonacci:
        hbit = Int.parityOf(self._mask & self._value)
        self._value >>= 1
        if hbit == 1:
          self._value |= self._hval
        return self._value
      if self._type == LfsrType.Galois:
        lbit = self._value & 0x1
        self._value >>= 1
        if lbit == 1:
          self._value ^= self._mask
        return self._value
      return 0
    else:
      if self._fast_sim_array == False:
        self._buildFastSimArray()
      size = self._size
      RowIndex = 0
      #steps = copy.deepcopy(steps)
      while steps > 0: 
        value0 = self._value
        if steps & 1 == 1:
          result = 0
          for b in range(size):
            if value0 & 1 == 1:
              result ^= self._fast_sim_array[RowIndex][b]
            value0 >>= 1
          self._value = result
        steps >>= 1
        RowIndex += 1
      return self._value    
  def getPeriod(self) -> int:
    """Simulates the LFSR to obtain its period (count of states in trajectory).

    Returns:
        int: result. If the result is == (1<<size) it means a subtrajectory was reached
              and it cannot determine the period.
    """
    MaxResult = Int.mersenne(self._size) + 1
    self._value = 1
    value0 = self._value
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
    self._value = 1
    if self.next(Int.mersenne(index)) != 1:
      return False
    lst = DB.getPrimitiveTestingCyclesList(index)
    for num in lst:
      self._value = 1
      if self.next(num) == 1:
        return False
    return True
  def reset(self) -> int:
    """Sets the value to 0x1.

    Returns:
        int: new value
    """
    self._value = 1
    return 1
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
      result.append(self._value)
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
      Aio.print(bin(self._value))
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
      result += str(Int.getBit(self._value, bitIndex))
      self.next()
    return result
  def printFastSimArray(self):
    if self._fast_sim_array == False:
      self._buildFastSimArray()
    for r in self._fast_sim_array:
      line = ""
      for c in r:
        line += str(bin(c)) + "\t"
      Aio.print(line)
    
      
    
# LFSR END ========================
  

  
