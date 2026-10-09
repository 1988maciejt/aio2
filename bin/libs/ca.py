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
  def _next1(self) -> bitarray:
    print("next1 ca")
    middle = self._baValue & self._ba_my_rules
    left = self._baValue << 1
    right = self._baValue >> 1
    self._baValue = left ^ middle ^ right
    return self._baValue
