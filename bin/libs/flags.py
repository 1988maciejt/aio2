from sys import flags
from libs.utils_int import *


class Flags:
  _flags = 0
  def __repr__(self) -> str:
    return "Flags(" + str(bin(self._flags)) + ")"
  def __str__(self) -> str:
    return str(bin(self._flags))
  def test(self,Index : int) -> bool:
    if Int.getBit(self._flags, Index) == 1:
      return True
    return False
  def get(self,Index : int) -> bool:
    return self.test(Index)
  def set(self, Index : int, Value = True) -> None:
    value_ = 0
    if Value:
      value_ = 1
    self._flags = Int.setBit(self._flags, Index, value_)
  def reset(self, Index : int) -> None:
    self._flags = Int.resetBit(self._flags, Index)
  def getAll(self) -> int:
    return self._flags
  def setAll(self, Flags : int) -> None:
    self._flags = flags


class NamedFlags:
  _dict = dict()
  def __repr__(self) -> str:
    return "NamedFlags(" + str(self._dict) + ")"
  def __str__(self) -> str:
    return str(self._dict)
  def test(self,Key : str) -> bool:
    if not Key in self._dict:
      return False
    if self._dict[Key]:
      return True
    return False
  def get(self,Key) -> bool:
    return self.test(Key)
  def set(self, Key, Value = True) -> None:
    self._dict[Key] = Value
  def reset(self, Key) -> None:
    self._dict[Key] = False
  def getAll(self) -> dict:
    return self._dict
  def setAll(self, Dict : dict) -> None:
    self._dict = Dict  
  