from prompt_toolkit.shortcuts import *
from libs.aio import *
from libs.pandas_table import *

class AioHelpArgument:
  __slots__ = ("Name", "Type", "Description", "Default")
  def __init__(self, Name : str, Description : str, Type = None, Default = None):
    self.Name = Name
    self.Type = Type
    self.Description = Description
    self.Default = Default
  
class AioHelpCategory:
  __slots__ = ("Name", "Description", "Items", "Arguments", "Parent")
  def __init__(self, Name : str, Description : str, Parent = None, Arguments = None):
    self.Name = Name
    self.Description = Description
    self.Items = []
    if Arguments is None:
      self.Arguments = {}
    else:
      self.Arguments = Arguments
    self.Parent = Parent
  def sortKey(self):
    return f'_{self.Name}'
  def showSearch(self, Text):
    Values = self.search(Text)
    if len(Values) < 1:
      message_dialog(title=self.Name, text=f"SEARCH FOR '{Text}'\n\nNO RESULTS.").run()
    else:
      Dialog = radiolist_dialog(title=self.Name, text=f"SEARCH FOR '{Text}'", values=Values)
      Result = "?"
      while Result is not None:
        Result = Dialog.run()
        if Result is not None:
          Result()
  def search(self, Text, ParentNames = ""):
    PNames = ""
    if len(self.Name) > 0:
      PNames = f'{self.Name} >> '
    if len(ParentNames) > 0:
      PNames = f'{ParentNames}{PNames}'
    Results = []
    ltext = str(Text).lower()
    if ltext in self.Name.lower():
      Results.append(self.getRadioListItem(ParentNames))
    else:
      for I in self.Items:
        if Aio.isType(I, "AioHelpCategory"):
          Results += I.search(Text, PNames)
        else:
          if ltext in I.Name.lower():
            Results.append(I.getRadioListItem(PNames))
    return Results
  def show(self):
    Values = []
    for I in self.Items:
      Text = "?"
      if Aio.isType(I, "AioHelpCategory"):
        Text = f'{I.Name}  >>'
      elif Aio.isType(I, "AioHelpProc"):
        Text = f'proc {I.Name}()'
      else:
        Text = f'{I.Name}'
      Values.append((I.show, Text))
    if len(Values) < 1:
      message_dialog(title=self.Name, text=self.Description).run()
    else:
      Dialog = radiolist_dialog(title=self.Name, text=self.Description, values=Values)
      Result = "?"
      while Result is not None:
        Result = Dialog.run()
        if Result is not None:
          Result()
  def addItem(self, Item):
    self.Items.append(Item)
    self.Items.sort(key=lambda x: x.sortKey())
    Item.Parent = self
  def addArgument(self, Arg : AioHelpArgument):
    self.Arguments[Arg.Name] = Arg
  def getArgument(self, Name):
    Result = self.Arguments.get(Name, None)
    if Result is None:
      if self.Parent is not None:
        return self.Parent.getArgument(Name)
    return Result
  def getRadioListItem(self, ParentNames=""):
    return (self.show, f'{ParentNames}{self.Name} >>')
  
class AioHelpProc:
  __slots__ = ("Name", "Arguments", "Description", "Parent")
  def __init__(self, Name : str, Description : str, Arguments : list, Parent = None):
    self.Name = Name
    self.Arguments = Arguments
    self.Description = Description
    self.Parent = Parent
  def show(self):
    message_dialog(title=self.Name, text=self.getFullString()).run()
  def sortKey(self):
    return f'proc_{self.Name}'
  def addArgument(self, ArgName : str):
    self.Arguments.append(ArgName)
  def getRadioListItem(self, ParentNames=""):
    return (self.show, f'proc {ParentNames}{self.Name}()')
  def getFullString(self) -> str:
    ArgList = []
    ArgTable = PandasTable([" ARGUMENT ", " TYPE ", " DEFAULT ", " DESCRIPTION "], 0, 0)
    if len(self.Arguments) > 0 and self.Parent is not None:
      for ArgName in self.Arguments:
        Arg = self.Parent.getArgument(ArgName)
        if Arg is None:
          ArgList.append(ArgName)
        if Arg is not None:
          if Arg.Default is None:
            ArgList.append(ArgName)
          else:
            ArgList.append(f'{ArgName}={Arg.Default}')         
          Name = Arg.Name
          Description = Arg.Description
          Default = Arg.Default
          if Default is None:
            Default = "-"
          Type = Arg.Type
          if Type is None:
            Type = "<any>"
          elif Aio.isType(Type, []):
            Aux = ""
            First = 1
            for T in Type:
              if not First:
                Aux += f',{T}'
              else:
                Aux += f'{T}'
              First = 0
            Type = Aux
          ArgTable.add([Name, Type, Default, Description])
    Usage = ""
    First = 1
    for A in ArgList:
      if First:
        Usage += f'{A}'
        First = 0
      else:
        Usage += f', {A}'
    Usage = f'{self.Name} ({Usage})'
    Args = ArgTable.toString("left") if len(ArgTable) > 0 else ""
    Result = f'{Usage}\n\n{self.Description}\n\n{Args}'
    return Result
          
  
