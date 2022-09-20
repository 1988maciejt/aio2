from libs.binstr import *

class Nlfsr:
  _Value = []
  _Length = 0
  _LastBit = 0
  _Offset = 0
  _Config = []
  def __init__(self, Length : int, Config : list) -> None:
    self._Length = Length
    self._Config = Config
    self.reset()
  def reset(self):
    self._Value.clear()
    self._Value = [0 for _ in range(self._Length)]
    self._LastBit = self._Length - 1
    self._Offset = 0
    self._Value[self._LastBit] = 1
  def getLength(self):
    return self._Length
  def next(self):
    Bit = 0
    self._LastBit += 1
    if self._LastBit >= self._Length:
      self._LastBit = 0
    for C in self._Config:
      if type(C) == type(0):
        Bit ^= self._Value[(C + self._Offset) % self._Length]
      else:
        Tmp = 1
        for b in C:
          Tmp &= self._Value[(b + self._Offset) % self._Length]
        Bit ^= Tmp
    self._Value[self._LastBit] = Bit
    self._Offset += 1
    if self._Offset >= self._Length:
      self._Offset = 0
  def toBinString(self):
    Result = BinString(self._Length, 0)
    for i in range(self._Length):
      index = (i + self._Offset) % self._Length
      if self._Value[index] == 1:
        Result.setBit(i)
    return Result
  