from enum import Enum
from libs.aio import *
import re
import copy
from libs.files import *
from tqdm import *
from p_tqdm import *
from random import uniform
from libs.asci_drawing import *
from aio_config import *
from shutil import copyfile, rmtree


class VerilogSignalDirection(Enum):
  INPUT     = 1
  OUTPUT    = 2
  INOUT     = 3
  INTERNAL  = 4
  UNDEFINED = 255
  
VERILOG_SIGNAL_DIRECTION_INPUT      = VerilogSignalDirection.INPUT
VERILOG_SIGNAL_DIRECTION_OUTPUT     = VerilogSignalDirection.OUTPUT
VERILOG_SIGNAL_DIRECTION_INOUT      = VerilogSignalDirection.INOUT
VERILOG_SIGNAL_DIRECTION_INTERNAL   = VerilogSignalDirection.INTERNAL
VERILOG_SIGNAL_DIRECTION_UNDEFINED  = VerilogSignalDirection.UNDEFINED


class VerilogSignalType(Enum):
  WIRE      = 1
  REG       = 2
  UNDEFINED = 255
  
VERILOG_SIGNAL_TYPE_WIRE      = VerilogSignalType.WIRE
VERILOG_SIGNAL_TYPE_REG       = VerilogSignalType.REG
VERILOG_SIGNAL_TYPE_UNDEFINED = VerilogSignalType.UNDEFINED


