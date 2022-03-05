import re
from libs.aio import *
from ast import Try, excepthandler
from unicodedata import name


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
  def __invert__(self) -> LogicValue:
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
  Name = "unnamed"
  _inputs = []
  _output = LogicValue("X")
  _type = "Unknown"
  _sequential = False
  def __str__(self) -> str:
    return str(self._output)
  def __repr__(self) -> str:
    return "LogicElement(\"" + self._type + "\")"
  def addInput(self, Element : LogicElement) -> None:
    self._inputs.append(Element)
  def getInputs(self):
    return self._inputs
  # Overload the update(self) method!!
  def update(self) -> LogicValue:
    return self._output
  def isSequential(self) -> bool:
    return self._sequential
  
class LogicFF(LogicElement):
  _input : LogicElement
  _midval = LogicValue("X")
  def __init__(self) -> None:
    super().__init__()
    self._sequential = True
  def __repr__(self) -> str:
    return "LogicFF()"
  def __str__(self) -> str:
    return str(self._output)
  def addInput(self, Element : LogicElement) -> None:
    self._input = Element
  def update(self) -> LogicValue:
    return self._output
  def set(self) -> None:
    self._output = LogicValue(1)
  def reset(self) -> None:
    self._output = LogicValue(0)
  def negedge(self) -> None:
    pass
  def posedge(self) -> None:
    pass
  
class LogicDFF(LogicFF):
  def __init__(self, Name = "unnamed") -> None:
    super().__init__()
    self.Name = Name
    self._type = "DFF"
  def __repr__(self) -> str:
    return "LogicDFF()"
  def __str__(self) -> str:
    return super().__str__()
  def posedge(self) -> None:
    result = LogicValue("X")
    try:
      result = self._input.update()
    except:
      result = LogicValue("X")
    self._midval = result
  def negedge(self) -> None:
    self._output = self._midval

  
class LogicInput(LogicElement):
  def __init__(self, Value = LogicValue("X"), Name = "unnamed") -> None:
    self._type = "INPUT"
    self._output = Value
    self.Name = Name
  def update(self) -> LogicValue:
    return self._output
  def getValue(self) -> LogicValue:
    return self._output
  def setValue(self, Value : LogicValue) -> None:
    self._output = Value
    
class LogicOutput(LogicElement):
  _input = LogicElement()
  def __init__(self, Name = "unnamed") -> None:
    super().__init__()
    self.Name = Name
  def __str__(self) -> str:
    return str(self.update())
  def addInput(self, InputElement : LogicElement) -> LogicElement:
    self._input = InputElement
    return InputElement
  def update(self) -> LogicValue:
    self._output = self._input.update()
    return self._output
  
      
  
class LogicGateNot(LogicElement):
  _input : LogicElement
  def __init__(self, Name = "unnamed") -> None:
    self._type = "NOT"
    self.Name = Name
  def addInput(self, Element : LogicElement) -> None:
    self._input = Element
  def update(self) -> LogicValue:
    try:
      result = ~self._input.update()
    except:
      result = LogicValue("X")
    self._output = result
    return result
  
class LogicGateOr(LogicElement):
  def __init__(self,  Name = "unnamed") -> None:
    self._type = "OR"
    self.Name = Name
  def update(self) -> LogicValue:
    result = LogicValue(0)
    for input in self._inputs:
      result |= input.update()
    self._output = result
    return result
  
class LogicGateNor(LogicElement):
  def __init__(self, Name = "unnamed") -> None:
    self._type = "NOR"
    self.Name = Name
  def update(self) -> LogicValue:
    result = LogicValue(0)
    for input in self._inputs:
      result |= input.update()
    result = ~result
    self._output = result
    return result
  
class LogicGateAnd(LogicElement):
  def __init__(self,  Name = "unnamed") -> None:
    self._type = "AND"
    self.Name = Name
  def update(self) -> LogicValue:
    result = LogicValue(1)
    for input in self._inputs:
      result &= input.update()
    self._output = result
    return result
  
class LogicGateNand(LogicElement):
  def __init__(self, Name = "unnamed") -> None:
    self._type = "NAND"
    self.Name = Name
  def update(self) -> LogicValue:
    result = LogicValue(1)
    for input in self._inputs:
      result &= input.update()
    result = ~result
    self._output = result
    return result
  
class LogicGateXor(LogicElement):
  def __init__(self, Name = "unnamed") -> None:
    self._type = "XOR"
    self.Name = Name
  def update(self) -> LogicValue:
    result = LogicValue(0)
    for input in self._inputs:
      result ^= input.update()
    self._output = result
    return result
  
