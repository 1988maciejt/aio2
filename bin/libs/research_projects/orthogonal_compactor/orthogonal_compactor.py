from libs.aio import *
from bitarray import *
from libs.utils_bitarray import *
from libs.utils_list import *
from libs.generators import *

class CompactorSimulator:
    
    __slots__ = ("ScanChainsCount", "GlobalSumPresent", "_ShiftRegistersPresent")
    
    def __init__(self, ScanChainsCount : int, GlobalSumPresent : bool = True) -> None:
        self.ScanChainsCount = int(ScanChainsCount)
        self.GlobalSumPresent = bool(GlobalSumPresent)
        self._ShiftRegistersPresent = set()
        
    def addShiftRegister(self, EveryN : int = 1, StartingFrom = 0):
        self._ShiftRegistersPresent.add( (EveryN, StartingFrom) )
        
    def removeShiftRegister(self, EveryN : int, StartingFrom = 0):
        self._ShiftRegistersPresent.remove( (EveryN, StartingFrom) )
        
    def getShiftRegistersPresent(self) -> tuple:
        return tuple(self._ShiftRegistersPresent)
        
    def simulate(self, InputData : bitarray) -> tuple:
        if self.GlobalSumPresent:
            GlobalSum = bitarray()
        ShiftRegisters = []
        ShiftRegistersResult = []
        for Item in self._ShiftRegistersPresent:
            N = Item[0]
            S = Item[1]
            ShiftRegisters.append(bau.zeros(self.ScanChainsCount - N + 1 - S))
            ShiftRegistersResult.append(bitarray())
        for Word in Generators().subLists(InputData, self.ScanChainsCount):
            if len(Word) < self.ScanChainsCount:
                Word += bau.zeros(self.ScanChainsCount - len(Word))
            if self.GlobalSumPresent:
                GlobalSum.append((Word.count(1) % 2))
            i = 0
            for Item in self._ShiftRegistersPresent:
                N = Item[0]
                S = Item[1]
                ShiftRegisters[i] >>= 1
                for j in range(len(ShiftRegisters[i])):
                    LocalSum = 0
                    for k in range(N):
                        LocalSum += Word[k + S]
                    ShiftRegisters[i][j] ^= (LocalSum % 2)
                ShiftRegistersResult[i].append(ShiftRegisters[i][-1])
                #print(Item, ShiftRegisters[i])
                i += 1
            #print(Word)
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
            Result.append( ((0, 0), GlobalSum) )
        i = 0
        for Item in self._ShiftRegistersPresent:
            Result.append( (Item, ShiftRegistersResult[i]) )
            i += 1
        return tuple(Result)