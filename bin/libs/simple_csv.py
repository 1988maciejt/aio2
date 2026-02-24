from multiprocessing import Value

import numpy
from libs.aio import *
from libs.files import *
from libs.pandas_table import *


class SimpleCSV:
    
    __slots__ = ('_coll_cnt', '_rows')
    
    def __init__(self, FileName: str, Separator : str = ","):
        if type(FileName) is SimpleCSV:
            from copy import deepcopy
            self._coll_cnt = FileName._coll_cnt
            self._rows = deepcopy(FileName._rows)
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
    
    def randomlySplitIntoTwoSubCSVs(self, Ratio : float = 0.5) -> tuple:
        import random
        if Ratio < 0 or Ratio > 1:
            Aio.printError("SimpleCSV.randomlySplitIntoTwoSubCSVs: Ratio must be between 0 and 1.")
        RowCount = self.getRowCount()
        RowIndices = list(range(RowCount))
        random.shuffle(RowIndices)
        SplitIndex = int(RowCount * Ratio)
        SubCSV1 = SimpleCSV([])
        SubCSV2 = SimpleCSV([])
        SubCSV1._coll_cnt = self._coll_cnt
        SubCSV2._coll_cnt = self._coll_cnt
        for i in range(SplitIndex):
            SubCSV1._rows.append(self._rows[RowIndices[i]].copy())
        for i in range(SplitIndex, RowCount):
            SubCSV2._rows.append(self._rows[RowIndices[i]].copy())
        return SubCSV1, SubCSV2
    
    def getNumpyArraysForML(self, YColumnCount : int = 1) -> tuple:
        x, y = [], []
        SplitPoint = self.getColumnCount() - YColumnCount
        for R in self.getAllRows():
            x.append(R[:SplitPoint])
            y.append(R[SplitPoint:])
        np_x = numpy.array(x, dtype=numpy.float32)
        np_y = numpy.array(y, dtype=numpy.float32)
        return np_x, np_y
    
    def shuffleRows(self) -> None:
        import random
        random.shuffle(self._rows)
        
