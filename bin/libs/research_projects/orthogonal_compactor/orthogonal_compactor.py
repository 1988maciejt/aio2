from typing import Any
from libs.aio import *
from bitarray import *
from libs.utils_bitarray import *
from libs.utils_list import *
from libs.generators import *
from libs.simpletree import *
from tqdm import tqdm
from p_tqdm import p_uimap
from functools import partial




class BitarrayExtendedMatrix:
    pass
class BitarrayExtendedMatrix:
    
    __slots__ = ('_rows', '_cols', "_echelon_form", "_recursion_level", "_unambiguous", "_ambiguous_ones", "_sorted")
    
    def __init__(self, Rows : list = None) -> None:
        self._rows = []
        self._cols = 0
        self._echelon_form = 0
        self._recursion_level = 0
        self._unambiguous = {}
        self._ambiguous_ones = []
        self._sorted = True
        if Rows is not None:
            for r in Rows:
                self.addRow(r)
        
    def __len__(self) -> int:
        return len(self._rows)
    
    def __getitem__(self, Index : int) -> bitarray:
        return self._rows[Index]
    
    def __repr__(self) -> str:
        return f"BitarrayExtendedMatrix(ROWS={self._rows}, COLS={self._cols})"
                
    def __str__(self) -> str:
        Result = ""
        Second, i = 0, 0
        for Row in self._rows:
            if Second:
                Result += "\n"
            else:
                Second = 1
            Result += f"{i} \t: {str(Row)[10:-2]}"
            if self.isUnambiguous(i):
                Result += " U"
            i += 1
        return Result
        
    def addRow(self, Row : bitarray) -> None:
        if type(Row) in (list, tuple):
            for R in Row:
                self.addRow(R)
            return
        if type(Row) is not bitarray:
            try:
                Row = bitarray(Row)
            except:
                Aio.printError('Row must be a bitarray or at least be conversibl;e to bitarray.')
                return
        if self._cols == 0:
            self._cols = len(Row)
        if len(Row) == self._cols:
            self._rows.append(Row)
            self._sorted = False
            self._echelon_form = 0
        else:
            Aio.printError(f"Row length ({len(Row)}) must be equal to the previous row length ({self._cols}).")
            
    def sortRows(self) -> None:
        if self._sorted:
            return
        self._unambiguous = {}
        import itertools, operator
        def sort_uniq(sequence):
            return map(
                operator.itemgetter(0),
                itertools.groupby(sorted(sequence, reverse=True)))
        self._rows = list(sort_uniq(self._rows))
        self._sorted = True
        
    def toEchelonForm(self, Debug = 0) -> None:
        if self._echelon_form:
            return
        self.sortRows()
        if Debug:
            print("toEchelonForm ---")
            print(f"Sorted:\n{self}")
        BaseRow = bau.zeros(self._cols)
        RowToSearchFirst = bau.ones(self._cols)
        BaseRow[0] = 1
        for ColI in range(self._cols-1):
            FirstRow = 0
            MaxRowI = -1
            for RowI in range(len(self._rows)):
                if self._rows[RowI] > RowToSearchFirst:
                    FirstRow = RowI + 1
            if Debug:
                print(f"FirstRow: {FirstRow}")
            for RowI in range(FirstRow, len(self._rows)):
                if self._rows[RowI] >= BaseRow:
                    if MaxRowI < 0:
                        MaxRowI = RowI
                        if Debug:
                            print("MaxRowI:", MaxRowI)
                    else:
                        if Debug:
                            print("To eliminate:",RowI)
                        self._rows[RowI] ^= self._rows[MaxRowI]
            self._sorted = False
            self.sortRows()
            BaseRow >>= 1
            RowToSearchFirst >>= 1
            if Debug:
                print(f"After {ColI} iter:\n{self}")
        self._echelon_form = 1
        self._unambiguous = {}
    
    def hasNoSolution(self) -> bool:
        self.toEchelonForm()
        for i in range(len(self._rows)-1):
            if self._rows[i][:-1] == self._rows[i+1][:-1]:
                return True
            if self._rows[i+1][:-1].count(1) == 0:
                return True
        return False
    
    def solve(self, MaxFailCount : int = 10, MaxRecursionDepth : int = 3, DoNotReduce=0):
        self.toEchelonForm()
        for RowI in range(len(self)-2, 0, -1):
            for RfixerI in range(RowI+1, len(self)):
                Aux = self._rows[RowI] ^ self._rows[RfixerI]
                if (Aux < self._rows[RowI]):
                    self._rows[RowI] = Aux
                    try:
                        del self._unambiguous[RowI]
                    except:
                        pass     
        for RowI in range(len(self)-1):
            for RfixerI in range(RowI+1, len(self)):
                if self.isUnambiguous(RfixerI):
                    Aux = self._rows[RowI] ^ self._rows[RfixerI]
                    if (Aux < self._rows[RowI]):
                        self._rows[RowI] = Aux
                        try:
                            del self._unambiguous[RowI]
                        except:
                            pass    
        if self.hasNoSolution():
            return None
        if not DoNotReduce:
            self.reduceEqs()
        if self.isUnambiguous():
            Result = bau.zeros(self._cols-1)
            Result = self.getUnambiguousVarsEqualTo1()
            if (len(Result) + len(self._ambiguous_ones)) > MaxFailCount:
                return None
            return [Result + self._ambiguous_ones] 
        else:        
            if self._recursion_level > MaxRecursionDepth:
                return None
            if self.isUnambiguousOnesCountGreaterThan(MaxFailCount - len(self._ambiguous_ones)):
                return None
            KnownOnesCount = self.getUnambiguousOnesCount()
            MaxNewOnes = MaxFailCount - len(self._ambiguous_ones) - KnownOnesCount
            if MaxNewOnes < 0:
                MaxNewOnes = 0
            Result = []
            if MaxNewOnes <= 1:     
                for i in range(len(self._rows)-1, 0, -1):
                    if not self.isUnambiguous(i) and not self._rows[i][-1]:
                        for vindex in self._rows[i][:-1].search(1):
                            for j in range(0, i, 1):
                                self._rows[j][vindex] = 0
                self.reduceEqs()
                self._unambiguous = {}
            TheBestIndex = len(self._rows)-1
            TheBestVars = self.isUnambiguous(TheBestIndex, ReturnNumberOfOnes=True)
            VarCandidates = []   
            if MaxNewOnes > 0:
                if TheBestVars > 5:
                    for urowi in range(TheBestIndex-1, 0, -1):
                        VarCount = self.isUnambiguous(urowi, ReturnNumberOfOnes=True)
                        if VarCount < TheBestVars:
                            TheBestIndex = urowi
                            TheBestVars = VarCount
                        if VarCount <= 5:
                            break
                for Var in self._rows[TheBestIndex][:-1].search(1):
                    VarCandidates.append(Var)
            else:
                SumVars = TheBestVars
                for Var in self._rows[TheBestIndex][:-1].search(1):
                    VarCandidates.append(Var)
                for urowi in range(TheBestIndex-1, 0, -1):
                    VarCount = self.isUnambiguous(urowi, ReturnNumberOfOnes=True)
                    SumVars += VarCount
                    if SumVars <= 50:
                        for Var in self._rows[urowi][:-1].search(1):
                            VarCandidates.append(Var)

            Combinations = []
            MaxK = len(VarCandidates)
            if MaxK > MaxNewOnes:
                MaxK = MaxNewOnes
            if MaxNewOnes > 0 and self._rows[TheBestIndex][-1]:
                for i in range(1, MaxK+1, 2):
                    Combinations += List.getCombinations(VarCandidates, i)
            else:
                for i in range(2, MaxK+1, 2):
                    Combinations += List.getCombinations(VarCandidates, i)
                Combinations.append([])
            for cmbI in range(len(Combinations)):
                Comb = Combinations[cmbI]
                Comb1 = set(Comb)
                Comb0 = set(VarCandidates) - Comb1
                print(self._recursion_level," :\t", '  '*self._recursion_level,"-> ", cmbI+1, "/", len(Combinations))
                M = self.copy()
                M._recursion_level = self._recursion_level + 1
                for c in Comb0:
                    Eq = bau.zeros(self._cols)
                    Eq[c] = 1
                    M.addRow(Eq)
                for c in Comb1:
                    Eq = bau.zeros(self._cols)
                    Eq[c] = 1
                    Eq[-1] = 1
                    M.addRow(Eq)
                R = M.solve(MaxFailCount, MaxRecursionDepth=MaxRecursionDepth)
                AioShell.removeLastLine()
                if R is not None:
                    for RI in R:
                        Result.append(RI)
            return Result
                    
    def reduceEqs(self) -> None:
        self.toEchelonForm()
        for i in range(len(self._rows)-1, -1, -1):
            if self.isUnambiguous(i):
                if self._rows[i][-1]:
                    self._ambiguous_ones.append(self._rows[i].find(1))
                del self._rows[i]
        self._unambiguous = {}
        return
    
    def getUnambiguousVarsEqualTo1(self) -> list:
        Result = []
        for i in range(len(self._rows)):
            if self.isUnambiguous(i):
                if self._rows[i][-1]:
                    Result.append(self._rows[i].find(1))
        return Result
            
    def isUnambiguous(self, RowIndex : int = None, ReturnNumberOfOnes = False) -> bool:
        if RowIndex is None:
            Result = True
            for i in range(len(self._rows)):
                if not self.isUnambiguous(i):
                    Result = False
                    break
            return Result
        else:
            Cached = self._unambiguous.get(RowIndex, None)
            if Cached is not None:
                Ones = Cached
            else:
                if RowIndex >= len(self._rows):
                    return 0
                Ones = self._rows[RowIndex][:-1].count(1)
                self._unambiguous[RowIndex] = Ones
            if ReturnNumberOfOnes:
                return Ones
            return Ones==1
        
    def isUnambiguousOnesCountGreaterThan(self, HowMuch : int) -> bool:
        C = 0
        for i in range(len(self._rows)):
            if self._rows[i][-1]:
                if self.isUnambiguous(i):
                    C += 1
                    if C > HowMuch:
                        return True
        return False

    def getUnambiguousOnesCount(self) -> int:
        C = 0
        for i in range(len(self._rows)):
            if self.isUnambiguous(i):
                if self._rows[i][-1]:
                    C += 1
        return C
    
    def copy(self) -> BitarrayExtendedMatrix:
        from copy import deepcopy
        Result = BitarrayExtendedMatrix()
        Result._rows = deepcopy(self._rows)
        Result._cols = self._cols
        Result._echelon_form = self._echelon_form
        Result._unambiguous = self._unambiguous.copy()
        Result._ambiguous_ones = self._ambiguous_ones.copy()
        Result._sorted = self._sorted
        return Result
    