class VerilogConstraints:
  __slots__ = ("_clist")
  def __init__(self) -> None:
    self._clist = []
  def __str__(self) -> str:
    return self.toString()
  def __repr__(self) -> str:
    return f'VerilogCInstraints({len(self._clist)})'
  def __len__(self) -> int:
    return len(self._clist)
  def __iter__(self):
    return self._clist.__iter__()
  def __next__(self):
    return self.__next__()
  def add(self, LineString : str):
    if LineString not in self._clist:
      self._clist.append(LineString)
  def getAll(self) -> list:
    return self._clist
  def toString(self) -> str:
    Results = ""
    for c in self._clist:
      Results += c + "\n"
    return Results
  


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
  __slots__ = ("_signals", "IndentationString")
  def __init__(self) -> None:
    self._signals = []
    self.IndentationString = ""
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
  def getSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED, GroupBuses = False) -> list:
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
      if not GroupBuses and signal.getBusWidth() > 1:
        ToFrom = signal.getBus()
        for i in range(ToFrom[1], ToFrom[0]+1):
          result.insert(0, f"{signal.Name}[{i}]")
      else:
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
    return "." + self.IOName + " (" + self.SignalName + ")"
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
  __slots__ = ("_params", "_conn", "ModuleName", "InstanceName", "IndentationString")
  def __init__(self, Instancename = "", Modulename = "") -> None:
    self.InstanceName = Instancename
    self.ModuleName = Modulename
    self.IndentationString = ""
    self._conn = VerilogInstanceConnections()
    self._params = VerilogParameters()
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
  __slots__ = ("_instances", "IndentationString")
  def __init__(self) -> None:
    self._instances = []
    self.IndentationString = ""
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
  __slots__ = ("_name", "_content", "_signals", "_params", "_instances", "IndentationString", "MyModules")
  def __init__(self, Content : str, MyModules = None) -> None:
    self._name = ""
    self._content : str
    self._signals = VerilogSignals()
    self._params = VerilogParameters()
    self._instances = VerilogInstances()
    self.IndentationString = ""
    self.MyModules = MyModules
    # Parse module name, parameters, nets
    self._content = Content
    CContent = ""
    for l in Content.split("\n"):
      CContent += re.sub(r'^(.*)\(\*.*\*\)(.*)$', r'\1\2', l) + "\n"
    ios = ""
    params = ""
    RegexModule = "module\s+([a-zA-Z0-9\_]+)\s*\(([^)]*)\)\;"
    RegexModuleWithParams = "module\s+([a-zA-Z0-9\_]+)\s*\(([^)]*)\)\s*\#\s*\(([^)]*)\);"
    R = re.search(RegexModule,CContent,re.MULTILINE)
    if R:
      self._name = R.group(1)
      ios = R.group(2)
      CContent = re.sub(RegexModule,"",CContent,re.MULTILINE)
    else:
      R = re.search(RegexModuleWithParams,CContent,re.MULTILINE)
      if R:
        self._name = R.group(1)
        params = R.group(2)
        ios = R.group(3)
        CContent = re.sub(RegexModuleWithParams,"",CContent,re.MULTILINE)
      else:
        Aio.printError("The given string:\n\r"+CContent+"\n\r is not a valid Verilog module")
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
      io = io.strip()
      if len(io) < 1:
        continue
      Sig = VerilogSignal(io,Type,Direction,Bus)
      self._signals.add(Sig)
    # parse instances with params
    RegexInstanceWithParam = r'(\w+)\s+\#\s*\((.*?)\)\s+(\w+)\s*\((.*?)\);'
    Strings = re.findall(RegexInstanceWithParam,CContent,re.DOTALL)
    for S in Strings:
      if S[0] == "module":
        continue
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
    RegexInstanceWithoutParam = r'^\s*(\w+)\s+(\w+)\s*\(([^#]*?)\);'
    Strings = re.findall(RegexInstanceWithoutParam,CContent,re.DOTALL+re.MULTILINE)
    for S in Strings:
      if S[0] == "module":
        continue
      Instance = VerilogInstance(S[1], S[0])
      ConStrings = S[2].split("\n")
      for String in ConStrings:
        Conn = VerilogInstanceConnection("","")
        Conn.fromString(String)
        if Conn:
          Instance.addConnection(Conn)
      self._instances.addInstance(Instance)
    # internal signals
    RegexInternalSignal = f'(wire|reg)\s*((\[([0-9]+):([0-9]+)\])|())\s+([^=;]+)'
    RegexIoSignal = f'(input|output|inout)\s*([^=;]+)'
    CContent = CContent.replace(",\n", ",")
    for Line in CContent.split("\n"):
      Direction = VerilogSignalDirection.INTERNAL
      Existing = 0
      R = re.search(RegexIoSignal,Line)
      if R:
        Direction = VerilogSignalDirection.INOUT
        if "input" in R.group(1):
          Direction = VerilogSignalDirection.INPUT
        if "output" in R.group(1):
          Direction = VerilogSignalDirection.OUTPUT
        Line = R.group(2)
        Existing = 1
      R = re.search(RegexInternalSignal,Line)
      if Existing and not R:
        R = re.search(RegexInternalSignal,f'wire {Line}')
      if R:
        _Type = R.group(1)
        _From = R.group(4)
        _To = R.group(5)
        _Names = R.group(7).split(',')
        Type = VerilogSignalType.WIRE
        if "reg" in _Type:
          Type = VerilogSignalType.REG
        _bush = 0
        _busl = 0
        if _From is not None:
          _bush = int(_From)
        if _To is not None:
          _busl = int(_To)
        Bus = [_bush, _busl]
        for Name in _Names:
          Name = Name.strip()
          if len(Name) < 1 or ")" in Name or "]" in Name:
            continue
          if Existing:
            for IoSig in self._signals._signals:    
              if IoSig.Name == Name:
                self._signals._signals.remove(IoSig)
                break
          Sig = VerilogSignal(Name, Type, Direction, Bus)
          self._signals.add(Sig)
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
  def getSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED, OfInstance = "", OfModule = "", GroupBuses = False) -> list:
    result = []
    instances = []
    if (Direction != VerilogSignalDirection.UNDEFINED or Type != VerilogSignalType.UNDEFINED) and len(OfInstance) > 0:
      Aio.printError("Cannot determina Direction and/or Type of signal of an instance")
      return []
    DiveIntoInstances = True
    if OfModule == self._name:
      DiveIntoInstances = False
    if len(OfInstance) > 0:
      instances = self._instances.getInstancesByName(OfInstance)
      if len(OfModule) > 0 and re.match(OfModule, self._name):
        result += self._signals.getSignalNames(RegexPattern,Direction,Type,GroupBuses)
    else:
      instances = self._instances.getInstancesByName(".*")
      result += self._signals.getSignalNames(RegexPattern,Direction,Type,GroupBuses)
    if self.MyModules is not None and DiveIntoInstances:
      for instance in instances:
        IName = instance.InstanceName
        MName = instance.ModuleName
        Module = self.MyModules.getModuleByName(MName)
        Aux = Module.getSignalNames(RegexPattern, Direction, Type, OfInstance, MName)
        for A in Aux:
          result.append(IName + "." + A)
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
  def countAllSubModules(self) -> int:
    Counter = 0
    SubModules = []
    for i in self._instances:
      MName = i.ModuleName
      if MName not in SubModules:
        Counter += 1
        SubModules.append(MName)
    for mname in SubModules:
      m = self.MyModules.getModuleByName(mname)
      if m is None:
        Counter += 1
      else:
        Counter += m.countAllSubModules()
    return Counter
  def getInstantiationInfo(self):
    Result = {}
    Result["name"] = self._name
    Result["inputs"] = self.getSignalNames(Direction=VerilogSignalDirection.INPUT, OfModule=self._name, GroupBuses=1)
    Result["outputs"] = self.getSignalNames(Direction=VerilogSignalDirection.OUTPUT, OfModule=self._name, GroupBuses=1)
    Result["inouts"] = self.getSignalNames(Direction=VerilogSignalDirection.INOUT, OfModule=self._name, GroupBuses=1)
    Buses = {}
    for i in Result["inputs"] + Result["outputs"] + Result["inouts"]:
      bus = self._signals.getSignalByName(i).getBus()
      if bus[0]-bus[1] <= 0:
        Buses[i] = ""
      else:
        Buses[i] = f"[{bus[0]}:{bus[1]}]"
    Result["buses"] = Buses
    return Result
  def getDependencyInfoString(self, Indentation = "") -> str:
    MyVerilog = self.MyModules.MyVerilog
    if not Aio.isType(MyVerilog, "Verilog"):
      Aio.printError("No Verilog instance!")
      return ""
    Result = ""
    for index in range(len(self._instances)):
      last = (index == len(self._instances)-1)
      myindent = f'{AsciiDrawing_Characters.VERTICAL_RIGTH}{AsciiDrawing_Characters.HORIZONTAL}'
      if last:
        myindent = f'{AsciiDrawing_Characters.LOWER_LEFT}{AsciiDrawing_Characters.HORIZONTAL}'
      i = self._instances[index]
      iname = i.InstanceName
      imodule = MyVerilog.getModuleByName(i.ModuleName)
      imodulename = imodule.getName()
      Result += f'\n{Indentation}{myindent}{iname}  ({imodulename}) {imodule.getDependencyInfoString(Indentation + AsciiDrawing_Characters.VERTICAL + " ")}'
    return Result
      
  
