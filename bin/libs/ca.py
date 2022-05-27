from curses.ascii import SP
from libs.utils_array import *
from libs.utils_int import *
from libs.database import *
from libs.aio import *
from libs.lfsr import *
from libs.PolynomialsArithmetic import *
import copy

class Ca:
  """Cellular automata object.
  """
  _my_rules : int
  _value : int
  _size : int
  _fast_sim_array = False
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
  def __init__(self, SizeOrPolynomial : int, Rules = 0):
    """Initializes the CA object.

    Args:
        Size (int): bit-size of the CA
        Rules (int): rules vector. Bit==1 means 150 rule, Bit==0 means 90 rule.
          Example rules 0b101, 0b110110
    """
    if type(SizeOrPolynomial) == type(Polynomial([0])):
      PPoly = SizeOrPolynomial.toInt()
      SPoly = 1 << (p_degree(PPoly)-1)    
      self._my_rules = None
      while type(self._my_rules) == type(None):
        self._my_rules = Ca.rules_from_bpoly(PPoly, SPoly)
        SPoly += 1
      self._value = 1
      self._size = p_degree(PPoly)
    else:
      self._my_rules = Rules
      self._value = 1
      self._size = SizeOrPolynomial
  def __str__(self) -> str:
    return str(bin(self._value))
  def __repr__(self) -> str:
    result = "Ca(" + str(self._size) + ", " + str(bin(self._my_rules)) + ")"
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
    return self._value
  def getSize(self) -> int:
    return (self._size)
  def next(self, steps=1) -> int:
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return 0
    if steps == 0:
      return self._value
    if steps == 1:
      result = 0
      for i in range(0, self._size):
        left = 0
        right = 0
        if i > 0:
          left = Int.getBit(self._value, i - 1)
        if i < (self._size-1):
          right = Int.getBit(self._value, i + 1)
        bit = left ^ right
        if Int.getBit(self._my_rules, i) == 1:
          bit ^= Int.getBit(self._value, i)
        result = Int.setBit(result, i, bit)
      self._value = result
      return self._value
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
  def reset(self, NewValue = 1) -> int:
    self._value = NewValue
    return NewValue
  def rules_from_bpoly(polyint : int, polyint2 : int) -> int:
    deg = p_degree(polyint)
    result = 0
    a = polyint
    b = polyint2
    for i in range(deg):
#      print(f'{bin(a)}, {bin(b)}')
      if not b:
        return None
      tpl = p_divmod(a, b)
      #print (f'{i}:  divmod({a}, {b}) = {tpl}')
      a = b
      b = tpl[1]
      if tpl[0] & 1:
        result |= (1 << i)
    if a == 1:
      return result
    return None  
  def look_for_second_poly(modulus : int, fi):
    n = p_degree(modulus)
    print(f'modulus: {bin(modulus)}')
    polyint_prim = p_derivative(modulus)
    print(f'prim:    {bin(polyint_prim)}')
    f = p_mod_mul(0b110, polyint_prim, modulus)
    print(f'f:       {bin(f)}')
    finv = p_mod_inv(f, modulus)
    g = p_mod_pow(finv, 2, modulus)
    print(f'g:       {bin(g)}')
#    fi = 1
#    if (n & 1) == 0:
#      fi = p_get_next_trace1(1, modulus, True)
    print(f'fi:      {bin(fi)}') 
    beta = 0
    for i in range(1, n):
      g2isum = 0
      for j in range(0, i):
        g2i = p_mod_pow(g, 2**j, modulus)
        g2isum ^= g2i
      fi2i = p_mod_pow(fi, 2**i, modulus)
      beta ^= p_mod_mul(fi2i, g2isum, modulus) 
    print(f'beta: {bin(beta)}')
    q1 = p_mod_mul(beta, f, modulus)
    print(f'q1: {bin(q1)}')
    return q1
#    q2 = p_mod_inv(q1, modulus)
#    print(f'q2: {bin(q2)}')