import pandas
from libs.aio import *

class XlsTable:
  __slots__ = ("_vspaces", "_main_dict", "_auto_id", "_id_num", "_len")
  def __init__(self, HeaderList : list, AutoId=0) -> None:
    self._auto_id = 1 if AutoId else 0
    self._id_num = 1
    self._len = 0
    self._main_dict = {}
    if self._auto_id:
      self._main_dict["Id"] = []
    for S in HeaderList:
      self._main_dict[S] = []
  def __del__(self):
    del self._main_dict
  def __repr__(self) -> str:
    return f'XlsTable({list(self._main_dict.keys())})'
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
    for k in self._main_dict.keys():
      if First and self._auto_id:
        self._main_dict[k].append(str(self._id_num))
        self._id_num += 1
        First = 0
        continue
      self._main_dict[k].append(str(RowList[Index]))
      Index += 1
  def toString(self, justify='right'):
    if self._len < 1:
      return "<no data>"
    df = pandas.DataFrame.from_dict(self._main_dict)
    return df.to_string(index=0, justify=justify)
  def print(self):
    Aio.print(self.toString())