from libs.utils_int import *

class BinString:
  BitCount = 64
  _val = 0
  def __init__(self, BitCount = 64, Value = 0) -> None:
    self.BitCount = BitCount
    self.setValue(Value)
  def __str__(self) -> str:
    r = ""
    v = self._val
    for i in range(self.BitCount):
      if v & 1:
        r = "1" + r
      else:
        r = "0" + r
      v >>= 1
    return r
  def __repr__(self) -> str:
    return "BinString(" + self.__str__() + ")"
  def setValue(self, Value):
    stype = str(type(Value))
    if "int" in stype:
      self._val = Value
    if "str" in stype:
      self._val = 0
      for c in Value:
        self._val <<= 1
        if c == "1":
          self._val |= 1
  def getValue(self):
     msk = (1 << self.BitCount) - 1
     return self._val & msk
  def setBit(self, Index : int, BitValue = 1):
    self._val = Int.setBit(self._val, Index, BitValue)
  def resetBit(self, Index : int):
    self._val = Int.resetBit(self._val, Index)
  def getBit(self, Index : int) -> int:
    return Int.getBit(self._val, Index)
  def copy(self):
    return BinString(self.BitCount, self._val)
  def shiftIn(self, BitValue : int, Left=True):
    if Left:
      self._val <<= 1
      self._val += BitValue
    else:
      self._val >>= 1
      Int.setBit(self._val, self.BitCount-1, BitValue)
    return self
  def shiftOut(self, BitValue : int, Right=True):
    if Right:
      bit = self._val & 1
      self._val >>= 1
      return bit
    else:
      bit = self.getBit(self.BitCount - 1)
      self._val <<= 1
      return bit
  def __iter__(self):
    self._ii = 0
    return self
  def __next__(self):
    if self._ii < self.BitCount:
      b = Int.getBit(self._val, self._ii)
      self._ii += 1
      return b
    raise StopIteration
  def __add__(self, other):
    new = self.copy()
    new._val += other.getValue()
    return new
  def __sub__(self, other):
    new = self.copy()
    new._val -= other.getValue()
    return new
  def __mul__(self, other):
    new = self.copy()
    new._val *= other.getValue()
    return new
  def __truediv__(self, other):
    new = self.copy()
    new._val /= other.getValue()
    return new
  def __floordiv__(self, other):
    new = self.copy()
    new._val //= other.getValue()
    return new
  def __mod__(self, other):
    new = self.copy()
    new._val %= other.getValue()
    return new
  def __rshift__(self, other):
    new = self.copy()
    new._val >>= other
    return new
  def __lshift__(self, other):
    new = self.copy()
    new._val <<= other
    return new
  def __and__(self, other):
    new = self.copy()
    new._val &= other.getValue()
    return new
  def __or__(self, other):
    new = self.copy()
    new._val |= other.getValue()
    return new
  def __xor__(self, other):
    new = self.copy()
    new._val ^= other.getValue()
    return new
  def __lt__(self, other):
    return (self.getValue() < other.getValue())
  def __gt__(self, other):
    return (self.getValue() > other.getValue())
  def __le__(self, other):
    return (self.getValue() <= other.getValue())
  def __ge__(self, other):
    return (self.getValue() >= other.getValue())
  def __eq__(self, other):
    return (self.getValue() == other.getValue())
  def __ne__(self, other):
    return (self.getValue() != other.getValue())
  def __iadd__(self, other):
    self._val += other.getValue()
    return self
  def __isub__(self, other):
    self._val -= other.getValue()
    return self
  def __imul__(self, other):
    self._val *= other.getValue()
    return self
  def __idiv__(self, other):
    self._val /= other.getValue()
    return self
  def __ifloordiv__(self, other):
    self._val //= other.getValue()
    return self
  def __imod__(self, other):
    self._val %= other.getValue()
    return self
  def __irshift__(self, other):
    self._val >>= other
    return self
  def __ilshift__(self, other):
    self._val <<= other
    return self
  def __iand__(self, other):
    self._val &= other.getValue()
    return self
  def __ior__(self, other):
    self._val |= other.getValue()
    return self
  def __ixor__(self, other):
    self._val ^= other.getValue()
    return self
  def __neg__(self):
    new = self.copy()
    new._val = (1 << new.BitCount) - new._val 
    return new
  def __pos__(self):
    return self.copy()
  def __invert__(self):
    new = self.copy()
    new._val = (1 << new.BitCount) - new._val 
    return new