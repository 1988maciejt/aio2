from libs.utils_int import *
from libs.utils_str import *
from libs.utils_list import *
from collections import Counter
from math import ceil
import multiprocessing

class BinString:
  pass
class BinString:
  BitCount = 64
  _val = 0
  def merge(BinStringsList : list) -> BinString:
    BSLLen = len(BinStringsList)
    if BSLLen > 0:
      res_size = BinStringsList[0].BitCount
      res_val = BinStringsList[0]._val
      for i in range(1, BSLLen):
        ilen = BinStringsList[i].BitCount
        ival = BinStringsList[i]._val
        res_size += ilen
        res_val = ((res_val << ilen) | ival)
      return BinString(res_size, res_val)
    else:
      return BinString(1, 0)
  def fromList(BitCount=64, Data=[]) -> list:
    result = []
    for d in Data:
      result.append(BinString(BitCount, d))
    return result
  def __init__(self, BitCount = 64, Value = 0) -> None:
    if type("") == type(BitCount):
      Value = BitCount
      BitCount = len(BitCount)
    self.BitCount = BitCount
    self.setValue(Value)
  def __hash__(self) -> int:
    return ((1 << self.BitCount) - 1) & self._val
  def __bytes__(self):
    return self.toBytes()
  def __int__(self):
    msk = (1 << self.BitCount) - 1
    return self._val * msk
  def __str__(self) -> str:
    r = ""
    v = self._val
    for i in range(self.BitCount):
      if v & 1:
        r = "1" + r
      else:
        r = "0" + r
      v >>= 1
    return r
  def toBytes(self) -> bytes:
    BytesCount = ceil(self.BitCount / 8)
    msk = (1 << self.BitCount) - 1
    rlist = [0 for i in range(BytesCount)]
    val = self._val & msk
    for i in range(BytesCount-1,-1,-1):
      rlist[i] = val & 255
      val >>= 8
    return bytes(rlist)
  def toHexString(self, shorten=False, Superscripts=True):
    msk = (1 << self.BitCount) - 1
    val = self._val & msk
    s = hex(val)[2:].upper()
    if shorten:
      r = ""
      last = ""
      cntr = 0
      for c in s:
        cntr += 1
        if c != last:
          if cntr > 1:
            if Superscripts:
              r += last + Str.toSuperScript(cntr) 
            else:
              r += last + "(" + str(cntr) + ")"
          else:
            r += last
          cntr = 0
        last = c      
      if cntr > 0:
        if Superscripts:
          r += last + Str.toSuperScript(cntr+1) 
        else:
          r += last + "(" + str(cntr+1) + ")"
      else:
        r += last
      return r
    else:
      return s
  def __repr__(self) -> str:
    return "BinString(" + self.__str__() + ")"
  def __getitem__(self, Index) -> int:
    return Int.getBit(self._val, Index)
  def __setitem__(self, Index, Value) -> int:
    self._val = Int.setBit(self._val, Index, Value)
  def __len__(self) -> int:
    return self.BitCount
  def __assign__(self, other):
    self._val = other._val
  def setValue(self, Value):
    stype = str(type(Value))
    if "int" in stype:
      self._val = Value
    if "str" in stype:
      self._val = 0
      for c in Value:
        self._val <<= 1
        if c == "1":
          self._val |= 1
  def getValue(self):
    msk = (1 << self.BitCount) - 1
    return self._val & msk
  def setBit(self, Index : int, BitValue = 1):
    self._val = Int.setBit(self._val, Index, BitValue)
  def resetBit(self, Index : int):
    self._val = Int.resetBit(self._val, Index)
  def getBit(self, Index : int) -> int:
    return Int.getBit(self._val, Index)
  def copy(self):
    return BinString(self.BitCount, self._val)
  def shiftIn(self, BitValue : int, MSB=True):
    if MSB:
      self._val >>= 1
      self._val = Int.setBit(self._val, self.BitCount-1, BitValue)
    else:
      self._val <<= 1
      self._val += BitValue
    return self
  def shiftOut(self, LSB=True):
    if LSB:
      bit = self._val & 1
      self._val >>= 1
      return bit
    else:
      bit = self.getBit(self.BitCount - 1)
      self._val <<= 1
      return bit
  def onesCount(self):
    cntr = 0
    msk = (1 << self.BitCount) - 1
    num = self._val & msk
    while num > 0:
      cntr += 1
      num = num & (num - 1)
    return cntr
  def zerosCount(self):
    return self.BitCount - self.onesCount()
  def parity(self):
    return self.onesCount() & 1
  def getReversed(self):
    BSNew = self.copy()
    aux = self.copy()
    for _ in range(self.BitCount):
      BSNew.shiftIn(aux.shiftOut(), False)
    return BSNew
  def split(self, BusesList : list) -> list:
    """aplit 

    Args:
        BusesList (list): list of bus sizes.
        
    Example:
      BinString(64, 0xFF00FFFF).split([8,8,16])
      -> [BinString(8,0xFF), BinString(8,0x00), BinString(16,0xFFFF)]
    """
    buses = BusesList.copy()
    buses.reverse()
    result = []
    LsbIndex = 0
    for bus in buses:
      mask = ((1<<bus) - 1) << LsbIndex
      val = (self._val & mask) >> LsbIndex
      result.append(BinString(bus, val))
      LsbIndex += bus
    result.reverse()
    return result
  def __iter__(self):
    self._ii = 0
    return self
  def __next__(self):
    if self._ii < self.BitCount:
      b = Int.getBit(self._val, self._ii)
      self._ii += 1
      return b
    raise StopIteration
  def __add__(self, other):
    new = self.copy()
    new._val += other.getValue()
    return new
  def __sub__(self, other):
    new = self.copy()
    new._val -= other.getValue()
    return new
  def __mul__(self, other):
    new = self.copy()
    new._val *= other.getValue()
    return new
  def __truediv__(self, other):
    new = self.copy()
    new._val /= other.getValue()
    return new
  def __floordiv__(self, other):
    new = self.copy()
    new._val //= other.getValue()
    return new
  def __mod__(self, other):
    new = self.copy()
    new._val %= other.getValue()
    return new
  def __rshift__(self, other):
    new = self.copy()
    new._val >>= other
    return new
  def __lshift__(self, other):
    new = self.copy()
    new._val <<= other
    return new
  def __and__(self, other):
    new = self.copy()
    new._val &= other.getValue()
    return new
  def __or__(self, other):
    new = self.copy()
    new._val |= other.getValue()
    return new
  def __xor__(self, other):
    new = self.copy()
    new._val ^= other.getValue()
    return new
  def __lt__(self, other):
    return (self.getValue() < other.getValue())
  def __gt__(self, other):
    return (self.getValue() > other.getValue())
  def __le__(self, other):
    return (self.getValue() <= other.getValue())
  def __ge__(self, other):
    return (self.getValue() >= other.getValue())
  def __eq__(self, other):
    if type(other) == type(None):
      return False
    return (self.getValue() == other.getValue())
  def __ne__(self, other):
    if type(other) == type(None):
      return True
    return (self.getValue() != other.getValue())
  def __iadd__(self, other):
    self._val += other.getValue()
    return self
  def __isub__(self, other):
    self._val -= other.getValue()
    return self
  def __imul__(self, other):
    self._val *= other.getValue()
    return self
  def __idiv__(self, other):
    self._val /= other.getValue()
    return self
  def __ifloordiv__(self, other):
    self._val //= other.getValue()
    return self
  def __imod__(self, other):
    self._val %= other.getValue()
    return self
  def __irshift__(self, other):
    self._val >>= other
    return self
  def __ilshift__(self, other):
    self._val <<= other
    return self
  def __iand__(self, other):
    self._val &= other.getValue()
    return self
  def __ior__(self, other):
    self._val |= other.getValue()
    return self
  def __ixor__(self, other):
    self._val ^= other.getValue()
    return self
  def __neg__(self):
    new = self.copy()
    new._val = (1 << new.BitCount) - new._val 
    return new
  def __pos__(self):
    return self.copy()
  def __invert__(self):
    new = self.copy()
    new._val = (1 << new.BitCount) - new._val 
    return new
  
