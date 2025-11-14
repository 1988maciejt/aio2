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
      
  def allPermutationsForm2lists(self, List1 : list, List2 : list):
    global _PAUSE
    for i1 in List1:
      for i2 in List2:
        if not self._enabled:
          return
        yield (i1, i2)
        while _PAUSE:
          sleep(0.35)
          
  def onesInHex(self, Hex : str):
    global _PAUSE
    try:
      v = int(Hex, 16)
    except:
      return
    b = bau.int2ba(v, endian='little')
    for i in b.search(1):
      if not self._enabled:
        return
      yield i
      while _PAUSE:
        sleep(0.35)
      
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
      
  def subListsFromGenerator(self, gen, SublistSize : int):
    global _PAUSE
    y = []
    for x in gen:
      if not self._enabled:
        break
      y.append(x)
      if len(y) >= SublistSize:
        yield y
        y = []
      while _PAUSE:
        sleep(0.35)
    if not self._enabled:
      return
    if len(y) > 0:
      yield y
      
  def wrapper(self, iterator):
    global _PAUSE
    for x in iterator:
      if not self._enabled:
        break
      yield x
      while _PAUSE:
        sleep(0.35)
        
  def readFileLineByLine(self, FileName, OnlyLinesRegex : str = None):
    global _PAUSE
    try:
      if type(OnlyLinesRegex) is str:
        with open(FileName, 'r') as file:
          for line in file:
            if not self._enabled:
              break
            if not re.match(OnlyLinesRegex, line):
              continue
            if len(line) > 0 and line[-1] == "\n":
              line = line [:-1]
            yield line
            while _PAUSE:
              sleep(0.35)
      else:
        with open(FileName, 'r') as file:
          for line in file:
            if not self._enabled:
              break
            if len(line) > 0 and line[-1] == "\n":
              line = line [:-1]
            yield line
            while _PAUSE:
              sleep(0.35)
    except:
      pass
      #Aio.printError(f"File {FileName} not found or can't be opened.")
    
      
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
    if type(Word) is str:
      Word = bitarray(Word)
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
        
  def dayAndMonthOfYear(self, Year : int, ReturnAlsoDayOfYear = False):
    global _PAUSE
    from datetime import datetime
    DOY = 1
    for Month in range(1, 13):
      for Day in range(1, 32):
        if not self._enabled:
          return
        if Day > 28:
          try:
            datetime(Year, Month, Day)
          except:
            break
        if ReturnAlsoDayOfYear:
          yield (Month, Day, DOY)
          DOY += 1
        else:
          yield (Month, Day)
        while _PAUSE:
          sleep(0.35)
    
  def divideIntoSubArraysToIterateThroughAllTuples(self, Word : bitarray, TupleSize : int, MaxTuplesCountPerSubArray : int = 1000000) -> list:
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
      
  def floatFor(self, Start : float, Stop : float, Step : float):
    from libs.utils_float import FloatUtils
    global _PAUSE
    StartRounded = FloatUtils.roundToResolution(Start, Step)
    Adder = Start - StartRounded
    CurrentBase = StartRounded
    Current = CurrentBase + Adder
    while Current < Stop:
      if not self._enabled:
        return
      yield Current
      while _PAUSE:
        sleep(0.35)
      CurrentBase = FloatUtils.roundToResolution(CurrentBase + Step, Step)    
      Current = FloatUtils.roundToDecimalPlacesAsInAnotherFloat(CurrentBase + Adder, Step)