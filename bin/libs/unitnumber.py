from __future__ import unicode_literals
from libs.eseries import *
import enum

UnitsTriangles = [
    ("V", "Ohm", "A"),
    ("W", "A", "V"),
    ("1", "s", "Hz")
  ]

class Unit:
  pass

def lookMulInUnitsTriangles(U1 : Unit, U2 : Unit) -> Unit:
  for s in UnitsTriangles:
    upper = s[0]
    lower1 = s[1]
    lower2 = s[2]
    if U1.get() == lower1 and U2.get() == lower2:
      return Unit(upper)
    elif U1.get() == lower2 and U2.get() == lower1:
      return Unit(upper)
  return Unit(U1.get() + "*" + U2.get())


def lookDivInUnitsTriangles(U1 : Unit, U2 : Unit) -> Unit:
  for s in UnitsTriangles:
    upper = s[0]
    lower1 = s[1]
    lower2 = s[2]
    if U1.get() == upper:
      if U2.get() == lower1:
        return Unit(lower2)
      elif U2.get() == lower2:
        return Unit(lower1)
  return Unit(U1.get() + "/" + U2.get())
  

class Unit:
  _unit = ""
  def __init__(self, UnitValue = "") -> None:
    self.set(UnitValue)
  def __bool__(self) -> bool:
    return (len(self._unit) > 0)
  def __str__(self) -> str:
    return self.get()
  def __repr__(self) -> str:
    return "Unit('" + self.get() + "')"
  def get(self) -> str:
    if self:
      return self._unit
    return "1"
  def set(self, UnitValue : str) -> None:
    if UnitValue == "1":
      self._unit = ""
    else:
      self._unit = UnitValue
  def __add__(self, other : Unit) -> Unit:
    if self._unit != other._unit:
      raise TypeError("Inconsistents units. Cannot add " + str(self._unit) + " to " + str(other._unit) + ".")
    return Unit(self._unit)
  def __sub__(self, other : Unit) -> Unit:
    if self._unit != other._unit:
      raise TypeError("Inconsistents units. Cannot subtract " + str(self._unit) + " and " + str(other._unit) + ".")
    return Unit(self._unit)
  def __mul__(self, other : Unit) -> Unit:
    return lookMulInUnitsTriangles(self, other)
  def __truediv__(self, other : Unit) -> Unit:
    return lookDivInUnitsTriangles(self, other)
  def __eq__(self, other : Unit) -> bool:
    return (self._unit == other._unit)
  def __ne__(self, other : Unit) -> bool:
    return (self._unit != other._unit)
  
      
  
class UnitNumber:
  pass
