from libs.utils_int import *

class Generators:
  _enabled = 1
  def enable():
    Generators._enabled = 1
  def disable():
    Generators._enabled = 0
    
  def primes(start : int, stop : int):
    v = start - 1
    v = Int.nextPrime(v)
    while v < stop and Generators._enabled:
      yield v
      v = Int.nextPrime(v)
      
  def range(start : int, stop : int, step = 1):
    val = start
    while val < stop and Generators._enabled:  
      yield val
      val += step 
      
  def subRanges(start : int, stop : int, chunk : int, step = 1):
    StartIt = start
    RangeIt = chunk * step
    Break = 0
    while Generators._enabled:      
      StopIt = StartIt + RangeIt
      if StopIt > stop:
        StopIt = stop
        Break = 1
      yield range(StartIt, StopIt, step)
      #yield Generators.range(StartIt, StopIt, step)
      if Break:
        break
      StartIt = StopIt
      
  def wrapper(iterator):
    for x in iterator:
      if not Generators._enabled:
        break
      yield x