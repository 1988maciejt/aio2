from libs.lfsr import *
from bitarray import *
import multiprocessing
from random import uniform

_globalsum = 0

class Nlfsr(Lfsr):
  _baValue = None
  _size = 0
  _Config = []
  _ConfigSingle = []
  _ConfigAnds = []
  _reversed_config = False
  _points = []
  _start = bitarray()
  _offset = 0
  def clear(self):
    pass
  def copy(self):
    return Nlfsr(self)
  def __del__(self):
    self._Config.clear()
    self._baValue.clear()
  def __init__(self, Size : int, Config = [], ReversedConfigList = False) -> None:
    if Aio.isType(Size, "Nlfsr"):
      self._size = Size._size      
      self._Config = Size._Config.copy()
      self._baValue = Size._baValue.copy()
      self._reversed_config = Size._reversed_config
      self._points = Size._points
      self._ConfigAnds = Size._ConfigAnds
      self._ConfigSingle = Size._ConfigSingle
    else:  
      self._size = Size
      self._Config = Config
      self._baValue = bitarray(self._size)
      self._reversed_config = ReversedConfigList
      self.reset()
      self._ConfigSingle = []
      self._ConfigAnds = []
      for C in self._Config:
        if type(C) == type(0):
          B = C
          if not self._reversed_config:
            B = -B-1
          self._ConfigSingle.append(B)
        else:
          AList = []
          for sC in C:
            if self._reversed_config:
              AList.append(sC)
            else:
              AList.append(-sC-1)
          self._ConfigAnds.append(AList)
  def __repr__(self) -> str:
    result = "Nlfsr(" + str(self._Config) + ")"
    return result
  def _fsimBuildTable(self):
    self._fsimAnds = []
    self._fsimSingle = []
    for Offset in range(self._size):
      SList = []
      AList = []
      for C in self._ConfigSingle:
        SList.append((C-Offset) % self._size)
      for C in self._ConfigAnds:
        A = []
        for sC in C:
          A.append((sC-Offset) % self._size)
        AList.append(A)
      self._fsimSingle.append(SList)
      self._fsimAnds.append(AList)
  def next(self, steps=1):
    if steps < 0:
      Aio.printError("'steps' must be a positve number")
      return 0
    else:
      for _ in range(steps):
        self._next1()
    return self._baValue
  def isMaximumSingle(self):
    Cycles = Int.mersenne(self._size)
    self.reset()
    V0 = self._baValue
    self.next(Cycles)
    return (self._baValue == V0)
  def isMaximum(self):
    self.reset()
    bneg = bitarray(self._size)
    bneg.setall(0)
    bor = bitarray(self._size)
    bor.setall(0)
    for C in self._ConfigSingle:
      bneg[C] = 1
    for C in self._ConfigAnds:
      bneg[C[0]] = 1
      for sC in C:
        bor[sC] = 1
    for _ in range(self._size>>1):
      b = int(uniform(0, self._size))
      self._baValue[b] = 1
    Max = 2**self._size
    MaxSetSize = 1000000
    NumCount = int(Max / MaxSetSize)
    NumCount = self._size +4
    if NumCount < 10:
      NumCount = 2
    if NumCount > 48:
      NumCount = 48
    print(f'NumCount = {NumCount}, bneg = {bneg}, bor = {bor}')
    self._points = multiprocessing.Manager().list()
    for _ in range(NumCount):
      while self._baValue in self._points:
        self.next()
        self._baValue |= bor
      self._points.append(self._baValue.copy())
      self.next()
      self._baValue ^= bneg
    arguments = []
    for Start in self._points:
      n = self.copy()
      n._start = Start.copy()
      arguments.append(n)
#      print(repr(n), n._start)
    pool = multiprocessing.Pool()
    Test = pool.map(_NlfsrIsMaximumHelper, arguments)
    Cycles = sum(Test)
    print(Cycles, "= sum of", Test)

    

def _NlfsrIsMaximumHelper(NlfsrObject : Nlfsr):
  print("Start new...")
  Points = list(NlfsrObject._points)
  NlfsrObject._baValue = NlfsrObject._start
  MaxResult = 2**NlfsrObject._size
  NlfsrObject.next()
  Result = 1
  cntr = 100000
  while not NlfsrObject._baValue in Points and Result < MaxResult:
    NlfsrObject.next()
    Result += 1
    cntr -= 1
    if cntr == 0:
      cntr = 100000
      Points = list(NlfsrObject._points)
  print("Stop",NlfsrObject._baValue)
  if NlfsrObject._baValue in NlfsrObject._points:
    NlfsrObject._points.remove(NlfsrObject._baValue)
  return Result