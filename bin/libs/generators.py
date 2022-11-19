from libs.utils_int import *

class Generators:
  __slots__ = ("_enabled")
  def __init__(self):
    self._enabled = 11
  def enable(self):
    self._enabled = 1
  def disable(self):
    self._enabled = 0
    
  def primes(self, start : int, stop : int):
    v = start - 1
    v = Int.nextPrime(v)
    while v < stop and self._enabled:
      yield v
      v = Int.nextPrime(v)
      
  def range(self, start : int, stop : int, step = 1):
    val = start
    while val < stop and self._enabled:  
      yield val
      val += step 
      
  def subRanges(self, start : int, stop : int, chunk : int, step = 1):
    StartIt = start
    RangeIt = chunk * step
    Break = 0
    while self._enabled:      
      StopIt = StartIt + RangeIt
      if StopIt > stop:
        StopIt = stop
        Break = 1
      yield range(StartIt, StopIt, step)
      if Break:
        break
      StartIt = StopIt
      
  def wrapper(self, iterator):
    for x in iterator:
      if not self._enabled:
        break
      yield x