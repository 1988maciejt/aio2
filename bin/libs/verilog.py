from enum import Enum
from libs.aio import *
import re
import copy
from libs.files import *


class VerilogSignalDirection(Enum):
  INPUT = 1
  OUTPUT = 2
  INOUT = 3
  INTERNAL = 4
  UNDEFINED = 255

  
class VerilogSignalType(Enum):
  WIRE = 1
  REG = 2
  UNDEFINED = 255


class VerilogParameter:
  Name : str
  Value : str
  def __init__(self, Name : str, Value = "UNDEFINED") -> None:
    self.Name = Name
    self.Value = Value
  def __str__(self) -> str:
    return self.Name + " = " + self.Value
  def __repr__(self) -> str:
    return "VerilogParameter(" + self.Name + ")"
  def __bool__(self) -> bool:
    if len(self.Name) > 0:
      return True
    return False
  def fromString(self, String : str) -> bool:
    R = re.search(r'(.*)//',String,re.DOTALL)
    if R:
      String = R.group(1)
    String = String.strip()
    if len(String) > 2:
      R = re.search(r'\.(\w+)\s*\(\s*([^\s()]*?)\s*?\)',String)
      if R:
        self.Name = R.group(1)
        self.Value = R.group(2)
        return True
      R = re.search(r'(\w+)\s*=\s*([^\s()]*?+)',String)
      if R:
        self.Name = R.group(1)
        self.Value = R.group(2)
        return True
    self.Name = ""
    self.Value = ""
    return False


