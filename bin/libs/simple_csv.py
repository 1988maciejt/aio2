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
        
    def toTable(self, TitleRowIncluded : bool = False, RowNumbers : bool = False) -> AioTable:
        if len(self._rows) == 0:
            Aio.printError("SimpleCSV.toTable: No data available to convert to table.")
        Header = []
        if RowNumbers:
            Header.append("")
        if TitleRowIncluded:
            StartIndex = 1
            Header += self._rows[0]
        else:
            StartIndex = 0
            Header += [i for i in range(self._coll_cnt)]
        Table = AioTable(Header)
        for i in range(StartIndex, len(self._rows)):
            Row = []
            if RowNumbers:
                Row.append(i)
            Row += self._rows[i]
            Table.addRow(Row)
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
    
    def print(self, TitleRowIncluded : bool = False, RowNumbers : bool = False):
        Table = self.toTable(TitleRowIncluded, RowNumbers)
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

    def getColumnData(self, ColumnId : int) -> list:
        if ColumnId >= self._coll_cnt:
            return None
        Data = [Row[ColumnId] for Row in self._rows]
        return Data
    
    def __getitem__(self, index : int) -> "SimpleCSV":
        NewCsv = self.copy()
        for i in range(len(NewCsv._rows)):
            NewCsv._rows[i] = NewCsv._rows[i][index]
            if type(NewCsv._rows[i]) is not list:
                NewCsv._rows[i] = [NewCsv._rows[i]]
        Columns = [i for i in range(NewCsv._coll_cnt)]
        Columns = Columns[index]
        if type(Columns) is not list:
            Columns = [Columns]
        NewCsv._coll_cnt = len(Columns)
        return NewCsv
        
        
class CSVDedicatedDataMapper:
    
    __slots__ = ('_a', '_b', '_csv')
    
    def __init__(self, CSV : SimpleCSV, Mean : float = 0, StdDev : float = 1, ColumnIds : list = None):
        if type(CSV) is CSVDedicatedDataMapper:
            self._a = CSV._a.copy()
            self._b = CSV._b.copy()
            self._csv = CSV._csv.copy()
        else:
            self._a = {}
            self._b = {}
            self._csv = CSV
            self._calculateMappingParameters(ColumnIds, Mean, StdDev)

    def copy(self) -> "CSVDedicatedDataMapper":
        return CSVDedicatedDataMapper(self)
        
    def _calculateMappingParameters(self, ColumnIds : list = None, Mean : float = 0, StdDev : float = 1) -> None:
        from libs.utils_list import List
        CSV : SimpleCSV = self._csv
        if ColumnIds is None:
            ColumnIds = [i for i in range(CSV.getColumnCount())]    
        if type(ColumnIds) is int:
            ColumnIds = [ColumnIds] 
        self._a = {}
        self._b = {}
        for ColumnId in ColumnIds:
            ColumnData = self._csv.getColumnData(ColumnId)
            a, b = List.calculateStandarizationParametersAandB(ColumnData, Mean, StdDev)
            self._a[ColumnId] = a
            self._b[ColumnId] = b

    def mapCSV(self) -> SimpleCSV:
        for ColId in self._a.keys():
            a = self._a[ColId]
            b = self._b[ColId]
            for RowI in range(self._csv.getRowCount()):
                self._csv._rows[RowI][ColId] = a * float(self._csv._rows[RowI][ColId]) + b
        return self._csv   
    
    def unmapCSV(self, Resolution : float = 0.00001) -> SimpleCSV:
        from libs.utils_float import FloatUtils
        for ColId in self._a.keys():
            a = self._a[ColId]
            b = self._b[ColId]
            for RowI in range(self._csv.getRowCount()):
                self._csv._rows[RowI][ColId] = FloatUtils.roundToResolution((self._csv._rows[RowI][ColId] - b) / a, Resolution)
        return self._csv   

    def getCsv(self) -> SimpleCSV:
        return self._csv
    
    def __getitem__(self, index : int) -> "CSVDedicatedDataMapper":
        NewMapper = self.copy()
        NewCsv : SimpleCSV = NewMapper._csv
        Columns = [i for i in range(NewCsv._coll_cnt)]
        Columns = Columns[index]
        if type(Columns) is not list:
            Columns = [Columns]
        NewMapper._csv = NewCsv[index]
        NewMapper._a, NewMapper._b = {}, {}
        for ColI, Col in enumerate(Columns):
            if Col in self._a:
                NewMapper._a[ColI] = self._a[Col]
                NewMapper._b[ColI] = self._b[Col]
        return NewMapper