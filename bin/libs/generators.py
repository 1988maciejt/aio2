from libs.utils_int import *
from libs.utils_bitarray import *
from bitarray import *
import bitarray.util as bau
from libs.utils_bitarray import *
from time import sleep
import random

_PAUSE = 0

def generatorsPaused() -> bool:
  global _PAUSE
  return True if _PAUSE else False

def pauseGenerators(State = False):
  global _PAUSE
  _PAUSE = 1 if State else 0

class Generators:
  __slots__ = ("_enabled")
  def __init__(self):
    self._enabled = 11
  def enable(self):
    self._enabled = 1
  def disable(self):
    self._enabled = 0
    
  def primes(self, start : int, stop : int):
    global _PAUSE
    v = start - 1
    v = Int.nextPrime(v)
    while v < stop and self._enabled:
      yield v
      while _PAUSE:
        sleep(0.35)
      v = Int.nextPrime(v)
      
  def range(self, start : int, stop : int, step = 1):
    global _PAUSE
    val = start
    while val < stop and self._enabled:  
      yield val
      while _PAUSE:
        sleep(0.35)
      val += step 
      
  def subRanges(self, start : int, stop : int, chunk : int, step = 1):
    global _PAUSE
    StartIt = start
    RangeIt = chunk * step
    Break = 0
    while self._enabled:      
      StopIt = StartIt + RangeIt
      if StopIt > stop:
        StopIt = stop
        Break = 1
      yield range(StartIt, StopIt, step)
      while _PAUSE:
        sleep(0.35)
      if Break:
        break
      StartIt = StopIt
      
  def subLists(self, lst : list, SublistSize : int):
    global _PAUSE
    for i in range(0, len(lst), SublistSize):
      if not self._enabled:
        break
      yield lst[i:(i+SublistSize)]
      while _PAUSE:
        sleep(0.35)
      
  def wrapper(self, iterator):
    global _PAUSE
    for x in iterator:
      if not self._enabled:
        break
      yield x
      while _PAUSE:
        sleep(0.35)
      
  def subListsFromIterator(self, Iterator, ChunkSize : int):
    global _PAUSE
    Result = []
    for I in Iterator:
      if not self._enabled:
        return
      Result.append(I)
      if len(Result) >= ChunkSize:
        yield Result
        while _PAUSE:
          sleep(0.35)
        Result = []
    if len(Result) > 0:
      yield Result
      while _PAUSE:
        sleep(0.35)
      
  def allBitarraySequences(self, Length, Endiannes='big'):
    global _PAUSE
    for i in range (1 << Length):
      if not self._enabled:
        return
      yield bau.int2ba(i, length=Length, endian=Endiannes)
      while _PAUSE:
        sleep(0.35)
      
  def randBitarray(self, Size : int, Count : int):
    global _PAUSE
    for i in range(Count):
      if not self._enabled:
        return
      #yield Bitarray.rand(Size)
      yield bau.urandom(Size)
      while _PAUSE:
        sleep(0.35)
      
  def flippedBitInBitarray(self, Word : bitarray):
    global _PAUSE
    Len = len(Word)
    for i in range(Len):
      if not self._enabled:
        return
      Result = Word.copy()
      Result[i] ^= 1
      yield Result
      while _PAUSE:
        sleep(0.35)
        
  def randomlyOrdered(self, lst):
    global _PAUSE
    if Aio.isType(lst, []):
      L = lst.copy()
    else:
      L = [i for i in lst]
    RandUp = len(L)-1
    for i in range(len(L)):
      if not self._enabled:
        return
      R = random.randint(i, RandUp)
      yield L[R]
      if R != i:
        L[R] = L[i]
      while _PAUSE:
        sleep(0.35)
        
        
    
    def divideIntoSubArraysToIterateThroughAllTuples(Word : bitarray, TupleSize : int, MaxTuplesCountPerSubArray : int = 1000000) -> list:
      global _PAUSE
      W = Word.copy()
      W += W[:(TupleSize-1)]
      BlockSize = MaxTuplesCountPerSubArray + TupleSize - 1
      Start = 0
      Stop = BlockSize
      All = 0
      while Stop <= len(W):
        if not self._enabled:
          return
        yield W[Start:Stop]
        if (Stop == len(W)):
            All = 1
        Start += MaxTuplesCountPerSubArray
        Stop += MaxTuplesCountPerSubArray
        while _PAUSE:
          sleep(0.35)
      if not All:
        if not self._enabled:
          return
        yield W[Start:]
      W.clear()
    
    