class CSVDedicatedDataMapper:
    
    __slots__ = ('_a', '_b', '_csv', '_mapped')
    
    def __init__(self, CSV : SimpleCSV, ColumnIds : list = None, Mean : float = 0, StdDev : float = 1):
        if type(CSV) is CSVDedicatedDataMapper:
            self._a = CSV._a.copy()
            self._b = CSV._b.copy()
            self._csv = CSV._csv.copy()
            self._mapped = CSV._mapped
        else:
            self._a = {}
            self._b = {}
            self._csv = CSV
            self._mapped = None
            self._calculateMappingParameters(ColumnIds, Mean, StdDev)
            
    def __str__(self) -> str:
        Result = ""
        for k in self._a.keys():
            Result += f"Column {k}: a={self._a[k]}, b={self._b[k]}\n"
        return Result

    def __len__(self) -> int:
        return len(self._csv)

    def copy(self, AnotherCsv : SimpleCSV = None) -> "CSVDedicatedDataMapper":
        Result = CSVDedicatedDataMapper(self)
        if AnotherCsv is not None:
            if not Result.replaceCsv(AnotherCsv):
                Aio.printError(f"CSVDedicatedDataMapper.copy: The provided CSV has different column count than the original CSV. Cannot replace.")
            Result._mapped = None
        return Result
        
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
            if ColumnId >= CSV.getColumnCount():
                Aio.printError(f"CSVDedicatedDataMapper: ColumnId {ColumnId} is out of range for the provided CSV.")
            ColumnData = self._csv.getColumnData(ColumnId)
            a, b = List.calculateStandarizationParametersAandB(ColumnData, Mean, StdDev)
            self._a[ColumnId] = a
            self._b[ColumnId] = b

    def mapCSV(self) -> SimpleCSV:
        if self._mapped is not None and self._mapped:
            Aio.printWarning("CSVDedicatedDataMapper.mapCSV: The CSV is already mapped. Mapping again may take an unexpected effect.")
        for ColId in self._a.keys():
            a = self._a[ColId]
            b = self._b[ColId]
            for RowI in range(self._csv.getRowCount()):
                self._csv._rows[RowI][ColId] = a * float(self._csv._rows[RowI][ColId]) + b
        self._mapped = True
        return self._csv   
    
    def unmapCSV(self, Resolution : float = 0.00001) -> SimpleCSV:
        if self._mapped is not None and not self._mapped:
            Aio.printWarning("CSVDedicatedDataMapper.unmapCSV: The CSV is not mapped. Unmapping again may take an unexpected effect.")
        from libs.utils_float import FloatUtils
        for ColId in self._a.keys():
            a = self._a[ColId]
            b = self._b[ColId]
            for RowI in range(self._csv.getRowCount()):
                if (a != 0):
                    self._csv._rows[RowI][ColId] = FloatUtils.roundToResolution((self._csv._rows[RowI][ColId] - b) / a, Resolution)
                else:
                    self._csv._rows[RowI][ColId] = FloatUtils.roundToResolution((self._csv._rows[RowI][ColId] - b), Resolution)
        self._mapped = False
        return self._csv   

    def getCsv(self) -> SimpleCSV:
        return self._csv
    
    def __getitem__(self, index : int) -> "CSVDedicatedDataMapper":
        NewMapper = self.copy()
        NewMapper._mapped = self._mapped
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
    
    def replaceCsv(self, NewCSV : SimpleCSV) -> bool:
        if self._csv.getColumnCount() != NewCSV.getColumnCount():
            return False
        self._csv = NewCSV
        self._mapped = None
        return True
        
    def removeColumn(self, index : int) -> None:
        for Row in self._csv._rows:
            del Row[index]
        for k in list(self._a.keys()):
            if k == index:
                del self._a[k]
                del self._b[k]
            elif k > index:
                self._a[k-1] = self._a[k]
                self._b[k-1] = self._b[k]
                del self._a[k]
                del self._b[k]    
        self._csv._coll_cnt -= 1
        
    def getColumnCount(self) -> int:
        return self._csv.getColumnCount()
    
    def getRowCount(self) -> int:
        return self._csv.getRowCount()
    
    def getAllRows(self) -> list:
        return self._csv.getAllRows()
    
    def randomlySplitIntoTwoSubDataMappers(self, Ratio : float = 0.5) -> tuple:
        CSV1, CSV2 = self._csv.randomlySplitIntoTwoSubCSVs(Ratio)
        Mapper1 = self.copy(CSV1)
        Mapper2 = self.copy(CSV2)
        Mapper1._mapped = self._mapped
        Mapper2._mapped = self._mapped
        return Mapper1, Mapper2
    
    def filterRows(self, ColumnId : int, IncludingRegex : str = None, ExcludingRegex : str = None) -> "CSVDedicatedDataMapper":
        NewCsv = self._csv.filterRows(ColumnId, IncludingRegex, ExcludingRegex)
        NewMapper = self.copy(NewCsv)
        NewMapper._mapped = self._mapped
        return NewMapper
    
    def getNumpyArraysForML(self, YColumnCount : int = 1) -> tuple:
        return self._csv.getNumpyArraysForML(YColumnCount)
    
    def shuffleRows(self) -> None:
        self._csv.shuffleRows()
    
    @staticmethod
    def createMLPredictionMapper(MLYpredictions : numpy.ndarray, AnyYMapper : "CSVDedicatedDataMapper", YColumnCount : int = 1) -> "CSVDedicatedDataMapper":
        PredictCsv = SimpleCSV(MLYpredictions.tolist())
        PredictMapper = AnyYMapper[-YColumnCount:].copy(PredictCsv)
        return PredictMapper