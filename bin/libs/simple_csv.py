from multiprocessing import Value
from libs.aio import *
from libs.files import *
from libs.pandas_table import *


class SimpleCSV:
    
    __slots__ = ('_coll_cnt', '_rows')
    
    def __init__(self, FileName: str, Separator : str = ","):
        if type(FileName) is SimpleCSV:
            self._coll_cnt = FileName._coll_cnt
            self._rows = FileName._rows.copy()
            return
        if type(FileName) is list:
            Rows = []
            self._coll_cnt = 0
            for Row in FileName:
                if len(Row) > self._coll_cnt:
                    self._coll_cnt = len(Row)
                Rows.append(Row.copy())
            for Row in Rows:
                for i, v in enumerate(Row):
                    if type(Row[i]) is str:
                        try:
                            Row[i] = int(v)
                        except:
                            try:
                                Row[i] = float(v)
                            except:
                                pass
                while len(Row) < self._coll_cnt:
                    Row.append(None)
            self._rows = Rows
            return
        Rows = []
        self._coll_cnt = 0
        for Line in File.readLineByLineGenerator(FileName):
            Row = Line.split(Separator)
            if len(Row) > self._coll_cnt:
                self._coll_cnt = len(Row)
            Rows.append(Row)
        for Row in Rows:
            for i, v in enumerate(Row):
                try:
                    Row[i] = int(v)
                except:
                    try:
                        Row[i] = float(v)
                    except:
                        pass
            while len(Row) < self._coll_cnt:
                Row.append(None)
        self._rows = Rows
        
    def __len__(self) -> int:
        return len(self._rows)
    
    def copy(self) -> "SimpleCSV":
        return SimpleCSV(self)
    
    def __add__(self, other) -> "SimpleCSV":
        MaxCol = max(self.getColumnCount(), other.getColumnCount())
        Rows = []
        for Row in self._rows:
            RowToAdd = Row.copy()
            if len(RowToAdd) < MaxCol:
                RowToAdd += ["" for _ in range(MaxCol - len(RowToAdd))]
            Rows.append(RowToAdd)
        for Row in other._rows:
            RowToAdd = Row.copy()
            if len(RowToAdd) < MaxCol:
                RowToAdd += ["" for _ in range(MaxCol - len(RowToAdd))]
            Rows.append(RowToAdd)
        return SimpleCSV(Rows)
    
    def toFile(self, FileName : str, Separator : str = ",") -> None:
        with open(FileName, "w", encoding="utf-8") as F:
            for Row in self._rows:
                Line = Separator.join([str(i) for i in Row])
                F.write(Line + "\n")
    
    def filterRows(self, ColumnId : int, IncludingRegex : str = None, ExcludingRegex : str = None) -> "SimpleCSV":
        import re
        if type(IncludingRegex) in [set, list]:
            IncludingRegex = "|".join([f"({i})" for i in IncludingRegex])
        if type(ExcludingRegex) in [set, list]:
            ExcludingRegex = "|".join([f"({i})" for i in ExcludingRegex])
        NewRows = []
        for Row in self._rows:
            Value = str(Row[ColumnId])
            Include = True
            if IncludingRegex is not None:
                if re.search(IncludingRegex, Value) is None:
                    Include = False
            if ExcludingRegex is not None:
                if re.search(ExcludingRegex, Value) is not None:
                    Include = False
            if Include:
                NewRows.append(Row.copy())
        NewCSV = SimpleCSV([])
        NewCSV._coll_cnt = self._coll_cnt
        NewCSV._rows = NewRows
        return NewCSV
    
    def getRowCount(self) -> int:
        return len(self._rows)
    
    def getColumnCount(self) -> int:
        return self._coll_cnt
        
    def __getitem__(self, index : int) -> int:
        return self._rows[index]
    
    def removeRow(self, index : int) -> None:
        del self._rows[index]
        
    def removeColumn(self, index : int) -> None:
        for Row in self._rows:
            del Row[index]
        self._coll_cnt -= 1
        
    def toTable(self, TitleRowIncluded : bool = False) -> AioTable:
        if len(self._rows) == 0:
            Aio.printError("SimpleCSV.toTable: No data available to convert to table.")
        if TitleRowIncluded:
            StartIndex = 1
            Table = AioTable(self._rows[0])
        else:
            StartIndex = 0
            Table = AioTable([i for i in range(self._coll_cnt)])
        for i in range(StartIndex, len(self._rows)):
            Table.addRow(self._rows[i])
        return Table
    
    def popRow(self, index : int) -> list:
        Row = self._rows[index]
        del self._rows[index]
        return Row
    
    def popRandomRow(self) -> list:
        import random
        index = random.randint(0, len(self._rows)-1)
        Row = self._rows[index]
        del self._rows[index]
        return Row
    
    def getAllRows(self) -> list:
        return self._rows
    
    def print(self, TitleRowIncluded : bool = False):
        Table = self.toTable(TitleRowIncluded)
        Table.print()
        
    def addColumnsFromAnotherCSV(self, OtherCSV : "SimpleCSV") -> None:
        RowMax = max(self.getRowCount(), OtherCSV.getRowCount())
        ColCount = self.getColumnCount() + OtherCSV.getColumnCount()
        NewData = []
        for i in range(RowMax):
            ThisRow = self._rows[i] if i < len(self._rows) else [None for _ in range(self._coll_cnt)]
            OtherRow = OtherCSV._rows[i] if i < len(OtherCSV._rows) else [None for _ in range(OtherCSV._coll_cnt)]
            NewData.append(ThisRow + OtherRow)
        self._rows = NewData
        self._coll_cnt = ColCount
        
    def addRowsFromAnotherCSV(self, OtherCSV : "SimpleCSV") -> None:
        ColCount = max(self.getColumnCount(), OtherCSV.getColumnCount())
        NewData = []
        for Row in self._rows:
            NewRow = Row + [None for _ in range(ColCount - len(Row))]
            NewData.append(NewRow)
        for Row in OtherCSV._rows:
            NewRow = Row + [None for _ in range(ColCount - len(Row))]
            NewData.append(NewRow)
        self._rows = NewData
        self._coll_cnt = ColCount
        
        
