from math import *
from random import *


class RingOscillator:
  _T = 1
  _dT = 0.1
  _Tmin = 0.95
  _Tmax = 1.05
  _Sigma = 1
  _LastTime = -1
  _1s = []
  _0s = []
  _jstart = []
  _jstop = []
  def _randT(self) -> float:
    #return uniform(self._Tmin, self._Tmax)
    return gauss(self._T, self._Sigma)
  def __init__(self, T : float, DeltaT : float) -> None:
    self._T = T
    self._dT = DeltaT
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
    self._Sigma = (DeltaT / 2) / 0.699
    self.reset()
  def getT(self) -> float:
    return self._T
  def setT(self, T : float) -> None:
    self._T = T
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
    self._Sigma = (self._dT / 2) / 0.699
  def getDeltaT(self) -> float:
    return self._dT
  def setDeltaT(self, DeltaT : float) -> None:
    self._dT = DeltaT
    self._Tmin = self._T - self._dT/2
    self._Tmax = self._T + self._dT/2
    self._Sigma = (self._dT / 2) / 0.699
  def reset(self) -> None:
    self._LastTime = self._randT() / 2
    self._1s = [0]
    self._0s = [self._LastTime]
    jstart = self._LastTime
    jstop = self._T / 2
    if jstop > jstart:
      self._jstart = [jstart]
      self._jstop = [jstop]
    else:
      self._jstart = [jstop]
      self._jstop = [jstart]
    self._jstart = [self._LastTime]
    self._jstop = [self._T / 2]
  def value(self, Time : float) -> int:
    if Time < 0:
      return 0    
    if Time > (self._LastTime + self._T):
      while self._LastTime < (Time*1.1):
        r1 = self._1s[-1]
        r0 = self._0s[-1]
        jstart = self._LastTime + self._T / 2
        if r0 > r1:
          self._LastTime = r1 + self._randT()
          jstart = r1 + self._T
          self._1s.append(self._LastTime)
        else:
          self._LastTime = r0 + self._randT()
          jstart = r0 + self._T
          self._0s.append(self._LastTime)
        jstop = self._LastTime
        if jstop > jstart:
          self._jstart.append(jstart)
          self._jstop.append(jstop)
        else:
          self._jstart.append(jstop)
          self._jstop.append(jstart)
    t1 = 0
    for v in self._1s:
      if v >= Time:
        break
      t1 = v
    t0 = 0
    for v in self._0s:
      if v >= Time:
        break
      t0 = v
    if t1 > t0:
       return 1
    return 0
  def isJitter(self, Time : float) -> bool:
    if Time < 0:
      return False
    if Time > (self._LastTime + self._T):
      self.value(Time)
    tStart = 0
    for v in self._jstart:
      if v > Time:
        break
      tStart = v
    tStop = 0
    for v in self._jstop:
      if v > Time:
        break
      tStop = v
    if tStart > tStop:
      return True
    return False
  def sample(self, N : int, Ts : float, t0 = -1, Reset = False) -> str:
    if t0 < 0:
      t0 = self._T / 2
    if Reset:
      self.reset()
    t = t0
    result = ""
    for i in range(N):
      result += (str(self.value(t)))
      t += Ts
    return result