# +++ NEW SOLVER +++++++++++++++++++++++++++++++++++++++++++++++++++    

class CompactorSolverEquation:
    pass    
class CompactorSolver:
    pass

class CompactorSolverEquation:
    
    __slots__ = ("_equation", "_value", "_first_one", "_ones_count")
    
    def __init__(self, Equation : bitarray, Value : int) -> None:
        self._equation = Equation.copy()
        self._value = Value
        self._first_one = None
        self._ones_count = None
        
    def __len__(self) -> int:
        return len(self._equation)
    
    def __repr__(self) -> str:
        return f"CompactorSolverEquation({len(self)}, {self._value})"
    
    def __str__(self) -> str:
        Result = f"{str(self._equation)} {self._value}  ({self.getFirstOnePosition()},{self.getOnesCount()})"
        if self.isUnambigolous():
            Result += " U"
        return Result
    
    def __eq__(self, Other : CompactorSolverEquation) -> bool:
        if self._value != Other._value:
            return False
        if self._first_one is not None and Other._first_one is not None:
            if self._first_one != Other._first_one:
                return False
        if self._ones_count is not None and Other._ones_count is not None:
            if self._ones_count != Other._ones_count:
                return False
        return self._equation != Other._equation
    
    def __ne__(self, Other : CompactorSolverEquation) -> bool:
        return not self.__eq__(Other)
        
    def __lt__(self, Other : CompactorSolverEquation) -> bool:
        if self._first_one is not None and Other._first_one is not None:
            if self._first_one < Other._first_one:
                return True
            if self._first_one > Other._first_one:
                return False
        return self._equation < Other._equation
    
    def __le__(self, Other : CompactorSolverEquation) -> bool:
        if self._first_one is not None and Other._first_one is not None:
            if self._first_one < Other._first_one:
                return True
            if self._first_one > Other._first_one:
                return False
        return self._equation <= Other._equation
        
    def __gt__(self, Other : CompactorSolverEquation) -> bool:
        if self._first_one is not None and Other._first_one is not None:
            if self._first_one > Other._first_one:
                return True
            if self._first_one < Other._first_one:
                return False
        return self._equation > Other._equation
    
    def __ge__(self, Other : CompactorSolverEquation) -> bool:
        if self._first_one is not None and Other._first_one is not None:
            if self._first_one > Other._first_one:
                return True
            if self._first_one < Other._first_one:
                return False
        return self._equation >= Other._equation
    
    def getFirstOnePosition(self) -> int:
        if self._first_one is None:
            self._first_one = self._equation.find(1)
        return self._first_one
    
    def getOnesCount(self) -> int:
        if self._ones_count is None:
            self._ones_count = self._equation.count(1)
        return self._ones_count
    
    def isEmpty(self) -> bool: # 00000... = 0
        return self.getOnesCount() == 0 and self._value == 0
    
    def isUnambigolous(self) -> bool: # tylko jedna zmienna
        return self.getOnesCount() == 1
    
    def isContradictory(self) -> bool: # rownanie sprzeczne (0000... = 1)
        return self.getOnesCount() == 0 and self._value == 1
    
    def xorInPlace(self, Other : CompactorSolverEquation):
        self._equation ^= Other._equation
        self._value ^= Other._value
        self._ones_count = None
        if Other._first_one is not None and self._first_one is not None:
            if Other._first_one < self._first_one:
                self._first_one = Other._first_one
            if Other._first_one == self._first_one:
                self._first_one = None
        else:
            self._first_one = None
            
    def xorInPlaceIfVariableExists(self, Other : CompactorSolverEquation, VarIndex : int):
        if self._first_one is not None:
            if VarIndex < self._first_one:
                return
            if VarIndex == self._first_one:
                self.xorInPlace(Other)
                return
        if self._equation[VarIndex]:
            self.xorInPlace(Other)
                
            
                    
    def getOnesPositions(self) -> list:
        return self._equation.search(1)
                
    def removeVariableWhichIs0(self, VarIndex : int):
        self._equation[VarIndex] = 0
        if self._first_one is not None and self._first_one == VarIndex:
            self._first_one = None
        self._ones_count = None
        
    def removeVariableWhichIs1(self, VarIndex : int):
        if self._equation[VarIndex]:
            self._equation[VarIndex] = 0
            self._value = (1 - self._value)
            if self._first_one is not None and self._first_one == VarIndex:
                self._first_one = None
            self._ones_count = None
        
    def getValue(self) -> int:
        return self._value
        
    def copy(self) -> CompactorSolverEquation:
        Result = CompactorSolverEquation(self._equation, self._value)
        Result._ones_count = self._ones_count
        Result._first_one = self._first_one
        
        
