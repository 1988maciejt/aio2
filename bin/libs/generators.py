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
      
  def subLists(self, lst : list, SublistSize : int):
    for i in range(0, len(lst), SublistSize):
      if not self._enabled:
        break
      yield lst[i:(i+SublistSize)]
      
  def wrapper(self, iterator):
    for x in iterator:
      if not self._enabled:
        break
      yield x
      
  def subListsFromIterator(self, Iterator, ChunkSize : int):
    Result = []
    for I in Iterator:
      if not self._enabled:
        return
      Result.append(I)
      if len(Result) >= ChunkSize:
        yield Result
        Result = []
    if len(Result) > 0:
      yield Result