from curses.ascii import SP
from libs.utils_array import *
from libs.utils_int import *
from libs.database import *
from libs.aio import *
from libs.lfsr import *
from libs.PolynomialsArithmetic import *
from bitarray import *
import bitarray.util as bau
import copy
from libs.lfsr import *

class Ca(Lfsr):
  """Cellular automata object.
  """
  _ba_my_rules = bitarray(0)
  _baValue = bitarray(0)
  _size : int
  _ba_fast_sim_array = None
  def copy(self):
    return Ca(self)
  def __del__(self):
    pass
  def __init__(self, Rules : bitarray):
    """Initializes the CA object.

    Args:
        Rules (bitarray): rules vector. Bit==1 means 150 rule, Bit==0 means 90 rule.
    """
    if Aio.isType(Rules, "Ca"):
      self._ba_my_rules = Rules._ba_my_rules.copy()
      self._size = Rules._size
      self._baValue = Rules._baValue.copy()
    else:
      if Aio.isType(Rules, "bitarray"):
        self._ba_my_rules = Rules.copy()
      else:
        self._ba_my_rules = bitarray(Rules)
      self._size = len(Rules)
      self._baValue = bitarray(self._size)
      self.reset()
  def __repr__(self) -> str:
    result = "Ca(" + str(self._size) + ", " + self._ba_my_rules.to01() + ")"
    return result
  def __str__(self) -> str:
    return self._baValue.to01()
  def next(self, steps=1) -> bitarray:
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return 0
    if steps == 0:
      return self._baValue
    if steps == 1:
      middle = self._baValue & self._ba_my_rules
      left = self._baValue << 1
      right = self._baValue >> 1
      self._baValue = left ^ middle ^ right
      return self._baValue
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