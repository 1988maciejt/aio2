import pandas
from libs.aio import *

class PandasTable:
  
  __slots__ = ("_vspaces", "_main_dict", "_auto_id", "_id_num", "_len","_multiline")
  
  def __init__(self, HeaderList : list, AddVerticalSpaces=0, AutoId=0, MultiLine=True) -> None:
    self._auto_id = 1 if AutoId else 0
    self._vspaces = 1 if AddVerticalSpaces else 0
    self._id_num = 1
    self._len = 0
    self._main_dict = {}
    self._multiline = MultiLine
    if self._auto_id:
      self._main_dict["Id"] = []
    for S in HeaderList:
      self._main_dict[str(S)] = []
      
  def __del__(self):
    del self._main_dict
    
  def __repr__(self) -> str:
    return f'PandasTable({list(self._main_dict.keys())})'
  
  def __str__(self) -> str:
    return self.toString()
  
  def __len__(self) -> int:
    return self._len
  
  def size(self) -> int:
    return self._len
  
  def add(self, RowList : list):
    self._len += 1
    Index = 0
    First = 1
    if self._vspaces:
      self._addVSpace()
    for k in self._main_dict.keys():
      if First and self._auto_id:
        self._main_dict[k].append(str(self._id_num))
        self._id_num += 1
        First = 0
        continue
      VLines = str(RowList[Index])
      if self._multiline:
        Iterator = VLines.split("\n")
      else:
        Iterator = [VLines]
      for Line in Iterator:
        self._main_dict[k].append(Line)
      Index += 1
    self._autoFill()
  
  addRow = add
    
  def toString(self, justify='right'):
    if self._len < 1:
      return "<no data>"
    df = pandas.DataFrame.from_dict(self._main_dict)
    return df.to_string(index=0, justify=justify)
  
  def toXls(self, FileName : str) -> str:
    from libs.utils_str import Str
    FileName = Str.mustEndWith(FileName, ".xlsx")
    writer = pandas.ExcelWriter(FileName, engine="xlsxwriter")
    df = pandas.DataFrame.from_dict(self._main_dict)
    for Column in df.columns:
      df[Column] = pandas.to_numeric(df[Column], errors='ignore')
    df.to_excel(writer, index=0)
    writer.close()
    return FileName
      
  toXlsx = toXls
    
  def print(self):
    Aio.print(self.toString())
    
  def _addVSpace(self):
    for k in self._main_dict.keys():
      self._main_dict[k].append(" ")
      
  def _autoFill(self):
    MaxLen = 0
    for k in self._main_dict.keys():
      klen = len(self._main_dict[k])
      if klen > MaxLen:
        MaxLen = klen
    for k in self._main_dict.keys():
      while len(self._main_dict[k]) < MaxLen:
        self._main_dict[k].append(" ")
      
      
    
    
class AioTable(PandasTable):

  def __repr__(self) -> str:
    return f'AioTable({list(self._main_dict.keys())})'

  @staticmethod  
  def fromSetOfFiles(FileNamesList : list, RegexDictionary : dict, RowTitles : list = None, ReportLastValueIfMany : bool = False, MultiProcessing : bool = True) -> "AioTable":
    RowTitleIsFileName = 0
    if RowTitles is None:
      RowTitles = FileNamesList
      RowTitleIsFileName = 1
    if type(RowTitles) in [list, tuple] and len(RowTitles) < len(FileNamesList):
      RowTitles = FileNamesList
      RowTitleIsFileName = 1
    from libs.files import File
    from p_tqdm import p_imap
    if len(RowTitles) > 0:
      Header = ["" for _ in range(len(RowTitles[0]))] + list(RegexDictionary.keys())
    else:
      if RowTitleIsFileName:
        Header = ["FileName"] + list(RegexDictionary.keys())
      else:
        Header = [""] + list(RegexDictionary.keys())
    Table = AioTable(Header)
    if MultiProcessing:
      def single(Idx):
        Row = [RowTitles[Idx]]
        Res = File.parseValues(FileNamesList[Idx], RegexDictionary, ReportLastValueIfMany)
        for key in RegexDictionary.keys():
          Row.append(Res[key])
        return Row
      for Row in p_imap(single, range(len(FileNamesList))):
        Table.add(Row)
      AioShell.removeLastLine()
    else:
      for i, FileName in enumerate(FileNamesList):
        Row = [RowTitles[i]]
        Res = File.parseValues(FileName, RegexDictionary, ReportLastValueIfMany)
        for key in RegexDictionary.keys():
          Row.append(Res[key])
        Table.add(Row)
    return Table  
    
  def _getWidths(self) -> list:
    Result = []
    for Col in self._main_dict.keys():
      ColWid = 0
      for Row in self._main_dict[Col]:
        CW = Str.getWidth(Row)
        if CW > ColWid:
          ColWid = CW
      Result.append(ColWid)
    Keys = list(self._main_dict.keys())
    for i in range(len(Keys)):
      KL = len(Keys[i])
      if KL > Result[i]:
        Result[i] = KL
    return Result
  
  def _getHLine(self, Widths : list, Indent = 0):
    Result = " " * Indent + "+"
    for W in Widths:
      Result += "-" * (W+2)
      Result += "+"
    return Result
  
  def _getHeader(self, Widths : list, JustificationList=[], Indent = 0):
    Result = " " * Indent + "|"
    for W, K, i in zip(Widths, self._main_dict.keys(), range(len(Widths))):
      try:
        Justify = JustificationList[i]
      except:
        Justify = "l"
      Result += " " + Str.getAligned(K, W, Justify) + " "
      Result += "|"
    return Result
  
  def _getRow(self, Row : list, Widths : list, JustificationList=[], Indent = 0):
    Result = " " * Indent + "|"
    for W, K, i in zip(Widths, Row, range(len(Widths))):
      try:
        Justify = JustificationList[i]
      except:
        Justify = "l"
      Result += " " + Str.getAligned(K, W, Justify) + " "
      Result += "|"
    return Result
  
  def toString(self, JustificationList=[], Indent = 0):
    Widths = self._getWidths()
    Result = self._getHLine(Widths, Indent) + "\n"
    Result += self._getHeader(Widths, JustificationList, Indent) + "\n"
    Result += self._getHLine(Widths, Indent) + "\n"
    Keys = list(self._main_dict.keys())
    RowsCount = len(self._main_dict[Keys[0]])
    for RI in range(RowsCount):
      Row = []
      for Key in Keys:
        Row.append(self._main_dict[Key][RI])
      Result += self._getRow(Row, Widths, JustificationList, Indent) + "\n"
    Result += self._getHLine(Widths, Indent)
    return Result
  
  def print(self, JustificationList=[], Indent = 0):
    Aio.print(self.toString(JustificationList, Indent))
    

class AioTableUtils:
  
  @staticmethod
  def tablesToXlsx(FileName : str, TablesDictOrList : dict) -> str:
    from libs.utils_str import Str
    FileName = Str.mustEndWith(FileName, ".xlsx")
    if not (type(TablesDictOrList) is dict):
      Dict = {}
      for i, Table in enumerate(TablesDictOrList):
        Dict[f"Table_{i}"] = Table
      TablesDictOrList = Dict
    with pandas.ExcelWriter(FileName, engine="xlsxwriter") as writer:
      for SheetName, Table in TablesDictOrList.items():
        df = pandas.DataFrame.from_dict(Table._main_dict)
        for Column in df.columns:
          df[Column] = pandas.to_numeric(df[Column], errors='ignore')
        df.to_excel(writer, sheet_name=SheetName, index=False)