class UnitNumber:
  _mantissa = 0.0
  _unit = Unit()
  _prefix = ""
  _exponent = 0
  _fpd = 2
  def __bool__(self) -> bool:
    if self._mantissa == 0.0 and self._exponent == 0 and len(self._unit) == 0:
      return False
    return True 
  def __init__(self, Value, UnitValue = "", FractionPartDigits = 2) -> None:
    self._fpd = FractionPartDigits
    if isinstance(Value, (str)):
      self.fromString(Value)
      if isinstance(UnitValue, (int)):
        self._fpd = UnitValue
    else:
      if isinstance(UnitValue, (Unit)):
        self._unit = UnitValue
      else:
        self._unit = Unit(UnitValue)
      self.setNumber(Value)
  def __str__(self) -> str:
    if len(str(self._unit) + self._prefix) > 0:
      return f'{self._mantissa:.{self._fpd}f}_{self._prefix}{str(self._unit)}'
    return f'{self._mantissa:.{self._fpd}f}'
  def __repr__(self) -> str:
    return self.__str__()
  def __eq__(self, other : UnitNumber) -> bool:
    if self.toNumber() == other.toNumber() and self._unit == other._unit:
      return True
    return False
  def __len__(self) -> int:
    return len(str(self))
  def __ne__(self, other : UnitNumber) -> bool:
    return not self.__eq__(other)
  def __neg__(self) -> UnitNumber:
    u = UnitNumber()
    u.setNumber = -self.toNumber()
    u._unit = self._unit
    return u
  def __abs__(self) -> UnitNumber:
    u = UnitNumber()
    u.setNumber = abs(self.toNumber())
    u._unit = self._unit
    return u
  def __gt__(self, other : UnitNumber) -> bool:
    return self.toNumber() > other.toNumber()
  def __ge__(self, other : UnitNumber) -> bool:
    return self.toNumber() >= other.toNumber()
  def __lt__(self, other : UnitNumber) -> bool:
    return self.toNumber() < other.toNumber()
  def __le__(self, other : UnitNumber) -> bool:
    return self.toNumber() <= other.toNumber()
  def fromString(self, Text : str) -> None:
    R = re.search(r'([0-9.]+)_(\S+)', Text)
    n = Text
    u = ""
    e = 1.0
    if R:
      n = R.group(1)
      u = R.group(2)
    else:
      R = re.search(r'([0-9.]+)_', Text)
      if R:
        n = R.group(1)
    if len(u) > 0:
      if u[0] == "k":
        e = 1000
        u = u[1:]
      elif u[0] == "M":
        e = 1000000
        u = u[1:]
      elif u[0] == "G":
        e = 1000000000
        u = u[1:]
      elif u[0] == "T":
        e = 1000000000000
        u = u[1:]
      elif u[0] == "m":
        if (u == "m"):
          e = 1
          u = "m"          
        else:
          e = 0.001
          u = u[1:]
      elif u[0] == "u":
        e = 0.000001
        u = u[1:]
      elif u[0] == "n":
        e = 0.000000001
        u = u[1:]
      elif u[0] == "p":
        e = 0.000000000001
        u = u[1:]
      elif u[0] == "f":
        e = 0.000000000000001
        u = u[1:]
    self.setNumber(float(n) * e)
    self._unit = Unit(u)
  def getUnit(self) -> Unit:
    return self._unit
  def setUnit(self, Unit : Unit) -> None:
    self._unit = Unit
  def getPrefix(self) -> str:
    return self._prefix
  def getNumber(self) -> float:
    return self._num
  def roundUpToEx(self, EIndex = 3) -> UnitNumber:
    return UnitNumber(ESeries.roundUp(self.toNumber(), EIndex), self._unit, self._fpd) 
  def roundDownToEx(self, EIndex = 3) -> UnitNumber:
    return UnitNumber(ESeries.roundDown(self.toNumber(), EIndex), self._unit, self._fpd) 
  def roundToEx(self, EIndex = 3) -> UnitNumber:
    return UnitNumber(ESeries.round(self.toNumber(), EIndex), self._unit, self._fpd)     
  def setNumber(self, Number : float) -> None:
    me = getMantissaExponent(Number)
    self._mantissa = me[0]
    self._exponent = me[1]
    while (self._exponent % 3) != 0:
      self._exponent -= 1
      self._mantissa *= 10
    prefixes = [(12, "T"),
            (9, "G"),
            (6, "M"),
            (3, "k"), 
            (0, ""),
            (-3, "m"),
            (-6, "u"),
            (-9, "n"),
            (-12, "p"),
            (-15, "f")]
    self._prefix = ""
    for p in prefixes:
      val = p[0]
      prefix = p[1]
      if self._exponent == val:
        self._prefix = prefix
  def setFractionPartDigits(self, FractionPartDigits : int) -> None:
    self._fpd = FractionPartDigits
  def toNumber(self) -> float:
    return self._mantissa * (10 ** self._exponent)
  def __add__(self, other : UnitNumber) -> UnitNumber:
    if self._unit != other._unit:
      raise TypeError("Cannot add " + str(self) + " and " + str(other) + ". Invalid units.")
    return UnitNumber(self.toNumber() + other.toNumber(), self._unit, other._fpd) 
  def __sub__(self, other : UnitNumber) -> UnitNumber:
    if self._unit != other._unit:
      raise TypeError("Cannot subtract " + str(self) + " and " + str(other) + ". Invalid units.")
    return UnitNumber(self.toNumber() - other.toNumber(), self._unit, other._fpd)
  def __mul__(self, other) -> UnitNumber:
    if isinstance(other, (float,int)):
      return UnitNumber(self.toNumber() * other, self._unit)
    return UnitNumber(self.toNumber() * other.toNumber(), self._unit * other._unit, other._fpd) 
  def __truediv__(self, other) -> UnitNumber:
    if isinstance(other, (float,int)):
      return UnitNumber(self.toNumber() / other, self._unit)
    return UnitNumber(self.toNumber() / other.toNumber(),  self._unit / other._unit, other._fpd) 
  def __pow__(self, other : UnitNumber) -> UnitNumber:
    if other._unit:
      raise TypeError("Cannot perform Power to the <unit> object")
    return UnitNumber(self.toNumber() ** other.toNumber(), self._unit + "**" + str(other.toNumber()), other._fpd)
  def __hash__(self) -> int:
    return hash((self._unit.get(), self._exponent, self._mantissa))  
  def __getitem__(self, key : int):
    if key == 0:
      return self.toNumber()
    if key == 1:
      return self._unit
    if key == 2:
      return self._fpd
    return None

    
    
      
# short:
class U(UnitNumber):
  """This is the alias for UnitNumber."""
  pass