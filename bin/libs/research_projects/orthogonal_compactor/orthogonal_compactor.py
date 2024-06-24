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
    
    def solve(self, MaxFailCount : int = 10, MaxRecursionDepth : int = 3, Debug=0):
        self.toEchelonForm()
        if Debug:
            print(f"{' '*self._recursion_level}solve -----------")
        for RowI in range(len(self)-1):
            for RfixerI in range(RowI+1, len(self)):
                Aux = self._rows[RowI] ^ self._rows[RfixerI]
                if (Aux < self._rows[RowI]):
                    self._rows[RowI] = Aux
                    try:
                        del self._unambiguous[RowI]
                    except:
                        pass    
        if self.hasNoSolution():
            return None
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
            AmbiguousIndices = []
            for urowi in range(len(self._rows)):
                VarCount = self.isUnambiguous(urowi, ReturnNumberOfOnes=True)
                if VarCount > 1:
                    AmbiguousIndices.append((urowi, VarCount))
            #AmbiguousIndices.sort(key = lambda x: x[1])
            VarCandidates = []   
            if MaxNewOnes > 0:
                TheBestIndex = AmbiguousIndices[0][0]
                TheBestVars = AmbiguousIndices[0][1]
                IdealVars = 5
                if TheBestVars > IdealVars:
                    for i in range(1, len(AmbiguousIndices)):
                        if AmbiguousIndices[i][1] <= IdealVars:
                            TheBestIndex = AmbiguousIndices[i][0]
                            TheBestVars = AmbiguousIndices[i][1]
                            break
                        elif AmbiguousIndices[i][1] < TheBestVars:
                            TheBestIndex = AmbiguousIndices[i][0]
                            TheBestVars = AmbiguousIndices[i][1]
                TheBestAmbiguous = self._rows[TheBestIndex]
                for Var in TheBestAmbiguous[:-1].search(1):
                    VarCandidates.append(Var)
            else:
                IdealVars = 50
                TheBestVars = 0
                for AI in AmbiguousIndices:
                    TheBestIndex = AI[0]
                    TheBestVars += AI[1]
                    TheBestAmbiguous = self._rows[TheBestIndex]
                    for Var in TheBestAmbiguous[:-1].search(1):
                        VarCandidates.append(Var)
                    if TheBestVars > IdealVars:
                        break
            Combinations = []
            MaxK = len(VarCandidates)
            if MaxK > MaxNewOnes:
                MaxK = MaxNewOnes
            if TheBestAmbiguous[-1]:
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
        ToRemove = []
        for i in range(len(self._rows)-1, -1, -1):
            if self.isUnambiguous(i):
                if self._rows[i][-1]:
                    self._ambiguous_ones.append(self._rows[i].find(1))
                ToRemove.append(i)
            else:
                break
        for i in ToRemove:
            del self._rows[i]
        ToRemove = []
        for i in range(len(self._rows)):
            if self.isUnambiguous(i):
                if self._rows[i][-1]:
                    self._ambiguous_ones.append(self._rows[i].find(1))
                ToRemove.append(i)
            else:
                break
        for i in reversed(ToRemove):
            del self._rows[i]
        self._unambiguous = {}
    
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
    
    def _getLinearEquationMaskaForGlobalXor(self, Signature : bitarray) -> list:
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
        EqSystem = BitarrayExtendedMatrix(Eqs)
        if 0:
            print(OutputData)
            print(Signatures)
            print("BASE EQUATION SYSTEM:")
            print(EqSystem)
            print("STARTING SOLVER:")
        Solutions = EqSystem.solve(MaxFaultsCount, MaxRecursionDepth=MaxRecursionDepth)
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
        ShiftRegistersNonOverlap = [bau.zeros(ceil(self.ScanChainsCount / Item[0])) for Item in self._ShiftRegistersNonOverlapPresent]
        ShiftRegistersResult = [bitarray() for _ in range(len(self._ShiftRegistersPresent))]
        ShiftRegistersNonOverlapResult = [bitarray() for _ in range(len(self._ShiftRegistersPresent))]
        WordIndex = 0
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
                            LocalSum += Word[((self.ScanChainsCount-1) - (j + O)) % self.ScanChainsCount]
                        else:
                            LocalSum += Word[(j + O) % self.ScanChainsCount]
                        j += 1
                        if j >= self.ScanChainsCount:
                            break
                    ShiftRegistersNonOverlap[bi][j] ^= (LocalSum % 2)
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
        Result = []
        if self.GlobalSumPresent:
            Result.append( ((0, 0, True), GlobalSum) )
        i = 0
        for Item in self._ShiftRegistersPresent:
            Result.append( (Item + tuple([True]), ShiftRegistersResult[i]) )
            i += 1
        i = 0
        for Item in self._ShiftRegistersNonOverlapPresent:
            Result.append( (Item + tuple([True]), ShiftRegistersNonOverlapResult[i]) )
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