class VerilogModules:
  __slots__ = ("_modules", "IndentationString", "TopModuleName", "MyVerilog")
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
  def __init__(self, MyVerilog) -> None:
    self._modules = []
    self.IndentationString = ""
    self.TopModuleName = ""
    self.MyVerilog = MyVerilog
  def __len__(self) -> int:
    return len(self._modules)
  def __getitem__(self, key) -> VerilogModule:
    return self._modules[key]
  def __repr__(self) -> str:
    return "VerilogModules(" + str(len(self._modules)) + ")"
  def __str__(self) -> str:
    result = self.IndentationString + "VERILOG_MODULES {\n"
    result += self.IndentationString + "top_module_name : " + self.TopModuleName + "\n"
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
          Module = VerilogModule(SModule, self)
          self._modules.append(Module)
        else:
          SModule += Line + "\n"
    if len(self.TopModuleName) < 1 and len(self._modules) > 0:
      self.TopModuleName = self._modules[0].getName()
  def getModules(self) -> list:
    return self._modules
  def getModuleByName(self, Name : str) -> VerilogModule:
    for m in self._modules:
      if m.getName() == Name:
        return m
    return None;
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
  __slots__ = ("Modules", "IndentationString", "Constraints")
  def __init__(self, Content = "") -> None:
    self.Modules = VerilogModules(self)
    if len(Content) > 10:
      self.addContent(Content)
    self.IndentationString = ""
    self.Constraints = VerilogConstraints()
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
    NewTop = self.getBestTopModuleName()
    self.setTopModuleName(NewTop)
  def addConstraint(self, LineString : str) -> None:
    self.Constraints.add(LineString)
  def addContentFromFile(self, FileName : str) -> None:
    self.addContent(readFile(FileName))
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
  def getForceStatementsForSingleStuckAt(self) -> list:
    return [i for i in self.GenerateForceStatementsForSingleStuckAt()]
  def GenerateSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED, OfInstance = "", OfModule = "", GroupBuses = False):
    SNames = self.getSignalNames(RegexPattern, Direction, Type, OfInstance, OfModule, GroupBuses)
    for SName in SNames:
      yield SName
  def GenerateForceStatementsForSingleStuckAt(self):
    for SName in self.GenerateSignalNames():
      for Value in ["1'b0", "1'b1"]:
        yield f"force {SName} = {Value};"
  def GenerateForceModulesForSingleStuckAt(self, ForceMduleName = "force"):
    for Force in self.GenerateForceStatementsForSingleStuckAt():
      yield f"""module {ForceMduleName} ();
  initial begin
    {Force}
  end
endmodule"""
  def getSignalNames(self, RegexPattern = "", Direction = VerilogSignalDirection.UNDEFINED, Type = VerilogSignalType.UNDEFINED, OfInstance = "", OfModule = "", GroupBuses = False) -> list:
    result = []
    ModuleName = OfModule
    if len(ModuleName) < 1 and len(OfInstance) < 1:
      ModuleName = self.Modules.TopModuleName
    for m in self.Modules.getModulesByName(ModuleName):
      for s in m.getSignalNames(RegexPattern,Direction,Type,OfInstance,OfModule,GroupBuses):
        result.append(m.getName() + "." + s)
    return result
  def getContent(self) -> str:
    return self.Modules.getContent()
  def writeToFile(self, FileName = "top.v"):
    writeFile(FileName, self.getContent())
  def writeConstraintsToFile(self, FileName = "constraints.xdc"):
    Text = ""
    for C in self.Constraints:
      Text += C + "\n"
    writeFile(FileName, Text)
  def setTopModuleName(self, ModuleName : str) -> bool:
    if self.Modules.getModuleByName(ModuleName):
      self.Modules.TopModuleName = ModuleName
      return True
    Aio.printError("'" + ModuleName + "' not found in modules.")
    return False
  def getTopModuleName(self) -> str:
    return self.Modules.TopModuleName
  def getTopModule(self) -> VerilogModule:
    return self.Modules.getModuleByName(self.Modules.TopModuleName)
  def synthesize(self, OutputFileName : str, TopModuleName = None, Xilinx = False, TechLibFileName = None, ReturnProcessedResult = False, AreaUnit = "#NAND", AreaFactor = 1, WriteSDF = False, ReportTiming = False):
    if shell_config.useDC():
      tmpFileName = "tmp.v"
      dcScriptFileName = "dc_script"
      self.writeToFile(tmpFileName)
      try: os.remove(".synopsys_dc.setup")
      except: pass
      try: os.remove("adk.db")
      except: pass
      os.symlink(Aio.getPath() + "siemens/synopsys_dc.setup", ".synopsys_dc.setup")
      if TechLibFileName is not None:
        os.symlink(TechLibFileName, "adk.db")
      else:
        os.symlink(Aio.getPath() + "siemens/adk.db", "adk.db")
      DcScript = f"""
analyze -format verilog {tmpFileName}

elaborate {self.Modules.TopModuleName}
link
check_design

compile
report_area

write -format verilog -output {OutputFileName} {self.Modules.TopModuleName} -hier
"""
      if WriteSDF:
        DcScript += f"write_sdf {OutputFileName}.sdf\n"
      if ReportTiming:
        DcScript += f"report_timing -path full -input_pins > {OutputFileName}.rpt\n"
      DcScript += "exit\n"
      writeFile(dcScriptFileName, DcScript)
      result = Aio.shellExecute(f'/home/tnt/tools/DC_SHELL/O-2018.06-SP4/base/bin/dc_shell -f {dcScriptFileName}', 1, 1)
      if ReturnProcessedResult:
        ResDict = {}
        ParamList = ["Number of ports",
                     "Number of nets",
                     "Number of cells",
                     "Number of combinational cells",
                     "Number of sequential cells",
                     "Number of macros/black boxes",
                     "Number of buf/inv",
                     "Number of references",
                     "Combinational area",
                     "Buf/Inv area",
                     "Noncombinational area",
                     "Macro/Black Box area",
                     "Total cell area"]
        for Param in ParamList:
          R = re.search(f'{Param}:\s+([0-9]+)', result, re.MULTILINE)
          if R:
            DictVal = int(R.group(1))
            if "area" in Param:
              DictKey = F"{Param} [{AreaUnit}]"
              DictVal *= AreaFactor
            else:
              DictKey = Param.replace("Number of", "#")
            ResDict[DictKey] = DictVal
        return ResDict
      return result
    else:
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
      result = Aio.shellExecute(f'yosys {ysFileName}', 1, 1)
      return result
    
  def getTopModule(self) -> VerilogModule:
    return self.Modules.getModuleByName(self.Modules.TopModuleName)
  
  def getTopModuleName(self) -> str:
    return self.Modules.TopModuleName
    
  def getModulesDependencyDict(self) -> dict:
    Parents = {}
    Children = {}
    AllChildrenCount = {}
    TopCandidates = []
    for m in self.Modules:
      MName = m.getName()
      ChildList = []
      for i in m.getInstances():
        ChildList.append(i.ModuleName)
      Parents[MName] = []
      Children[MName] = ChildList
      AllChildrenCount[MName] = m.countAllSubModules()
    for parent in Children.keys():
      for child in Children[parent]:
        if Parents.get(child, None) is not None:
          Parents[child].append(parent)
    for child in Parents.keys():
      if len(Parents[child]) == 0:
        TopCandidates.append(child)
    return { "parents" : Parents,
            "children" : Children,
            "top_candidates" : TopCandidates,
            "all_children_count" : AllChildrenCount}
    
  def getBestTopModuleName(self):
    dd = self.getModulesDependencyDict()
    tops = dd["top_candidates"]
    ccounts = dd["all_children_count"]
    besttop = ""
    bestcc = 0
    for top in tops:
      if ccounts[top] > bestcc:
        bestcc = ccounts[top]
        besttop = top
    return besttop
  
  def printDependencyTree(self, BaseModuleName = ""):
    BaseModule = None
    if BaseModuleName == "":
      BaseModule = self.getTopModule()
    else:
      BaseModule = self.getModuleByName(BaseModuleName)
    if BaseModule is None:
      Aio.printError(f"Module '{BaseModuleName}' does not exists.")
      return
    Result = f'{BaseModule.getName()} {BaseModule.getDependencyInfoString()}'
    Aio.print(Result)
    
  def showSchematic(self, DontRemoveVsimWorkspace = False):
    if shell_config.useQuesta():
      Path = f"questa_view/"
      os.mkdir(Path)
      FileName = f"full_verilog.v"
      self.writeToFile(f"{Path}{FileName}")
      copyfile(Aio.getPath() + "siemens/modelsim.ini", "modelsim.ini")
      ERR = Aio.shellExecute(f"cd {Path} && vlog {Aio.getPath()}siemens/pad_cells.v", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"cd {Path} && vlog {Aio.getPath()}siemens/adk.v", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"cd {Path} && vlog {FileName}", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f'''cd {Path} && vsim {self.getTopModuleName()} -debugDB -do "add schematic -full sim:/{self.getTopModuleName()}"''', 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      if not DontRemoveVsimWorkspace:
        try:
          shutil.rmtree(Path[:-1])
        except:
          pass
    else:
      Aio.printError("The 'visualize' feature is only available with Questa sim")
    
    
    
    
    
    
    
  
  
class VerilogTestbenchClock:
  __slots__ = ("Name", "Period", "DutyCycle", "EnableInput")
  def __init__(self, Name : str, Period = 1, DutyCycle = 0.5, EnableInput = False) -> None:
    self.Period = Period
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
    onTimeNs = round(self.DutyCycle * self.Period, 3)
    offTimeNs = round(self.Period - onTimeNs, 3)
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
  __slots__ = ("_my_verilog", "Name", "Clocks", "_code", "_forces", "_catchers", "SimulationStopTime", "TimeUnit", "TimePrecision")
  
  def __init__(self, MyVerilog = Verilog(), Name = "tb", SimulationStopTime = 10000) -> None:
    self._my_verilog = MyVerilog
    self.Name = Name
    self.Clocks = []
    self._code = []
    self._forces = []
    self._catchers = []
    self.SimulationStopTime = SimulationStopTime
    self.TimeUnit = "1ns"
    self.TimePrecision = "1ps"
    
  def __repr__(self) -> str:
    return "VerilogTestbench(" + self.Name + ", " + self._my_verilog.getTopModuleName() + ")"
  
  def __str__(self) -> str:
    return self.getBody()
  
  def setVerilog(self, MyVerilog : Verilog) -> None:
    self._my_verilog = MyVerilog
    
  def getVerilog(self) -> Verilog:
    return self._my_verilog
  
  def getBody(self, RndStr = "", OneTimeForce = "") -> str:
    Result = f'module {self.Name} (' + "\n"
    Result += ");\n\n"
    VII = self._my_verilog.getTopModule().getInstantiationInfo()
    AllInputs = []
    AllOutputs = []
    for Clock in self.Clocks:
      Result += Clock.getSignalDeclaration() + "\n"
      AllInputs.append(Clock.Name)
    for i in VII["inputs"]:
      if i not in AllInputs:
        Result += f'reg{VII["buses"][i]} {i};\n'
        AllInputs.append(i)
    for i in VII["inouts"] + VII["outputs"]:
      if i not in AllOutputs:
        Result += f'wire{VII["buses"][i]} {i};\n'
        AllOutputs.append(i)
    for c in self._catchers:
      sig = c[0]
      Result += f'integer f{sig};\n'
    Result += f'\n'
    Result += f'{VII["name"]} {VII["name"]}_inst (\n'
    AllList = VII["inputs"] + VII["inouts"] + VII["outputs"]
    for i in range(len(AllList)):
      sname = AllList[i]
      if i == len(AllList)-1:
        Result += f'  .{sname} ({sname})\n'
      else:
        Result += f'  .{sname} ({sname}),\n'
    Result += f');\n'
    for Clock in self.Clocks:
      Result += "\n" + Clock.getBody() + "\n"
    if len(self._forces) > 0 or len(OneTimeForce) > 0:
      Result += "\ninitial begin\n"
      if len(OneTimeForce) > 0:
        force = OneTimeForce.replace(f' {VII["name"]}', f' {self.Name}.{VII["name"]}_inst')
        Result += f'  {force}\n'
      for f in self._forces:
        force = str(f).replace(f' {VII["name"]}', f' {self.Name}.{VII["name"]}_inst')
        Result += f'  {force}\n'
      Result += "end\n"
    for c in self._code:
      Result += "\n" + c + "\n";
    if len(self._catchers) > 0:
      for c in self._catchers:
        sig = c[0]
        time = c[1]
        Result += "\ninitial begin"
        Result += f"""  
  f{sig} = $fopen("{sig}{RndStr}.catch", "w");
  #{time};
  $fdisplayh(f{sig}, {sig});
  $fclose(f{sig});\n"""
        Result += "end\n"
    Result += f"\ninitial begin\n"
    Result += f"  #{self.SimulationStopTime};\n  $stop;\n"
    Result += f"end\n"
    Result += "\nendmodule"
    return Result
  
  def addClock(self, TBClock : VerilogTestbenchClock):
    self.Clocks.append(TBClock)
    
  def createClock(self, Name : str, Period = 1, DutyCycle = 0.5, EnableInput = False) -> VerilogTestbenchClock:
    Clock = VerilogTestbenchClock(Name, Period, DutyCycle, EnableInput)
    self.Clocks.append(Clock)
    return Clock  
  
  def addVerilogCode(self, VerilogCode : str):
    self._code.append(VerilogCode)
  
  def addSignalCatcher(self, SignalName : str, CatchingTime : int):
    self._catchers.append([str(SignalName), CatchingTime])
  
  def addForce(self, ForceLine : str):
    self._forces.append(ForceLine)
  
  def getForces(self) -> list:
    return self._forces
  
  def removeForce(self, ForceLine : str):
    self._forces.remove(ForceLine)

  def clearForces(self):
    self._forces.clear()
    
  def writeFullVerilog(self, FileName = "verilog_testbench_full.v", RndStr = "", OneTimeForce = ""):
    writeFile(FileName, f'''`timescale {self.TimeUnit}/{self.TimePrecision}\n\n''' + self.getBody(RndStr, OneTimeForce) + "\n\n" + self._my_verilog.getContent())

  def showSchematic(self, DontRemoveVsimWorkspace = False):
    if shell_config.useQuesta():
      Path = f"questa_view/"
      os.mkdir(Path)
      FileName = f"full_tb.v"
      self.writeFullVerilog(f"{Path}{FileName}")
      copyfile(Aio.getPath() + "siemens/modelsim.ini", "modelsim.ini")
      ERR = Aio.shellExecute(f"cd {Path} && vlog {Aio.getPath()}siemens/pad_cells.v", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"cd {Path} && vlog {Aio.getPath()}siemens/adk.v", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"cd {Path} && vlog {FileName}", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f'''cd {Path} && vsim {self.Name} -debugDB -do "add schematic -full sim:/{self.Name}"''', 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      if not DontRemoveVsimWorkspace:
        try:
          shutil.rmtree(Path[:-1])
        except:
          pass
    else:
      Aio.printError("The 'visualize' feature is only available with Questa sim")
    
  def simulate(self, OneTimeForce = "") -> dict:
    RndStr = str(int(uniform(1, 99999999999999)))
    Path = ""
    if shell_config.useQuesta():
      Path = f"questa_{RndStr}/"
      os.mkdir(Path)
      FileName = f"full_tb.v"
      self.writeFullVerilog(f"{Path}{FileName}", RndStr, OneTimeForce)
      copyfile(Aio.getPath() + "siemens/modelsim.ini", "modelsim.ini")
      ERR = Aio.shellExecute(f"cd {Path} && vlog {Aio.getPath()}siemens/pad_cells.v", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"cd {Path} && vlog {Aio.getPath()}siemens/adk.v", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"cd {Path} && vlog {FileName}", 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
      Batch = f'''
run {self.SimulationStopTime} {self.TimeUnit}
quit -f
'''
      ERR = Aio.shellExecute(f'''cd {Path} && vsim {self.Name} <<! {Batch}''', 1, 1)
      if re.match(r'Errors:\s*[1-9]', ERR, re.MULTILINE):
        Aio.print(ERR)
    else:
      FileName = f"full_tb{RndStr}.v"
      self.writeFullVerilog(FileName, RndStr, OneTimeForce)
      WorkFile = f'work_design{RndStr}.iverilog'
      ERR = Aio.shellExecute(f"iverilog -o {WorkFile} {FileName}", 0, 1)
      if len(ERR) > 2:
        Aio.print(ERR)
      ERR = Aio.shellExecute(f"vvp -n {WorkFile}", 0, 1)
      if len(ERR) > 2:
        Aio.print(ERR)
      os.remove(WorkFile)
      os.remove(FileName)
    Result = {}
    for c in self._catchers:
      name = c[0]
      CFname = f"{Path}{name}{RndStr}.catch"
      try:
        Result[name] = readFile(CFname)
        os.remove(CFname)
      except:
        Result[name] = None
    if len(Path) > 1:
      try:
        shutil.rmtree(Path[:-1])
      except:
        pass
    return Result
  
  def simulateSingleStuckAtFaults(self):
    reference = self.simulate()
    Forces = self._my_verilog.getForceStatementsForSingleStuckAt()
    FaultsCount = len(Forces)
    NotDetectable = []
    Results = p_map(self.simulate, Forces)
    for i in range(len(Forces)):
      result = Results[i]
      force = Forces[i]
      IsDetectable = 0
      for k in reference.keys():
        if result[k] != reference[k] and result[k] is not None :
          IsDetectable = 1
          break
      if not IsDetectable:
        NotDetectable.append(force)
    DetectableCounter = FaultsCount - len(NotDetectable)
    Coverage = round(DetectableCounter * 100 / FaultsCount , 2)
    Aio.print(f'Single stuck-at simulation finished.')
    if len(NotDetectable) > 0:
      Aio.print(f'Not detectable faults:')
      for force in NotDetectable:
        Aio.print(f'  {force}')
    Aio.print(f'Fault coverage: {Coverage} %')
    return [Coverage, NotDetectable]
          
