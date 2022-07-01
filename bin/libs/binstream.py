from libs.binstr import *
from libs.utils_int import *
from libs.aio import *

class BinStreamIn:
  _myfile = None
  _bit_to_read_from_byte = 7
  _last_byte = None
  _ascii = False
  def __init__(self, BinFileName : str, ASCII = False) -> None:
    self._ascii = ASCII
    self._myfile = open(BinFileName, 'rb')
  def __repr__(self) -> str:
    return f'BinStreamIn({self._myfile.name})'
  def __str__(self) -> str:
    return f'BinStreamIn({self._myfile.name})'
  def getBit(self) -> int:
    if self._ascii:
      while True:
        res = self._myfile.read(1)
        if res:
          if res[0] == 48:
            return 0
          elif res[0] == 49:
            return 1
        else:
          return None       
    else:
      bresult = None  
      if self._last_byte == None:
        res = self._myfile.read(1)
        if res:
          self._last_byte = res[0]
          bresult = Int.getBit(self._last_byte, 7)
          self._bit_to_read_from_byte = 6
      else:
        bresult = Int.getBit(self._last_byte, self._bit_to_read_from_byte)
        if self._bit_to_read_from_byte > 0:
          self._bit_to_read_from_byte -= 1
        else:
          self._last_byte = None
    return bresult
  def getBinString(self, Length : int) -> BinString:
    Num = 0
    for i in range(Length):
      r = self.getBit()
      if r == None:
        return None
      Num = (Num << 1) | r
    return BinString(Length, Num)
  
class BinStreamOut:
  _myfilename = None
  _my_bsb = None
  def __init__(self, BinFileName : str, AppendToFile = False, ASCII = False) -> None:
    self._ascii = ASCII
    self._myfilename = BinFileName
    self._my_bsb = BinStringBytes(BinFileName, AppendToFile, ASCII)
  def __repr__(self) -> str:
    return f'BinStreamOut({self._myfilename})'
  def __str__(self) -> str:
    return f'BinStreamOut({self._myfilename})'
  def append(self, BitOrBinString):
    if Aio.isType(BitOrBinString, "BinString"):
      val = BitOrBinString
    elif Aio.isType(BitOrBinString, "int"):
      val = BinString(1, BitOrBinString)
    else:
      val = BinString(str(BitOrBinString))
    self._my_bsb.append(val)
  def closeFile(self):
    self._my_bsb.closeFile()