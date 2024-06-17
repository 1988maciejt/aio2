from libs.aio import *
from bitarray import *
from libs.utils_bitarray import *
from libs.utils_list import *
from libs.generators import *
from libs.simpletree import *
from tqdm import tqdm
from p_tqdm import p_uimap
from functools import partial


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
    
    def findFaultPatterns(self, FaultFreeInputData : bitarray, OutputData : list, MaxFaultsCount : int = 12, MaxFaultsPerCycle : int = 2, MaxFaultsDistancePerCycle : int = 3, MaxFaultDistanceInCyclesDomain : int = 5) -> list:
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
                if len(Splitted) <= 1:
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