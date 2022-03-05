import math
from pickle import NONE
import re


class CAS:
  pass
class CASObject:
  pass
class CASValue(CASObject):
  pass
class CASFunction(CASObject):
  pass


class CASObject:
  _mycas = NONE
  def __str__(self) -> str:
    return str(self.eval())
  def __repr__(self) -> str:
    return "CASObject('" + str(self) + "')"
  def __bool__(self) -> bool:
    return True
  def eval(self) -> CASValue:
    pass
  def isNumber(self) -> bool:
    pass
  
  
class CASValue(CASObject):
  _value = 0
  def __init__(self, Value = 0, Cas = NONE) -> None:
    self._value = Value
  def __str__(self) -> str:
    return str(self._value)
  def eval(self) -> CASValue:
    if self._mycas != NONE:
      if not self.isNumber():
        if self._mycas.Variables.exists(self._value):
          return CASValue(self._mycas.Variables.recall(self._value))
    return self
  def isFloat(self) -> bool:
    try:
      x = float(self._value)
    except:
      return False
    return True
  def toFloat(self) -> float:
    return float(self._value)
  def isInt(self) -> bool:
    try:
      x = int(self._value)
    except:
      return False
    return True
  def toInt(self) -> int:
    return int(self._value)
  def isNumber(self) -> bool:
    return self.isInt() or self.isFloat()
  def value(self):
    return self._value
    
    
  
class CASFunction(CASObject):
  _fargs = []
  _fname = ""
  def __init__(self, FName : str, FArgs = [], Cas = NONE) -> None:
    if not isinstance(FArgs, (list)):
      if isinstance(FArgs, (CASObject)):
        self._fargs = [ FArgs ]
      else:
        self._fargs = [ CASValue(FArgs, self._mycas) ]
    else:
      for a in FArgs:
        if isinstance(a, (CASObject)):
          self._fargs.append(a)
        else:
          self._fargs.append(CASValue(a, self._mycas))
    self._fname = FName
  def eval(self) -> CASValue:
    eargs = []
    for a in self._fargs:
      eargs.append(a.eval())
    if self._fname == "sin" and eargs[0].isFloat():
      return CASValue(math.sin(eargs[0].toFloat()), self._mycas)
    elif self._fname == "cos" and eargs[0].isFloat():
      return CASValue(math.cos(eargs[0].toFloat()), self._mycas)
    else:
      sargs = ""
      NotFirst = False
      for ea in eargs:
        if NotFirst:
          sargs += ","
        else:
          NotFirst = True
        sargs += str(ea)
      string = self._fname + "(" + sargs + ")"
      return CASValue(string, self._mycas)
      
        
class CASOperator(CASObject):
  _argl : CASObject
  _argr : CASObject
  _oname = ""
  def __init__(self, Operator : str, LeftArg : CASObject, RightArg : CASObject, Cas = NONE) -> None:
    if isinstance(LeftArg, (CASObject)):
      self._argl = LeftArg
    else:
      self._argl = CASValue(LeftArg, self._mycas)
    if isinstance(RightArg, (CASObject)):
      self._argr = RightArg
    else:
      self._argr = CASValue(RightArg, self._mycas)
    self._oname = Operator
  def eval(self) -> CASValue:
    vl = self._argl.eval()
    vr = self._argr.eval()
    if vl.isFloat() and vr.isFloat():
      if self._oname == "+":
        return CASValue(vl.toFloat() + vr.toFloat(), self._mycas)
      if self._oname == "-":
        return CASValue(vl.toFloat() - vr.toFloat(), self._mycas)
      if self._oname == "*":
        return CASValue(vl.toFloat() * vr.toFloat(), self._mycas)
      if self._oname == "/":
        return CASValue(vl.toFloat() / vr.toFloat(), self._mycas)
      if self._oname == "mod":
        return CASValue(vl.toFloat() % vr.toFloat(), self._mycas)
    n = self._oname
    if n == "mod":
      n = " mod "
    return CASValue("(" + str(vl) + n + str(vr) + ")")
  

class CASVariables:
  _dict = {}
  def __str__(self) -> str:
    return str(self._dict)
  def __repr__(self) -> str:
    return "CASVariables(" + ")"
  def store(self, Name : str, Value) -> None:
    self._dict[Name] = Value
  def recall(self, Name : str):
    try:
      return self._dict[Name]
    except:
      return False
  def remove(self, Name : str) -> None:
    try:
      del self._dict[Name]
    except:
      pass
  def clearAll(self) -> None:
    self._dict.clear()
  def exists(self, Name : str) -> bool:
    try:
      aux = self._dict[Name]
      return True
    except:
      return False
  def list(self, RegexPattern = "") -> list:
    result = []
    for k in self._dict.keys():
      if re.match(RegexPattern, k):
        result.append(k)
    return result
    
    
class CAS:
  _variables = CASVariables()
  _casobjects = list
  def Variables(self) -> CASVariables:
    return self._variables
  def addObject(self, object : CASObject) -> None:
    self._casobjects.append(object)
  def Objects(self) -> list:
    return self._casobjects
  def addFromString(self, string) -> CASObject:
    pass
  # create parser!
  