class CompactorSolver:
    
    __slots__ = ("_equations", "_unambigolous_ones", "_max_ones", "_recursion_level")
    
    def __init__(self, MaxOnesCount : int, Equations : list = None) -> None:
        self._unambigolous_ones = []
        self._max_ones = MaxOnesCount
        self._equations = []
        self._recursion_level = 0
        if type(Equations) is list:
            for Eq in Equations:
                self.addEquation(Eq)
        
    def __repr__(self) -> str:
        return f"CompactorSolver({len(self)})"
    
    def __str__(self) -> str:
        Result = ""
        Second = 0
        for i in range(len(self)):
            if Second:
                Result += "\n"
            else:
                Second = 1
            Result += "  " * self._recursion_level
            Result += f"{i}: \t{str(self._equations[i])}"
        return Result
    
    def __len__(self) -> int:
        return len(self._equations)
    
    def removeVarsFor0(self, VarIndex : int):
        for Eq in self._equations:
            Eq.removeVariableWhichIs0(VarIndex)
            
    def removeVarsFor1(self, VarIndex : int):
        for Eq in self._equations:
            Eq.removeVariableWhichIs1(VarIndex)
        self._unambigolous_ones.append(VarIndex)
            
    def addEquation(self, Equation : CompactorSolverEquation):
        if 0 and Equation.isUnambigolous():
            VPos = Equation.getFirstOnePosition()
            if Equation.getValue():
                for e in self._equations:
                    e.removeVariableWhichIs1(VPos)
                self._unambigolous_ones.append(Equation.getFirstOnePosition())
            else:
                for e in self._equations:
                    e.removeVariableWhichIs0(VPos)
            return
        self._equations.append(Equation)
        
    def cleanEquations(self) -> bool:
        i = 0
        while i < len(self._equations):
            Eq = self._equations[i]
            if Eq.isContradictory():
                return False
            if Eq.isEmpty():
                del self._equations[i]
                continue
            if Eq.isUnambigolous():
                if Eq.getValue():
                    for j in range(len(self)):
                        if i == j:
                            continue
                        self._equations[j].removeVariableWhichIs1(Eq.getFirstOnePosition())
                    self._unambigolous_ones.append(Eq.getFirstOnePosition())
                    if len(self._unambigolous_ones) > self._max_ones:
                        return False
                else:
                    for j in range(len(self)):
                        if i == j:
                            continue
                        self._equations[j].removeVariableWhichIs0(Eq.getFirstOnePosition())
                del self._equations[i]
                continue
            i += 1
        return True
            
    def getFoundOnes(self) -> list:
        return self._unambigolous_ones.copy()
    
    def howManyNewOnesToFind(self) -> int:
        Result = self._max_ones - len(self._unambigolous_ones)
        if Result < 0:
            Result = 0
        return Result
        
    def solve(self, MaxRecursionDepth : int = 100) -> list:
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "MaxOnes:", self._max_ones)
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "Given eqs:")
        #print(self)        
        if not self.cleanEquations():
            #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "return [] because clear is false:")
            return []
        self.gaussRound()
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "Gaussed eqs:")
        #print(self)
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "Known ones:", self._unambigolous_ones)
        if not self.cleanEquations():
            #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "return [] because clear is false:")
            return []
        if len(self) == 0:
            #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", f"return because of size 0 [{self._unambigolous_ones}]:")
            return [self._unambigolous_ones]
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "Processed eqs:")
        #print(self)
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", "Known ones:", self._unambigolous_ones)
        if self.howManyNewOnesToFind() <= 1:
            #print("HERE")
            for i in range(len(self)):
                if self._equations[i].getValue() == 0:
                    Vars = self._equations[i].getOnesPositions()
                    for v in Vars:
                        for j in range(len(self)):
                            self._equations[j].removeVariableWhichIs0(v)
            if not self.cleanEquations():
                return []
            if len(self) == 0:
                #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", f"return after zeroing[{self._unambigolous_ones}]:")
                return [self._unambigolous_ones]
        if self._recursion_level >= MaxRecursionDepth:
            return []
        BestIndex = 0
        BestVars = self._equations[BestIndex].getOnesCount()
        BestVal = self._equations[BestIndex].getValue()
        for i in range(len(self)):
            VarCount = self._equations[i].getOnesCount()
            Val = self._equations[i].getValue()     
            if Val and VarCount <= 10:
                BestVal = Val
                BestIndex = i
                BestVars = VarCount
                break
            elif not BestVal and VarCount < BestVars:
                BestVal = Val
                BestIndex = i
                BestVars = VarCount
            elif VarCount < BestVars > 10:
                BestVal = Val
                BestIndex = i
                BestVars = VarCount      
        #print("  ", "BestIndex:", BestIndex, "BestVars:", BestVars, "BestVal:", BestVal)
        VarCandidates = self._equations[BestIndex].getOnesPositions()
        Val = self._equations[BestIndex].getValue()
        OneCombinations = []
        MaxK = self.howManyNewOnesToFind()
        if MaxK > len(VarCandidates):
            MaxK = len(VarCandidates)
        if Val == 0:
            OneCombinations.append([])
            for k in range(2, MaxK+1, 2):
                OneCombinations += List.getCombinations(VarCandidates, k)
        else:
            for k in range(1, MaxK+1, 2):
                OneCombinations += List.getCombinations(VarCandidates, k)
        from copy import deepcopy
        Results = []
        for i in range(len(OneCombinations)):
            print(self._recursion_level," :\t -> ", i+1, "/", len(OneCombinations), " \t", f"EQS: {len(self._equations)}, MaxNewOnes: {self.howManyNewOnesToFind()},  Val: {BestVal}")
            Comb = OneCombinations[i]
            NewSolver = CompactorSolver(self.howManyNewOnesToFind())
            NewSolver._equations = deepcopy(self._equations)
            NewSolver._recursion_level = self._recursion_level + 1
            for VarCandid in VarCandidates:
                if VarCandid in Comb:
                    NewSolver.removeVarsFor1(VarCandid)
                else:
                    NewSolver.removeVarsFor0(VarCandid)
            ResAux = NewSolver.solve(MaxRecursionDepth)
            for Res in ResAux:
                Results.append(self._unambigolous_ones + Res)
            AioShell.removeLastLine()
        #print(self._recursion_level," :\t", '  '*self._recursion_level,"  ", f"return {Results}:")
        return Results
        
    def gaussRound(self):
        if len(self) < 1:
            return
        for VarPos in range(len(self._equations[0])):
            for i in range(len(self)):
                if self._equations[i].getFirstOnePosition() == VarPos:
                    for j in range(len(self)):
                        if i != j:
                            self._equations[j].xorInPlaceIfVariableExists(self._equations[i], VarPos)
                    break
    
    

class CompactorSimulator:
    pass
