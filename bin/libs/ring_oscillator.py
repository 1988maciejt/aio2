from importlib.machinery import WindowsRegistryFinder
from math import *
import multiprocessing
from random import *
from libs.aio import *
import gc
import zlib
from libs.binstr import *


class RingOscillator:
  """Object used to simulate ring oscillators (RO).
  """
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
  _C = 0
  _N = 0
  CalculateJitter = True
  def _gets(n) -> str:
    ro = RingOscillator(RingOscillator._T, RingOscillator._dT, False)
    res = ro.sample(RingOscillator._Wlen, RingOscillator._Ts, RingOscillator._Toff)
    RingOscillator._result.append(res)
    del ro
    cnt = len(RingOscillator._result)
    if cnt % 200 == 0:
      perc = round(cnt * 100 / RingOscillator._N,1)
      Aio.printTemp("  RO sim:",perc,"%            ")
  def getSampleSet(N : int, WordLen : int, Tavg : float, dT : float, Ts : float, TOffset = 0.0) -> list:
    RingOscillator._T = Tavg
    RingOscillator._dT = dT
    RingOscillator._Ts = Ts
    RingOscillator._Toff = TOffset
    RingOscillator._Wlen = WordLen
    RingOscillator._N = N
    RingOscillator._cnt = 0
    man = multiprocessing.Manager()
    RingOscillator._result = man.list()
    pool = multiprocessing.Pool()
    pool.map_async(RingOscillator._gets, range(N))
    pool.close()
    pool.join()
    Aio.printTemp("                                                      ")
    ret = list(RingOscillator._result)
    del RingOscillator._result
    return ret
  def _randT(self) -> float:
    return gauss(self._T, self._Sigma) 
  def __init__(self, T : float, DeltaT : float, CalculateJitter = True) -> None:
    self._T = T
    self._dT = DeltaT
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
    self._Sigma = (DeltaT / 2) / 0.699
    self.reset()
    self.CalculateJitter = CalculateJitter
  def getT(self) -> float:
    """returns the average RO period"""
    return self._T
  def setT(self, T : float) -> None:
    """Sets the average RO period"""
    self._T = T
    self._Tmin = T - self._dT/2
    self._Tmax = T + self._dT/2
    self._Sigma = (self._dT / 2) / 0.699
  def getDeltaT(self) -> float:
    """Returns the +/- period deviation value"""
    return self._dT
  def setDeltaT(self, DeltaT : float) -> None:
    """Sets the +/- period deviation value"""
    self._dT = DeltaT
    self._Tmin = self._T - self._dT/2
    self._Tmax = self._T + self._dT/2
    self._Sigma = (self._dT / 2) / 0.699
  def reset(self) -> None:
    """Resets the simulation tables"""
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
    """Returns the simulated RO output value at given time"""
    if Time < 0:
      return 0    
    if Time > (self._LastTime + self._T):
      while self._LastTime < (Time*1.1):
        r1 = self._1s[-1]
        r0 = self._0s[-1]
        if r0 > r1:
          self._LastTime = r1 + self._randT()
          self._1s.append(self._LastTime)
        else:
          self._LastTime = r0 + self._randT()
          self._0s.append(self._LastTime)
        if self.CalculateJitter:  
          jstart = self._LastTime + self._T / 2
          if r0 > r1:
            jstart = r1 + self._T
          else:
            jstart = r0 + self._T
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
    """Returns True if a value at given time is catched at Jitter
    """
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
  def sample(self, N : int, Ts : float, t0 = -1) -> BinString:
    """Gets a string of 0|1 values

    Args:
        N (int): how many samples to get
        Ts (float): sampling period
        t0 (int, optional): when to grab the first sample.
            When < 0, then the first sample is grabbed at T_avg/2. 
            Defaults to -1.
        Reset (bool, optional): Whether to reset or not the simulation tables 
            before started sampling. Defaults to False.

    Returns:
        BinString: BinaryString
    """
    if t0 < 0:
      t0 = self._T / 2
    t = t0
    result = BinString(N, 0)
    v = False
    tstamp = 0
    for i in range(N):
      if t <= 0: 
        result.shiftIn(0)
      else:
        while tstamp < t:
          v = not v
          tstamp += self._randT()/2
        if v:
          result.shiftIn(0)
        else:
          result.shiftIn(1)
      t += Ts
    return result
  