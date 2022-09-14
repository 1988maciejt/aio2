from queue import Full


class SimpleCommandParameter:
  Name = ""
  DefaultValue = None
  HelpText = ""
  Bool = False
  Positional = False
  CaseSensitive = True
  _used = False
  def __init__(self, Name : str, DefaultValue = None, HelpText = "", Bool = False, Positional = False, CaseSensitive = True) -> None:
    self.Name = Name
    self.HelpText = HelpText
    self.Bool = Bool
    self.Positional = Positional
    self.CaseSensitive = CaseSensitive
    if Bool:
      self.DefaultValue = False
    else:
      self.DefaultValue = DefaultValue
  def getSyntax(self) -> str:
    Result = self.Name
    if self.Positional:
      Result = "<" + Result + ">" 
    else:
      if not self.Bool:
        Result += " <Value>"
      if self.DefaultValue == None or self.Bool:
        Result = "[" + Result + "]"  
    return Result
  def getHelp(self) -> str:
    Result = self.Name
    if self.Positional:
      Result = "<" + Result + ">\t" 
    else:
      if self.Bool:
        Result += "\t(optional) "
      else:
        Result += " <Value>\t"
        if self.DefaultValue == None:
          Result += "(optional, default: " + self.DefaultValue + ") "
    Result += self.HelpText
    return Result
  def matching(self, Candidate : str) -> float:
    n = self.Name
    c = Candidate
    if len(c) > len(n):
      return 0.0
    if not self.CaseSensitive:
      n = n.lower()
      c = c.lower()
    if n.startswith(c):
      return float(len(c)) / float(len(n))
    return 0.0 

class SimpleCommand:
  Name = ""
  HelpText = ""
  CaseSensitive = True
  Callback = None
  def __init__(self, Name : str, Callback = None, HelpText = "", CaseSensitive = True) -> None:
    self.Name = Name
    self.HelpText = HelpText
    self.CaseSensitive = CaseSensitive
    self.Callback = Callback
    self._params = []
  def addParameter(self, Parameter : SimpleCommandParameter):
    self._params.append(Parameter)
  def getSyntax(self) -> str:
    Result = self.Name 
    for p in self._params:
      Result += " " + p.getSyntax()
    return Result
  def getHelp(self) -> str:
    Result = self.getSyntax() + "\n"
    if self.HelpText != "":
      Result += "\n" + self.HelpText + "\n"
    if len(self._params) > 0:
      Result += "\nPARAMETERS:\n"
    for p in self._params:
      Result += "\n " + p.getHelp()
    return Result
  def matching(self, Candidate : str) -> float:
    n = self.Name
    c = Candidate
    if len(c) > len(n):
      return 0.0
    if not self.CaseSensitive:
      n = n.lower()
      c = c.lower()
    if n.startswith(c):
      return float(len(c)) / float(len(n))
    return 0.0 

class SimpleCommandParser:
  def addCommand(self, Command : SimpleCommand):
    self._cmds.append(Command)
  def __init__(self, AddHelpCommand = True) -> None:
    self._cmds = []
    if AddHelpCommand:
      c = SimpleCommand("help", CaseSensitive=False, Callback=SimpleCommandGetHelp, HelpText="Returns help of a given command name")
      c.addParameter(SimpleCommandParameter("name", HelpText="Command name", Positional=True))
      self.addCommand(c)
  def getCommandByName(self, Name : str):
    BestMatch = 0.0
    Command = None
    for c in self._cmds:
      WordMatching = c.matching(Name)
      if WordMatching > BestMatch:
        BestMatch = WordMatching
        Command = c
    return Command
  def getCommandNames(self, FullSyntax = False, Sorted = True) -> list:
    Result = []
    for c in self._cmds:
      if FullSyntax:
        Result.append(c.getSyntax())
      else:
        Result.append(c.Name)
    if Sorted:
      Result.sort()
    return Result
  def parse(self, Text : str) -> dict:
    Result = { "CMD": None, "ERR" : [], "CBK": None, "MYPARSER": self}
    Words = []
    Word = ""
    LongWord = False
    for c in Text:
      if c in [" ", "\t", "\r", "\n"]:
        if LongWord:
          Word += c
        elif len(Word) > 0:
          Words.append(Word)
          Word = ""
      elif c == '"':
        if LongWord:
          Words.append(Word)
          Word = ""
          LongWord = False
        elif Word == "":
          LongWord = True
        else:
          Word += c
      else:
        Word += c
    if len(Word) > 0:
      Words.append(Word)
    if len(Words) < 1: 
      return Result
    Skip = False
    BestMatch = 0.0
    Command = None
    Word = Words[0]
    for c in self._cmds:
      WordMatching = c.matching(Word)
      if WordMatching > BestMatch:
        BestMatch = WordMatching
        Command = c
    if BestMatch < 0.001:
      return Result
    Result["CMD"] = Command
    Result["CBK"] = Command.Callback  
    for p in Command._params:
      Result[p.Name] = p.DefaultValue
      p._used = False
    for i in range(1, len(Words)):
      if Skip:
        Skip = False
        continue
      Word = Words[i] 
      BestMatch = 0.0
      Parameter = None
      for p in Command._params:
        if p._used:
          continue
        if p.Positional:
          BestMatch = 1
          Parameter = p
          break    
        else:
          WordMatching = p.matching(Word)
          if WordMatching == BestMatch:       
            BestMatch = 0
            break
          if WordMatching > BestMatch:
            BestMatch = WordMatching
            Parameter = p
      if BestMatch > 0.001:
        if Parameter.Positional:
          Result[Parameter.Name] = Word
        else:
          if Parameter.Bool:
            Result[Parameter.Name] = True
          else:
            Result[Parameter.Name] = Words[i+1]
            Skip = True
        Parameter._used = True
      else:
        el = Result["ERR"]
        el.append("Unknown parameter " + Word)
        Result["ERR"] = el
    return Result     
  def execute(self, CommandLine : str):
    Dict = self.parse(CommandLine)
    Err = Dict["ERR"]
    if len(Err) > 0:
      ErrStr = "Execution error!\n"
      ErrStr += "Call: '" + CommandLine + "'\n"
      for e in Err:
        ErrStr += "   " + e + "\n"
      return ErrStr
    Callback = Dict["CBK"]
    if Callback:
      return Callback(Dict)
    else:
      return ("ERROR: No callback during execution of '" + CommandLine + "'")
    
  
def SimpleCommandGetHelp(args):
  Parser = args["MYPARSER"]
  Name = args["name"]
  Command = Parser.getCommandByName(Name)
  if Command:
    HelpText = "\n" + Command.getHelp() + "\n"
  else:
    HelpText = "Command '" + Name + "' not found."
  return HelpText