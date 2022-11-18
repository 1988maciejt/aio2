import pandas
from aio import *

class PandasTable:
  __slots__ = ("_vspaces", "_main_dict", "_auto_id", "_id_num")
  def __init__(self, HeaderList : list, AddVerticalSpaces=0, AutoId=0) -> None:
    self._auto_id = 1 if AutoId else 0
    self._vspaces = 1 if AddVerticalSpaces else 0
    self._id_num = 1
    self._main_dict = {}
    if self._auto_id:
      self._main_dict["Id"] = []
    for S in HeaderList:
      self._main_dict[S] = []
  def __del__(self):
    del self._main_dict
  def __repr__(self):
    return f'PandasTable({list(self._main_dict.keys())})'
  def __str__(self):
    return self.toString()
  def add(self, RowList : list):
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
      for Line in VLines.split("\n"):
        self._main_dict[k].append(Line)
      Index += 1
    self._autoFill()
  def toString(self):
    df = pandas.DataFrame.from_dict(self._main_dict)
    return df.to_string(index=0)
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
      
      
    
    
    