def aioHelpCatExists(Name):
  global AioHelpGlobal
  Exists = 0
  for I in AioHelpGlobal.Items:
    if I.Name == Name:
      Exists = 1
      break
  return Exists
  
def addAioHelpCategory(Category : AioHelpCategory, SkipChecking = 0):
  global AioHelpGlobal
  if SkipChecking or not aioHelpCatExists(Category.Name):
    AioHelpGlobal.addItem(Category)
  
def aiohelp(Pattern = ""):
  global AioHelpGlobal
  if len(Pattern) > 0:
    AioHelpGlobal.showSearch(Pattern)
  else:
    AioHelpGlobal.show()
  
    
    
    
##########################################################
#  Creating HELP                                         #
##########################################################
if 'AioHelpGlobal' not in locals():
  
  ### AIO ################################################
  AioHelpGlobal = AioHelpCategory("", "Maciej Trawka's All-In-One v2")
  AioGroup = AioHelpCategory("AIO", "All-In-One v2 related classes and procs.")
  AioGroup.addArgument(AioHelpArgument("Code", "A string containing Python code", ["str"]))
  AioGroup.addArgument(AioHelpArgument("Iterations", "How many times repeat the given code", ["int"], 1))
  AioGroup.addItem(AioHelpProc(
    Name="timeIt",
    Description="""Measures execution time of the given code.""",
    Arguments=["Code", "Iterations"]
  ))
  
  ### AIO >> Aio #########################################
  AioCat = AioHelpCategory("class Aio", "Includes general All-In-One helper procs.")
  AioCat.addArgument(AioHelpArgument("Object", "Any object"))
  AioCat.addArgument(AioHelpArgument("object", "Any data", ["list","dict","any"]))
  AioCat.addArgument(AioHelpArgument("ItsType", "Reference object or string containing type name", ["any", "string"]))
  AioCat.addArgument(AioHelpArgument("indent", "How many indentation spaces to add", ["int"], 0))
  AioCat.addArgument(AioHelpArgument("Repr", "If True, use 'repr' method instead of 'str'", ["bool"], False))
  AioCat.addArgument(AioHelpArgument("FileName", "HTML transcript file name (relative path)", ["str"], "transcript.html"))
  AioCat.addArgument(AioHelpArgument("Dark", "If True, use dark theme", ["bool"], True))
  AioCat.addArgument(AioHelpArgument("WrapLines", "If True, wraps lines", ["bool"], False))
  AioCat.addArgument(AioHelpArgument("Linkify", "If True, uses linkified version", ["bool"], True))
  AioCat.addArgument(AioHelpArgument("SectionName", "Section / Subsection name", ["str"]))
  AioCat.addArgument(AioHelpArgument("ShellCommand", "Command to execute", ["str"]))
  AioCat.addArgument(AioHelpArgument("StdOut", "Catch standard output stream", ["bool"], True))
  AioCat.addArgument(AioHelpArgument("StdErr", "Catch error output stream", ["bool"], False))
  AioCat.addArgument(AioHelpArgument("num", "Integer number", ["int"]))
  AioCat.addArgument(AioHelpArgument("cstring", "Number stores as compressed string", ["str"]))
  AioCat.addItem(AioHelpProc(
    Name="Aio.isType",
    Description="""Returns True, if an Object's type is equal to the referenced type.
    
    EXAMPLE:
    Aio.isType([1,2,3], []) -> True
    Aio.isType([1,2,3], "list") -> True
    Aio.isType([1,2,3], 123) -> False""",
    Arguments=["Object", "ItsType"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.format",
    Description="""Returns a multiline string containing formatted data, especially list or dictionary.""",
    Arguments=["object", "indent", "Repr"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.getTerminalColumns",
    Description="""Returns count of terminal columns.""",
    Arguments=[]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.getTerminalRows",
    Description="""Returns count of terminal rows.""",
    Arguments=[]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.getPath",
    Description="""Returns absolute path to the AIO bin directory.""",
    Arguments=[]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.transcriptToHTML",
    Description="""Saves transcript as HTML.""",
    Arguments=["FileName", "Dark", "WrapLines", "Linkify"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.resetTranscript",
    Description="""Clears the transcript cache. Useful to divide HTML transcript into many files.\nSee Aio.transcriptToHTML() for more details.""",
    Arguments=[]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.print",
    Description="""Does the same as standard Python's print(*args) proc.
The only difference is, that if Aio2 executes a testcase, then prints also to the transcript.""",
    Arguments=["*args"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.printError",
    Description="""Does the same as standard Python's print("ERROR:", *args) proc.
The only difference is, that if Aio2 executes a testcase, then prints also to the transcript.""",
    Arguments=["*args"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.printTemp",
    Description="""Does the same as standard Python's print(*args) proc, but the printed
text will be overwritten by next print() call.
Usefull for progress bars, and so on.""",
    Arguments=["*args"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.transcriptSectionBegin",
    Description="""Creates transcript section.""",
    Arguments=["SectionName"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.transcriptSubsectionBegin",
    Description="""Creates transcript subsection.""",
    Arguments=["SectionName"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.shellExecute",
    Description="""Executes a shell command (with args) and returns a string containing output stream.""",
    Arguments=["ShellCommand", "StdOut", "StdErr"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.numToCompressedString",
    Description="""Returns a compressed string containing a given integer.
Usefull to store integer numbers in text files (not human-readable, but space saving).
Use Aio.compressedStringToNum() to revert that operation.""",
    Arguments=["num"]
  ))
  AioCat.addItem(AioHelpProc(
    Name="Aio.compressedStringToNum",
    Description="""Converts compressed-string into integer.
Used as opposite to Aio.numToCompressedString().""",
    Arguments=["cstring"]
  ))
  
  AioGroup.addItem(AioCat)
  addAioHelpCategory(AioGroup, 1)
  
    
  ### BentFunction #######################################
  BentFunctionCat = AioHelpCategory("class BentFunction", "Useful for bent functions analysis.")
  BentFunctionCat.addArgument(AioHelpArgument("self", "BentFunction object", ["BentFunction"]))
  BentFunctionCat.addArgument(AioHelpArgument("Source", "Pointer to source value (i.e. Lfsr value, or so on)", ["bitarray"]))
  BentFunctionCat.addArgument(AioHelpArgument("MapList", "List of source value bit indexes used to compute output value", ["list"]))
  BentFunctionCat.addArgument(AioHelpArgument("LUT", "Bent function look-up-table", ["bitarray"]))
  BentFunctionCat.addArgument(AioHelpArgument("InputCount", "Bent function input count", ["int"]))
  BentFunctionCat.addArgument(AioHelpArgument("n", "Requested count of results (0 means 'no limit')", ["int"], 0))
  BentFunctionCat.addItem(AioHelpProc(
    Name="BentFunction.__init__",
    Description="""BentFunction object constructor.""",
    Arguments=["self", "Source", "MapList", "LUT"]
  ))
  BentFunctionCat.addItem(AioHelpProc(
    Name="BentFunction.value",
    Description="""Computes and returns BentFunction value.""",
    Arguments=["self"]
  ))
  BentFunctionCat.addItem(AioHelpProc(
    Name="BentFunction.listBentFunctionLuts",
    Description="""Search for bent function LUTs.
Returns a list of bitarray objects (LUTs).""",
    Arguments=["InputCount", "n"]
  ))
  
  addAioHelpCategory(BentFunctionCat, 1)
  
    
  ### Polys, LFSR, CA, NLFSR #############################
  LfsrPolysGroup = AioHelpCategory("LFSR, NLFSR, CA, POLYNOMIALS", "Includes classes usefull for primitive polynomials, Lfsr, Ca, Nlfsr analysis.")
  PolynomialCat = AioHelpCategory("class Polynomial", "Polynomial GF(2) object and utilities.\nPolynomial objects are also iterators.")
  PolynomialCat.addArgument(AioHelpArgument("self", "Polynomial object", ["Polynomial"]))
  PolynomialCat.addArgument(AioHelpArgument("coefficients_list", "List of all polynomial's coefficients", ["list","Polynomial","int","hex_string"]))
  PolynomialCat.addArgument(AioHelpArgument("CoefficientList", "List of all polynomial's coefficients", ["list"]))
  PolynomialCat.addArgument(AioHelpArgument("balancing", "Difference between farthest and closed distance between successive coefficients", ["int"], 0))
  PolynomialCat.addArgument(AioHelpArgument("CoeffsCount", "Specifies coefficients count of the candidate polynomials (0 = no limit)", ["int"], 0))
  PolynomialCat.addArgument(AioHelpArgument("DontTouchBounds", "If True, highest and lowest coefficients are not touched", ["bool"], True))
  PolynomialCat.addArgument(AioHelpArgument("OddOnly", "If True, lists only polys having odd coefficients count", ["bool"], True))
  PolynomialCat.addArgument(AioHelpArgument("IncludeDegree", "if True, the highest coefficients is included", ["bool"], True))
  PolynomialCat.addArgument(AioHelpArgument("shorten", "If True, lists only polys having odd coefficients count", ["bool"], True))
  PolynomialCat.addArgument(AioHelpArgument("Silent", "If False, additional info is temporarily printed during operation", ["bool"], True))
  PolynomialCat.addArgument(AioHelpArgument("degree", "Polynomial's degree", ["int"]))
  PolynomialCat.addArgument(AioHelpArgument("coeffs_count", "Coefficient count (including degree and 0)", ["int"]))
  PolynomialCat.addArgument(AioHelpArgument("LayoutFriendly", "Only layout-friendly polynomials", ["bool"], False))
  PolynomialCat.addArgument(AioHelpArgument("MinimumDistance", "Minimum allowed distance between successive coefficients", ["int"], 0))
  PolynomialCat.addArgument(AioHelpArgument("NoResultsSkippingIteration", "if equal to X>0, then breaks if no results after X iterations", ["int"], 0))
  PolynomialCat.addArgument(AioHelpArgument("MaxSetSize", "How many polys should be tested at one shot in parallel", ["int"], 10000))
  PolynomialCat.addArgument(AioHelpArgument("ExcludeList", "List of polynomials to exclude from testing", ["list"]))
  PolynomialCat.addArgument(AioHelpArgument("FilteringCallback", "Filtering callback. Must be a proc returning bool (True = acceptable)", ["proc"], None))
  PolynomialCat.addArgument(AioHelpArgument("ReturnAlsoAllCandidaes", "If True, returns a list of 2 lists:Results and Candidates", ["bool"], False))
  PolynomialCat.addArgument(AioHelpArgument("StartBalancing", "Start searching from this balancing value", ["int"], 1))
  PolynomialCat.addArgument(AioHelpArgument("EndBalancing", "Stop searching at this balancing value", ["int"], 10))
  PolynomialCat.addArgument(AioHelpArgument("EveryN", "Average distance between successive taps", ["int"]))
  PolynomialCat.addArgument(AioHelpArgument("max_distance", "Maximum distance between successive taps", ["int"], 3))
  PolynomialCat.addArgument(AioHelpArgument("Sequence", "Sequence of bits (any generator/iterator) or Lfsr object", ["bitarray,Lfsr,str,any"]))
  PolynomialCat.addArgument(AioHelpArgument("StartingPolynomial", "Starting Polynomial of coefficients list", ["Polynomial,list"], "None"))
  PolynomialCat.addArgument(AioHelpArgument("AnotherPolynomial", "Polynomial of coefficients list", ["Polynomial,list"]))
  PolynomialCat.addArgument(AioHelpArgument("MinNotMatchingTapsCount", "Min count of different taps", ["int"], 0))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.__init__",
    Description="""Polynomial object constructor.""",
    Arguments=["self", "coefficients_list", "balancing"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getDifferentTapCount",
    Description="""Returns a numbers meaning: how many taps in this Polynomial is different from taps in another one.""",
    Arguments=["self", "AnotherPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getDifferentTaps",
    Description="""Returns a list of taps which are NOT a part of another Polynomial.""",
    Arguments=["self", "AnotherPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.copy",
    Description="""Returns a fdeep copy of Polynomial object.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printAllPrimitivesHavingSpecifiedCoeffs",
    Description="""Prints all primitive polynomials having coefficients included in a given list.""",
    Arguments=["CoefficientList", "CoeffsCount", "DontTouchBounds", "OddOnly"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.listAllPrimitivesHavingSpecifiedCoeffs",
    Description="""Returns a list of all primitive polynomials having coefficients included in a given list.""",
    Arguments=["CoefficientList", "CoeffsCount", "DontTouchBounds", "OddOnly"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getAllHavingSpecifiedCoeffs",
    Description="""Returns a list of all polynomials having coefficients included in a given list.""",
    Arguments=["CoefficientList", "CoeffsCount", "DontTouchBounds", "OddOnly"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.toKassabStr",
    Description="""Returns a string containing polynomial dexription consistent with Mark Kassab's C++ code.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printFullInfo",
    Description="""Prints full information about the polynomial.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.toHexString",
    Description="""Returns a string containing polynomial description in hexadecimal convention.""",
    Arguments=["self", "IncludeDegree", "shorten"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getCoefficients",
    Description="""Returns list of coefficients.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getCoefficientsCount",
    Description="""Returns coefficients count.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getReciprocal",
    Description="""Returns reciprocal version of polynomial.
    
    For example:
    Polynomial([6,4,3,1,0]).getReversed() -> Polynomial([6,5,3,2,0]).""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getDegree",
    Description="""Returns polynomials degree.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getTapsCount",
    Description="""Returns LFSR taps count in case of a LFSR created basing on this polynomial.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getMinimumDistance",
    Description="""Calculates and returns the minimum distance between successive coefficients.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.getBalancing",
    Description="""Calculates and returns the balaning factor of the polynomial.
Balancing is the difference between farthest and closest distance between successive coefficients.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.toInt",
    Description="""Returns an integer representing the given polynomial.
    
    For example:
    bin(Polynomial([3,1,0]).toInt()) -> 0b1011.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.toBitarray",
    Description="""Returns an bitarray object representing the given polynomial.
    
    For example:
    bin(Polynomial([3,1,0]).toInt()) -> bitarray('1011').""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.isPrimitive",
    Description="""Returns True if the polynomial is primitive.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.nextPrimitive",
    Description="""Returns next primitive Polynomial (from the same Polynomials class).""",
    Arguments=["self", "Silent"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.isLayoutFriendly",
    Description="""Returns True if the polynomial is layout-friendly.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.createPolynomial",
    Description="""Returns first polynomial having specified properties.
Such polynomial may be used as generator, for example:
    
    poly0 = Polynomial.createPolynomial(8, 3, 3)
    for poly in poly0:
      print(poly)
      
    >>> [8, 3, 0]
    >>> [8, 4, 0]
    >>> [8, 5, 0]""",
    Arguments=["degree", "coeffs_count", "balancing", "LayoutFriendly", "MinimumDistance"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.checkPrimitives",
    Description="""Filters candidates and returns only primitive ones.""",
    Arguments=["Candidates", "n", "Silent"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.toTigerStr",
    Description="""Returns tiger repsentation of the Polynomial object.
    
    For example:
    Polynomial([5,3,2,1,0]).toTigerStr() -> '[5, -3, 2, -1, 0]'""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.listTigerPrimitives",
    Description="""Returns a list of tiger primitives (polys defining a tiger ring).""",
    Arguments=["degree", "coeffs_count", "balancing", "LayoutFriendly", "MinimumDistance", "n", "NoResultsSkippingIteration","StartingPolynomial","MinNotMatchingTapsCount"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printTigerPrimitives",
    Description="""Prints tiger primitives (polys defining a tiger ring).""",
    Arguments=["degree", "coeffs_count", "balancing", "LayoutFriendly", "MinimumDistance", "n", "NoResultsSkippingIteration","StartingPolynomial","MinNotMatchingTapsCount"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.listPrimitives",
    Description="""Returns a list of primitive polynomials.""",
    Arguments=["degree", "coeffs_count", "balancing", "LayoutFriendly", "MinimumDistance", "n", "Silent", "MaxSetSize", "ExcludeList", "FilteringCallback", "ReturnAlsoAllCandidaes", "NoResultsSkippingIteration","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printPrimitives",
    Description="""Prints primitive polynomials.""",
    Arguments=["degree", "coeffs_count", "balancing", "LayoutFriendly", "MinimumDistance", "n", "Silent", "MaxSetSize", "ExcludeList", "FilteringCallback", "NoResultsSkippingIteration","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.firstPrimitive",
    Description="""Returns first found primitive polynomial.""",
    Arguments=["degree", "coeffs_count", "balancing", "LayoutFriendly", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.firstMostBalancedPrimitive",
    Description="""Returns first found most balanced primitive polynomial.""",
    Arguments=["degree", "coeffs_count", "StartBalancing", "EndBalancing", "LayoutFriendly", "Silent"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.firstEveryNTapsPrimitive",
    Description="""Returns first found primitive polynomial having specified, average distance between successive coefficients.""",
    Arguments=["degree", "EveryN", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.listEveryNTapsPrimitives",
    Description="""Returns list of primitive polynomials having specified, average distance between successive coefficients.""",
    Arguments=["degree", "EveryN", "n", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printEveryNTapsPrimitives",
    Description="""Prints primitive polynomials having specified, average distance between successive coefficients.""",
    Arguments=["degree", "EveryN", "n", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.firstDensePrimitive",
    Description="""Returns first found dense primitive polynomial.""",
    Arguments=["degree", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.listDensePrimitives",
    Description="""Returns list of dense primitive polynomials.""",
    Arguments=["degree", "n", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printDensePrimitives",
    Description="""Prints dense primitive polynomials.""",
    Arguments=["degree", "n", "Silent","StartingPolynomial"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.firstTapsFromTheLeftPrimitive",
    Description="""Returns first found primitive polynomial having taps grouped close to the left side.""",
    Arguments=["degree", "coeffs_count", "max_distance", "Silent"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.listTapsFromTheLeftPrimitives",
    Description="""Returns list primitive polynomials having taps grouped close to the left side.""",
    Arguments=["degree", "coeffs_count", "max_distance", "n", "Silent"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.printTapsFromTheLeftPrimitives",
    Description="""Prints primitive polynomialshaving taps grouped close to the left side.""",
    Arguments=["degree", "coeffs_count", "max_distance", "n", "Silent"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.decodeUsingBerlekampMassey",
    Description="""Returns Polynomial decoded from the given sequence of bits using Berlekamp-Massey algorithm.
Available argument for this proc is also Lfsr object.""",
    Arguments=["Sequence"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.derivativeGF2",
    Description="""Returns new Polynomial being a GF(2) derivative of the given one.""",
    Arguments=["self"]
  ))
  PolynomialCat.addItem(AioHelpProc(
    Name="Polynomial.setStartingPointForIterator",
    Description="""Sets starting point for using the Polynomial object as an iterator.
Returns True, if the new starting point is set correctly, returns False if verification of the new one failed.

To reset the starting point set StartingPolynomial=None.""",
    Arguments=["self","StartingPolynomial"]
  ))
  
  LfsrTypeCat = AioHelpCategory("enum LfsrType", """Type of a Lfsr.\n
  LfsrType.Galois                        alias: GALOIS
  LfsrType.Fibonacci                     alias: FIBONACCI  
  LfsrType.RingGenerator                 alias: RING_GENERATOR
  LfsrType.RingWithSpecifiedTaps         alias: RING_WITH_SPECIFIED_TAPS
  LfsrType.TigerRing                     alias: TIGER_RING
  """)
  
  LfsrCat = AioHelpCategory("class Lfsr", "Class used to simulate LFSRs.\nLfsr objects are also iterators.")
  LfsrCat.addArgument(AioHelpArgument("self", "Lfsr object", ["Lfsr"]))
  LfsrCat.addArgument(AioHelpArgument("polynomial", "Polynomial, other Lfsr or size of the Lfsr in case of RingWithSpecifiedTaps", ["Polynomial,list,int"]))
  LfsrCat.addArgument(AioHelpArgument("lfsr_type", "Type of the Lfsr object", ["LfsrType"], "LfsrType.Fibonacci"))
  LfsrCat.addArgument(AioHelpArgument("manual_taps", "List of taps: [ [Source, Dest], ...]", ["list"]))
  LfsrCat.addArgument(AioHelpArgument("TapIndex", "Index of tap in the Lfsr's taps list", ["int"]))
  LfsrCat.addArgument(AioHelpArgument("ListOfXoredOutputs", "List of FF indexes", ["list"]))
  LfsrCat.addArgument(AioHelpArgument("DelayedBy", "How many cycles delayed", ["int"]))
  LfsrCat.addArgument(AioHelpArgument("OutputCount", "How many outputsd", ["int"]))
  LfsrCat.addArgument(AioHelpArgument("MinimumSeparation", "Minimum separation between outputs", ["int"], 100))
  LfsrCat.addArgument(AioHelpArgument("MaxXorInputs", "How huge XOR gates may be used?", ["int"], 3))
  LfsrCat.addArgument(AioHelpArgument("MinXorInputs", "How small XOR gates may be used?", ["int"], 1))
  LfsrCat.addArgument(AioHelpArgument("FirstXor", "If not specified, FF[0] is used as a reference", ["list,None"], None))
  LfsrCat.addArgument(AioHelpArgument("steps", "How many steps to simulate", ["int"], 1))
  LfsrCat.addArgument(AioHelpArgument("step", "How many steps between consecutive values", ["int"], 1))
  LfsrCat.addArgument(AioHelpArgument("n", "How many values (0 means all possible)", ["int"], 0))
  LfsrCat.addArgument(AioHelpArgument("reset", "Reset Lfsr before simulation", ["bool"], True))
  LfsrCat.addArgument(AioHelpArgument("Reset", "Reset Lfsr before simulation", ["bool"], True))
  LfsrCat.addArgument(AioHelpArgument("BitIndex", "index of FF at which output the sequence is observed", ["int"], 0))
  LfsrCat.addArgument(AioHelpArgument("Length", "Sequence length (0 means maximum)", ["int"], 0))
  LfsrCat.addArgument(AioHelpArgument("Sequence", "Bit sequence or list of bit sequences", ["int"], 0))
  LfsrCat.addArgument(AioHelpArgument("InjectionAtBit", "It this FF input the sequence is injected", ["int"], 0))
  LfsrCat.addArgument(AioHelpArgument("StartValue", "Seed (initial value of the Lfsr)", ["bitarray,None"], None))
  LfsrCat.addArgument(AioHelpArgument("ModuleName", "Verilog module name", ["str"]))
  LfsrCat.addArgument(AioHelpArgument("SingleInjector", "Add injector input at FF[0]?", ["bool"], False))
  LfsrCat.addArgument(AioHelpArgument("CorrectionInput", "Include correction mechanism?", ["bool"], False))
  LfsrCat.addArgument(AioHelpArgument("index", "FF index", ["int"]))
  LfsrCat.addArgument(AioHelpArgument("LfsrsList", "List of Lfsr objects", ["list"]))
  LfsrCat.addArgument(AioHelpArgument("SerialChunkSize", "How many Lfsrs test in series during multiprocess", ["int"], 20))
  LfsrCat.addArgument(AioHelpArgument("ReturnAlsoNotTested", "If True, returns a list of lists: [Maximum, NotTested]", ["bool"], False))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.__init__",
    Description="""Lfsr object constructor.
In case of ring with specified taps use such call:

  Lfsr(<Size>, RING_WITH_SPECIFIED_TAPS, [ [Source0, Destination0], [Source1, Destination1], ...])
  
...where: Source is index of FF's output,
          Destination is index of FF's input at which tap is xored with previous FF output
""",
    Arguments=["self","polynomial","lfsr_type","manual_taps"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.reverseTap",
    Description="""Reverse a given tap (used to make dual Lfsr)""",
    Arguments=["self","TapIndex"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getDual",
    Description="""Returns dual Lfsr object""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getTaps",
    Description="""Returns pointer to the Lfsr's taps list""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getPhaseShiftIndexes",
    Description="""Given a list of XOREd FF indexes.
Returns a list of other XORed FF indexes producing sequence delayed by specified cycles.
Used to create phase shifters.""",
    Arguments=["self","ListOfXoredOutputs","DelayedBy"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.createPhaseShifter",
    Description="""Reurns a PhaseShifter object, connected with this Lfsr.""",
    Arguments=["self","OutputCount","MinimumSeparation","MaxXorInputs","MinXorInputs","FirstXor"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getValue",
    Description="""Reurns a pointer to the actual Lfsr's value (bitarray object).""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getSize",
    Description="""Reurns Lfsr's size.""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.next",
    Description="""Calculates next value of the Lfsr.
Also, returns a pointer to the new value (bitarray object).
If steps>1, then uses fast simulation method.""",
    Arguments=["self","steps"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getPeriod",
    Description="""Returns Lfsr's period. May be slow, uses normal simulation method and cycles counting.""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.isMaximum",
    Description="""Returns True if the Lfsr produces M-Sequence.""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.reset",
    Description="""Resets the Lfsr's value (all zeros, FF[0]=1).
Also, returns a pointer to the new value (bitarray object).""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getValues",
    Description="""Returns a list of consecutive values produced by the Lfsr (list of bitarray objects).""",
    Arguments=["self","n","step","reset"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.printValues",
    Description="""Prints consecutive values produced by the Lfsr.""",
    Arguments=["self","n","step","reset"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getMSequence",
    Description="""Returns a bitarray object containing M-Sequence of the Lfsr.""",
    Arguments=["self","BitIndex","Reset"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getSequence",
    Description="""Returns a bitarray object containing a sequence produced by the Lfsr.""",
    Arguments=["self","BitIndex","Reset","Length"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.printFastSimArray",
    Description="""Prints content of a fast simulation array of the Lfsr.""",
    Arguments=["self"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.simulateForDataString",
    Description="""Simulates the Lfsr with a sequence injected at given FF.
The "Sequence" may be also a list of sequences, so that the process will be realised using multiprocessing.
Returns a final value (bitarray object) or a list of values, if Sequence is a list.""",
    Arguments=["self","Sequence","InjectionAtBit","StartValue"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.toVerilog",
    Description="""Returns a string containing Verilog description of the Lfsr.""",
    Arguments=["self","ModuleName","SingleInjector","CorrectionInput"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.getJTIndex",
    Description="""Returns the FF index recalculated by using prof. Tyszer's convention.""",
    Arguments=["self","index"]
  ))
  LfsrCat.addItem(AioHelpProc(
    Name="Lfsr.checkMaximum",
    Description="""Returns a list of filtered Lfsr object producing M-Sequence.
If 'n' is specified, it is also possible to get a list Lfsr skipped from testing (due to N achieved)
by specifying argument 'ReturnAlsoNotTested=True'. In such case returned is a list of two lists:
  [ <found_masimum_Lfsrs>, <not_tested_Lfsrs> ]""",
    Arguments=["LfsrsList","n","SerialChunkSize","ReturnAlsoNotTested"]
  ))
  
  ProgrammableRingGeneratorCat = AioHelpCategory("class ProgrammableRingGenerator", "Class used to analyse programmable ring generators.")
  ProgrammableRingGeneratorCat.addArgument(AioHelpArgument("self", "ProgrammableRingGenerator object", ["ProgrammableRingGenerator"]))
  ProgrammableRingGeneratorCat.addArgument(AioHelpArgument("SizeOrProgrammableLfsrConfiguration", "Size of the programmable ring generator or reference to\nProgrammableLfsrConfiguration object", ["int","ProgrammableLfsrConfiguration"]))
  ProgrammableRingGeneratorCat.addArgument(AioHelpArgument("TapsList", "List containing configurable taps description.\nEach tap is described by a dict object", ["list"]))
  ProgrammableRingGeneratorCat.addArgument(AioHelpArgument("OperateOnTapsOnly", "If True, then operates on taps lists,\nnot on Lfsr objects. Saves memory", ["bool", False]))
  ProgrammableRingGeneratorCat.addArgument(AioHelpArgument("Optimization", "If True, optimizes taps usage (to use as less as\npossible without polynomial(s) losses)", ["bool", False]))
  ProgrammableRingGeneratorCat.addArgument(AioHelpArgument("optimization", "If True, optimizes taps usage (to use as less as\npossible without polynomial(s) losses)", ["bool", True]))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.__init__",
    Description="""Object constructor. 
Consider, taps are defined as list of dict object. Each dict object describes reconfigurable tap.

Examples of taps:
  
  mandatory tap from 5 to 2:      { 0: [5,2] }
  on/off from 3 to 6:             { 0: [3,6], 1: None }  // None means "off"
  demux from 3 to 5 or 6:         { 0: {3,5], 1: [3,6] }}
  ...the same with "off" option:  { 0: {3,5], 1: [3,6] }, 2: None }""",
    Arguments=["self","SizeOrProgrammableLfsrConfiguration","TapsList","OperateOnTapsOnly"]
  ))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.getPolynomialsAndLfsrsDictionary",
    Description="""Returns a dictionary containing found polynomials being a keys.
Each polynomial may be obtained by one (or more) Lfsr/taps configuration, so values are lists of those Lfsrs/taps lists.""",
    Arguments=["self","Optimization"]
  ))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.getPolynomials",
    Description="""Returns a list containing all found primitive polynomials provided by this programmable ring.""",
    Arguments=["self"]
  ))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.getAllPosssibleTaps",
    Description="""Returns a list containing all possible taps( [Source, Destination]).""",
    Arguments=["self"]
  ))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.getUnusedTaps",
    Description="""Returns a list of unused taps.""",
    Arguments=["self","optimization"]
  ))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.getUsedTaps",
    Description="""Returns a list of used taps.""",
    Arguments=["self","optimization"]
  ))
  ProgrammableRingGeneratorCat.addItem(AioHelpProc(
    Name="ProgrammableRingGenerator.getLfsrs",
    Description="""Returns a list Lfsrs (or taps lists, if the ProgrammableRingGenerator object operates on taps list)""",
    Arguments=["self","Optimization"]
  ))
  
  ProgrammableLfsrConfigurationCat = AioHelpCategory("class ProgrammableLfsrConfiguration", "Makes it easy to create Programmable Ring Generator reconfigured taps list.")
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("self", "ProgrammableLfsrConfiguration object", ["ProgrammableLfsrConfiguration"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("Size", "Lfsr size", ["int"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("From", "Tap source (index of FF's output)", ["int"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("To", "Tap destination (index of FF input)", ["int"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("*Taps", "any number of simple taps ([Source, Destination])", ["lists"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("TapDict", "Reconfigurable tap dictionary", ["dict"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("SourceList", "List of source FF indexes", ["list"]))
  ProgrammableLfsrConfigurationCat.addArgument(AioHelpArgument("DestinationList", "List of destination FF indexes", ["list"]))
  
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.__init__",
    Description="""Constructor of ProgrammableRingGeneratorConfig object.""",
    Arguments=["self","Size"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.remove",
    Description="""Removes a given reconfigurable tap.""",
    Arguments=["self","TapDict"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.addMandatory",
    Description="""Adds mandatory (always-on) tap. Also, returns the created Taps Dictionary.""",
    Arguments=["self","From","To"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.addGated",
    Description="""Adds gated (active/inactive) tap. Also, returns the created Taps Dictionary.""",
    Arguments=["self","From","To"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.addMux",
    Description="""Adds muxed taps. Or more precise: adds taps from which only one is active at the same time.
If you want to add option to completely switch-off the (de)mux, then add 'None' to taps
Also, returns the created Taps Dictionary.""",
    Arguments=["self","*Taps"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.addAllCombinationsMux",
    Description="""Creates and adds all-combinations mux basing on given list of sources and list of destinations.""",
    Arguments=["self","SourceList","DestinationList"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.getTaps",
    Description="""Returns a list containing all added configurable taps.""",
    Arguments=["self"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.getSize",
    Description="""Returns FFs count.""",
    Arguments=["self"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.getSize",
    Description="""Returns FFs count.""",
    Arguments=["self"]
  ))
  ProgrammableLfsrConfigurationCat.addItem(AioHelpProc(
    Name="ProgrammableLfsrConfiguration.print",
    Description="""Prints all added configurable taps one-by-one, multiline.""",
    Arguments=["self"]
  ))
  
  LfsrPolysGroup.addItem(PolynomialCat)
  LfsrPolysGroup.addItem(LfsrTypeCat)
  LfsrPolysGroup.addItem(LfsrCat)
  LfsrPolysGroup.addItem(ProgrammableRingGeneratorCat)
  LfsrPolysGroup.addItem(ProgrammableLfsrConfigurationCat)
  addAioHelpCategory(LfsrPolysGroup, 1)
  
  