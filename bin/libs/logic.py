
class LogicValue:
  pass
class LogicValue:
  _val = False
  _mask = True
  def __init__(self, Value) -> None:
    self.setValue(Value)
  def __bool__(self) -> bool:
    if not self._mask and self._val:
      return True
    return False
  def __repr__(self) -> str:
    return "LogicValue(" + str(self) + ")"
  def __str__(self) -> str:
    return self.getValue()
  def __not__(self) -> LogicValue:
    if self._mask:
      return LogicValue("X")
    if self._val:
      return LogicValue(0)
    return LogicValue(1)
  def __or__(self,other) -> LogicValue:
    if self._mask and other._mask:
      return LogicValue("X")
    if (self._val and not self._mask) or (other._val and not other._mask):
      return LogicValue(1)
    if self._mask or other._mask:
      return LogicValue("X")
    return LogicValue(0)
  def __and__(self,other) -> LogicValue:
    if self._mask and other._mask:
      return LogicValue("X")
    if (not self._val and not self._mask) or (not other._val and not other._mask):
      return LogicValue(0)
    if self._mask or other._mask:
      return LogicValue("X")
    return LogicValue(1)
  def __xor__(self,other) -> LogicValue:
    if self._mask or other._mask:
      return LogicValue("X")
    if self._val == other._val:
      return LogicValue(0)
    return LogicValue(1)
  def setValue(self,Value) -> None:
    if str(Value) == "0" or Value == False:
      self._val = False
      self._mask = False
    elif str(Value) == "1" or Value == True:
      self._val = True
      self._mask = False
    else:
      self._val = False
      self._mask = True
  def getValue(self) -> str:
    if self._mask:
      return "X"
    if self._val:
      return "1"
    return "0"
  
class LogicElement:
  pass
class LogicElement:
  _inputs = []
  _output = LogicValue("X")
  _type = "Unknown"
  def __str__(self) -> str:
    return str(self._output)
  def __repr__(self) -> str:
    return "LogicElement(\"" + self._type + "\")"
  def addInput(self, Element : LogicElement) -> None:
    self._inputs.append(Element)
  def getInputs(self):
    return self._inputs
  def _backwardUpdate(self) -> None:
    for input in self._inputs:
      input.update()
  # Overload the update(self) method!!
  def update(self) -> LogicValue:
    pass
  
  
class LogicInput(LogicElement):
  def __init__(self, Value = LogicValue("X")) -> None:
    self._type = "PRIMARY_INPUT"
    self._output = Value
  def update(self) -> LogicValue:
    return self._output
  def getValue(self) -> LogicValue:
    return self._output
  def setValue(self, Value : LogicValue) -> None:
    self._output = Value
  
class LogicGateNot(LogicElement):
  _input : LogicElement
  def __init__(self, Input = None) -> None:
    self._type = "GATE_NOT"
    if "logic.Logic" in str(type(Input)):
      self._input = Input
  def addInput(self, Element : LogicElement) -> None:
    self._input = Element
  def update(self) -> LogicValue:
    self._input._backwardUpdate()
    result = ~self._input._output
    self._output = result
    return result
  
class LogicGateOr(LogicElement):
  def __init__(self, Inputs : list) -> None:
    self._type = "GATE_OR"
    for input in Inputs:
      self.addInput(input)
  def update(self) -> LogicValue:
    self._backwardUpdate()
    result = LogicValue(0)
    for input in self._inputs:
      result |= input._output
    self._output = result
    return result
  
class LogicGateNor(LogicElement):
  def __init__(self, Inputs : list) -> None:
    self._type = "GATE_NOR"
    for input in Inputs:
      self.addInput(input)
  def update(self) -> LogicValue:
    self._backwardUpdate()
    result = LogicValue(0)
    for input in self._inputs:
      result |= input._output
    result = ~result
    self._output = result
    return result
  
class LogicGateAnd(LogicElement):
  def __init__(self, Inputs : list) -> None:
    self._type = "GATE_AND"
    for input in Inputs:
      self.addInput(input)
  def update(self) -> LogicValue:
    self._backwardUpdate()
    result = LogicValue(1)
    for input in self._inputs:
      result &= input._output
    self._output = result
    return result
  
class LogicGateNand(LogicElement):
  def __init__(self, Inputs : list) -> None:
    self._type = "GATE_NAND"
    for input in Inputs:
      self.addInput(input)
  def update(self) -> LogicValue:
    self._backwardUpdate()
    result = LogicValue(1)
    for input in self._inputs:
      result &= input._output
    result = ~result
    self._output = result
    return result
  
class LogicGateXor(LogicElement):
  def __init__(self, Inputs : list) -> None:
    self._type = "GATE_XOR"
    for input in Inputs:
      self.addInput(input)
  def update(self) -> LogicValue:
    self._backwardUpdate()
    result = LogicValue(0)
    for input in self._inputs:
      result ^= input._output
    self._output = result
    return result
  
class LogicGateXnor(LogicElement):
  def __init__(self, Inputs : list) -> None:
    self._type = "GATE_XNOR"
    for input in Inputs:
      self.addInput(input)
  def update(self) -> LogicValue:
    self._backwardUpdate()
    result = LogicValue(0)
    for input in self._inputs:
      result ^= input._output
    result = ~result
    self._output = result
    return result