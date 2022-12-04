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
  def __init__(self, Name : str, Description : str, Parent = None, Arguments = {}):
    self.Name = Name
    self.Description = Description
    self.Items = []
    self.Arguments = Arguments
    self.Parent = Parent
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
      PNames = f'{self.Name}.'
    if len(ParentNames) > 0:
      PNames = f'{ParentNames}.{PNames}'
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
      Usage = ""
      First = 1
      for A in ArgList:
        if First:
          Usage += f'{A}'
          First = 0
        else:
          Usage += f', {A}'
      Usage = f'{self.Name} ({Usage})'
      ArgTable.add([Name, Type, Default, Description])
      Result = f'{Usage}\n\n{self.Description}\n\n{ArgTable.toString("left")}'
      return Result
          
if 'AioHelpGlobal' not in locals():
  AioHelpGlobal = AioHelpCategory("", "Maciej Trawka's All-In-One v2")
  
def addAioHelpCategory(Category : AioHelpCategory):
  global AioHelpGlobal
  Exists = 0
  for I in AioHelpGlobal.Items:
    if I.Name == Category.Name:
      Exists = 1
      break
  if not Exists:
    AioHelpGlobal.addItem(Category)
  
def aiohelp(Pattern = ""):
  global AioHelpGlobal
  if len(Pattern) > 0:
    AioHelpGlobal.showSearch(Pattern)
  else:
    AioHelpGlobal.show()
  
    