class VerilogParameters:
  _params = []
  IndentationString = ""
  def __bool__(self) -> bool:
    if len(self._params) > 0:
      return True
    return False
  def __contains__(self, item) -> bool:
    if isinstance(item, (str)):
      return bool(self.getParameterByName(item))
    elif isinstance(item, (VerilogParameter)):
      return (item in self._params)
    return False
  def __getitem__(self, key) -> VerilogParameter:
    return self._params[key]
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_PARAMETERS {\n"
    for par in self._params:
      result += self.IndentationString + "  " + str(par) + "\n"
    result += self.IndentationString + "}"
    return result
  def __repr__(self) -> str:
    return "VerilogParameters(" + str(len(self._params)) + ")"
  def __len__(self) -> int:
    return len(self._params)    
  def getParameterByName(self, Name : str) -> VerilogParameter:
    for par in self._params:
      if par.Name == Name:
        return par
    return VerilogParameter("")
  def add(self, Parameter : VerilogParameter) -> None:
    P = self.getParameterByName(Parameter.Name)
    if P:
      P.Value = Parameter.Value
    else:
      ParN = copy.deepcopy(Parameter)
      self._params.insert(0, ParN)


class VerilogSignal:
  Type : VerilogSignalType
  Direction : VerilogSignalDirection
  Name : str
  _bus_width : int
  _bus_high : int
  _bus_low : int
  Testable : bool
  def __init__(self, Name : str, Type = VerilogSignalType.WIRE, Direction = VerilogSignalDirection.INTERNAL, Bus = [0,0], testable = True) -> None:
    self.Type = Type
    self.Direction = Direction
    self.Name = Name
    self._bus_high = Bus[0]
    self._bus_low = Bus[1]
    self._bus_width = self._bus_high - self._bus_low + 1
    self.Testable = testable
  def __str__(self) -> str:
    result = ""
    if self.Direction == VerilogSignalDirection.INOUT:
      result += "inout "
    if self.Direction == VerilogSignalDirection.INPUT:
      result += "input "
    if self.Direction == VerilogSignalDirection.OUTPUT:
      result += "output "
    if self.Type == VerilogSignalType.REG:
      result += "reg "
    else:
      result += "wire "
    if self._bus_width > 1:
      result += "[" + str(self._bus_high) + ":" + str(self._bus_low) + "] "
    result += self.Name + ";"
    return result
  def __repr__(self) -> str:
    return "VerilogSignal('" + self.Name + "')"
  def __bool__(self) -> bool:
    if len(self.Name) > 0:
      return True
    return False
  def getDirection(self) -> VerilogSignalDirection:
    return self._dir
  def setDirection(self, Dir : VerilogSignalDirection) -> None:
    self._dir = Dir
  def setBus(self, Bus = [0,0]) -> None:
    self._bus_high = Bus[0]
    self._bus_low = Bus[1]
    self._bus_width = self._bus_high - self._bus_low + 1
  def getBus(self) -> list:
    return [self._bus_high, self._bus_low]
  def getBusWidth(self) -> int:
    return self._bus_width

  
class VerilogSignals:
  _signals = []
  IndentationString = ""
  def __bool__(self) -> bool:
    if len(self._signals) > 0:
      return True
    return False
  def __contains__(self, item) -> bool:
    if isinstance(item, (str)):
      return bool(self.getConnectionByIOName(item))
    elif isinstance(item, (VerilogSignal)):
      return (item in self._signals)
    return False
  def __getitem__(self, key) -> VerilogSignal:
    return self._signals[key]
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_SIGNALS {\n"
    for sig in self._signals:
      result += self.IndentationString + "  " + str(sig) + "\n"
    result += self.IndentationString + "}"
    return result
  def __repr__(self) -> str:
    return "VerilogSignals(" + str(len(self._signals)) + ")"
  def __len__(self) -> int:
    return len(self._signals)    
  def getSignalByName(self, Name : str) -> VerilogSignal:
    for signal in self._signals:
      if signal.Name == Name:
        return signal
    return VerilogSignal("")
  def getSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED) -> list:
    result = []
    for signal in self._signals:
      if Direction != VerilogSignalDirection.UNDEFINED:
        if Direction != signal.Direction:
          continue
      if Type != VerilogSignalType.UNDEFINED:
        if Type != signal.Type:
          continue
      if len(RegexPattern) > 0:
        if not re.search(RegexPattern, signal.Name):
          continue
      result.insert(0, signal.Name)
    return result
  def add(self, Signal : VerilogSignal) -> None:
    S = self.getSignalByName(Signal.Name)
    if S:
      if S.Direction == VerilogSignalDirection.INOUT:
        S.Direction = Signal.Direction
      if S.Type == VerilogSignalType.WIRE:
        S.Type = Signal.Type
      if S.getBusWidth == 1:
        S.setBus(Signal.getBus())
    else:
      NS = copy.deepcopy(Signal)
      self._signals.insert(0, NS)


class VerilogInstanceConnection:
  SignalName : str
  IOName : str
  def __init__(self, SignalName : str, IOName : str) -> None:
    self.SignalName = SignalName
    self.IOName = IOName
  def __bool__(self) -> bool:
    if len(self.SignalName) > 0 and len(self.IOName) > 0:
      return True
    return False
  def __str__(self) -> str:
    return "." + self.IOName + " ( " + self.SignalName + ")"
  def __repr__(self) -> str:
    return "VerilogInstanceConnection(" + self.IOName + ")"
  def fromString(self, String : str) -> bool:
    R = re.search(r'(.*)//',String,re.DOTALL)
    if R:
      String = R.group(1)
    String = String.strip()
    if len(String) > 2:
      R = re.search(r'\.(\w+)\s*\(\s*([^\s()]*?)\s*?\)',String)
      if R:
        self.IOName = R.group(1)
        self.SignalName = R.group(2)
        return True
    self.IOName = ""
    self.SignalName = ""
    return False


class VerilogInstanceConnections:
  _conn = []
  IndentationString = ""
  def __bool__(self) -> bool:
    if len(self._conn > 0):
      return True
    return False
  def __contains__(self, item) -> bool:
    if isinstance(item, (str)):
      return bool(self.getConnectionByIOName(item))
    elif isinstance(item, (VerilogInstanceConnection)):
      return (item in self._conn)
    return False
  def __len__(self) -> int:
    return len(self._conn)
  def __getitem__(self, key) -> VerilogInstanceConnection:
    return self._conn[key]
  def __str__(self) -> str:
    result = self.IndentationString + "CONNECTIONS {\n"
    for c in self._conn:
      result += self.IndentationString + "  " + str(c) + "\n"
    result += self.IndentationString + "}"
    return result
  def __repr__(self) -> str:
    return "VerilogInstanceConnections(" + len(self._conn) + ")"
  def getConnectionByIOName(self, IOName : str) -> VerilogInstanceConnection:
    for c in self._conn:
      if c.IOName == IOName:
        return c
    return VerilogInstanceConnection("","")
  def getSignalNameByIOName(self, IOName : str) -> str:
    return self.getConnectionByIOName(IOName).SignalName
  def add(self, Connection : VerilogInstanceConnection) -> None:
    C = self.getConnectionByIOName(Connection.IOName)
    if C:
      C.SignalName = Connection.SignalName
    else:
      NCon = copy.deepcopy(Connection)
      self._conn.insert(0, NCon)
  def getConnections(self) -> list:
    return self._conn


class VerilogInstance:
  _params = VerilogParameters()
  _conn = VerilogInstanceConnections()
  ModuleName = ""
  InstanceName = ""
  IndentationString = ""
  def __init__(self, Instancename = "", Modulename = "") -> None:
    self.InstanceName = Instancename
    self.ModuleName = Modulename
  def __bool__(self) -> bool:
    if len(self.ModuleName) > 0 and len(self.InstanceName) > 0:
      return True
    return False
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_INSTAMCE {\n"
    result += self.IndentationString + "  InstanceName: " + self.InstanceName + "\n"
    result += self.IndentationString + "  ModuleName: " + self.ModuleName + "\n"
    self._params.IndentationString = self.IndentationString + "  "
    result += str(self._params) + "\n"
    self._conn.IndentationString = self.IndentationString + "  "
    result += str(self._conn) + "\n"
    result += self.IndentationString + "}"
    return result
  def __repr__(self) -> str:
    return "VerilogInstance(" + self.ModuleName + "," + self.InstanceName + ")"
  def addParameter(self, Parameter : VerilogParameter) -> None:
    self._params.add(Parameter)
  def addConnection(self, Connection : VerilogInstanceConnection) -> None:
    self._conn.add(Connection)
  def getConnection(self, IOName : str) -> VerilogInstanceConnection:
    return self._conn.getConnectionByIOName(IOName)
  def getParameter(self, Name : str) -> VerilogParameter:
    return self._params.getParameterByName(Name)  
  def getIONames(self, RegexPattern = "") -> list:
    result = []
    for conn in self._conn.getConnections():
      if len(RegexPattern) > 0:
        if not re.search(RegexPattern,conn.IOName):
          continue
      result.append(conn.IOName)
    return result
  
  
class VerilogInstances:
  _instances = []
  IndentationString = ""
  def __bool__(self) -> bool:
    if len(self._instances) > 0:
      return True
    return False
  def __contains__(self, item) -> bool:
    if isinstance(item, (str)):
      return bool(self.getInstanceByName(item))
    elif isinstance(item, (VerilogInstance)):
      return (item in self._instances)
    return False
  def __len__(self) -> int:
    return len(self._instances)
  def __getitem__(self, key) -> VerilogInstance:
    return self._instances[key]
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_INSTANCES {\n"
    for i in self._instances:
      i.IndentationString = self.IndentationString + "  "
      result += str(i) + "\n"
    result += self.IndentationString + "}"
    return result
  def __repr__(self) -> str:
    return "VerilogInstances(" + str(len(self._instances)) + ")"
  def addInstance(self, Instance : VerilogInstance) -> None:
    self._instances.insert(0, copy.deepcopy(Instance))
  def getInstanceByName(self, InstanceName : str) -> VerilogInstance:
    for i in self._instances:
      if i.InstanceName == InstanceName:
        return i
    return VerilogInstance()
  def getInstancesByName(self, RegexPattern : str) -> list:
    result = []
    for i in self._instances:
      if re.search(RegexPattern, i.InstanceName):
        result.append(i)
    return result 
  def getInstanceNames(self, RegexPattern : str) -> list:
    result = []
    for i in self._instances:
      if re.search(RegexPattern, i.InstanceName):
        result.append(i.InstanceName)
    return result 


class VerilogModule:
  _name = ""
  _content : str
  _signals = VerilogSignals()
  _params = VerilogParameters()
  _instances = VerilogInstances()
  IndentationString = ""
  def __init__(self, Content : str) -> None:
    # Parse module name, parameters, nets
    self._content = Content
    ios = ""
    params = ""
    R = re.search("module\s+([a-zA-Z0-9\_]+)\s*\(([^)]*)\)\;",Content,re.MULTILINE)
    if R:
      self._name = R.group(1)
      ios = R.group(2)
    else:
      R = re.search("module\s+([a-zA-Z0-9\_]+)\s*\(([^)]*)\)\s*\#\s*\(([^)]*)\);",Content,re.MULTILINE)
      if R:
        self._name = R.group(1)
        params = R.group(2)
        ios = R.group(3)
      else:
        Aio.printError("The given string:\n\r"+Content+"\n\r is not a valid Verilog module")
        return
    ios_list = ios.split(",")
    params_list = params.split(",")
    for par_ in params_list:
      par = par_.strip()
      R = re.search("(\S+)\s*=\s*(\S+)",par,re.MULTILINE)
      if R:
        P = VerilogParameter(R.group(1), R.group(2))
        self._params.add(P)
    for io_ in ios_list:
      _direction = "inout"
      _type = "wire"
      _bush = 0
      _busl = 0
      io = io_.strip()
      R = re.search("(input|output|inout)\s+(.*)",io,re.MULTILINE)
      if R:
        _direction = R.group(1)
        io = R.group(2)
      R = re.search("(wire|reg)\s+(.*)",io,re.MULTILINE)
      if R:
        _type = R.group(1)
        io = R.group(2)
      R = re.search("\[([0-9]+):([0-9]+)\]\s(\S+)",io,re.MULTILINE)
      if R:
        _bush = int(R.group(1))
        _busl = int(R.group(2))
        io = R.group(3)
      Type = VerilogSignalType.WIRE
      if "reg" in _type:
        Type = VerilogSignalType.REG
      Direction = VerilogSignalDirection.INOUT
      if "input" in _direction:
        Direction = VerilogSignalDirection.INPUT
      if "output" in _direction:
        Direction = VerilogSignalDirection.OUTPUT
      Bus = [_bush, _busl]
      Sig = VerilogSignal(io,Type,Direction,Bus)
      self._signals.add(Sig)
    # parse instances with params
    RegexInstanceWithParam = r'(\w+)\s+\#\s*\((.*?)\)\s+(\w+)\s*\((.*?)\);'
    Strings = re.findall(RegexInstanceWithParam,Content,re.DOTALL)
    for S in Strings:
      Instance = VerilogInstance(S[2], S[0])
      ParamStrings = S[1].split("\n")
      for String in ParamStrings:
        Parameter = VerilogParameter("")
        Parameter.fromString(String)
        if Parameter:
          Instance.addParameter(Parameter)
      ConStrings = S[3].split("\n")
      for String in ConStrings:
        Conn = VerilogInstanceConnection("","")
        Conn.fromString(String)
        if Conn:
          Instance.addConnection(Conn)
      self._instances.addInstance(Instance)
    # parse instances without params
    RegexInstanceWithParam = r'^\s*(\w+)\s+(\w+)\s*\(([^#]*?)\);'
    Strings = re.findall(RegexInstanceWithParam,Content,re.DOTALL+re.MULTILINE)
    for S in Strings:
      Instance = VerilogInstance(S[1], S[0])
      ConStrings = S[2].split("\n")
      for String in ConStrings:
        Conn = VerilogInstanceConnection("","")
        Conn.fromString(String)
        if Conn:
          Instance.addConnection(Conn)
      self._instances.addInstance(Instance)
  def __repr__(self) -> str:
    return "VerilogMosule('" + self._name + "')"
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_MODULE {\n"
    result += self.IndentationString + "  Name: " +  self._name + "\n"
    self._params.IndentationString = self.IndentationString + "  "
    result += str(self._params) + "\n"
    self._signals.IndentationString = self.IndentationString + "  "
    result += str(self._signals) + "\n"
    self._instances.IndentationString = self.IndentationString + "  "
    result += str(self._instances) + "\n"
    result += self.IndentationString + "}"
    return result
  def __bool__(self) -> bool:
    if len(self._content) > 1:
      return True
    return False
  def getName(self) -> str:
    return self._name
  def getSignals(self) -> VerilogSignals:
    return self._signals
  def getSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED, OfInstance = "") -> list:
    result = []
    instances = []
    if (Direction != VerilogSignalDirection.UNDEFINED or Type != VerilogSignalType.UNDEFINED) and len(OfInstance) > 0:
      Aio.printError("Cannot determina Direction and/or Type of signal of an instance")
      return []
    if len(OfInstance) > 0:
      instances = self._instances.getInstancesByName(OfInstance)
    else:
      instances = self._instances.getInstancesByName(".*")
    if len(OfInstance) == 0:
      result = self._signals.getSignalNames(RegexPattern,Direction,Type)
    for instance in instances:
      aux = instance.getIONames(RegexPattern)
      for io in aux:
        result.append(instance.InstanceName + "." + io)
    result.sort()
    return result
  def getParameters(self) -> VerilogParameters:
    return self._params
  def getInstance(self, InstanceName : str) -> VerilogInstance:
    return self._instances.getInstanceByName(InstanceName)
  def getInstances(self, RegexPattern = "") -> VerilogInstances:
    if len(RegexPattern) > 0:
      return self._instances.getInstancesByName(RegexPattern)
    return self._instances
  def getInstanceNames(self, RegexPattern = "") -> list:
    return self._instances.getInstanceNames(RegexPattern)
  def getContent(self) -> str:
    return self._content
  
  
class VerilogModules:
  _modules = []
  IndentationString = ""
  def __bool__(self) -> bool:
    if len(self._modules) > 0:
      return True
    return False
  def __contains__(self, item) -> bool:
    if isinstance(item, (str)):
      return bool(self.getModuleByName(item))
    elif isinstance(item, (VerilogModule)):
      return (item in self._modules)
    return False
  def __len__(self) -> int:
    return len(self._modules)
  def __getitem__(self, key) -> VerilogModule:
    return self._modules[key]
  def __repr__(self) -> str:
    return "VerilogModules(" + str(len(self._modules)) + ")"
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_MODULES {\n"
    for m in self._modules:
      m.IndentationString = self.IndentationString + "  "
      result += str(m) + "\n"
    result += self.IndentationString + "}"
    return result
  def addFromString(self, String : str) -> None:
    Lines = String.split("\n")
    InModule = False
    SModule = ""
    for Line in Lines:
      if not InModule:
        if re.match(r'^\s*module\s+\w+', Line):
          InModule = True
          SModule = Line + "\n"
      else:
        if re.match(r'^\s*endmodule\s*', Line):
          InModule = False
          SModule += Line 
          Module = VerilogModule(SModule)
          self._modules.append(Module)
        else:
          SModule += Line + "\n"
  def getModules(self) -> list:
    return self._modules
  def getModuleByName(self, Name : str) -> VerilogModule:
    for m in self._modules:
      if m.getName() == Name:
        return m
    return VerilogModule("");
  def getModulesByName(self, RegexPattern : str) -> list:
    result = []
    for m in self._modules:
      if re.match(RegexPattern, m.getName()):
        result.append(m)
    return result
  def getModuleNames(self, RegexPattern : str) -> list:
    result = []
    for m in self._modules:
      if re.match(RegexPattern, m.getName()):
        result.append(m.getName())
    result.sort()
    return result
  def getContent(self) -> str:
    result = ""
    for m in self._modules:
      result += m.getContent() + "\n\n"
    return result
    
  
class Verilog:
  pass    
class Verilog:
  Modules = VerilogModules()
  IndentationString = ""
  _top = ""
  def __init__(self, Content = "") -> None:
    self.Modules.addFromString(Content)
  def __bool__(self) -> bool:
    return bool(self.Modules)
  def __contains__(self, item) -> bool:
    if isinstance(item, (str)):
      return bool(self.Modules.getModuleByName(item))
    elif isinstance(item, (VerilogModule)):
      return (item in self.Modules.getModules())
    return False
  def __getitem__(self, key) -> VerilogModule:
    return self.Modules[key]
  def __len__(self) -> int:
    return len(self.Modules)
  def __repr__(self) -> str:
    return "Verilog(" + str(len(self.Modules)) + ")"
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG {\n"
    self.Modules.IndentationString = self.IndentationString + "  "
    result += str(self.Modules) + "\n"
    result += self.IndentationString + "}"
    return result
  def addContent(self, Content : str) -> None:
    self.Modules.addFromString(Content)
  def read(self,FileName : str) -> None:
    return 
  def read(FileName : str) -> Verilog:
    V = Verilog()
    V.read(FileName)
    return V
  def getModules(self) -> list:
    return self.Modules.getModules()
  def getModulesByName(self, RegexPattern = "") -> list:
    return self.Modules.getModulesByName(RegexPattern)
  def getModuleByName(self, Name : str) -> VerilogModule:
    return self.Modules.getModuleByName(Name)
  def getModuleNames(self, RegexPattern = "") -> list:
    result = []
    for m in self.Modules.getModulesByName(RegexPattern):
      result.append(m.getName())
    return result
  def getSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED, OfInstance = "", OfModule = "") -> list:
    result = []
    for m in self.Modules.getModulesByName(OfModule):
      for s in m.getSignalNames(RegexPattern,Direction,Type,OfInstance):
        result.append(m.getName() + "." + s)
    return result
  def getContent(self) -> str:
    return self.Modules.getContent()
  def writeToFile(self, FileName : str):
    writeFile(FileName, self.getContent())
  def setTopModuleName(self, ModuleName : str) -> bool:
    if self.Modules.getModuleByName(ModuleName):
      self._top = ModuleName
      return True
    Aio.printError("'" + ModuleName + "' not found in modules.")
    return False
  def getTopModuleName(self) -> str:
    return self._top
  def getTopModule(self) -> VerilogModule:
    return self.Modules.getModuleByName(self._top)
  def synthesize(self, OutputFileName : str, TopModuleName = None, Xilinx = False, TechlibFileName = None):
    tmpFileName = "/tmp/tmp.v"
    ysFileName = "synth.ys"
    self.writeToFile(tmpFileName)
    Script = f'read_verilog -sv {tmpFileName} \n'
    if Xilinx:
      Script += f'synth_xilinx '
    else:
      Script += f'hierarchy '
    if TopModuleName != None:
      Script += f'-top {TopModuleName} '
    Script += f'\n'
    Script += "techmap \n"
    Script += "proc; fsm; opt; memory; opt \n"
    if TechlibFileName != None:
      Script += f'dfflibmap -prepare -liberty {TechlibFileName} \n'
      Script += f'abc -liberty {TechlibFileName} \n'
    Script += f'write_verilog -noattr -noexpr {OutputFileName} \n'
    writeFile(ysFileName, Script)
    result = Aio.shellExecute(f'yosys {ysFileName}')
    Aio.print(result)
    
    
  
  
class VerilogTestbenchClock:
  Name = "clk"
  Frequency = 1000
  DutyCycle = 0.5
  EnableInput = False
  def __init__(self, Name : str, Frequency = 1000, DutyCycle = 0.5, EnableInput = False) -> None:
    self.Frequency = Frequency
    self.DutyCycle = DutyCycle
    self.Name = Name
    self.EnableInput = EnableInput
  def __repr__(self) -> str:
    return f'VerilogTestbenchClock({self.Name}, {self.Frequency}, {self.DutyCycle})'
  def __str__(self) -> str:
    return self.__repr__()
  def getSignalDeclaration(self):
    Result = "reg " + self.Name
    if self.EnableInput:
      Result += ", " + self.Name + "_enable"
    Result += ";"
    return Result
  def getEnableInputName(self):
    return self.Name + "_enable"
  def getBody(self):
    onTimeNs = round(self.DutyCycle * 1000000000 / self.Frequency, 3)
    offTimeNs = round(1000000000 / self.Frequency - onTimeNs, 3)
    Result = "initial begin\n"
    Result += f'  {self.Name} <= 1\'b0;\n'
    Result += "  forever begin\n"
    if self.EnableInput:
      Result += f'    if ({self.Name}_enable) begin\n'
      Result += f'      #{offTimeNs} {self.Name} <= 1\'b1;\n'
      Result += f'      #{onTimeNs} {self.Name} <= 1\'b0;\n'
      Result += f'    end\n'
    else:
      Result += f'    #{offTimeNs} {self.Name} <= 1\'b1;\n'
      Result += f'    #{onTimeNs} {self.Name} <= 1\'b0;\n'
    Result += "  end\n"
    Result += "end"
    return Result  
  
class VerilogTestbench:
  _my_verilog = Verilog
  Name = "tb"
  Clocks = []
  def __init__(self, Name = "tb", MyVerilog = Verilog()) -> None:
    self._my_verilog = MyVerilog
    self.Name = Name
  def __repr__(self) -> str:
    return "VerilogTestbench(" + self.Name + ", " + self._my_verilog.getTopModuleName() + ")"
  def __str__(self) -> str:
    result = "VERILOG_TESTBENCH {\n"
    result += f'  Name = {self.Name}' + "\n"
    for Clock in self.Clocks:
      result += "  " + str(Clock) + "\n"
    self._my_verilog.IndentationString = "  "
    result += str(self._my_verilog) + "\n"
    result += "}"
    return result
  def setVerilog(self, MyVerilog : Verilog) -> None:
    self._my_verilog = MyVerilog
  def getVerilog(self) -> Verilog:
    return self._my_verilog
  def getBody(self) -> str:
    Result = f'module {self.Name} (' + "\n"
    Result += ");\n\n"
    for Clock in self.Clocks:
      Result += Clock.getSignalDeclaration() + "\n"
    for Clock in self.Clocks:
      Result += "\n" + Clock.getBody() + "\n"
    Result += "\nendmodule"
    return Result
  def addClock(self, TBClock : VerilogTestbenchClock):
    self.Clocks.append(TBClock)
  def createClock(self, Name : str, Frequency = 1000, DutyCycle = 0.5, EnableInput = False) -> VerilogTestbenchClock:
    Clock = VerilogTestbenchClock(Name, Frequency, DutyCycle, EnableInput)
    self.Clocks.append(Clock)
    return Clock