class LogicGateXnor(LogicElement):
  def __init__(self, Name = "unnamed") -> None:
    self._type = "XNOR"
    self.Name = Name
  def update(self) -> LogicValue:
    result = LogicValue(0)
    for input in self._inputs:
      result ^= input.update()
    result = ~result
    self._output = result
    return result
  
  
  
class LogicClock:
  Name = "unnamed"
  _my_objects = []
  def __init__(self, Name = "unnamed") -> None:
    self.Name = Name
  def __str__(self) -> str:
    result = ""
    for o in self._my_objects:
      result += str(o)
    return result
  def __repr__(self) -> str:
    return "LogicClock(" + str(len(self._my_objects)) + ")"
  def __bool__(self) -> bool:
    if len(self._my_objects) > 0:
      return True
    return False
  def __len__(self) -> int:
    return len(self._my_objects)
  def addFF(self, FF : LogicFF) -> None:
    self._my_objects.append(FF)
  def removeFF(self, FF : LogicFF) -> None:
    self._my_objects.remove(FF)
  def getFFs(self) -> list:
    return self._my_objects
  def pulse(self) -> None:
    for ff in self._my_objects:
      ff.posedge()
    for ff in self._my_objects:
      ff.negedge()
  def set(self) -> None:
    for ff in self._my_objects:
      ff.set()
  def reset(self) -> None:
    for ff in self._my_objects:
      ff.reset()
    
    
class Logic:
  Name = "unnamed"
  _elements = []
  _combinationals = []
  _sequentials = []
  _clocks = []
  _inputs = []
  _outputs = []
  def __init__(self, Name = "unnamed") -> None:
    self.Name = Name
  def __repr__(self) -> str:
    return "Logic('" + self.Name + "')"
  def __str__(self) -> str:
    result = ""
    for o in self._outputs:
      result += str(o)
    return result
  def addOutput(self, OutputName : str, OfElement : LogicElement) -> LogicOutput:
    Output = LogicOutput(OutputName)
    Output.addInput(OfElement)
    self._outputs.append(Output)
    return Output
  def addElement(self, Element : LogicElement, AutoClock = True) -> LogicElement:
    self._elements.append(Element)
    if Element.isSequential():
      self._sequentials.append(Element)
      if AutoClock:
        acs = self.getClocks("AutoClock")
        if len(acs) == 1:
          ac = acs[0]
        else:
          ac = self.addClock(LogicClock("AutoClock"))
        ac.addFF(Element)
    else:
      self._combinationals.append(Element)
    return Element
  def removeElement(self, Element : LogicElement) -> None:
    self._elements.remove(Element)
    self._combinationals.remove(Element)
    self._sequentials.remove(Element)
    self._inputs.remove(Element)
    self._outputs.remove(Element)
  def getElements(self, RegexPattern = "") -> list:
    results = []
    for c in self._elements:
      if re.match(RegexPattern, c.Name):
        results.append(c)
    return results
  def getInputs(self, RegexPattern = "") -> list:
    results = []
    for c in self._inputs:
      if re.match(RegexPattern, c.Name):
        results.append(c)
    return results
  def getOutputs(self, RegexPattern = "") -> list:
    results = []
    for c in self._outputs:
      if re.match(RegexPattern, c.Name):
        results.append(c)
    return results
  def getSequentialElements(self, RegexPattern = "") -> list:
    results = []
    for c in self._sequentials:
      if re.match(RegexPattern, c.Name):
        results.append(c)
    return results
  def getCombinationalElements(self, RegexPattern = "") -> list:
    results = []
    for c in self._combinationals:
      if re.match(RegexPattern, c.Name):
        results.append(c)
    return results
  def addClock(self, Clock : LogicClock) -> LogicClock:
    self._clocks.append(Clock)
    return Clock
  def removeClock(self, Clock : LogicClock) -> LogicClock:
    self._clocks.remove(Clock)
  def getClocks(self, RegexPattern = "") -> list:
    results = []
    for c in self._clocks:
      if re.match(RegexPattern, c.Name):
        results.append(c)
    return results
  def clockPulse(self, Clock = "AutoClock") -> None:
    if type(Clock) == type(LogicClock):
      Clock.pulse()
    else:
      clocks = self.getClocks(Clock)
      for c in clocks:
        c.pulse()
  def reset(self) -> None:
    for c in self._clocks:
      c.reset()
