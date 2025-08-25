from curses.ascii import isprint
import re
from math import sqrt, isqrt
from libs.utils_str import *
from libs.aio import *

class Int:
  
  _primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
  def isPrime(Value : int) -> bool:
    value = abs(Value)
    if value <= 1:
      return False
    if value == 2:
      return True
    DMax = isqrt(value)+1
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
  
  def nextPrime(value : int) -> int:
    if value < 0:
      return -Int.prevPrime(abs(value))
    if value in [0, 1]:
      return 2
    v2 = value + 1
    if not (v2 & 1):
      v2 += 1
    while not Int.isPrime(v2):
      v2 += 2
    return v2
  
  def prevPrime(value : int) -> int:
    if value == 3:
      return 2
    elif value in [1, 2]:
      return -2
    elif value <= 0:
      return -Int.nextPrime(abs(value))
    v2 = value - 1
    if not (v2 & 1):
      v2 -= 1
    while not Int.isPrime(v2):
      v2 -= 2
    return v2
  
  def factorizeRND(Number : int, Verbose : bool = False) -> tuple:
    from math import gcd, isqrt
    from random import randint
    Max = isqrt(Number) + 1
    if Verbose:
      print(f'Input:   {Number}')
      print(f'Max div: {Max}')
    Aux = 1
    while Aux != 0:
      Rnd = randint(3, Max)  #982451653 
      Aux = Number % Rnd
      if Verbose:
        AioShell.removeLastLine()
        print(f'Rnd: {Rnd}, rest: {Aux}')
    Second = Number // Rnd
    if Verbose:
      print(f'{Rnd}, {Second}')
    return Rnd, Second
  
  def factorizeMT1(Number : int, Verbose : bool = False, Start : int = 2) -> tuple:
#    if Number < 10000000000000000:
#      return Int.factorizeRND(Number, Verbose)
    from math import isqrt
    Max = isqrt(Number) + 1
    if Verbose:
      print(f'Input:   {Number}')
    Div1 = Start
    LEN = len(str(Max)) - 10
    if LEN < 0:
      LEN = 0
    from tqdm import tqdm
    with tqdm(total=Max, bar_format="{l_bar}{bar} {percentage:3." + str(LEN) + "f}%") as pbar:
      while (Div1 < Max):
        Div2 = Div1 + 1
        MDiv1 = Number % Div1
        MDiv2 = Number % Div2
        Step = 2
        if Verbose:
          print("==========================================")
          print(f'{Number} mod {Div1} = {MDiv1}')
          print(f'{Number} mod {Div2} = {MDiv2}')
        if MDiv1 == 0:
          if Verbose:
            print(f'{Div1} is a factor')
          return Div1, Number // Div1
        elif MDiv2 == 0:
          if Verbose:
            print(f'{Div2} is a factor')
          return Div2, Number // Div2
        elif MDiv2 > MDiv1:
          #Div1 += 2
          if Verbose:
            print(f"Up")
        elif MDiv1 == MDiv2:
          #Div1 += 2
          if Verbose:
            print(f"Constant")
        else: # MDiv2 < MDiv1:
          if Verbose:
            print(f"Down")
          a = MDiv2 - MDiv1   # only when Div2 = Div1 + 1!!!!
          b = MDiv1 - a * Div1
          if (-b) // a == 0:
            Step = ((-b) // a) - Div1
          else:
            Step = ((-b) // a) - Div1 + 1
          if Verbose:
            print(f"a = {a}, b = {b}")
        Div1 += Step
        pbar.update(Step)
    if Verbose:
      print(f'No factors found for {Number} in range 2..{Max}')
    return None
  
  def primesGenerator(From : int, To : int):
    v = From - 1
    v = Int.nextPrime(v)
    while v <= To:
      yield v
      v = Int.nextPrime(v)
      
  def areRelativelyPrime(Numbers : list) -> bool:
    from libs.utils_list import List
    from math import gcd
    MaxGcd = 0
    for Pair in List.getCombinations(Numbers, 2):
      Gcd = gcd(Pair[0], Pair[1])
      if Gcd > MaxGcd:
        MaxGcd = Gcd
    if MaxGcd > 1:
      return False
    return True
    
  
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

  def iterateFromLsb(Value : int, BitCount : int):
    Mask = 1
    for _ in range(BitCount):
      yield 1 if (Value & Mask) else 0
      Mask <<= 1
      
  def toGray(Value : int) -> int:
    return (Value ^ (Value>>1))
  
  def splitLettersAndInt(Value : str, DefaultStr = "", DefaultInt = 0) -> tuple:
    if Aio.isType(Value, 0):
      return (DefaultStr, Value)
    R = re.search(r'([^0^1^2^3^4^5^6^7^8^9]*)\s*([0-9]*)', str(Value))
    if R:
      s = R.group(1)
      n = R.group(2)
      try:
        n = int(n)
      except:
        n = DefaultInt
      if s == "":
        s = DefaultStr
    return (s, n)
  
  @staticmethod
  def toInt(Value, Default: int = 0) -> int:
    try:
      return int(Value)
    except:
      return Default
    
  @staticmethod
  def hash(Value) -> int:
    return (((Value + 789) * 17) ** 3) + 1000000000000000 % 99999999999973