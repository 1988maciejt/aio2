from math import *
from random import *


class RingOscillator:
  _T = 1
  _dT = 0.1
  _Tmin = 0.95
  _Tmax = 1.05
  _LastTime = -1
  _1s = []
  _0s = []
  def _randT(self) -> float:
    return uniform(self._Tmin, self._Tmax)
  def __init__(self, T : float, DeltaT : float) -> None:
    self._T = T
    self._dT = DeltaT
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
    self.reset()
  def getT(self) -> float:
    return self._T
  def setT(self, T : float) -> None:
    self._T = T
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
  def getDeltaT(self) -> float:
    return self._dT
  def setDeltaT(self, DeltaT : float) -> None:
    self._dT = DeltaT
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
  def reset(self) -> None:
    self._LastTime = self._randT() / 2
    self._1s = [0]
    self._0s = [self._LastTime]
  def value(self, Time : float) -> int:
    if self._LastTime <= 0:
      self._LastTime = self._randT() / 2
      ro_1s = [0]
      ro_0s = [self._LastTime]
    if Time < 0:
      return 0    
    if Time > self._LastTime:
      while self._LastTime < (Time*1.3):
        r1 = self._1s[-1]
        r0 = self._0s[-1]
        self._LastTime += self._randT()
        if r0 > r1:
          self._1s.append(self._LastTime)
        elif r1 > r0:
          self._0s.append(self._LastTime)
    t1 = 0
    for v in self._1s:
      if v > Time:
        break
      t1 = v
    t0 = 0
    for v in self._0s:
      if v > Time:
        break
      t0 = v
    if t1 > t0:
       return 1
    return 0
  def sample(self, N : int, Ts : float, t0 = 0.0, Reset = False) -> str:
    if Reset:
      self.reset()
    t = t0
    result = ""
    for i in range(N):
      result += (str(self.value(t)))
      t += Ts
    return result