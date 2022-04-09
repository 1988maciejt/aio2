import re

class Int:

  def fromString(num : str, base = 10) -> int:
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