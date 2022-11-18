from libs.utils_int import *

class Generators:
  _enabled = 1
  _stop = 0
  def enable():
    Generators._enabled = 1
    Generators._stop = 0
  def disable():
    Generators._enabled = 0
    Generators._stop = 0
  def stop():
    Generators._enabled = 0
    Generators._stop = 1
    
  def primes(start : int, stop : int):
    v = start - 1
    v = Int.nextPrime(v)
    while v < stop and Generators._enabled:
      yield v
      v = Int.nextPrime(v)
    if Generators._stop:
      Generators._stop = 0
      Generators._enabled = 1
      
  def range(start : int, stop : int, step = 1):
    val = start
    while val < stop and Generators._enabled:  
      yield val
      val += step
    if Generators._stop:
      Generators._stop = 0
      Generators._enabled = 1      
      
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
      if Break:
        break
      StartIt = StopIt
    if Generators._stop:
      Generators._stop = 0
      Generators._enabled = 1
      
  def wrapper(iterator):
    for x in iterator:
      if not Generators._enabled:
        break
      yield x
    if Generators._stop:
      Generators._stop = 0
      Generators._enabled = 1