class CSVDedicatedDataMapper:
    
    __slots__ = ('_a', '_b', '_csv')
    
    def __init__(self, CSV : SimpleCSV, MinValue : float = -1, MaxValue : float = 1, ColumnIds : list = None):
        self._a = {}
        self._b = {}
        self._csv = CSV
        self._calculateMappingParameters(ColumnIds, MinValue, MaxValue)
        
    def calculateMappingParameters(self, ColumnIds : list = None, MinValue : float = -1, MaxValue : float = 1) -> None:
        CSV : SimpleCSV = self._csv
        if ColumnIds is None:
            ColumnIds = [i for i in range(CSV.getColumnCount())]    
        if type(ColumnIds) is int:
            ColumnIds = [ColumnIds] 
        self._dividors = {}
        self._adders = {}
        for ColumnId in ColumnIds:
            ColMin = None
            ColMax = None
            for Row in CSV.getAllRows():
                Value = Row[ColumnId]
                if type(Value) not in [int, float]:
                    continue
                Value = float(Value)
                if ColMin is None or Value < ColMin:
                    ColMin = Value
                if ColMax is None or Value > ColMax:
                    ColMax = Value
            a = (MaxValue - MinValue) / (ColMax - ColMin)
            b = MinValue - a * ColMin
            self._a[ColumnId] = a
            self._b[ColumnId] = b

    def getMappedCSV(self) -> SimpleCSV:
        CSV : SimpleCSV = self._csv
        MappedCSV = CSV.copy()
        for ColId in self._a.keys():
            a = self._a[ColId]
            b = self._b[ColId]
            for Row in MappedCSV.getAllRows():
                Value = Row[ColId]
                if type(Value) not in [int, float]:
                    continue
                MappedValue = a * float(Value) + b
                Row[ColId] = MappedValue
        return MappedCSV   

    def mapCSV(self, CSV : SimpleCSV) -> SimpleCSV:
        MappedCSV = CSV.copy()
        for ColId in self._a.keys():
            if ColId >= MappedCSV.getColumnCount():
                continue
            a = self._a[ColId]
            b = self._b[ColId]
            for Row in MappedCSV.getAllRows():
                Value = Row[ColId]
                if type(Value) not in [int, float]:
                    continue
                MappedValue = a * float(Value) + b
                Row[ColId] = MappedValue
        return MappedCSV   

    def unmapCSV(self, CSV : SimpleCSV) -> SimpleCSV:
        UnMappedCSV = CSV.copy()
        for ColId in self._a.keys():
            if ColId >= UnMappedCSV.getColumnCount():
                continue
            a = self._a[ColId]
            b = self._b[ColId]
            for Row in UnMappedCSV.getAllRows():
                Value = Row[ColId]
                if type(Value) not in [int, float]:
                    continue
                UnMappedValue = (Value - b) / a
                Row[ColId] = UnMappedValue
        return UnMappedCSV   