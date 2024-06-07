from libs.aio import *
from bitarray import *
from libs.utils_bitarray import *
from libs.utils_list import *
from libs.generators import *
from libs.simpletree import *


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
                ShiftRegistersResult[i].append(ShiftRegisters[i][-1])
                #print(Item, ShiftRegisters[i])
                i += 1
            i = 0
            for Item in self._ShiftRegistersNonOverlapPresent:
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
                ShiftRegistersNonOverlapResult[i].append(ShiftRegistersNonOverlap[i][-1])
                i += 1
        if FlushAllBitsFromShiftRegisters:
            for i in range(self.ScanChainsCount):
                if self.GlobalSumPresent:
                    GlobalSum.append(0)
                j = 0
                for Item in self._ShiftRegistersPresent:
                    N = Item[0]
                    S = Item[1]
                    ShiftRegisters[j] >>= 1
                    ShiftRegistersResult[j].append(ShiftRegisters[j][-1])
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
    
    def findFaultPatterns(self, FaultFreeInputData : bitarray, OutputData : list, MaxFaultsCount : int = 12, MaxFaultsPerCycle : int = 2, MaxFaultsDistancePerCycle : int = 3) -> list:
        Result = []
        FaultCandidatesPerCycle = self.getFaultCandidatesPerTimeSlot(MaxFaultsPerCycle, MaxFaultsDistancePerCycle)
        FaultCandidatesPerCycleMasks = [bau.zeros(self.ScanChainsCount)]
        FaultCandidatesPerCycleCount = [0]
        for fc in FaultCandidatesPerCycle:
            Word = bau.zeros(self.ScanChainsCount)
            for i in fc:
                Word[i] = 1
            FaultCandidatesPerCycleCount.append(len(fc))
            FaultCandidatesPerCycleMasks.append(Word)        
        CyclesCount = ceil(len(FaultFreeInputData) / self.ScanChainsCount)
        FaultFreeInputWords = List.splitIntoSublists(FaultFreeInputData, self.ScanChainsCount)
        SearchingTree = SimpleTree()
        for Cycle in range(1, CyclesCount+1):
            print(f"Cycle {Cycle} ======================================")
            if (Cycle == 1):
                for i in range(len(FaultCandidatesPerCycleMasks)):
                    SimRes = self.simulate(FaultFreeInputWords[0] ^ FaultCandidatesPerCycleMasks[i], 1, False)
                    if self._areSimResOK(OutputData, SimRes):
                        print(f"{ FaultCandidatesPerCycleMasks[i]} PASS    {FaultCandidatesPerCycleCount[i]}")
                        SearchingTree.add(FaultCandidatesPerCycleCount[i], [i])
                    else:
                        print(f"{ FaultCandidatesPerCycleMasks[i]} Failed")
            SearchingTree.print()