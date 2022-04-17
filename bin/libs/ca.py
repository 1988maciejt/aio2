from libs.utils_array import *
from libs.utils_int import *
from libs.database import *
from libs.aio import *
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
  def __init__(self, Size : int, Rules : int):
    """Initializes the CA object.

    Args:
        Size (int): bit-size of the CA
        Rules (int): rules vector. Bit==1 means 150 rule, Bit==0 means 90 rule.
          Example rules 0b101, 0b110110
    """
    self._my_rules = Rules
    self._value = 1
    self._size = Size
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
    