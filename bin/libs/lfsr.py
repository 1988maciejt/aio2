from ast import Pass
from libs.database import *
from libs.printing import *
from libs.utils_array import *
from libs.utils_int import *
from enum import Enum
import copy


# POLYNOMIAL CLASS ================

class Polynomial:
  Pass

class Polynomial:
  
  _coefficients_list = []
  _balancing = 0
  
  def __init__(self, coefficients_list : list, balancing = 0):
    self._coefficients_list = coefficients_list
    self._coefficients_list.sort(reverse=True)
    self._balancing = balancing
    
  def __str__(self) -> str:
    return str(self._coefficients_list)
  
  def __repr__(self) -> str:
    return "Polynomial(" + str(self._coefficients_list) + ")"
    
  def getCoefficients(self) -> list:
    """Returns list of coefficients.
    """
    return self._coefficients_list
  
  def getCoefficientsCount(self) -> int:
    """Returns coefficients count.
    """
    return len(self._coefficients_list)
  
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
    l = Lfsr(self, LfsrType.Galois)
    return l.isMaximum()
  
  def nextPrimitive(self) -> bool:
    """Looks for the next primitive polynomial.

    Returns:
        bool: True if primitive found, otherwise False.
    """
    while True:
      if not self.makeNext():
        return False
      if self.isPrimitive():
        return True
      
  def createPolynomial(degree : int, coeffs_count : int, balancing = 0) -> Polynomial:
    """Returns a polynomial, usefull for LFSRs.

    Args:
        degree (int): polynomial degree (i.e. size of LFSR)
        coeffs_count (int): coefficients count (i.e. LFSRs taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking).
    """
    if coeffs_count < 1:
      print_error ("'oefficients_count' must be >= 1")
      return Polynomial([])
    if degree < (coeffs_count-1):
      print_error ("'coefficients_count - 1' must be <= 'degree'")
      return Polynomial([])  
    result = [degree]
    if balancing > 0:
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
  
  def findPrimitivePolynomials(degree : int, coeffs_count : int, balancing = 0, n = 0, quiet = False) -> list:
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
      poly2 = copy.copy(poly)
      result.insert(0,poly2)
      if not quiet:
        print("Found prim. poly:", poly.getCoefficients())
      if n == 1:
        return result
    while poly.nextPrimitive():
      poly2 = copy.deepcopy(poly)
      result.insert(0,poly2)
      if not quiet:
        print("Found prim. poly:", poly.getCoefficients())
      if n > 0:
        if len(result) >= n:
          break
    return result

  def getFirstPrimitive(degree : int, coeffs_count : int, balancing = 0) -> list:
    """Returns a first found primitive (over GF(2)) polynomial.

    Args:
        degree (int): polynomial degree (i.e. LFSR size)
        coeffs_count (int): coefficients count (i.e. LFSR taps count + 2)
        balancing (int, optional): balancing factor. Defaults to 0 (no balance checking)

    Returns:
        list: _description_
    """
    return Polynomial.findPrimitivePolynomials(degree,coeffs_count,balancing,1,True)[0]

# POLYNOMIAL END ==================




class LfsrType(Enum):
  Galois = 1
  Fibonacci = 2



class Lfsr:
  
  _my_poly : list
  _mask : int
  _value : int
  _type : LfsrType
  _hval : int
  _size : int
  _fast_sim_array = False
  
  def __init__(self, poly : Polynomial, lfsr_type : LfsrType):
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
      print_error("'steps' must be a positve number")
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
      steps = copy.deepcopy(steps)
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
    
  

  