class BinStringList:
  def onesCount(BinStringList : list) -> int:
    pool = multiprocessing.Pool()
    partial = pool.map(BinString.onesCount, BinStringList)
    pool.close()
    pool.join()
    result = 0
    for s1 in partial:
      result += s1
    return result
  def split(BinStringList : list, BusesList : list) -> list:
    buses = len(BusesList)
    result = [ [] for i in range(buses)]
    for b in BinStringList:
      bsp = b.split(BusesList)
      for i in range(buses):
        result[i].append(bsp[i])
    return result
  def merge(BinStringsListOfLists : list) -> list:
    result = []
    buses_count = len(BinStringsListOfLists)
    bslen = len(BinStringsListOfLists[0])
    for i in range(bslen):
      row = []
      for j in range(buses_count):
        row.append(BinStringsListOfLists[j][i])
      result.append(BinString.merge(row))
    return result  
  def toBytes(lst : list) -> bytes:
    BytesResult = bytes(0)
    IntResult = 0
    BitCount = 0
    for item in lst:
      BitCount += item.BitCount
      IntResult <<= item.BitCount
      IntResult += item._val
      if BitCount > 500:
        if BitCount & 0b111 == 0:
          BytesResult += BinString(BitCount, IntResult).toBytes()
          IntResult = 0
          BitCount = 0
    if BitCount > 0:
      Rest = 8 - (BitCount % 8)
      BitCount += Rest
      IntResult <<= Rest
      BytesResult += BinString(BitCount, IntResult).toBytes()
    return BytesResult
	
class BinStringBytes:
  _flushed_len = 0
  _length = 0
  _bytes_table = bytes(0)
  _rest_val = 0
  _rest_len = 0
  _file = None
  def __init__(self, FileName = None, AppendToFile = False):
    if FileName != None:
      self.openFile(FileName, AppendToFile)
  def __str__(self) -> str:
    return str(self.toBytes())
  def __repr__(self) -> str:
    return "BinStringBytes(" + self.__str__() + ")"
  def __len__(self) -> int:
    return self._length + self._flushed_len
  def __bytes__(self):
    return self.toBytes()
  def openFile(self, FileName, AppendToFile = False):
    if AppendToFile:
      self._file = open(FileName, 'ab')
    else:
      self._file = open(FileName, 'wb')
  def closeFile(self):
    if self._file != None:
      self._file.write(self.toBytes())
      self._file.close()
      self._file = None
  def append(self, Value : BinString):
    self._rest_len += Value.BitCount
    self._rest_val <<= Value.BitCount
    self._rest_val |= Value._val
    if self._rest_len > 1000:
      if self._rest_len & 0b111 == 0:
        self._bytes_table += BinString(self._rest_len, self._rest_val).toBytes()
        self._rest_len = 0
        self._rest_val = 0
    if self._file != None:
      if len(self._bytes_table) >= 1024:
        self._file.write(self._bytes_table)
        self._flushed_len += len(self._bytes_table)
        self._bytes_table = bytes(0)
  def toBytes(self) -> bytes:
    BRes = self._bytes_table
    if self._rest_len > 0:
      Rest = 8 - (self._rest_len % 8)
      Val = self._rest_val << Rest
      BRes += BinString(Rest+self._rest_len, Val).toBytes()
    return BRes