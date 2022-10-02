import re
from math import sqrt
from libs.utils_str import *

class Int:
  
  _primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
  def isPrime(value : int) -> bool:
    DMax = int(sqrt(value))+1
    Prime = True
    NM = Int._primes[-1]
    while Int._primes[-1] < DMax:
      NM += 2
      if Int.isPrime(NM):
        Int._primes.append(NM)
    for N in Int._primes:
      if N > DMax:
        break
      if (value % N) == 0:
        Prime = False
        break
    return Prime
  
  def shiftLeft(value : int, bitsize : int, steps=1) -> int:
    if (steps < 0):
      return Int.shiftRight(value, bitsize, -steps)
    clr = (1 << bitsize) - 1
    return (value << steps) & clr
  
  def shiftRight(value : int, bitsize : int, steps=1) -> int:
    if (steps < 0):
      return Int.shiftLeft(value, bitsize, -steps)
    return value >> steps

  def rotateLeft(value : int, bitsize : int, steps=1) -> int:
    if (steps < 0):
      return Int.rotateRight(value, bitsize, -steps)
    v = value
    mask = (1 << (bitsize-1))
    clr = (mask << 1) - 1
    for i in range(steps):
      b = v & mask
      v <<= 1
      if (b != 0):
        v |= 1
        v &= clr
    return v
        
  def rotateRight(value : int, bitsize : int, steps=1) -> int:
    if (steps < 0):
      return Int.rotateLeft(value, bitsize, -steps)
    v = value
    bit = (1 << (bitsize-1))
    for i in range(steps):
      b = v & 1
      v >>= 1
      if (b != 0):
        v |= bit
    return v

  def fromString(num : str, base = 10) -> int:
    pattern = r'([⁰¹²³⁴⁵⁶⁷⁸⁹]+)'
    sub = r'(\1)'
    num = re.sub(pattern, sub, num)
    num = Str.fromSuperScript(num)
    pattern = r'(\S)\(([0-9]+)\)'
    while True:
      r = re.search(pattern, num)
      if r:
        s = r.group(1)*int(r.group(2))
        num = re.sub(pattern, s, num, count=1)
      else:
        break
    return int(num, base)

  def parityOf(int_type : int) -> int:
    parity = 0
    while (int_type):
      parity = 1 - parity
      int_type = int_type & (int_type - 1)
    return(parity)

  def mersenne(index : int) -> int:
    return ((1 << index) - 1)

  def getBit(Value : int, BitIndex : int) -> int:
    return ((Value >> BitIndex) & 1)
  
  def setBit(Value : int, BitIndex : int, BitValue = 1) -> int:
    if BitValue != 0:
      Value = Value | (1 << BitIndex)
    else:
      Mask = (Value ^ ~Value ^ (1 << BitIndex))
      Value = Value & Mask
    return Value
  
  def resetBit(Value : int, BitIndex : int) -> int:
    return Int.setBit(Value, BitIndex, 0)
  
  def toggleBit(Value : int, BitIndex : int) -> int:
    bit = 1 << BitIndex
    return Value ^ bit