class CompactorSimulator:
    
    __slots__ = ("ScanChainsCount", "GlobalSumPresent", "_ShiftRegistersPresent", "_ShiftRegistersNonOverlapPresent")
    
    def copy(self) -> CompactorSimulator:
        Result = CompactorSimulator(self.ScanChainsCount, self.GlobalSumPresent)
        Result._ShiftRegistersPresent = self._ShiftRegistersPresent.copy()
        Result._ShiftRegistersNonOverlapPresent = self._ShiftRegistersNonOverlapPresent.copy()
        return Result
    
    def __init__(self, ScanChainsCount : int, GlobalSumPresent : bool = True) -> None:
        if type(ScanChainsCount) is CompactorSimulator:
            self.ScanChainsCount = ScanChainsCount.ScanChainsCount
            self.GlobalSumPresent = ScanChainsCount.GlobalSumPresent    
            self._ShiftRegistersPresent = ScanChainsCount._ShiftRegistersPresent.copy() 
            self._ShiftRegistersNonOverlapPresent = ScanChainsCount._ShiftRegistersNonOverlapPresent.copy()
        else:
            self.ScanChainsCount = int(ScanChainsCount)
            self.GlobalSumPresent = bool(GlobalSumPresent)
            self._ShiftRegistersPresent = set()
            self._ShiftRegistersNonOverlapPresent = set()
            
    def setOption(self, Option : int = 1):
        self._ShiftRegistersPresent = set()
        self._ShiftRegistersNonOverlapPresent = set()
        if Option == 2:
            self.GlobalSumPresent = True
            self.addShiftRegister(2, -1, False)
            self.addShiftRegister(-2, 0, False)
        else:
            self.GlobalSumPresent = True
            self.addShiftRegister(1, 0, True)
            self.addShiftRegister(-1, 0, True)
        
    def addShiftRegister(self, EveryN : int = 1, Offset = 0, Overlap : bool = True):
        if Overlap:
            self._ShiftRegistersPresent.add( (EveryN, Offset) )
        else:
            self._ShiftRegistersNonOverlapPresent.add( (EveryN, Offset) )
        
    def removeShiftRegister(self, EveryN : int, Offset = 0, Overlap : bool = True):
        if Overlap:
            self._ShiftRegistersPresent.remove( (EveryN, Offset) )
        else:
            self._ShiftRegistersNonOverlapPresent.remove( (EveryN, Offset) )
        
    def getShiftRegistersPresent(self, Overlap : bool = True) -> tuple:
        if Overlap:
            return tuple(self._ShiftRegistersPresent)
        return tuple(self._ShiftRegistersNonOverlapPresent)
    
    def _getLinearEquationMaskaForGlobalXorOld(self, Signature : bitarray) -> list:
        Result = []
        Cycles = len(Signature) - self.ScanChainsCount
        VarCount = self.ScanChainsCount * Cycles
        for Cycle in range(Cycles):
            Eq = bau.zeros(VarCount + 1)
            for i in range(Cycle * self.ScanChainsCount, (Cycle+1) * self.ScanChainsCount, 1):
                Eq[i] = 1
            if Signature[Cycle]:
                Eq[-1] = 1
            Result.append(Eq)
        return Result
    
    def _getLinearEquationMaskaForGlobalXor(self, Signature : bitarray) -> list:
        Result = []
        Cycles = len(Signature) - self.ScanChainsCount
        VarCount = self.ScanChainsCount * Cycles
        for Cycle in range(Cycles):
            Eq = bau.zeros(VarCount)
            for i in range(Cycle * self.ScanChainsCount, (Cycle+1) * self.ScanChainsCount, 1):
                Eq[i] = 1
            Eq = CompactorSolverEquation(Eq, Signature[Cycle])
            Result.append(Eq)
        return Result
    
    def _getLinearEquationMaskaForOverlappedRegisterOld(self, Signature : tuple) -> list:
        Result = []
        Cycles = len(Signature[1]) - self.ScanChainsCount
        VarCount = self.ScanChainsCount * Cycles
        if Signature[0][0] < 0:
            Up = False
        else:
            Up = True
        EveryN = abs(Signature[0][0])
        Offset = Signature[0][1]
        for SIndex in range(1, len(Signature[1])):
            Eq = bau.zeros(VarCount + 1)
            for C in range(0, Cycles, 1):
                if Up:
                    S = self.ScanChainsCount - SIndex + C
                    if S >= self.ScanChainsCount:
                        break
                    if S < 0: 
                        continue
                    for MUL in range(0, EveryN, 1):
                        Sin = (S + Offset + MUL) % self.ScanChainsCount
                        #print(SIndex, C, Sin)
                        Eq[self.cellPositionToEquationMaskIndex(C, Sin)] = 1
                else:
                    S = SIndex - C - 1
                    if S >= self.ScanChainsCount:
                        continue
                    if S < 0: 
                        break
                    for MUL in range(0, EveryN, 1):
                        Sin = (S - Offset - MUL) % self.ScanChainsCount
                        #print(SIndex, C, Sin)
                        Eq[self.cellPositionToEquationMaskIndex(C, Sin)] = 1
            if Signature[1][SIndex]:
                Eq[-1] = 1
            Result.append(Eq)
        return Result
    
    def _getLinearEquationMaskaForOverlappedRegister(self, Signature : tuple) -> list:
        Result = []
        Cycles = len(Signature[1]) - self.ScanChainsCount
        VarCount = self.ScanChainsCount * Cycles
        if Signature[0][0] < 0:
            Up = False
        else:
            Up = True
        EveryN = abs(Signature[0][0])
        Offset = Signature[0][1]
        for SIndex in range(1, len(Signature[1])):
            Eq = bau.zeros(VarCount)
            for C in range(0, Cycles, 1):
                if Up:
                    S = self.ScanChainsCount - SIndex + C
                    if S >= self.ScanChainsCount:
                        break
                    if S < 0: 
                        continue
                    for MUL in range(0, EveryN, 1):
                        Sin = (S + Offset + MUL) % self.ScanChainsCount
                        #print(SIndex, C, Sin)
                        Eq[self.cellPositionToEquationMaskIndex(C, Sin)] = 1
                else:
                    S = SIndex - C - 1
                    if S >= self.ScanChainsCount:
                        continue
                    if S < 0: 
                        break
                    for MUL in range(0, EveryN, 1):
                        Sin = (S - Offset - MUL) % self.ScanChainsCount
                        #print(SIndex, C, Sin)
                        Eq[self.cellPositionToEquationMaskIndex(C, Sin)] = 1
            Eq = CompactorSolverEquation(Eq, Signature[1][SIndex])
            Result.append(Eq)
        return Result
    
    def getLinearEquationMasks(self, Signatures) -> list:
        Result = []
        for Signature in Signatures:
            if Signature[0][0] == 0:
                Result += self._getLinearEquationMaskaForGlobalXor(Signature[1])
            elif Signature[0][2]:
                Result += self._getLinearEquationMaskaForOverlappedRegister(Signature)
        return Result
    
    def findFaultPatternsSolvingEquations(self, FaultFreeInputData : bitarray, OutputData : list, MaxFaultsCount : int = 18, MaxRecursionDepth = 100) -> list:
        FaultFreeOutputData = self.simulate(FaultFreeInputData)
        Signatures = []
        for i in range(len(OutputData)):
            Signature = [OutputData[i][0]]
            Signature.append(OutputData[i][1] ^ FaultFreeOutputData[i][1])
            Signatures.append(Signature)
        Eqs = self.getLinearEquationMasks(Signatures)
        #EqSystem = BitarrayExtendedMatrix(Eqs)
        EqSystem = CompactorSolver(MaxFaultsCount, Eqs)
        if 0:
            print(OutputData)
            print(Signatures)
            print("BASE EQUATION SYSTEM:")
            print(EqSystem)
            print("STARTING SOLVER:")
        #Solutions = EqSystem.solve(MaxFaultsCount, MaxRecursionDepth=MaxRecursionDepth)
        Solutions = EqSystem.solve(MaxRecursionDepth)
        Result = []
        for Sol in Solutions:
            Res = []
            for S in Sol:
                Res.append(self.EquationMaskIndexToCellPosition(S))
            Result.append(Res)
        return Result
    
    def cellPositionToEquationMaskIndex(self, Cycle : int, ScanIndex : int) -> int:
        return Cycle * self.ScanChainsCount + ScanIndex
    
    def EquationMaskIndexToCellPosition(self, Index : int) -> tuple:
        return (Index // self.ScanChainsCount, Index % self.ScanChainsCount)
        
    def simulate(self, InputData : bitarray, WordsLimit : int = None, FlushAllBitsFromShiftRegisters : bool = True) -> tuple:
        if self.GlobalSumPresent:
            GlobalSum = bitarray()
        ShiftRegisters = [bau.zeros(self.ScanChainsCount) for _ in range(len(self._ShiftRegistersPresent))]
        ShiftRegistersNonOverlap = [bau.zeros(ceil(self.ScanChainsCount / abs(Item[0]))) for Item in self._ShiftRegistersNonOverlapPresent]
        ShiftRegistersResult = [bitarray() for _ in range(len(self._ShiftRegistersPresent))]
        ShiftRegistersNonOverlapResult = [bitarray() for _ in range(len(self._ShiftRegistersNonOverlapPresent))]
        WordIndex = 0
        ScanLength = len(InputData) // self.ScanChainsCount
        for Word in Generators().subLists(InputData, self.ScanChainsCount):
            if WordsLimit is not None and WordIndex >= WordsLimit:
                break
            WordIndex += 1
            if len(Word) < self.ScanChainsCount:
                Word += bau.zeros(self.ScanChainsCount - len(Word))
            if self.GlobalSumPresent:
                GlobalSum.append((Word.count(1) % 2))
            i = 0
            for Item in self._ShiftRegistersPresent:
                ShiftRegistersResult[i].append(ShiftRegisters[i][-1])
                N = Item[0]
                Rev = False
                if N < 0:
                    N = abs(N)
                    Rev = True
                O = Item[1]
                ShiftRegisters[i] >>= 1
                for j in range(self.ScanChainsCount):
                    LocalSum = 0
                    for k in range(N):
                        if Rev:
                            LocalSum += Word[((self.ScanChainsCount-1) - (j + O + k)) % self.ScanChainsCount]
                        else:
                            LocalSum += Word[(j + O + k) % self.ScanChainsCount]
                    ShiftRegisters[i][j] ^= (LocalSum % 2)
                #print(Item, ShiftRegisters[i])
                i += 1
            i = 0
            for Item in self._ShiftRegistersNonOverlapPresent:
                ShiftRegistersNonOverlapResult[i].append(ShiftRegistersNonOverlap[i][-1])
                N = Item[0]
                Rev = False
                if N < 0:
                    N = abs(N)
                    Rev = True
                O = Item[1]
                ShiftRegistersNonOverlap[i] >>= 1
                j = 0
                bi = 0
                while j < self.ScanChainsCount:
                    LocalSum = 0
                    for k in range(N):
                        if Rev:
                            LocalSum += Word[((self.ScanChainsCount-1) - (j + O + k)) % self.ScanChainsCount]
                        else:
                            LocalSum += Word[(j + O + k) % self.ScanChainsCount]
                    j += N
                    ShiftRegistersNonOverlap[i][bi] ^= (LocalSum % 2)
                    bi += 1
                i += 1
        if FlushAllBitsFromShiftRegisters:
            for i in range(self.ScanChainsCount):
                if self.GlobalSumPresent:
                    GlobalSum.append(0)
                j = 0
                for Item in self._ShiftRegistersPresent:
                    N = Item[0]
                    S = Item[1]
                    ShiftRegistersResult[j].append(ShiftRegisters[j][-1])
                    ShiftRegisters[j] >>= 1
                    j += 1
                for Item in self._ShiftRegistersNonOverlapPresent:
                    N = Item[0]
                    S = Item[1]
                    ShiftRegistersNonOverlapResult[j].append(ShiftRegistersNonOverlap[j][-1])
                    ShiftRegistersNonOverlap[j] >>= 1
                    j += 1
        Result = []
        if self.GlobalSumPresent:
            Result.append( ((0, 0, True), GlobalSum[:ScanLength]) )
        i = 0
        for Item in self._ShiftRegistersPresent:
            Result.append( (Item + tuple([True]), ShiftRegistersResult[i][1:self.ScanChainsCount+ScanLength]))
            i += 1
        i = 0
        for Item in self._ShiftRegistersNonOverlapPresent:
            Result.append( (Item + tuple([True]), ShiftRegistersNonOverlapResult[i][1:ceil(self.ScanChainsCount/abs(Item[0]))+ScanLength]) )
            i += 1
        return tuple(Result)

    def getFaultCandidatesPerTimeSlot(self, MaxParallelFaults : int = 2, MaxFaultsDistance : int = 3) -> list:
        Result = []
        Indices = [i for i in range(self.ScanChainsCount)]
        for i in range(MaxParallelFaults):
            for Comb in List.getCombinations(Indices, i+1):
                if Comb[-1] - Comb[0] <= MaxFaultsDistance:
                    Result.append(Comb)
        return Result
    
    def _areSimResOK(self, GoldRes, SimRes) -> bool:
        for i in range(len(SimRes)):
            if not Bitarray.areLeftBitsEqual(GoldRes[i][1], SimRes[i][1]):
                return False
        return True
    
    def _mpSim(self, TreeItem, FaultFreeInputWords, FaultCandidatesPerCycleMasks, FaultCandidatesPerCycleCount, FaultCandidatesScanChainMinMax, MaxFaultsCount, MaxFaultDistanceInCyclesDomain, MaxFaultsDistancePerCycle, OutputData, Cycle) -> tuple:
        Id = TreeItem[0]
        FaultCounter = TreeItem[1][0]
        OldMin = TreeItem[1][1]
        OldMax = TreeItem[1][2]
        FullWord = bitarray()
        BranchesToRemove = []
        WhatToAdd = []
        for i in range(len(Id)):
            FullWord += (FaultFreeInputWords[i] ^ FaultCandidatesPerCycleMasks[Id[i]])
        #AnyPassed = False
        for i in range(len(FaultCandidatesPerCycleMasks)):
            FaultCounterNew = FaultCounter + FaultCandidatesPerCycleCount[i]
            IdNew = Id + [i]
            if FaultCounterNew > MaxFaultsCount:
                continue
            ActMin = FaultCandidatesScanChainMinMax[i][0]
            ActMax = FaultCandidatesScanChainMinMax[i][1]
            if ActMin is not None:
                if OldMin is not None:
                    if ActMin < OldMin:
                        NewMin = OldMin
                    else:
                        NewMax = ActMin
                    if ActMax > OldMax:
                        NewMax = OldMax
                    else:
                        NewMin = ActMax
                else:
                    NewMin = ActMin
                    NewMax = ActMax
            else:
                NewMin = OldMin
                NewMax = OldMax
            if NewMax is not None and NewMin is not None and (NewMax - NewMin) > MaxFaultsDistancePerCycle:
#                print("OLD", OldMin, OldMax, "  ACT", ActMin, ActMax)
                continue
            PNum0 = None
            LastPNum = 0
            for j in range(len(IdNew)):
                PNum = IdNew[j]
                if PNum > 0:
                    if PNum0 is None:
                        PNum0 = j
                    LastPNum = j
            if PNum0 is not None and (LastPNum - PNum0) > MaxFaultDistanceInCyclesDomain:
                continue
            FullWordNew = FullWord + (FaultFreeInputWords[len(Id)] ^ FaultCandidatesPerCycleMasks[i])
            SimRes = self.simulate(FullWordNew, Cycle, False)
            if self._areSimResOK(OutputData, SimRes):
                WhatToAdd.append([IdNew, [FaultCounterNew, NewMin, NewMax]])
            #    AnyPassed = True
            #if not AnyPassed:
            #    BranchesToRemove.append(Id)
        return (BranchesToRemove, WhatToAdd)
    
    def _mpSimSerial(self, TreeItems, FaultFreeInputWords, FaultCandidatesPerCycleMasks, FaultCandidatesPerCycleCount, FaultCandidatesScanChainMinMax, MaxFaultsCount, MaxFaultDistanceInCyclesDomain, MaxFaultsDistancePerCycle, OutputData, Cycle) -> tuple:
        BranchesToRemove = []
        WhatToAdd = []
        for TreeItem in TreeItems:
            btr, bta = self._mpSim(TreeItem, FaultFreeInputWords, FaultCandidatesPerCycleMasks, FaultCandidatesPerCycleCount, FaultCandidatesScanChainMinMax, MaxFaultsCount, MaxFaultDistanceInCyclesDomain, MaxFaultsDistancePerCycle, OutputData, Cycle)
            BranchesToRemove += btr
            WhatToAdd += bta
        return (BranchesToRemove, WhatToAdd)
    
    def findFaultPatterns(self, FaultFreeInputData : bitarray, OutputData : list, MaxFaultsCount : int = 8, 
                    MaxFaultsPerCycle : int = 2, MaxFaultsDistancePerCycle : int = 3, MaxFaultDistanceInCyclesDomain : int = 4) -> list:
        Result = []
        FaultCandidatesPerCycle = self.getFaultCandidatesPerTimeSlot(MaxFaultsPerCycle, MaxFaultsDistancePerCycle)
        FaultCandidatesPerCycleMasks = [bau.zeros(self.ScanChainsCount)]
        FaultCandidatesPerCycleCount = [0]
        FaultCandidatesScanChainMinMax = [[None, None]]
        for fc in FaultCandidatesPerCycle:
            Word = bau.zeros(self.ScanChainsCount)
            for i in fc:
                Word[i] = 1
            FaultCandidatesPerCycleCount.append(len(fc))
            FaultCandidatesPerCycleMasks.append(Word)   
            FaultCandidatesScanChainMinMax.append([min(fc), max(fc)])     
        CyclesCount = ceil(len(FaultFreeInputData) / self.ScanChainsCount)
        FaultFreeInputWords = List.splitIntoSublists(FaultFreeInputData, self.ScanChainsCount)
        SearchingTree = [] #SimpleTree()
        for Cycle in tqdm(range(1, CyclesCount+1)):
            #print(f"Cycle {Cycle} ======================================")
            if (Cycle == 1):
                for i in range(len(FaultCandidatesPerCycleMasks)):
                    SimRes = self.simulate(FaultFreeInputWords[0] ^ FaultCandidatesPerCycleMasks[i], 1, False)
                    if self._areSimResOK(OutputData, SimRes):
                        SearchingTree.append([[i], [FaultCandidatesPerCycleCount[i], FaultCandidatesScanChainMinMax[i][0], FaultCandidatesScanChainMinMax[i][1]]])
            else:
                NewSearchingTree = []
                #Splitted = List.splitIntoSublists(SearchingTree.getLevelItems(Cycle-2), 1000)
                Splitted = List.splitIntoSublists(SearchingTree, 1000)
                if len(Splitted) == 0:
                    break
                if len(Splitted) == 1:
                    for TreeItem in tqdm(Splitted[0]):
                        BranchesToRemove, WhatToAdd = self._mpSim(TreeItem, FaultFreeInputWords, FaultCandidatesPerCycleMasks, FaultCandidatesPerCycleCount, FaultCandidatesScanChainMinMax, MaxFaultsCount, MaxFaultDistanceInCyclesDomain, MaxFaultsDistancePerCycle, OutputData, Cycle)
                        NewSearchingTree += WhatToAdd
                else:
                    for tpl in p_uimap(partial(self._mpSimSerial, FaultFreeInputWords=FaultFreeInputWords, FaultCandidatesPerCycleMasks=FaultCandidatesPerCycleMasks, FaultCandidatesPerCycleCount=FaultCandidatesPerCycleCount, FaultCandidatesScanChainMinMax=FaultCandidatesScanChainMinMax, MaxFaultsCount=MaxFaultsCount, MaxFaultDistanceInCyclesDomain=MaxFaultDistanceInCyclesDomain, MaxFaultsDistancePerCycle=MaxFaultsDistancePerCycle, OutputData=OutputData, Cycle=Cycle), Splitted):
                        BranchesToRemove, WhatToAdd = tpl
                        NewSearchingTree += WhatToAdd     
                AioShell.removeLastLine()
                SearchingTree = NewSearchingTree
        AioShell.removeLastLine()
        Result = []
        for TreeItem in SearchingTree:
            Id = TreeItem[0]
            FullWord = bitarray()
            for i in range(len(Id)):
                FullWord += (FaultFreeInputWords[i] ^ FaultCandidatesPerCycleMasks[Id[i]])
            SimRes = self.simulate(FullWord)
            if self._areSimResOK(OutputData, SimRes):
                Result.append(FullWord)
        return Result
    
    
    def cudaFindFaultPatterns(self, FaultFreeInputData : bitarray, OutputData : list, MaxFaultsCount : int = 8, 
                    MaxFaultsPerCycle : int = 2, MaxFaultsDistancePerCycle : int = 3, MaxFaultDistanceInCyclesDomain : int = 4,
                    CudaBlocks : int = 1024, CudaThreads : int = 1024, MaxSearchingTreeBranches : int = 40000000) -> list:
        from libs.cuda_utils import CudaCProgram
        FaultFreeOutputData = self.simulate(FaultFreeInputData)
        CompRegisters, CompValues = [], []
        for i in range(len(OutputData)):
            CReg = OutputData[i][0][:2]
            CVal = OutputData[i][1] ^ FaultFreeOutputData[i][1]
            CompRegisters.append(CReg)
            CompValues.append(CVal)
        ScanLength = ceil(len(FaultFreeInputData) / self.ScanChainsCount)
        if 0:
            print("scan_length", ScanLength)
            print("scan_count", self.ScanChainsCount)
            print("compactor_registers", CompRegisters)
            print("compactor_value", CompValues)
            print("max_total_fails", MaxFaultsCount)
            print("max_fails_per_clock_cycle", MaxFaultsPerCycle)
            print("max_fails_vertical_distance", MaxFaultsDistancePerCycle)
            print("max_fails_horizontal_distance", MaxFaultDistanceInCyclesDomain)
            print("max_tree_branches", MaxSearchingTreeBranches)
        cu = CudaCProgram(Aio.getPath() + 'libs/research_projects/orthogonal_compactor/search_fail_map.cu', 
                            scan_length=ScanLength, scan_count=self.ScanChainsCount,
                            compactor_registers=CompRegisters, compactor_value=CompValues,
                            max_total_fails=MaxFaultsCount, max_fails_per_clock_cycle=MaxFaultsPerCycle,
                            max_fails_vertical_distance=MaxFaultsDistancePerCycle, max_fails_horizontal_distance=MaxFaultDistanceInCyclesDomain,
                            max_tree_branches=MaxSearchingTreeBranches,
                            cuda_blocks=CudaBlocks, cuda_threads=CudaThreads)
        r = cu.run()
        try:        
            return ast.literal_eval(r)
        except:
            return r
        
            
    #########################################################
    # SEARCHING FUNCTION
    #########################################################
    def _fsIndices(self, SCAN_COUNT : int, auxi : int, xi : int, Option : int = 1) -> tuple:
        if Option == 2:
            li = auxi//2 + xi
            ui = SCAN_COUNT//2 - auxi//2 + xi - 1 - (auxi%2)
            if ui < xi: 
                ui += SCAN_COUNT//2
        else:
            ui = auxi+xi
            li = xi+SCAN_COUNT-auxi-1
        return li, ui
    
    def _fsCandidates(self, SCAN_COUNT : int, UpperReg : bitarray, LowerReg : bitarray, XorReg : bitarray, JustFound : list = [], FailsToSkip = [], SpeedUp : bool = False, Option : int = 1, IgnoreUpperRegister : bool = False) -> tuple:
        Candidates = []
        Found = JustFound.copy()
        FoundInGroup = 0
        # searching for 3 1s
        #print(Indent, "Searching for 3 1s")
        #print("CANDIDATES")
        #print("UpperReg:", UpperReg)
        #print("XorReg:", XorReg)
        #print("LowerReg:", LowerReg)
        if not IgnoreUpperRegister:
            for xi in XorReg.search(1):
                for auxi in range(SCAN_COUNT):
                    li, ui = self._fsIndices(SCAN_COUNT, auxi, xi, Option)
                    FF = tuple([xi, auxi])
                    if FF in Found or FF in FailsToSkip:
                        continue
                    if UpperReg[ui] and LowerReg[li] and XorReg[xi]:
                        Candidates.append(tuple([li, xi, ui, FF]))
                        FoundInGroup = 3
                if SpeedUp:
                    if len(Candidates) > 0:
                        break
        if len(Candidates) < 1:
            # searching for 2 1s
            #print(Indent, "Searching for 2 1s")
            for xi in range(len(XorReg)):
                for auxi in range(SCAN_COUNT):
                    li, ui = self._fsIndices(SCAN_COUNT, auxi, xi, Option)
                    FF = tuple([xi, auxi])
                    if FF in Found or FF in FailsToSkip:
                        continue
                    if UpperReg[ui] and LowerReg[li]:
                        Candidates.append(tuple([li, xi, ui, FF, "x"]))
                        FoundInGroup = 2
                    elif UpperReg[ui] and XorReg[xi]:
                        Candidates.append(tuple([li, xi, ui, FF, "l"]))
                        FoundInGroup = 2
                    elif LowerReg[li] and XorReg[xi]:    
                        Candidates.append(tuple([li, xi, ui, FF, "u"]))
                        FoundInGroup = 2
        if len(Candidates) < 1:
            # searching for 1 1s
            #print(Indent, "Searching for 1 1s")
            FoundSOmething = 0
            for xi in range(len(XorReg)):
                for auxi in range(SCAN_COUNT):
                    li, ui = self._fsIndices(SCAN_COUNT, auxi, xi, Option)
                    FF = tuple([xi, auxi])
                    if FF in Found or FF in FailsToSkip:
                        #print(Indent, "FF in Found or FailsToSkip")
                        continue
                    if UpperReg[ui] or LowerReg[li] or XorReg[xi]:
                        Candidates.append(tuple([li, xi, ui, FF]))
                        FoundInGroup = 1
                        FoundSOmething = 1
                if FoundSOmething:
                    break
        #print("JustFound:", JustFound)
        #print("Candidates:", Candidates)
        #print("FoundInGroup:", FoundInGroup)
        return Candidates, FoundInGroup, Found
        



    def _fastSolve(self, SCAN_COUNT : int, UpperReg : bitarray, LowerReg : bitarray, XorReg : bitarray, MaxFailCount : int, MaxDifferentScanChains : int = None, SpeedUp = False, Adaptive : bool = False, ReturnAlsoPartialResults = False, JustFound : list = [], FailsToSkip = [], RecursionLevel : int = 0, Indent = "", Option : int = 1, TimeOut : int = None, IgnoreUpperRegister : bool = False):
        if TimeOut is not None:
            if TimeOut < 0:
                if ReturnAlsoPartialResults:
                    return [JustFound]
                return []
            t0 = time.time()
        #print(Indent, "searching, justfound:", JustFound)
        if len(JustFound) > MaxFailCount:   
            #print(Indent, "return - too much fails")
            if ReturnAlsoPartialResults:
                return [JustFound]
            return []
        if IgnoreUpperRegister:
            if LowerReg.count(1) == 0 and XorReg.count(1) == 0:
                #print(Indent, "return - signatures are empty")
                return [JustFound]
        else:
            if UpperReg.count(1) == 0 and LowerReg.count(1) == 0 and XorReg.count(1) == 0:
                #print(Indent, "return - signatures are empty")
                return [JustFound]
        if len(JustFound) > 1 and MaxDifferentScanChains is not None:
            ScanChains = set()
            for F in JustFound:
                ScanChains.add(F[1])
            if len(ScanChains) > MaxDifferentScanChains:
                #print(Indent, "return - MaxDifferentScanChains exceeded", MaxDifferentScanChains, JustFound)
                if ReturnAlsoPartialResults:
                    return [JustFound]
                return []
        Candidates, FoundInGroup, Found = self._fsCandidates(SCAN_COUNT, UpperReg, LowerReg, XorReg, JustFound, FailsToSkip, SpeedUp, Option, IgnoreUpperRegister)
        Results = []
        if SpeedUp:
            if len(Candidates) > 0:
                CandidSets = []
                if len(Candidates) == 1:
                    CandidSets.append([Candidates[0]])
                else:
                    for i in range(len(Candidates)):
                        Ci = Candidates[i]
                        CSet = [Ci]
                        for j in range(i+1, len(Candidates)):
                            Cj = Candidates[j]
                            if Ci[0] != Cj[0] and Ci[1] != Cj[1] and Ci[2] != Cj[2]:
                                CSet.append(Cj)
                                break
                        CandidSets.append(CSet)
                for Set in CandidSets:
                    NewXorReg = XorReg.copy()
                    NewUpperReg = UpperReg.copy()
                    NewLowerReg = LowerReg.copy()
                    JustFound = Found.copy()
                    for C in Set:
                        JustFound.append(C[3])
                        NewUpperReg[C[2]] ^= 1
                        NewXorReg[C[1]] ^= 1
                        NewLowerReg[C[0]] ^= 1
                    if TimeOut is not None:
                        t1 = time.time()
                        TimeOutNow = TimeOut - (t1 - t0)
                    else:
                        TimeOutNow = None
                    R = self._fastSolve(SCAN_COUNT, NewUpperReg, NewLowerReg, NewXorReg, MaxFailCount, MaxDifferentScanChains, SpeedUp, Adaptive, ReturnAlsoPartialResults, JustFound, [], RecursionLevel+1, Indent+"  ", Option=Option, TimeOut=TimeOutNow, IgnoreUpperRegister=IgnoreUpperRegister)
                    if Adaptive and len(R) > 0:
                        for x in R:
                            if len(x) < MaxFailCount:
                                MaxFailCount = len(x)
                    Results += R
            else:
                print(Indent, "No candidates")
        else:
            if len(Candidates) > 0:
                BranchIt = 0
                if FoundInGroup in [3, 2]:
                    for thisi in range(len(Candidates)):
                        for otheri in range(thisi+1, len(Candidates)):
                            if Candidates[thisi][0] == Candidates[otheri][0] or Candidates[thisi][1] == Candidates[otheri][1] or Candidates[thisi][2] == Candidates[otheri][2]:
                                BranchIt = 1
                                break
                        if BranchIt:
                            break
                else:
                    BranchIt = 1
                #print(Indent, "BranchIt: ", BranchIt)
                if BranchIt: 
                    #print(len(Candidates))
                    for C in Candidates:
                        JustFound = Found.copy()
                        JustFound.append(C[3])
                    #    print(Indent, "NEW BRANCH 3 ", C[3])
                        NewXorReg = XorReg.copy()
                        NewUpperReg = UpperReg.copy()
                        NewLowerReg = LowerReg.copy()
                        NewUpperReg[C[2]] ^= 1
                        NewXorReg[C[1]] ^= 1
                        NewLowerReg[C[0]] ^= 1
                        if TimeOut is not None:
                            t1 = time.time()
                            TimeOutNow = TimeOut - (t1 - t0)
                        else:
                            TimeOutNow = None
                        R = self._fastSolve(SCAN_COUNT, NewUpperReg, NewLowerReg, NewXorReg, MaxFailCount, MaxDifferentScanChains, SpeedUp, Adaptive, ReturnAlsoPartialResults, JustFound, [], RecursionLevel+1, Indent+"  ", Option=Option, TimeOut=TimeOutNow, IgnoreUpperRegister=IgnoreUpperRegister)    
                        if Adaptive and len(R) > 0:
                            for x in R:
                                if len(x) < MaxFailCount:
                                    MaxFailCount = len(x)
                        Results += R
                if not BranchIt: 
                    for C in Candidates:
                        Found.append(C[3])
                        UpperReg[C[2]] ^= 1
                        XorReg[C[1]] ^= 1
                        LowerReg[C[0]] ^= 1
                    if TimeOut is not None:
                        t1 = time.time()
                        TimeOutNow = TimeOut - (t1 - t0)
                    else:
                        TimeOutNow = None
                    R = self._fastSolve(SCAN_COUNT, UpperReg, LowerReg, XorReg, MaxFailCount, MaxDifferentScanChains, SpeedUp, Adaptive, ReturnAlsoPartialResults, Found, [], RecursionLevel+1, Indent+"  ", Option=Option, TimeOut=TimeOutNow, IgnoreUpperRegister=IgnoreUpperRegister)              
                    if Adaptive and len(R) > 0:
                        for x in R:
                            if len(x) < MaxFailCount:
                                MaxFailCount = len(x)
                    Results += R
        #print(Indent, "H") 
        return Results
    

    def fastSolve(self, SCAN_COUNT : int, UpperReg : bitarray, LowerReg : bitarray, XorReg : bitarray, MaxFailCount : int, MaxDifferentScanChains : int = None, SpeedUp = False, Adaptive : bool = False, ReturnAlsoPartialResults = False, TimeOut : int = None, IgnoreUpperRegister : bool = False) -> list:
        sr = list(self._ShiftRegistersPresent)
        sn = list(self._ShiftRegistersNonOverlapPresent)
        if self.GlobalSumPresent and len(sr) == 2 and len(sn) == 0 and sr[0] == (1, 0) and sr[1] == (-1, 0):
            Option = 1
        elif self.GlobalSumPresent and len(sn) == 2 and len(sr) == 0 and sn[0] == (-2, 0) and sn[1] == (2, -1):
            Option = 2
        else:
            Aio.printError("Incorrect compactor config")
            return []
        return self._fastSolve(SCAN_COUNT, UpperReg, LowerReg, XorReg, MaxFailCount, MaxDifferentScanChains, SpeedUp, Adaptive, ReturnAlsoPartialResults, Option=Option, TimeOut=TimeOut, IgnoreUpperRegister=IgnoreUpperRegister)
    
    
    
    
class OCExperimentalStuff:
    
    __slots__ = ("MyCompactor", "ScanChainLength")
    
    def __init__(self, MyCompactor : CompactorSimulator, ScanChainLength : int) -> None:
        self.MyCompactor = MyCompactor
        self.ScanChainLength = ScanChainLength
        
    def _areFailReportsIdentical(self, A : list, B : list) -> bool:
        if len(A) != len(B):
            return False
        for i in range(len(A)):
            if A[i] not in B:
                return False
        return True
        
    def _getExpData(self, FailPattern : list) -> tuple:
        TestVector = bau.zeros(self.ScanChainLength * self.MyCompactor.ScanChainsCount)
        for Fail in FailPattern:
            VarIndex = self.MyCompactor.cellPositionToEquationMaskIndex(Fail[0], Fail[1])
            TestVector[VarIndex] = 1
        Signatures = []
        Response = self.MyCompactor.simulate(TestVector)
        for R in Response:
            Signatures.append(R[1])
        return Signatures[2], Signatures[1], Signatures[0]
    
    def _doMeasurement(self, FailPatternCombo : tuple, MinFailCount : int = 1, MaxFailCount : int = None, MaxDifferentScanChains : int = None, SpeedUp : bool = True, AdaptiveSearch : bool = False, TimeOut : int = None, IgnoreUpperRegister : bool = False, ReturnAlsoPartialResults : bool = False) -> tuple:
        FailPattern = FailPatternCombo[1]
        PatternId = FailPatternCombo[0]
        S1, S2, S3 = self._getExpData(FailPattern)
        t0 = time.time()
        Found = []
        if MinFailCount is None:
            MinFailCount = len(FailPattern)
        FC = MinFailCount
        while len(Found) < 1:
            if MaxFailCount is not None and FC > MaxFailCount:
                break
            if TimeOut is not None and time.time() - t0 > TimeOut:
                break
            Found = self.MyCompactor.fastSolve(self.MyCompactor.ScanChainsCount, S1, S2, S3, FC, MaxDifferentScanChains, SpeedUp, AdaptiveSearch, TimeOut=TimeOut, IgnoreUpperRegister=IgnoreUpperRegister, ReturnAlsoPartialResults=ReturnAlsoPartialResults)
            FC += 1
        t1 = time.time()  
        ok = 0
        for R in Found:
            if self._areFailReportsIdentical(FailPattern, R):
                ok = 1
                break
        return PatternId, ok, t1-t0, len(Found), len(FailPattern), FC-1, FailPattern, Found

    def doExperiments(self, FaultPatternsList, MaxFailCount : int = None, MaxDifferentScanChains : int = None, SpeedUp : bool = True, AdaptiveSearch : bool = False, TimeOut : int = None, MinFailCount : int = 1, IgnoreUpperRegister : bool = False, ReturnAlsoPartialResults : bool = False) -> list:
        FP = []
        if type(FaultPatternsList) is dict:
            for item in FaultPatternsList.items():
                FP.append(item)
        elif type(FaultPatternsList) is list:
            for item in FaultPatternsList:
                FP.append(tuple([0, item]))
        Result = []
        for R in p_uimap(partial(self._doMeasurement, MinFailCount=MinFailCount, MaxFailCount=MaxFailCount, MaxDifferentScanChains=MaxDifferentScanChains, SpeedUp=SpeedUp, AdaptiveSearch=AdaptiveSearch, TimeOut=TimeOut, IgnoreUpperRegister=IgnoreUpperRegister, ReturnAlsoPartialResults=ReturnAlsoPartialResults), FP):
            Result.append(R)
        AioShell.removeLastLine()
        return Result
        
    def doExperimentsIterator(self, FaultPatternsList, MaxFailCount : int = None, MaxDifferentScanChains : int = None, SpeedUp : bool = True, AdaptiveSearch : bool = False, TimeOut : int = None, MinFailCount : int = 1, IgnoreUpperRegister : bool = False, ReturnAlsoPartialResults : bool = False):
        FP = []
        if type(FaultPatternsList) is dict:
            for item in FaultPatternsList.items():
                FP.append(item)
        elif type(FaultPatternsList) is list:
            for item in FaultPatternsList:
                FP.append(tuple([0, item]))
        for R in p_uimap(partial(self._doMeasurement, MinFailCount=MinFailCount, MaxFailCount=MaxFailCount, MaxDifferentScanChains=MaxDifferentScanChains, SpeedUp=SpeedUp, AdaptiveSearch=AdaptiveSearch, TimeOut=TimeOut, IgnoreUpperRegister=IgnoreUpperRegister, ReturnAlsoPartialResults=ReturnAlsoPartialResults), FP):
            yield R
        