from libs.database import *
from libs.printing import *
from libs.utils_array import *
from libs.utils_int import *
from enum import Enum


# POLYNOMIAL CLASS ================
class Polynomial:
  
  _coefficients_list = []
  _balancing = 0
  
  def __init__(self, coefficients_list : list, balancing = 0):
    self._coefficients_list = coefficients_list
    self._coefficients_list.sort(reverse=True)
    self._balancing = balancing
    
  def getCoefficients(self) -> list:
    return self._coefficients_list
  
  def getCoefficientsCount(self) -> int:
    return len(self._coefficients_list)
  
  def getDegree(self) -> int:
    return self._coefficients_list[0]
  
  def makeNext(self, balancing = -1) -> bool:
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
    clist = self._coefficients_list
    degree = int(clist[0])
    result = int(0)
    for i in range(len(clist)):
      coeff = clist[i]
      result += (1 << coeff)
    return result
  
  def toString(self) -> str:
    return str(self._coefficients_list)
  
  def isPrimitive(self) -> bool:
    l = Lfsr(self, LfsrType.Galois)
    return l.isMaximum()
  
  def nextPrimitive(self) -> bool:
    while True:
      if not self.makeNext():
        return False
      if self.isPrimitive():
        return True

# POLYNOMIAL END ==================




class LfsrType(Enum):
  Galois = 1
  Fibonacci = 2



class Lfsr:
  
  _my_poly : Polynomial
  _mask : int
  _value : int
  _type : LfsrType
  _hval : int
  _size : int
  _fast_sim_array = False
  
  def __init__(self, poly : Polynomial, lfsr_type : LfsrType):
    self._my_poly = poly
    self._type = lfsr_type
    self._size = self._my_poly.getDegree()
    if lfsr_type == LfsrType.Galois:
      self._mask = poly.toInt() >> 1
    else:
      self._mask = poly.toInt()
    self._value = 1
    self._hval = 1 << (poly.getDegree()-1)
    
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
    return self._value
  
  def getPeriod(self) -> int:
    return (self._my_poly.getCoefficientsCount() - 2)
    
  def next(self, steps=1) -> int:
    if steps < 0:
      print_error("'steps' must be a positve number")
      return 0
    if steps == 0:
      return self._value
    if steps == 1:
      if self._type == LfsrType.Fibonacci:
        hbit = parityOf(self._mask & self._value)
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
    
  def countStates(self) -> int:
    MaxResult = mersenne(self._size)
    self._value = 1
    value0 = self._value
    result = 1
    valuex = self.next()
    while valuex != value0 and result <= MaxResult:
      valuex = self.next()  
      result += 1
    return result
  
  def isMaximum(self) -> bool:
    index = self._size
    self._value = 1
    if self.next(mersenne(index)) != 1:
      return False
    lst = getPrimitiveTestingCyclesList(index)
    for num in lst:
      self._value = 1
      if self.next(num) == 1:
        return False
    return True
    
  

  
