from libs.aio import *
from bitarray import *
import bitarray.util as bau
from random import *
#from copy import deepcopy
from math import ceil
from functools import partial
from p_tqdm import *
from libs.generators import *
import re
from libs.pandas_table import *
import functools
from pyroaring import BitMap, BitMap64

_BATTERY_MODEL_TYPE = 1

class BatteryModelType (enumerate):
    NORMAL = 1
    BASED_ON_USED_ENCODING_CAPACITY = 2

def setBatteryModelType(Type : BatteryModelType):
    global _BATTERY_MODEL_TYPE
    if Type == BatteryModelType.NORMAL:
        _BATTERY_MODEL_TYPE = BatteryModelType.NORMAL
        Aio.print("Battery model type set to NORMAL (1)")
    elif Type == BatteryModelType.BASED_ON_USED_ENCODING_CAPACITY:
        _BATTERY_MODEL_TYPE = BatteryModelType.BASED_ON_USED_ENCODING_CAPACITY
        Aio.print("Battery model type set to BASED_ON_USED_ENCODING_CAPACITY (2)")
    else:
        Aio.printError(f"Illegal battery model type '{Type}'. Current type is '{_BATTERY_MODEL_TYPE}'")

class TestDataDecompressor:
    pass
class TestCube:
    pass
class TestCubeSet:
    pass
class EdtStructure:
    pass
class ScanCellsStructure:
    pass
class PatternCountComprensator:
    pass

class TestDataDecompressor:
    
    __slots__ = ('InputCount', 'OutputCount', 'LfsrLength', 'ScanLength', "MinimumBatteryLevel", "_MaximumSpecifiedBitPerCycleToBeCompressable")
    
    def __init__(self, InputCount : int, OutputCount : int, LfsrLength : int, ScanLength :  int, MinimumBatteryLevel : float = None):
        self.MinimumBatteryLevel = MinimumBatteryLevel
        self.InputCount = InputCount
        self.OutputCount = OutputCount
        self.LfsrLength = LfsrLength
        self._MaximumSpecifiedBitPerCycleToBeCompressable = None
        if type(ScanLength) is int:
            self.ScanLength = ScanLength
        elif type(ScanLength) is TestCube:
            self.ScanLength = int(ceil(len(ScanLength) / OutputCount))
            
    def copy(self) -> TestDataDecompressor:
        Result = TestDataDecompressor(self.InputCount, self.OutputCount, self.LfsrLength, self.ScanLength)
        Result.MinimumBatteryLevel = self.MinimumBatteryLevel
        return Result
    
    def getEncodingCapacity(self) -> int:
        return int(self.InputCount * ((self.LfsrLength // self.InputCount) + self.ScanLength))

    def __repr__(self) -> str:
        return f"TestDataDecompressor({self.InputCount}, {self.OutputCount}, {self.LfsrLength}, {self.ScanLength})"
        
    def __str__(self) -> str:
        return f"InputCount={self.InputCount}, OutputCount={self.OutputCount}, LfsrLength={self.LfsrLength}, ScanLength={self.ScanLength}, MinimumBatteryLevel={self.MinimumBatteryLevel}"
    
    def getPatternLength(self) -> int:
        return self.OutputCount * self.ScanLength
    
    def getScanChainCount(self) -> int:
        return self.OutputCount
    
    def getScanLength(self) -> int:
        return self.ScanLength
    
    def getInputCount(self) -> int:
        return self.InputCount
    
    def getLfsrLength(self) -> int:
        return self.LfsrLength
    
    def getInitialPhaseLength(self) -> int:
        return int(ceil(self.LfsrLength / self.InputCount))
    
    def getTestDataVolume(self, PatternCount : int = 1) -> int:
        return self.getTestTime() * self.getInputCount() * PatternCount
    
    def getTestTime(self, PatternCount : int = 1) -> int:
        return (self.getInitialPhaseLength() + self.getScanLength()) * PatternCount
    
    def getCompressionRatio(self) -> float:
        return self.getPatternLength() / self.getTestDataVolume()
    
    def getSpecifiedBitPerCycleDict(self, Cube : TestCube) -> dict:
        return {i: self.getSpecifiedBitPerCycleList(Cube)[i] for i in range(self.ScanLength)}           
    
    def getSpecifiedBitPerCycleList(self, Cube : TestCube) -> list:
        RList = [0] * self.ScanLength
        #for k in Cube._dict.keys():
        #    RList[k % self.ScanLength] += 1
        for k in Cube._ones:
            RList[k % self.ScanLength] += 1
        for k in Cube._zeros:
            RList[k % self.ScanLength] += 1
        return RList    
    
    def getMaximumSpecifiedBitPerCycleToBeCompressable(self) -> int:
        return self.LfsrLength + self.InputCount
    
    def getMaximumSpecifiedBitToBeCompressable(self) -> int:
        return int(self.LfsrLength + ((self.ScanLength - 1) * self.InputCount))
    
    def getMaximumCubeBitsPerDecompressor(self) -> int:
        return int(self.OutputCount * self.ScanLength)
    
    def isCompressable(self, Cube : TestCube, MinBatteryCharge : float = None) -> bool:
        if MinBatteryCharge is None:
            MinBatteryCharge = self.MinimumBatteryLevel
        global _BATTERY_MODEL_TYPE
        if _BATTERY_MODEL_TYPE == BatteryModelType.BASED_ON_USED_ENCODING_CAPACITY:
            #print(f"MinBatteryCharge = {MinBatteryCharge}")
            #print(f"UsedEncodingCapacity = {Cube.getSpecifiedBitCount()} / {self.getEncodingCapacity()}")
            if Cube.getSpecifiedBitCount() / self.getEncodingCapacity() > MinBatteryCharge:
                return False
        else:
            SpecifiedBitsPerCycle = self.getSpecifiedBitPerCycleList(Cube)
            # Battery model
            BatteryMax = self.LfsrLength
            BatteryMin = int(ceil(MinBatteryCharge * BatteryMax))
            BatteryChrg = BatteryMax
            for Vars in SpecifiedBitsPerCycle:
                BatteryChrg -= Vars
                if BatteryChrg < BatteryMin:
                    return False
                BatteryChrg += self.InputCount
                if BatteryChrg > BatteryMax:
                    BatteryChrg = BatteryMax
        return True


class EdtStructure:
    
    __slots__ = ('_decompressors', '_scan_len', '_len_sets', "MinimumBatteryLevel")
    
    def __init__(self, Decompressors : list = None, MinBatteryLevel : float = 0.1):
        self.MinimumBatteryLevel = MinBatteryLevel
        self._decompressors = []
        self._scan_len = 0
        self._len_sets = []
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver
        if Decompressors is not None:
            if type(Decompressors) is list:
                for Decompressor in Decompressors:
                    self.addDecompressor(Decompressor)
            elif type(Decompressors) in [TestDataDecompressor, DecompressorSolver]:
                self.addDecompressor(Decompressors)
            else:
                Aio.printError(f"Illegal type of decompressor '{type(Decompressors)}'")
            
    def copy(self) -> EdtStructure:
        Result = EdtStructure()
        Result._decompressors = [Decompressor.copy() for Decompressor in self._decompressors]
        Result._scan_len = self._scan_len
        Result._len_sets = self._len_sets.copy()
        Result.MinimumBatteryLevel = self.MinimumBatteryLevel
        return Result
    
    def setLfsrs(self, LfsrLength : int):
        if type(LfsrLength) is int:
            LfsrLength = [LfsrLength] * len(self._decompressors)
        for i, Decompressor in enumerate(self._decompressors):
            Decompressor.LfsrLength = LfsrLength[i]
    
    def setInputCount(self, InputCount : int):
        if type(InputCount) is int:
            InputCount = [InputCount] * len(self._decompressors)
        for i, Decompressor in enumerate(self._decompressors):
            Decompressor.InputCount = InputCount[i]
    
    def getEncodingCapacity(self) -> int:
        return sum([Decompressor.getEncodingCapacity() for Decompressor in self._decompressors])
    
    def getUsedEncodingCapacity(self, Cube : TestCube) -> float:
        return Cube.getSpecifiedBitCount() / self.getEncodingCapacity()
    
    def getUnusedEncodingCapacity(self, Cube : TestCube) -> float:
        Result = 1.0 - self.getUsedEncodingCapacity(Cube)
        if Result < 0:
            Result = 0.0
        return Result
    
    def __len__(self) -> int:
        return len(self._decompressors)
    
    def __repr__(self) -> str:
        return f"EdtStructure({self._decompressors})"
    
    def getCompressionRatio(self) -> float:
        Sum = 0
        for Decompressor in self._decompressors:
            Sum += Decompressor.getCompressionRatio()
        return Sum / len(self._decompressors)
    
    @staticmethod
    def fromFile(FileName : str, MinBatteryLevel : float = 0.1) -> EdtStructure:
        InCount, OutCount, LfsrLen, ScanLen = 0, 0, 0, 0
        Cntr = 0 
        for Line in Generators().readFileLineByLine(FileName):
            if Cntr >= 4:
                break
            if ScanLen == 0:
                R = re.search(r"scan_length\s+=\s+([0-9]+)", Line)
                if R:
                    ScanLen = int(R.group(1))
                    Cntr += 1
                    continue
            if LfsrLen == 0:
                R = re.search(r"decompressor_size\s+=\s+([0-9]+)", Line)
                if R:
                    LfsrLen = int(R.group(1))
                    Cntr += 1
                    continue
            if InCount == 0:
                R = re.search(r"n_input_channels\s+=\s+([0-9]+)", Line)
                if R:
                    InCount = int(R.group(1))
                    Cntr += 1
                    continue
            if OutCount == 0:
                R = re.search(r"n_scan_chains\s+=\s+([0-9]+)", Line)
                if R:
                    OutCount = int(R.group(1))
                    Cntr += 1
                    continue
        return EdtStructure(TestDataDecompressor(InCount, OutCount, LfsrLen, ScanLen), MinBatteryLevel)
    
    def __str__(self):
        Result = f"""Scan chain count  : {self.getScanChainCount()}
Scan chain length : {self.getScanLength()}
Compression ratio : {self.getCompressionRatio()}
Min battery level : {self.MinimumBatteryLevel}
Decompressors: [
"""
        Second = 0
        for Decompressor in self._decompressors:
            if Second:
                Result += ", "
            else:
                Second = 1
            Result += "  " + str(Decompressor)
        Result += "\n]"
        return Result
                
    def getScanLength(self) -> int:
        return self._scan_len
    
    def getDecompressorCount(self) -> int:
        return len(self._decompressors)
    
    def getInputCount(self) -> int:
        return sum([Decompressor.getInputCount() for Decompressor in self._decompressors])
    
    def getScanChainCount(self) -> int:
        return sum([Decompressor.getScanChainCount() for Decompressor in self._decompressors])
    
    def getFFCount(self) -> int:
        return sum([Decompressor.getLfsrLength() for Decompressor in self._decompressors])
    
    def getMaximumSpecifiedBitPerCycleToBeCompressable(self) -> int:
        return sum([Decompressor.getMaximumSpecifiedBitPerCycleToBeCompressable() for Decompressor in self._decompressors])
    
    def getMaximumSpecifiedBitToBeCompressable(self) -> int:
        return sum([Decompressor.getMaximumSpecifiedBitToBeCompressable() for Decompressor in self._decompressors])
    
    def getCubeBitsPerDecompressor(self) -> list:
        return [Decompressor.getMaximumCubeBitsPerDecompressor() for Decompressor in self._decompressors]
        
    def addDecompressor(self, Decompressor : TestDataDecompressor) -> bool:
        if self._scan_len == 0:
            self._scan_len = Decompressor.getScanLength()
        elif Decompressor.getScanLength() != self._scan_len:
            Aio.printError(f"Decompressor ScanLength must be {self._scan_len}.")
            return False
        self._decompressors.append(Decompressor)
        self._makeLenSets()
        return True
    
    def _makeLenSets(self):
        self._len_sets = []
        start = 0 
        for CLen in self.getCubeBitsPerDecompressor():
            stop = start + CLen
            self._len_sets.append(set(range(start, stop)))
            start = stop
    
    def isCompressable(self, Cube : TestCube, MinBatteryCharge : float = None) -> bool:
        if MinBatteryCharge is None:
            MinBatteryCharge = self.MinimumBatteryLevel
        if Cube.getSpecifiedCount() > self.getMaximumSpecifiedBitToBeCompressable():
            return False
        if len(self._decompressors) == 1:
            SubCubes = [Cube]
        else:
            SubCubes = Cube.splitIntoSubCubesBasingOnSets(self._len_sets)
        for i in range(len(self._decompressors)):
            if not self._decompressors[i].isCompressable(SubCubes[i], MinBatteryCharge=MinBatteryCharge):
                return False
        return True
    
    def getLongestLfsrSize(self) -> int:
        try:
            return max([Decompressor.getLfsrLength() for Decompressor in self._decompressors])   
        except:
            return 0
        
    def getTestTime(self, PatternCount : int = 1) -> int:
        Init = 0
        for Decompressor in self._decompressors:
            ThisInit = int(ceil(Decompressor.getLfsrLength() / Decompressor.getInputCount()))
            if Init <= ThisInit:
                Init = ThisInit
        return (Init + self.getScanLength()) * PatternCount
    
    def getTestDataVolume(self, PatternCount : int = 1) -> int:
        return self.getTestTime(PatternCount) * self.getInputCount()
        

class TestCube:
    
    __slots__ = ('_len', '_ones', '_zeros', '_primones', '_primzeros', 'Id', 'PatternId', 'BufferId', "WeightAdder", "SubCubes", "BufferSize", "SubCubesIds")
        
    @staticmethod
    def randomCube(Length : int, Pspecified : float = 0.1, P1 = 0.5, ExactFillRate : bool = False) -> TestCube:
        from random import random, randint
        Result = TestCube(Length)
        if ExactFillRate:
            Count = int(Length * Pspecified)
        else:
            Count = randint(1, ceil(Pspecified*Length*2))
            if Count > Length:
                Count = Length
        for i in range(Count):
            Result.setBit(randint(0, Length-1), 1 if random() < P1 else 0)
        return Result
    
    def __hash__(self) -> int:
        Result = 0
        Mask = 1
        for k in sorted(self._ones | self._zeros):
            if k in self._ones:
                Result |= Mask
            Mask <<= 1
        for k in sorted(self._primones | self._primzeros):
            if k in self._primones:
                Result |= Mask
            Mask <<= 1
        #for k in sorted(self._dict.keys()):
        #    if self._dict[k]:
        #        Result |= Mask
        #    Mask <<= 1
        #for k in sorted(self._primary_dict.keys()):
        #    if self._primary_dict[k]:
        #        Result |= Mask
        #    Mask <<= 1
        #return Result * len(self._dict) + len(self._primary_dict) * len(self)
        return Result * (len(self._ones) + len(self._zeros)) + len(self._primones) + len(self._primzeros) * len(self)
    
    def __init__(self, SpecifiedBits : str = '', TestCubeLenIfDictImplementation : int = 0, Id : int = -1, PatternId : int = -1, BufferId : int = -1, BufferSize : int = -1):
        #self._dict = {}
        #self._primary_dict = {}
        self._ones = BitMap() #set()
        self._zeros = BitMap()
        self._primones = BitMap()
        self._primzeros = BitMap()
        self.Id = int(Id)
        self.PatternId = int(PatternId)
        self.BufferId = int(BufferId)
        self.WeightAdder = 0
        self.SubCubes = 0
        self.SubCubesIds = BitMap64()
        self.BufferSize = BufferSize
        self._len = TestCubeLenIfDictImplementation
        if type(SpecifiedBits) is str and len(SpecifiedBits) > 0:
            self.setBits(SpecifiedBits)
        elif type(SpecifiedBits) is dict:
            self.setBits(SpecifiedBits, TestCubeLenIfDictImplementation)
        elif type(SpecifiedBits) is int:
            self._len = SpecifiedBits
        elif type(SpecifiedBits) is TestCube:
            #self._dict = SpecifiedBits._dict.copy()
            #self._primary_dict = SpecifiedBits._primary_dict.copy()
            self._ones = SpecifiedBits._ones.copy()
            self._zeros = SpecifiedBits._zeros.copy()
            self._primones = SpecifiedBits._primones.copy()
            self._primzeros = SpecifiedBits._primzeros.copy()
            self._len = SpecifiedBits._len
            self.Id = SpecifiedBits.Id
            self.BufferId = SpecifiedBits.BufferId
            self.PatternId = SpecifiedBits.PatternId
            self.WeightAdder = SpecifiedBits.WeightAdder
            self.SubCubes = SpecifiedBits.SubCubes
            self.BufferSize = SpecifiedBits.BufferSize
            try:
                self.SubCubesIds = SpecifiedBits.SubCubesIds.copy()
            except:
                pass
            
    def __len__(self):
        return self._len
    
    def __eq__(self, AnotherCube : TestCube):
        if len(self) != len(AnotherCube):
            return False
        #return self._dict == AnotherCube._dict and self._primary_dict == AnotherCube._primary_dict
        return self._ones == AnotherCube._ones and self._zeros == AnotherCube._zeros and self._primones == AnotherCube._primones and self._primzeros == AnotherCube._primzeros
    
    def __ne__(self, value):
        return not self.__eq__(value)
    
    def __str__(self):
        #return f"Id: {self.Id},\nSCAN: {self._dict}, \nPRIMARY: {self._primary_dict}"
        return f"Id: {self.Id},\nSCAN1: {self._ones},\nSCAN0: {self._zeros}, \nPRIMARY1: {self._primones}, \nPRIMARY0: {self._primzeros}"
    
    def __repr__(self):
        return f"TestCube(\"{str(self)}\")"
    
    def _getDictsLen(self) -> tuple:
        #return len(self._dict), len(self._primary_dict)
        return len(self._ones) + len(self._zeros), len(self._primones) + len(self._primzeros)
    
    def __getitem__(self, index):
        if type(index) is slice:
            start, stop, step = index.start, index.stop, index.step
            Result = TestCube("", self._len)
            #Result._dict = {i: v for i, v in self._dict.items() if i in range(start, stop, step)}
            for i in range(start, stop, step):
                if i in self._ones:
                    Result._ones.add(i)
                elif i in self._zeros:
                    Result._zeros.add(i)
            return Result
        return self.getBit(index)
    
    def __setitem__(self, index, value):
        self.setBit(index, value)
        
    def removeRandomBits(self, RemovingRatio : float):
        from libs.utils_list import List
        #HowManyToRemove = round(len(self._dict) * RemovingRatio)
        HowManyToRemove = round((len(self._ones) + len(self._zeros)) * RemovingRatio)
        #ToBeRemoved = List.randomSelect(list(self._dict.keys()), HowManyToRemove)
        ToBeRemoved = List.randomSelect(list(self._ones) | list(self._zeros), HowManyToRemove)
        for Bit in ToBeRemoved:
            #del self._dict[Bit]    
            self._ones.discard(Bit)  
            self._zeros.discard(Bit)
        
    def removeSpecifiedBits(self, AnotherCube : TestCube):
        #for k in AnotherCube._dict.keys():
        #    if k in self._dict:
        #        del self._dict[k]
        #for k in AnotherCube._primary_dict.keys():
        #    if k in self._primary_dict:
        #        del self._primary_dict[k]
        for k in AnotherCube._ones:
            self._ones.discard(k)
        for k in AnotherCube._zeros:
            self._zeros.discard(k)
        for k in AnotherCube._primones:
            self._primones.discard(k)
        for k in AnotherCube._primzeros:
            self._primzeros.discard(k)
        
    def getDifferentBitCount(self, AnotherCube : TestCube) -> int:
        d1, d2, pd1, pd2 = {}, [], [], []
        for i in self._ones:
            d1[i] = 1
        for i in self._zeros:
            d1[i] = 0
        for i in AnotherCube._ones:
            d2[i] = 1
        for i in AnotherCube._zeros:
            d2[i] = 0
        for i in self._primones:
            pd1[i] = 1
        for i in self._primzeros:
            pd1[i] = 0
        for i in AnotherCube._primones:
            pd2[i] = 1
        for i in AnotherCube._primzeros:
            pd2[i] = 0
        #d1 = self._dict
        #d2 = AnotherCube._dict
        #pd1 = self._primary_dict
        #pd2 = AnotherCube._primary_dict
        Result = 0
        CheckedBits = set()
        for k in d1.keys():
            if k in d2:
                if d1[k] != d2[k]:
                    Result += 1
            else:
                Result += 1
            CheckedBits.add(k)
        for k in d2.keys():
            if k in CheckedBits:
                continue
            if k in d1:
                if d1[k] != d2[k]:
                    Result += 1
            else:
                Result += 1
        CheckedBits = set()
        for k in pd1.keys():
            if k in pd2:
                if pd1[k] != pd2[k]:
                    Result += 1
            else:
                Result += 1
            CheckedBits.add(k)
        for k in pd2.keys():
            if k in CheckedBits:
                continue
            if k in pd1:
                if pd1[k] != pd2[k]:
                    Result += 1
            else:
                Result += 1
        return Result
        
    def getSpecifiedScanCellValues(self, ScanCount : int, ScanLength : int) -> list:
        Result = []
        for Index in self._zeros:
            Cycle = Index % ScanLength
            Scan = Index // ScanLength
            if Scan < ScanCount:
                Result.append([Scan, Cycle, 0])
            else:
                Aio.printError(f"Scan index {Scan} is out of range.")
        for Index in self._ones:
            Cycle = Index % ScanLength
            Scan = Index // ScanLength
            if Scan < ScanCount:
                Result.append([Scan, Cycle, 1])
            else:
                Aio.printError(f"Scan index {Scan} is out of range.")
        #for Index, Value in self._dict.items():
        #    Cycle = Index % ScanLength
        #    Scan = Index // ScanLength
        #    if Scan < ScanCount:
        #        Result.append([Scan, Cycle, Value])
        #    else:
        #        Aio.printError(f"Scan index {Scan} is out of range.")
        return Result
    
    def getScanCycleValues(self, ScanCount : int, ScanLength : int) -> dict:
        VList = self.getSpecifiedScanCellValues(ScanCount, ScanLength)
        Result = {}
        for i in range(ScanLength):
            Result[i] = {}
        for V in VList:
            Scan = V[0]
            Cycle = V[1]
            Value = V[2]
            Result[Cycle][Scan] = Value
        return Result
    
    def splitIntoSubCubes(self, SubCubesLen : list) -> list:
        Result = []
        Start = 0
        for SCLen in SubCubesLen:
            Stop = Start + SCLen
            Split = self[Start:Stop]
            #Split._primary_dict = self._primary_dict
            #Split._primones = self._primones.copy()
            #Split._primzeros = self._primzeros.copy()
            Result.append(Split)
            Start = Stop
        return Result
    
    def splitIntoSubCubesBasingOnSets(self, SubCubesLenSets : list) -> list:
        Result = []
        for SCLenSet in SubCubesLenSets:
            TC = TestCube("", len(SCLenSet))
            #TC._dict = {i: v for i, v in self._dict.items() if i in SCLenSet}
            TC._ones = {i for i in self._ones if i in SCLenSet}
            TC._zeros = {i for i in self._zeros if i in SCLenSet}
            #TC._primones = self._primones.copy()
            #TC._primzeros = self._primzeros.copy()
            Result.append(TC)
        return Result
    
    def setBits(self, SpecifiedBits : str, TestCubeLenIfDictImplementation : int = 0):
        # 0, 1 - values
        # X - don't care
        if type(SpecifiedBits) is dict:
            for item in SpecifiedBits.items():
                #self._dict[item[0]] = item[1]
                if item[1] == 1:
                    self._ones.add(item[0])
                    self._zeros.discard(item[0])
                elif item[1] == 0:
                    self._zeros.add(item[0])
                    self._ones.discard(item[0])
                else:
                    self._zeros.discard(item[0])
                    self._ones.discard(item[0])                    
            self._len = TestCubeLenIfDictImplementation
        else:
            SpecifiedBits = SpecifiedBits.upper()
            for i in range(len(SpecifiedBits)):
                if SpecifiedBits[i] == '0':
                    #self._dict[i] = 0
                    self._zeros.add(i)
                    self._ones.discard(i)
                elif SpecifiedBits[i] == '1':
                    #self._dict[i] = 1
                    self._ones.add(i)
                    self._zeros.discard(i)
                elif SpecifiedBits[i] in 'Xx':
                    self._zeros.discard(i)
                    self._ones.discard(i)
            self._len = len(SpecifiedBits)
            
    def setPrimaryBits(self, SpecifiedBits : str):
        # 0, 1 - values
        # X - don't care
        if type(SpecifiedBits) is dict:
            for item in SpecifiedBits.items():
                #self._primary_dict[item[0]] = item[1]
                if item[1] == 1:
                    self._primones.add(item[0])
                    self._zeros.discard(item[0])
                elif item[1] == 0:
                    self._primzeros.add(item[0])
                    self._primones.discard(item[0])
                else:
                    self._primzeros.discard(item[0])
                    self._primones.discard(item[0])     
        else:
            SpecifiedBits = SpecifiedBits.upper()
            for i in range(len(SpecifiedBits)):
                if SpecifiedBits[i] == '0':
                    #self._primary_dict[i] = 0
                    self._primzeros.add(i)
                    self._primones.discard(i)
                elif SpecifiedBits[i] == '1':
                    #self._primary_dict[i] = 0
                    self._primones.add(i)
                    self._primzeros.discard(i)
                elif SpecifiedBits[i] in 'Xx':
                    self._primzeros.discard(i)
                    self._primones.discard(i)
                
    def clearPrimaryBits(self):
        #self._primary_dict.clear()
        self._primzeros.clear()
        self._primones.clear()
        
    def clearScanBits(self):
        #self._dict.clear()
        self._ones.clear()
        self._zeros.clear()
        
    def clear(self):
        self.clearScanBits()
        self.clearPrimaryBits()
                
    def getFillRate(self) -> float:
        #return len(self._dict) / len(self)
        return (len(self._ones) + len(self._zeros)) / len(self)
    
    def getSpecifiedBitCount(self) -> int:
        #return len(self._dict)
        return len(self._ones) + len(self._zeros)
        
    def getSpecifiedBitPositions(self) -> list:
        #return list(self._dict.keys())
        return list(self._ones | self._zeros)
    
    def getSpecifiedPrimaryBitPositions(self) -> list:
        #return list(self._primary_dict.keys())
        return list(self._primones | self._primzeros)
        
    def copy(self) -> TestCube:
        Result = TestCube(self)
        return Result
    
    def getScanCellsDraw(self, ScanChainCount : int, ScanChainLength : int):
        from libs.asci_drawing import AsciiDrawing_Characters as Char
        D = self.getScanCycleValues(ScanChainCount, ScanChainLength)
        Lines = [Str.toRight(f"{i} "+Char.VERTICAL_LEFT, 6)  for i in range(ScanChainCount)]
        for Cycle in range(ScanChainLength-1, -1, -1):
            for Scan in range(ScanChainCount):
                Lines[Scan] += str(D[Cycle].get(Scan, '-'))
        for i in range(len(Lines)):
            Lines[i] += Char.VERTICAL
        Result = str.join("\n", reversed(Lines))
        return Result
    
    def printScanCells(self, ScanChainCount : int, ScanChainLength : int):
        Aio.print(self.getScanCellsDraw(ScanChainCount, ScanChainLength))
        
    def visualize(self, PngFileName : str, ScanChainCount : int, ScanChainLength : int) -> bool:
        from PIL import Image, ImageDraw
        Space = 1
        BitHeight = 4
        BitWidth = 4
        Width = ScanChainLength * (BitWidth + Space) + Space
        Height = ScanChainCount * (BitHeight + Space) + Space
        OneColor = 'red'
        ZeroColor = 'blue'
        XColor = 'black'
        image = Image.new('RGB', (Width, Height), color=(96, 96, 96))
        draw = ImageDraw.Draw(image)
        D = self.getScanCycleValues(ScanChainCount, ScanChainLength)
        for CycleI in range(ScanChainLength):
            for ScanI in range(ScanChainCount):
                CycleX = ScanChainLength - CycleI - 1
                ScanY = ScanChainCount - ScanI - 1
                x0 = CycleX * (BitWidth + Space) + Space
                y0 = ScanY * (BitHeight + Space) + Space
                x1 = x0 + BitWidth -1
                y1 = y0 + BitHeight -1
                Val = D[CycleI].get(ScanI, -1)
                if Val == 1:
                    color = OneColor
                elif Val == 0:
                    color = ZeroColor
                else:
                    color = XColor
                draw.rectangle((x0, y0, x1, y1), fill = color, outline = color)
        image.save(PngFileName)
        return True

    def mergeWithAnother(self, AnotherCube : TestCube) -> bool:
        if self.canBeMergedWithAnother(AnotherCube):
            self._forceMergeWithAnother(AnotherCube)
            return True
        return False
    
    def canBeMergedWithAnother(self, AnotherCube : TestCube) -> bool:
        if len(self) != len(AnotherCube):
            return False
        for AnotherPos in AnotherCube._ones:
            if AnotherPos in self._zeros:
                return False
        for AnotherPos in AnotherCube._zeros:
            if AnotherPos in self._ones:
                return False
        for AnotherPos in AnotherCube._primones:
            if AnotherPos in self._primzeros:
                return False
        for AnotherPos in AnotherCube._primzeros:
            if AnotherPos in self._primones:
                return False
        #for AnotherPos, AnotherVal in AnotherCube._dict.items():
        #    if AnotherPos in self._dict:
        #        if self._dict[AnotherPos] != AnotherVal:
        #            return False
        #for AnotherPos, AnotherVal in AnotherCube._primary_dict.items():
        #    if AnotherPos in self._primary_dict:
        #        if self._primary_dict[AnotherPos] != AnotherVal:
        #            return False
        return True
    
    def _forceMergeWithAnother(self, AnotherCube : TestCube):
        #self._dict.update(AnotherCube._dict)
        #self._primary_dict.update(AnotherCube._primary_dict)
        self._ones |= AnotherCube._ones
        self._zeros |= AnotherCube._zeros
        self._zeros -= self._ones
        self._primones |= AnotherCube._primones
        self._primzeros |= AnotherCube._primzeros
        self._primzeros -= self._primones
        
    def setPrimaryBit(self, BitIndex : int, BitValue : str) -> bool:
        if BitValue in [0, '0']:
            #self._primary_dict[BitIndex] = 0
            self._primzeros.add(BitIndex)
            self._primones.discard(BitIndex)
        elif BitValue in [1, '1']:
            #self._primary_dict[BitIndex] = 1
            self._primones.add(BitIndex)
            self._primzeros.discard(BitIndex)
        else:
                #del self._primary_dict[BitIndex]
            self._primzeros.discard(BitIndex)
            self._primones.discard(BitIndex)
        return True
    
    def setBit(self, BitIndex : int, BitValue : str) -> bool:
        if BitIndex >= len(self):
            return False
        if BitValue in [0, '0']:
            #self._dict[BitIndex] = 0
            self._zeros.add(BitIndex)
            self._ones.discard(BitIndex)
        elif BitValue in [1, '1']:
            #self._dict[BitIndex] = 1
            self._ones.add(BitIndex)
            self._zeros.discard(BitIndex)
        else:
                #del self._dict[BitIndex]
            self._zeros.discard(BitIndex)
            self._ones.discard(BitIndex)
        return True
    
    def getBit(self, BitIndex : int) -> int:
        #return self._dict.get(BitIndex, -1)
        if BitIndex in self._ones:
            return 1
        elif BitIndex in self._zeros:
            return 0
        else:
            return -1
    
    def getPrimaryBit(self, BitIndex : int) -> int:
        #return self._primary_dict.get(BitIndex, -1)
        if BitIndex in self._primones:
            return 1
        elif BitIndex in self._primzeros:
            return 0
        else:
            return -1
            
    def getSpecifiedCount(self) -> int:
        #return len(self._dict)
        return len(self._ones) + len(self._zeros)
    
    def getPrimarySpecifiedCount(self) -> int:
        #return len(self._primary_dict)
        return len(self._primones) + len(self._primzeros)
            
    
DebugList = []
class TestCubeSet:
    
    __slots__ = ('_cubes', 'BufferSize', 'CompressionFailLimit')
    
    def __init__(self, CubeOrList = None, CompressionFailLimit : int = 100, BufferSize : int = 512):
        self.CompressionFailLimit = CompressionFailLimit
        self.BufferSize = BufferSize
        self._cubes = []
        if CubeOrList is not None:
            if type(CubeOrList) in [list, tuple, set]:
                for Cube in CubeOrList:
                    self.addCube(Cube)
            elif type(CubeOrList) is TestCube:
                self.addCube(CubeOrList)
        
    def __len__(self):
        return len(self._cubes)
    
    def __str__(self):
        Result = ""
        Second = 0
        for Cube in self._cubes:
            if Second:
                Result += "\n-------------------------------------------------\n"
            else:   
                Second = 1
            Result += str(Cube)
        return Result
    
    def __repr__(self):
        return "TestCubeSet()"
    
    def __getitem__(self, index) -> TestCube:
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step
            Result = TestCubeSet()
            Result._cubes = self._cubes[start:stop:step]
            Result.BufferSize = self.BufferSize
            Result.CompressionFailLimit = self.CompressionFailLimit
            Result.recalculateIndices()
            return Result
        else:
            return self._cubes[index]
        
    def getMaxCubeId(self) -> int:
        MaxId = -1
        for Cube in self._cubes:
            if Cube.Id > MaxId:
                MaxId = Cube.Id
        return MaxId
        
    def getDroppedCubeCount(self) -> int:
        return self.getMaxCubeId() - len(self._cubes)
        
    def getDataVolume(self) -> int:
        """Returns sum of specified bit count."""
        Volume = 0
        for Cube in self._cubes:
            Volume += Cube.getSpecifiedBitCount()
        return Volume
    
    def getMaxCubeSpecifiedBits(self) -> int:
        Max = 0
        for Cube in self._cubes:
            SBC = Cube.getSpecifiedBitCount()
            if SBC > Max:
                Max = SBC
        return Max
    
    def getTheBiggestCubeSPecifiedBitCount(self) -> int:
        Max = 0
        for Cube in self._cubes:
            SBC = Cube.getSpecifiedBitCount()
            if SBC > Max:
                Max = SBC
        return Max
    
    def getSpecifiedBitCountHistogram(self, BarWidth : int = 10, Max : int = None) -> list:
        """Returns list of lists: [ [BarLowLimits], [BarValues] ].

        Args:
            BarWidth (int, optional): Defaults to 10.
            Max (int, optional): Defaults to None."""
        from libs.stats import Histogram
        Hist = Histogram()
        for Cube in self._cubes:
            Hist.addData(Cube.getSpecifiedBitCount())
        Hist._min = 0
        if Max is not None:
            Hist._max = Max
        return Hist.getPlotData()
    
    def getTestTime(self, edt : EdtStructure) -> int:
        return edt.getTestTime(len(self._cubes))
        
    def getIndexLowerOrEqualToId(self, Id : int) -> int:
        Index = 0
        if self.isIdImplemented():
            for i, Cube in enumerate(self._cubes):
                if Cube.Id > Id:
                    break
                Index = i
        else:
            BestDistance = len(self)
            for i, Cube in enumerate(self._cubes):
                if Cube.Id == Id:
                    Index = i
                    break
                if Cube.Id < Id:
                    if Id - Cube.Id < BestDistance:
                        BestDistance = Id - Cube.Id
                        Index = i
                if Cube.getSpecifiedCount() > Id:
                    break
        return Index
    
    def getFaultToCubeDict(self, FaultDict : dict) -> dict:
        Result = {}
        for Cube in self._cubes:
            if Cube.Id in FaultDict:
                Result[FaultDict[Cube.Id]] = Cube
        return Result
    
    @staticmethod
    def EABListToFaultToIDict(EABFaultList : list) -> dict:
        Result = {}
        for Item in EABFaultList:
            Id = Item[0]
            Fault = Item[1]
            Result[Fault] = Id
        return Result
    
    def getIndexEqualToId(self, Id : int) -> int:
        for i, Cube in enumerate(self._cubes):
            if Cube.Id == Id:
                return i
        return None
    
    def getFaultToCubeIdDict(self, FaultDict : dict) -> dict:
        Result = {}
        for Cube in self._cubes:
            if Cube.Id in FaultDict:
                Result[FaultDict[Cube.Id]] = Cube
        return Result
    
    @staticmethod
    def getSummaryFaultToCubeIdDict(TestCUbeSets : list, FaultDicts : list) -> dict:
        Result = {}
        for TC, FLT in zip(TestCUbeSets, FaultDicts):
            Result.update(TC.getFaultToCubeIdDict(FLT))
        return Result
    
    @staticmethod
    def getFaultsDictFromFaoultToCubeDict(FaultToCubeDict : dict) -> dict:
        Result = {}
        for Fault, Cube in FaultToCubeDict.items():
            Result[Cube.Id] = Fault
        return Result   
    
    @staticmethod
    def getEABListToEABDict(EABList : list) -> dict:
        Result = {}
        for item in EABList:
            Id = item[0]
            Fault = item[1]
            Lst = Result.get(Id, [])
            Lst.append(Fault)
            Result[Id] = Lst
        return Result
        
    def whereToInsertId(self, Id : int) -> tuple:
        """Returns:
        (WHereToInsert, HowManyToAddToId, HowManyToAddToTheRest)"""
        for i in range(len(self._cubes)):
            if self._cubes[i].Id > Id:
                return i, self._cubes[i].Id-Id, 1
        try:
            if self._cubes[-1].Id == Id:
                return len(self._cubes), 1, 0
        except:
            return 0, 0, 0
        return len(self._cubes), 0, 0
    
    def insertCubeById(self, Cube : TestCube, WeightFilterLength : int = 100):
        Pos, Add, AddR = self.whereToInsertId(Cube.Id)
        self._cubes.insert(Pos, Cube)
        Cube.WeightAdder = 0
        WeightedAdderAvg = self.getAvgWeightedAdderAtIdx(Pos, WeightFilterLength)
        if WeightedAdderAvg > 0:
        #    print(f"// WeightedAdderAvg at position {Pos} is {WeightedAdderAvg}")
            Cube.WeightAdder += WeightedAdderAvg
            AddR += WeightedAdderAvg
        #print(f"// inserting Cube {Cube.Id} at position {Pos} with add={Add} and addR={AddR}")
        Cube.Id += Add
        for i in range(Pos+1, len(self._cubes)):
        #    print(f"// Adding {AddR} to Id of cube {self._cubes[i].Id} = {self._cubes[i].Id+AddR} at position {i}")
            self._cubes[i].Id += AddR
        #print(f"// Ids: {[c.Id for c in self]}")
        return Pos, Add, AddR
            
    def getAvgWeightedAdderAtIdx(self, PositionIdx : int, AVGLen : int = 100) -> int:
        from libs.stats import MovingAverageFilter
        Filter = MovingAverageFilter(AVGLen)
        if PositionIdx < 0 or PositionIdx >= len(self._cubes):
            return 0
        for i in range(PositionIdx):
            Filter.add(self._cubes[i].WeightAdder)
        return int(Filter.getValue())
    
    def mixWithEABFaults(self, SelfFaultDict : dict, EABFaultList : list, IncrementalCubes : TestCubeSet, IncrementalFaultDict : dict, WeightFilterLength : int = 100):
        from copy import deepcopy
        EABFaultsDict = TestCubeSet.getEABListToEABDict(EABFaultList)
        if type(IncrementalCubes) is not list:
            IncrementalCubes = [IncrementalCubes]
        if type(IncrementalFaultDict) is not list:
            IncrementalFaultDict = [IncrementalFaultDict]
        IncrementalCubes = deepcopy(IncrementalCubes)
        IncrementalCubes.append(self)
        IncrementalFaultDict.append(SelfFaultDict)
        FaultToCubeDict = TestCubeSet.getSummaryFaultToCubeIdDict(IncrementalCubes, IncrementalFaultDict)
        #print(f"FaultToCubeDict: {FaultToCubeDict}")
        #print(f"EABFaultsDict: {EABFaultsDict}")
        EABIds = list(sorted(EABFaultsDict.keys()))
        #print(f"EABIds: {EABIds}")
        for i in range(len(EABIds)):
            EABId = EABIds[i]
            EABFaults = EABFaultsDict[EABId]
            for EABFault in EABFaults:
        #        print(f"Working on EABId {EABId} with fault {EABFault}")
                if EABFault in FaultToCubeDict:
        #            print(f"Fault {EABFault} is in FaultToCubeDict")
                    Cube = FaultToCubeDict[EABFault]
                    Cube.Id = EABId
                    Pos, Add, AddR = self.insertCubeById(Cube, WeightFilterLength)
                    FaultToCubeDict[EABFault] = Cube
                    EABId += Add
                    if AddR > 0:
                        for j in range(len(EABIds)-1, i, -1):
                            OldId = EABIds[j]
                            EABIds[j] += AddR
                            NewId = EABIds[j]
        #                    print(f"// Replacing {OldId} with {NewId} in EABFaultsDict")
                            EABFaultsDict[NewId] = EABFaultsDict[OldId]
                            del EABFaultsDict[OldId]
        return TestCubeSet.getFaultsDictFromFaoultToCubeDict(FaultToCubeDict)
        
    def addCubesInBetweenExisting(self, Cubes : list, AfterId : int):
        AfterIndex = self.getIndexLowerOrEqualToId(AfterId)
        Cube0 = self._cubes[AfterIndex]
        try:
            Cube1 = self._cubes[AfterIndex + 1]
            if Cube0.Id + len(Cubes) >= Cube1.Id:
                Adder = Cube0.Id + len(Cubes) - Cube1.Id + 1
            for i in range(AfterIndex + 1, len(self._cubes)):
                self._cubes[i].Id += len(Cubes)
        except: 
            pass
        BufferId = Cube0.BufferId
        BufferSize = Cube0.BufferSize
        PatternId = Cube0.PatternId
        IdI = Cube0.Id + 1
        PositionI = AfterIndex + 1
        for Cube in Cubes:
            NewCube = Cube.copy()
            NewCube.Id = IdI
            NewCube.BufferId = BufferId
            NewCube.BufferSize = BufferSize
            NewCube.PatternId = PatternId
            self._cubes.insert(PositionI, NewCube)
            PositionI += 1
            IdI += 1
        self.recalculateWeights()
        
    def _tryToExtrctTemplates_phase1(self, CommonGroupSize : int = 64, Overlapping : bool = False, CustomCubesForAnalysis : TestCubeSet = None) -> TestCubeSet:
        if CustomCubesForAnalysis is not None:
            CustomCubesForAnalysis.getCommonGroups(CommonGroupSize, Overlapping)
        return self.getBaseCubes().getCommonGroups(CommonGroupSize, Overlapping)

    def _tryToExtrctTemplates_phase2(self, CommonPairs,  DifferentTemplatesLowerLimit : float = 0.005, DifferentTemplatesUpperLimit : float = 0.05) -> TestCubeSet:
        Result = TestCubeSet()
        Group = TestCubeSet()
        Group.addCube(CommonPairs[0])
        for i in range(len(CommonPairs)-1):
            DiffBits = CommonPairs[i].getDifferentBitCount(CommonPairs[i+1]) / len(CommonPairs[i])
            if DiffBits >= DifferentTemplatesLowerLimit and DiffBits <= DifferentTemplatesUpperLimit:
                CC = Group.getCommonCube()
                CC.Id = Group[0].Id
                CC.BufferId = Group[0].BufferId
                CC.BufferSize = Group.BufferSize
                CC.PatternId = Group[0].PatternId
                Result.addCube(CC)
                Group = TestCubeSet()
            Group.addCube(CommonPairs[i])
        if len(Group) > 0:
            CC = Group.getCommonCube()
            CC.Id = Group[0].Id
            CC.BufferId = Group[0].BufferId
            CC.BufferSize = Group.BufferSize
            CC.PatternId = Group[0].PatternId
            Result.addCube(CC)
        return Result
        
    def tryToExtractTemplates(self, CommonGroupSize : int = 64, DifferentTemplatesLowerLimit : float = 0.005, DifferentTemplatesUpperLimit : float = 0.05, Overlapping : bool = False, CustomCubesForAnalysis : TestCubeSet = None) -> TestCubeSet:
        CommonPairs = self._tryToExtrctTemplates_phase1(CommonGroupSize, Overlapping, CustomCubesForAnalysis)
        return self._tryToExtrctTemplates_phase2(CommonPairs, DifferentTemplatesLowerLimit, DifferentTemplatesUpperLimit)
    
    def removeTemplates(self, TemplateSet : TestCubeSet):
        pids = set()
        for i, Cube in enumerate(TemplateSet._cubes):
            if Cube.PatternId not in pids:
                pids.add(Cube.PatternId)
                NewCube = Cube.copy()
                NewCube.removeSpecifiedBits(TemplateSet.getCubeByIdEqualOrLower(Cube.Id))
                self._cubes[i] = NewCube
        
    def getIdToIndexDict(self) -> dict:
        Result = {}
        for i, Cube in enumerate(self._cubes):
            Result[Cube.Id] = i
        return Result
        
    def splitIntoSubSetsBasingOnSpecifiedBitCount(self) -> dict:
        Result = {}
        for Cube in set(self._cubes):
            Count = Cube.getSpecifiedCount()
            Set = Result.get(Count, None)
            if Set is None:
                Set = TestCubeSet()
                Set.BufferSize = self.BufferSize
                Set.CompressionFailLimit = self.CompressionFailLimit
            Set.addCube(Cube)
            Result[Count] = Set
        return Result
    
    def calibrateBatteryLevelAssumingAllCompressible(self, edt : EdtStructure, PerFillRate : bool = False, Resolution : float = 0.001):
        if PerFillRate:
            MaxLevels = self.getMaximumBatteryLevelAssumingAllCompressible(edt, PerFillRate=True, Resolution=Resolution)
            Result = {}
            LastMax = 1
            for Key in sorted(MaxLevels.keys()):
                MaxVal = MaxLevels[Key]
                if MaxVal < LastMax:
                    Result[Key] = MaxVal
                    LastMax = MaxVal
            return Result
        else:
            from math import floor
            return floor(0.99 * self.getMaximumBatteryLevelAssumingAllCompressible(edt, Resolution=Resolution) / Resolution) * Resolution
    
    def getMaximumBatteryLevelAssumingAllCompressible(self, edt : EdtStructure, PerFillRate : bool = False, Resolution : float = 0.001):
        if PerFillRate:
            Dict = self.splitIntoSubSetsBasingOnSpecifiedBitCount()
            Result = {}
            from tqdm import tqdm
            for key in tqdm(list(sorted(Dict.keys()))):
                if key == 0:
                    continue
                Tc = Dict[key]
                Level = Tc.getMaximumBatteryLevelAssumingAllCompressible(edt, Resolution=Resolution)
                Result[key] = Level
            AioShell.removeLastLine()
            return Result
        else:
            Level = 0.0
            Tc = self.softCopy()
            Edt = edt.copy()
            Diff = 0.5
            Level = 0.5
            TooRestrictive = True
            while Diff >= Resolution:
                Diff /= 2
                Edt.MinimumBatteryLevel = Level
                Tc = self.softCopy()
                Tc.removeNotCompressable(Edt)
                if len(Tc) < len(self):
                    TooRestrictive = True
                    Level -= Diff
                else:
                    TooRestrictive = False
                    Level += Diff
            while TooRestrictive and Level > 0:
                Level -= Resolution
                Edt.MinimumBatteryLevel = Level
                Tc = self.softCopy()
                TooRestrictive = False
                if len(Tc) < len(self):
                    TooRestrictive = True
            from math import floor
            return floor(Level / Resolution) * Resolution
                
    def recalculateIndices(self):
        if self.isIdImplemented():
            Bias = self._cubes[0].Id - 1
            if Bias != 0:
                for i in range(len(self)):
                    CopiedCube = self._cubes[i].copy()
                    CopiedCube.Id -= Bias
                    self._cubes[i] = CopiedCube
        
    def sortById(self):
        self._cubes.sort(key=lambda x: x.Id)
        
    def removeRandomBits(self, RemovingRatio : float):
        for i in range(len(self._cubes)):
            Cube = self._cubes[i].copy()
            Cube.removeRandomBits(RemovingRatio)
            self._cubes[i] = Cube

    def getCommonCube(self) -> TestCube:
        if len(self) == 0:
            return TestCube()
        Result = self._cubes[0].copy()
        for i in range(1, len(self._cubes)):
            Result._ones &= self._cubes[i]._ones
            Result._zeros &= self._cubes[i]._zeros
            #ANotherDict = self._cubes[i]._dict
            #AnotherPrimaryDict = self._cubes[i]._primary_dict
            #for k, v in ANotherDict.items():
            #    if k in Result._dict:
            #        if Result._dict[k] != v:
            #            del Result._dict[k]
            #for k, v in AnotherPrimaryDict.items():
            #    if k in Result._primary_dict:
            #        if Result._primary_dict[k] != v:
            #            del Result._primary_dict[k]
        Result.Id = -1
        Result.BufferId = -1
        Result.PatternId = -1
        Result.WeightAdder = 0
        Result.SubCubes = len(self)
        return Result
        
    def toTable(self, IncludeUnused : bool = True) -> AioTable:
        Result = AioTable(["CubeId", "PatternId", "BufferId", "SubCubes", "SpecifiedBits", "FillRate"])
        for i in range(len(self._cubes)):
            Cube = self._cubes[i]
            BufferId = Cube.BufferId
            PatternId = Cube.PatternId
            CubeId = Cube.Id
            SpecifiedBits = Cube.getSpecifiedCount()
            SubCubes = Cube.SubCubes
            FillRate = Cube.getFillRate()
            Result.add([CubeId, PatternId, BufferId, SubCubes, SpecifiedBits, FillRate])
            if IncludeUnused and i < (len(self._cubes) - 1):
                WAdd = self._cubes[i+1].WeightAdder
                if WAdd > 0:
                    Result.add([f"< {WAdd} unused >", "", BufferId, WAdd, "", ""])
        return Result
    
    def getBaseCubes(self, ReturnAlsoRestCubes : bool = False) -> TestCubeSet:
        Result = TestCubeSet()
        pids = set()
        if ReturnAlsoRestCubes:
            RestCubes = TestCubeSet()
        for Cube in self._cubes:
            if Cube.PatternId not in pids:
                pids.add(Cube.PatternId)
                Result.addCube(Cube)
            elif ReturnAlsoRestCubes:
                RestCubes.addCube(Cube)
        if ReturnAlsoRestCubes:
            return Result, RestCubes
        return Result
    
    def getAverageSpecBits(self) -> float:
        if len(self._cubes) == 0:
            return 0.0
        Sum = 0
        for Cube in self._cubes:
            Sum += Cube.getSpecifiedBitCount()
        return Sum / len(self._cubes)
    
    def getStdDevSpecBits(self) -> float:
        if len(self._cubes) == 0:
            return 0.0
        Avg = self.getAverageSpecBits()
        Sum = 0.0
        for Cube in self._cubes:
            S = Cube.getSpecifiedBitCount()
            Sum += (S - Avg) * (S - Avg)
        from math import sqrt
        return sqrt(Sum / len(self._cubes))
    
    def getMinMaxAvgSpecBits(self) -> tuple:
        if len(self._cubes) == 0:
            return 0.0, 0.0, 0.0
        Min = 999999999999999999999.9
        Max = 0.0
        Sum = 0.0
        for Cube in self._cubes:
            S = Cube.getSpecifiedBitCount()
            Sum += S
            if S < Min:
                Min = S
            if S > Max:
                Max = S
        return Min, Max, Sum / len(self._cubes)
    
    def getBigCubes(self, Threshold : float = 0.8, ReturnAlsoRestCubes : bool = False) -> TestCubeSet:
        Result = TestCubeSet()
        if ReturnAlsoRestCubes:
            RestCubes = TestCubeSet()
        Min, Max, _ = self.getMinMaxAvgSpecBits()
        Thr = Min + ((Max - Min) * Threshold)
        for Cube in self._cubes:
            if Cube.getSpecifiedBitCount() >= Thr:
                Result.addCube(Cube)
            elif ReturnAlsoRestCubes:
                RestCubes.addCube(Cube)
        if ReturnAlsoRestCubes:
            return Result, RestCubes
        return Result
            
    
    def getCommonGroups(self, GroupSize : int = 2, Overlapping : bool = True) -> TestCubeSet:
        Result = TestCubeSet()
        if Overlapping:
            Iterator = range(len(self._cubes)-GroupSize+1)
        else:
            Iterator = range(0, len(self._cubes), GroupSize)
        for i in Iterator:
            Aux = TestCubeSet()
            for j in range(i, i+GroupSize):
                if j >= len(self._cubes):
                    break
                Aux.addCube(self._cubes[j])
            CC = Aux.getCommonCube()
            CC.Id = self._cubes[i].Id
            CC.BufferId = self._cubes[i].BufferId
            CC.BufferSize = self.BufferSize
            CC.PatternId = self._cubes[i].PatternId
            Result.addCube(CC)
        return Result
    
    def getBuffers(self) -> dict:
        Result = {}
        for Cube in self._cubes:
            BId = Cube.BufferId
            Buffer = Result.get(BId, TestCubeSet(CompressionFailLimit=self.CompressionFailLimit, BufferSize=self.BufferSize))
            Buffer.addCube(Cube)
            Result[BId] = Buffer
        return Result
    
    def getCubesByPatternId(self, PatternId : int) -> TestCubeSet:
        Result = TestCubeSet()
        for Cube in self._cubes:
            if Cube.PatternId == PatternId:
                Result.addCube(Cube)
        return Result
    
    def getPatternSpecBits(self) -> list:
        Result = []
        CubeList = self._cubes.copy()
        CubeList.sort(key=lambda x: x.PatternId)
        C0 = TestCube()
        PID = -1
        for C in CubeList:
            if C.PatternId != PID:
                if PID >= 0:
                    Result.append( C0.getSpecifiedBitCount() )
                PID = C.PatternId
                C0 = C.copy()
            else:
                C0.mergeWithAnother(C)
        if PID >= 0:
            Result.append( C0.getSpecifiedBitCount() )
        return Result
        
    def getPatterns(self, ReturnAlsoSubCubesDict : bool = False) -> TestCubeSet:
        Result = TestCubeSet()
        if ReturnAlsoSubCubesDict:
            SubCubesDict = {}
        ResDict = {}
        for Cube in self._cubes:
            PId = Cube.PatternId
            Pattern = ResDict.get(PId, None)
            if Pattern is None:
                Pattern = TestCube(TestCubeLenIfDictImplementation=len(Cube), PatternId=PId, BufferId=Cube.BufferId)
            if ReturnAlsoSubCubesDict:
                SubCubes = SubCubesDict.get(PId, [])
                SubCubes.append(Cube)
                SubCubesDict[PId] = SubCubes
            Pattern.mergeWithAnother(Cube)
            if Cube.SubCubes > 1:
                Pattern.SubCubes += Cube.SubCubes
            else:
                Pattern.SubCubes += 1
            Pattern.SubCubesIds.add(Cube.Id)
            ResDict[PId] = Pattern
        for key in sorted(ResDict.keys()):
            Result.addCube(ResDict[key])
        if ReturnAlsoSubCubesDict:
            return Result, SubCubesDict
        return Result
    
    def toTableOfPatterns(self) -> AioTable:
        Result = AioTable(["PatternId", "BufferId", "No. Cubes", "FillRate"])
        Patterns = self.getPatterns()
        for Pattern in Patterns._cubes:
            Row = [Pattern.PatternId, Pattern.BufferId, Pattern.SubCubes, Pattern.getFillRate()]
            Result.add(Row)
        return Result
            
    def visualize(self, PngFileName : str, MaxHeight : int = 1080) -> bool:
        if self.isEmpty():
            return False
        if not self.isIdImplemented():
            return False
        Len = self[-1].Id
        MaxCollSize = MaxHeight
        Colls = int(ceil(Len / MaxCollSize))
        if Colls > 1:
            Rows = MaxCollSize
        else:
            Rows = (Len % MaxCollSize)
        CollWidth = 14
        CollSpace = 1
        RowHeight = 1
        LeftMargin = 0
        Width = (CollWidth * Colls) + (CollSpace * (Colls-1))
        Height = Rows * RowHeight
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (Width, Height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)
        X1 = LeftMargin
        X2 = LeftMargin + CollWidth - 1 
        Y1 = 0
        Idx = 1
        Color1 = [i for i in range(80, 225, 48)]
        from libs.utils_list import List
        Colors = List.getPermutationsPfManyLists([Color1, Color1, Color1])
        random.shuffle(Colors)
        for C in self._cubes:
            for i in range(C.Id - Idx + 1):
                Y2 = Y1 + RowHeight - 1
                if Idx == C.Id:
                    color = tuple(Colors[C.PatternId % len(Colors)])
                    #color = 'green'
                else:
                    color = 'black'
                #print(X1, Y1, X2, Y2)
                draw.rectangle((X1, Y1, X2, Y2), fill = color, outline = color)
                Idx += 1
                Y1 += RowHeight
                if Y1 >= Height:
                    Y1 = 0
                    X1 += (CollWidth + CollSpace)
                    X2 += (CollWidth + CollSpace)
        image.save(PngFileName)
        return True
        
    @staticmethod
    def fromFile(FileName : str, ScanChainCount : int = -1, ScanChainLength : int = -1, IgnoreIds : bool = False, UnsortedCubes : bool = False, RecalculateIndices : bool = True, ReturnAlsoFaultsDict : bool = False, ReturnAlsoEABFaultsList : bool = False, ReturnAlsoSpecBitsDict : bool = False) -> TestCubeSet:
        if ScanChainCount <= 0 or ScanChainCount <= 0:
            edt = EdtStructure.fromFile(FileName)
            ScanChainCount = edt.getScanChainCount()
            ScanChainLength = edt.getScanLength()
        CubeLength = ScanChainLength * ScanChainCount
        Cube = None
        CubeTMPL = None
        ResultList = []
        Result = TestCubeSet()
        ResultTMPL = TestCubeSet()
        Result.BufferSize = []
        Id = -1
        PatternId = -1
        BufferId = -1
        OldMask = 0
        BuffSizePerPattern = 0
        PrimaryInputs = 99999
        PIAdder = 0
        ModeTMPL = False
        ThisCubeIsTMPL = False
        if ReturnAlsoFaultsDict:
            FaultsDict = {}
            #Fault = None
        if ReturnAlsoSpecBitsDict:
            SpecBitsDict = {}
        def checkResult():        
            if Cube is not None and Cube.getSpecifiedCount() > 0:
                if ThisCubeIsTMPL:
                    ResultTMPL.addCube(Cube)
                else:
                    Result.addCube(Cube)
            if (not IgnoreIds) and Id >= 0:
                if UnsortedCubes:
                    Ids = []
                    BuffIds = []
                    for i in range(len(Result)):
                        Ids.append(Result._cubes[i].Id)
                        BuffIds.append(Result._cubes[i].BufferId)
                    Ids.sort()
                    for i in range(len(Result)):
                        Result._cubes[i].Id = Ids[i]
                        Result._cubes[i].BufferId = BuffIds[i]
                else:
                    Result.sortById()
            if Id >= 0:
                Result.recalculateWeights()
            if RecalculateIndices:
                Result.recalculateIndices()
        EABList = []
        EABId = 1
        for Line in Generators().readFileLineByLine(FileName):
            if ReturnAlsoSpecBitsDict:
                R = re.search(r"TDVE[=:]\s+Cube\s+([0-9]+)[=:]\s+sc\s+[=:]\s+([0-9]+)", Line)
                if R:
                    SpecBitsDict[int(R.group(1))] = int(R.group(2))
                    continue
            # EDT aborts
            R = re.search(r"TDVE[=:]*\s*Cube\s*([0-9]+):\s*sc\s*[=:]\s*([0-9]+)", Line)
            if R:
                EABId = int(R.group(1)) + 1
                continue
            R = re.search(r'EDT\s*Abort\s\(([0-9]+)\):\s*\<([0-9]+)\s\(fin[:=]([0-9]+)\)\s*s-a-([01])\>\s*spec_sc[=:]([0-9]+)', Line)
            if R:
                FltId = int(R.group(2))
                FltFin = int(R.group(3))
                FltS_A = int(R.group(4))
                SC = int(R.group(5))
                EABList.append((Id, (FltId, FltFin, FltS_A), SC))
                continue
            # TMPL
            R = re.search(r"TMPL.*useAsPrimaryTestCubeWithoutRetargetingFault.*report", Line)
            if R:
                ModeTMPL = True
                ThisCubeIsTMPL = True
                continue
            R = re.search(r"TMPL.*original.*end", Line)
            if R:
                ModeTMPL = False
                continue
            # Regular
            R = re.search(r"num_test_cubes\s*[:=]\s*([0-9]+)\s*\(always\)", Line)
            if R:
                BuffSizePerPatternThis = int(R.group(1))
                if BuffSizePerPatternThis > BuffSizePerPattern:
                    BuffSizePerPattern = BuffSizePerPatternThis
                Result.BufferSize.append(BuffSizePerPattern)
                continue
            R = re.search(r"[:]\s*test\s*cube\s*pool\s*size\s*[=:]*\s*([0-9]+)", Line)
            if R:
            #    checkResult()
            #    Cube = None
            #    if len(Result) > 0:
            #        ResultList.append(Result)
            #    Result = TestCubeSet()
            #    for _ in range(64):
            #        Result.BufferSize.append(int(R.group(1)))
            #    Result.BufferSize = []
                continue
            R = re.search(r"umber\s*of\s*primary\s*inputs\s*=\s*([0-9]+)", Line)
            if R:
                PrimaryInputs = int(R.group(1))
                continue
            R = re.search(r"EDT\s*abort\s*limit\s*[=:]*\s*([0-9]+)", Line)
            if R:
                Result.CompressionFailLimit = int(R.group(1))
                continue
            R = re.search(r"pattern\s*=\s*([0-9]+)\s*mask\s*=\s*([0-9]+)", Line)
            if R:
                Mask = int(R.group(2))
                if Mask != OldMask:
                    #Result.BufferSize.append(BuffSizePerPattern)
                    PatternId += 1
                    if Mask == 1:
                        BufferId += 1
                OldMask = Mask
                continue
            R = re.search(r"TDVE[:]*\s*Cube\s*id\s*=\s*([0-9]+)", Line)
            if R:
                Id = int(R.group(1))
                continue
            R = re.search(r"TDVE[:]*\s*Cube\s*([0-9]+)", Line)
            if R:
                CubeIdx = int(R.group(1))
                if CubeIdx > 0:
                    PIAdder += PrimaryInputs
                    continue
                if Cube is not None:
                    if ThisCubeIsTMPL:
                        CubeTMPL = Cube.copy()
                    else:
                        Result.addCube(Cube)
                        if CubeTMPL is not None:
                            if Cube.getSpecifiedBitCount() != CubeTMPL.getSpecifiedBitCount():
                                Aio.print(Cube.Id, Cube.getSpecifiedBitCount(), CubeTMPL.getSpecifiedBitCount())
#                        else:
#                            Aio.print(Cube.Id, Cube.getSpecifiedBitCount())
                        CubeTMPL = None
                ThisCubeIsTMPL = ModeTMPL
                Cube = TestCube(CubeLength, Id=Id, PatternId=PatternId, BufferId=BufferId, BufferSize=BuffSizePerPattern)
                PIAdder = 0
                continue
            R = re.search(r"TDVE[:]*\s*([-0-9]+)\s+([0-9]+)\s([0-9]+)", Line)
            if R:
                Chain = int(R.group(1))
                BitIndex = int(R.group(2))
                BitVal = int(R.group(3))
                if Chain < 0: # primary
                    Cube.setPrimaryBit(BitIndex+PIAdder, BitVal)
                else:                
                    CubeBitIndex = Chain * ScanChainLength + BitIndex
                    Cube.setBit(CubeBitIndex, BitVal)
            if ReturnAlsoFaultsDict:
                R = re.search(r"Flt[:=]\s*\<\s*([0-9]+)\s*\(\s*fin\s*[:=]\s*([0-9]+)\)\s*s-a-([0-1])\>", Line)
                if R:
                    FltId = int(R.group(1))
                    FltFin = int(R.group(2))
                    FltS_A = int(R.group(3))
                    FaultsDict[Id] = (FltId, FltFin, FltS_A)
        checkResult()
        #print(EABIds)
        #print(EABList)
        Ret = []
        if len(ResultList) > 0:
            if len(Result) > 0:
                ResultList.append(Result)
            Ret.append(ResultList)
        else:
            Ret.append(Result)
        if ReturnAlsoFaultsDict:
            Ret.append(FaultsDict)
        if ReturnAlsoEABFaultsList:
            Ret.append(EABList)
        if ReturnAlsoSpecBitsDict:
            Ret.append(SpecBitsDict)
        if len(Ret) == 1:
            return Ret[0]
        return tuple(Ret)
    
    def getSpecBitsTable(self, FaultDict : dict = None) -> AioTable:
        if FaultDict is None:
            FaultDict = {}
        Table = AioTable(["CubeId", "SpecBits", "FaultId", "Fin", "S-A-?"])
        EMptyRow = ["<space>", "", "", "", ""]
        LastId = 0
        for Cube in self._cubes:
            Id = Cube.Id
            SpecBits = Cube.getSpecifiedCount()
            if Id > LastId+1:
                Table.add(EMptyRow)
            Row = [Id, SpecBits]
            if Id in FaultDict:
                FltId, FltFin, FltS_A = FaultDict[Id]
                Row += [FltId, FltFin, FltS_A]
            else:
                Row += ["", "", ""]
            Table.add(Row)
            LastId = Id
        return Table
            
    def recalculateWeights(self):
        for i in range(len(self._cubes)-1):
            WeightAdder = self._cubes[i+1].Id - self._cubes[i].Id - 1
            if WeightAdder != self._cubes[i].WeightAdder:
                CopiedCube = self._cubes[i].copy()
                CopiedCube.WeightAdder = WeightAdder
                self._cubes[i] = CopiedCube
            #self._cubes[i].WeightAdder = self._cubes[i+1].Id - self._cubes[i].Id - 1
        
    @staticmethod
    def _getCommonCUbes_single(TwoSamplesTuple):
        SelfSample = TwoSamplesTuple[0]
        OtherSample = TwoSamplesTuple[1]
        return SelfSample.getCommonCubes(OtherSample, Multiprocessing=False)
        
    def getCommonCubes(self, Another : TestCubeSet, Multiprocessing : bool = True) -> TestCubeSet:
        Result = TestCubeSet()
        if Multiprocessing:
            import gc
            import concurrent.futures
            from tqdm import tqdm
            from libs.generators import Generators
            CubesA = self.getSubCubeSets(10000)
            CubesB = Another.getSubCubeSets(10000)
            with concurrent.futures.ProcessPoolExecutor() as Executor:
                Tasks = [Executor.submit(TestCubeSet._getCommonCUbes_single, CubeSets) for CubeSets in Generators().allPermutationsForm2lists(CubesA, CubesB)]
                for Task in tqdm(concurrent.futures.as_completed(Tasks), total=len(Tasks), desc="Getting common cubes"):
                    SubRes = Task.result()
                    Result._cubes += SubRes._cubes
            AioShell.removeLastLine()
            gc.collect()
            print("FIltering...")
            Result.leaveOnlyUniqueCubes()
            AioShell.removeLastLine()
            gc.collect()
        else:
            CubesA, CubesB = self, Another
            DictA = CubesA._getSortedByDictLen()
            DictB = CubesB._getSortedByDictLen()
            for k, SetA in DictA.items():
                if k in DictB:
                    SetB = DictB[k]
                    for CubeA in SetA._cubes:
                        for CubeB in SetB._cubes:
                            if CubeA == CubeB:
                                ResCube = CubeA.copy()
                                ResCube.Id = -1
                                ResCube.PatternId = -1
                                ResCube.BufferId = -1
                                ResCube.WeightAdder = 0
                                ResCube.SubCubes = 0
                                Result.addCube(ResCube)
            #for Cube in self._cubes:
            #    if Cube in Another._cubes:
            #        ResCube = Cube.copy()
            #        ResCube.Id = -1
            #        ResCube.PatternId = -1
            #        ResCube.BufferId = -1
            #        ResCube.WeightAdder = 0
            #        ResCube.SubCubes = 0
            #        Result.addCube(ResCube)
        return Result
    
    intersection = getCommonCubes
    
    def _getSortedByDictLen(self) -> dict:
        Result = {}
        for Cube in self._cubes:
            DictLen = Cube._getDictsLen()
            TSet = Result.get(DictLen, TestCubeSet())
            TSet.addCube(Cube)
            Result[DictLen] = TSet
        return Result
    
    def leaveOnlyUniqueCubes(self, ReturnPairs : bool = False):
        Result = []
        Count = 0
        Pairs = []
        AuxDict = {}
        for Cube in self._cubes:
            CLen = Cube._getDictsLen()
            AuxRes = AuxDict.get(CLen, [])
            Idx = -1
            for i, c in enumerate(AuxRes):
                if Cube == c:
                    Idx = i
                    break
            if Idx < 0:
                AuxRes.append(Cube)
                AuxDict[CLen] = AuxRes
                Result.append(Cube)
            else:
                if ReturnPairs:
                    Pairs.append([Cube, AuxRes[Idx]])
                Count += 1
        self._cubes = Result
        del AuxDict
        if ReturnPairs:
            return Pairs
        return Count
    
    @staticmethod
    def randomCubeSet(CubeCount : int, Length : int, Pspecified : float = 0.1, P1 = 0.5, ExactFillRate : bool = False) -> TestCubeSet:
        Result = TestCubeSet()
        def single(args):
            return [TestCube.randomCube(Length, Pspecified, P1, ExactFillRate) for _ in range(200)]
        for C in p_uimap(single, range(CubeCount // 200), desc="Generating random cubes (x200)"):
            Result._cubes += C
        AioShell.removeLastLine()
        if len(Result._cubes) > CubeCount:
            Result._cubes = Result._cubes[:CubeCount]
        elif len(Result._cubes) < CubeCount:
            Result._cubes += [TestCube.randomCube(Length, Pspecified, P1) for _ in range(CubeCount - len(Result._cubes))]
        return Result
    
    def isIdImplemented(self) -> bool:
        if len(self._cubes) > 0:
            if self._cubes[0].Id < 0:
                return False
            if self._cubes[-1].Id < 0:
                return False
            return True
        return False
    
    def removeIds(self):
        for Cube in self._cubes:
            Cube.Id = -1
    
    def isEmpty(self) -> bool:
        return False if len(self._cubes) > 0 else True
    
    def shuffle(self) -> bool:
        from random import shuffle
        if self.isIdImplemented():
            if len(self._cubes) <= 2:
                return False
            Aux = []
            Cube = self._cubes[0]
            CubeLast = self._cubes[-1]
            for i in range(1, len(self._cubes)):
                Cube2 = self._cubes[i]
                Aux.append((Cube, Cube2.Id - Cube.Id))
                Cube = Cube2
            shuffle(Aux)
            Idx = 1
            self._cubes = []
            for CubeComb in Aux:
                Cube = CubeComb[0]
                Dist = CubeComb[1]
                Cube.Id = Idx
                self._cubes.append(Cube)
                Idx += Dist
            CubeLast.Id = Idx
            self._cubes.append(CubeLast)
        else:
            shuffle(self._cubes)
        return True
    
    def addCube(self, Cube : TestCube):
        self._cubes.append(Cube)
    
    def addRandomCubes(self, Count : int, CubeLen : int, Pspecified : float = 0.1, P1 = 0.5):
        for i in range(Count):
            self.addCube(TestCube.randomCube(CubeLen, Pspecified, P1))
    
    def copy(self) -> TestCubeSet:
        return self.softCopy()
    
    def deepCopy(self) -> TestCubeSet:
        Result = TestCubeSet()
        Result.BufferSize = self.BufferSize
        Result.CompressionFailLimit = self.CompressionFailLimit
        for Cube in self._cubes:
            Result._cubes.append(Cube.copy())
        return Result
    
    def softCopy(self) -> TestCubeSet:
        Result = TestCubeSet()
        Result.BufferSize = self.BufferSize
        Result.CompressionFailLimit = self.CompressionFailLimit
        Result._cubes = self._cubes.copy()
        return Result

    def getWeightedLen(self) -> int:
        Result = 0
        for Cube in self._cubes:
            Result += (1 + Cube.WeightAdder)
        return Result

    def removeCube(self, CubeIndex : int) -> bool:
        try:
            del self._cubes[CubeIndex]
            return True
        except:
            return False
    
    def getCube(self, index : int) -> TestCube:
        return self._cubes[index]
    
    def getSubCubeSets(self, SubSetSize : int) -> list:
        Result = []
        for i in range(0, len(self), SubSetSize):
            TestCubeSubset = TestCubeSet()
            TestCubeSubset._cubes = self._cubes[i:i+SubSetSize]
            Result.append(TestCubeSubset)
        return Result
    
    def getCubeByIdEqualOrLower(self, Id : int) -> TestCube:
        Result = None
        for Cube in self._cubes:
            if Cube.Id > Id:
                break
            Result = Cube
        return Result
    
    def _mergingRound(self, Edt : EdtStructure, PatternCount : int = 1, CompressabilityLimit : int = 3, Verbose : bool = False, OnlyPatternCount : bool = False, IdxAdder : int = 0, BuffAdder : int = 0, Templates : TestCubeSet = None, BaseCubesIds = set()) -> tuple:
        """Returns two TestCubeSet objects: (Patterns, Cubes)."""
        if self.CompressionFailLimit is not None:
            CompressabilityLimit = self.CompressionFailLimit
        Verbose = 0
        global DebugList
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver
        Cubes = self
        if OnlyPatternCount:
            Patterns = 0
        else:
            Patterns = TestCubeSet()
        Debug = 0
        UsingSolver = 0
        if type(Edt) is DecompressorSolver:
            Debug = 0
            UsingSolver = 1
            EdtBatt = Edt.getDecompressorForBatteryModelEstimations()
        Idx = IdxAdder
        while len(Cubes) > 0 and (Patterns < PatternCount if OnlyPatternCount else len(Patterns) < PatternCount):
            BaseIdx = 0
            if len(BaseCubesIds) > 0:
                for Idx, Cube in enumerate(Cubes):
                    if Cube.Id in BaseCubesIds:
                        BaseIdx = Idx
                        break
            Cube = Cubes._cubes[BaseIdx]
            if Templates is not None:
                Template = Templates.getCubeByIdEqualOrLower(Cube.Id)
                if Template is not None:
                    Cube = Cube.copy()
                    if not Cube.mergeWithAnother(Template):
                        if Verbose:
                            print(f"  Merging cube {Cube.Id} with template {Template.Id} unsuccessfull.")
                    else:
                        if Verbose:
                            print(f"  Merging {Cube.Id} with template {Template.Id} successfull.")
            if UsingSolver:
                CubeSolver = Edt.getEquationSystemForPattern(Cube)
            del Cubes._cubes[BaseIdx]
            SubCubes = 1
            SubCubeIds = set()
            SubCubeIds.add(Cube.Id)
            ToBeRemovedFromBuffer = []
            CompressionCounter = 0
            for ANotherCube in Cubes._cubes:
                if Verbose:
                    print(f"Next cube, {ANotherCube.getFillRate()}")
                MergingResult = Cube.canBeMergedWithAnother(ANotherCube)
                if Verbose:
                    print(f"  MergingResult: {MergingResult} ")
                if MergingResult: 
                    CubeAux = Cube.copy()
                    if UsingSolver:
                        CubeSolverAux = Edt.addEquationsDueToCubeMerging(CubeSolver, ANotherCube)
                    CubeAux._forceMergeWithAnother(ANotherCube)        
                    if Debug:
                        DebComp = EdtBatt.isCompressable(CubeAux)
                    if UsingSolver:
                        CompResult = Edt.isCompressableBasingOnEqSystem(CubeSolverAux)
                    else:
                        CompResult = Edt.isCompressable(CubeAux)
                    if CompResult:
                        if Verbose:
                            print(f"COMPRESSABLE")
                        if Debug:
                            if not DebComp:
                                DebugList.append([CubeAux.copy(), "SolverDidBatteryNot"])
                        Cube = CubeAux                    
                        if UsingSolver:
                            CubeSolver = CubeSolverAux
                        SubCubes += 1
                        SubCubeIds.add(ANotherCube.Id)
                        ToBeRemovedFromBuffer.append(ANotherCube)
                    else:
                        if Verbose:
                            print(f"NOT compressable")
                        if Debug:
                            if not DebComp:
                                DebugList.append([CubeAux.copy(), "BatteryDidSolverNot"])
                        CompressionCounter += 1
                        if CompressionCounter > CompressabilityLimit:
                            break
            if OnlyPatternCount:
                Patterns += 1
            else:
                Cube.SubCubes = SubCubes
                Cube.SubCubesIds = SubCubeIds
                Cube.PatternId = Idx
                Cube.BufferId = BuffAdder
                Cube.Id = Idx + 1
                Cube.WeightAdder = 0
                Idx += 1
                Patterns._cubes.append(Cube)
            for i in ToBeRemovedFromBuffer:
                Cubes._cubes.remove(i)
        return Patterns
    
    def _mergingRoundCombined(self, Edt, PatternCount : int = 64, CompressabilityLimit : int = 3, Verbose : bool = False, OnlyPatternCount : bool = False) -> tuple:
        """Returns two TestCubeSet objects: (Patterns, Cubes)."""
        if self.CompressionFailLimit is not None:
            CompressabilityLimit = self.CompressionFailLimit
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver                       
        if type(Edt) is not DecompressorSolver:
            Aio.printError("Edt must be DecompressorSolver object.")
            return None, None, None, None
        from math import exp
        MinFillRate = exp(1 - 0.008 * Edt.getCompressionRatio()) / 100
        EdtBattery = Edt.getDecompressorForBatteryModelEstimations()
        Cubes = self
        if OnlyPatternCount:
            Patterns = 0
        else:   
            Patterns = TestCubeSet()
        BackTracingCounter = 0
        SolverCalls = 0
        while len(Cubes) > 0 and (Patterns < PatternCount if OnlyPatternCount else len(Patterns) < PatternCount):
            #Cubes.sort()
            Cube = Cubes.getCube(0).copy()
            ToBeRemovedFromBuffer = [0]
            CompressionCounter = 0
            FirstGoodFillrate = 1
            for i in range(1, len(Cubes)):
                CubeAux = Cube.copy()
                MergingResult = CubeAux.mergeWithAnother(Cubes._cubes[i])
                if MergingResult: 
                    if CubeAux.getFillRate() >= MinFillRate:
                        if FirstGoodFillrate:
                            FirstGoodFillrate = 0
                            if EdtBattery.isCompressable(CubeAux):
                                Cube = CubeAux
                                ToBeRemovedFromBuffer.append(i)
                            else:
                                # do backtrace with solver
                                BackTracingCounter += 1
                                BacktraceList = ToBeRemovedFromBuffer.copy()
                                ToBeRemovedFromBuffer = [0]
                                Cube = Cubes.getCube(0).copy()
                                CubeAux = Cube.copy()
                                for j in range(1, len(BacktraceList)):
                                    CubeAux.mergeWithAnother(Cubes.getCube(BacktraceList[j]))
                                    SolverCalls += 1
                                    if Edt.isCompressable(CubeAux):
                                        ToBeRemovedFromBuffer.append(BacktraceList[j])
                                        Cube = CubeAux.copy()
                                    else:
                                        break
                        else:
                            if EdtBattery.isCompressable(CubeAux):
                                Cube = CubeAux
                                ToBeRemovedFromBuffer.append(i)
                            else:       
                                CompressionCounter += 1
                                if CompressionCounter > CompressabilityLimit:
                                    break
                    else:
                        Cube = CubeAux
                        ToBeRemovedFromBuffer.append(i)
            if OnlyPatternCount:
                Patterns += 1
            else:
                Patterns._cubes.append(Cube)
            for i in reversed(ToBeRemovedFromBuffer):
                del Cubes._cubes[i]
        return Patterns, BackTracingCounter, SolverCalls
    
    def merge(self, Edt : EdtStructure, PatternCountPerRound : int = 1, Verbose : bool = False, CombinedCompressionChecking : bool = False, OnlyPatternCount : bool = False, Templates : TestCubeSet = None, BaseCubesIds = set()) -> TestCubeSet:
        if self.BufferSize is not None:
            BufferLength = self.BufferSize
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver  
        global DebugList   
        CompressabilityLimit = self.CompressionFailLimit
        BufferLength = self.BufferSize
        if Verbose:
            if Templates is not None:
                print("// Merging with templates //")
        if CombinedCompressionChecking and type(Edt) is not DecompressorSolver:
            Aio.printError("Edt must be DecompressorSolver object if CombinedCompressionChecking is set.")
            return None
        elif type(Edt) is DecompressorSolver:
            DebugList = []
        elif type(Edt) is TestDataDecompressor:
            MBL = Edt.MinimumBatteryLevel
            Edt = EdtStructure(Edt)
            Edt.MinimumBatteryLevel = MBL
        Buffer = TestCubeSet()
        if type(BufferLength) is int:
            BufferLength = [BufferLength]
        if len(BufferLength) < 1:
            BufferLength = [512]
        if self.isIdImplemented():
            CubeIdImplemented = True
            SearchFromIdx = 0
            Len = BufferLength[0]
            for i in range(len(self._cubes)):
                if self._cubes[i].Id > Len:
                    SearchFromIdx = i
                    break
            Buffer._cubes = self._cubes[0:SearchFromIdx]
            CompLimit0 = CompressabilityLimit
            CompressabilityLimit = CompLimit0 * len(Buffer) // BufferLength[0]
        else:
            CubeIdImplemented = False
            Buffer._cubes = self._cubes[0:BufferLength[0]]
        index = BufferLength[0]
        if Verbose:
            BuffLenAtTheBeginningOfRound = Buffer.getWeightedLen()
        #else:
        #    sleep(0.00037)
        if CombinedCompressionChecking:
            Patterns, BackTracingCounterSum, SolverCallsSum = Buffer._mergingRoundCombined(Edt, PatternCountPerRound, CompressabilityLimit, Verbose, OnlyPatternCount)
        else:
            Patterns = Buffer._mergingRound(Edt, PatternCountPerRound, CompressabilityLimit, Verbose, OnlyPatternCount, 0, 0, Templates, BaseCubesIds)
        IdxAdder = 0
        BuffAdder = 0
        if not OnlyPatternCount:
            BuffAdder = 1
            try:
                IdxAdder = Patterns[-1].Id
            except:
                pass
        BufferLenIndex = 0
        if Verbose:
            if CubeIdImplemented:
                print(f"// Using CubeId //")
            if OnlyPatternCount:
                print(f"Furst round finished. BufferLen: {BuffLenAtTheBeginningOfRound} -> {Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={Patterns}")
            else:
                print(f"Furst round finished. BufferLen: {BuffLenAtTheBeginningOfRound} -> {Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={len(Patterns)}")
        #else:
        #    sleep(0.0005)
        while index < len(self):
            BufferLenIndex += 1 
            if BufferLenIndex >= len(BufferLength):
                BufferLenIndex = len(BufferLength) - 1
            if CubeIdImplemented:
                NewBufferLen = BufferLength[BufferLenIndex]
                try:
                    LastId = Buffer._cubes[-1].Id + NewBufferLen - Buffer.getWeightedLen()  #- len(Buffer._cubes)  
                except:
                    LastId = self._cubes[SearchFromIdx].Id + NewBufferLen
                From = SearchFromIdx
                for k in range(SearchFromIdx, len(self._cubes)):
                    if self._cubes[k].Id >= LastId:
                        SearchFromIdx = k
                        break
                if From == SearchFromIdx:
                    SearchFromIdx += 1
                index = SearchFromIdx
                Buffer._cubes += self._cubes[From:SearchFromIdx]
                CompressabilityLimit = CompLimit0 * len(Buffer) // NewBufferLen
            else:
                NewBufferLen = BufferLength[BufferLenIndex]
                HowManyToAdd = NewBufferLen - len(Buffer)
                Buffer._cubes += self._cubes[index:index+HowManyToAdd]
                index += HowManyToAdd
            if len(Buffer) <= 0:
                break
            if Verbose:
                BuffLenAtTheBeginningOfRound = Buffer.getWeightedLen()
            if CombinedCompressionChecking:
                SubPatterns, BackTracingCounterSum, SolverCallsSum = Buffer._mergingRoundCombined(Edt, PatternCountPerRound, CompressabilityLimit, Verbose, OnlyPatternCount)
            else:
                SubPatterns = Buffer._mergingRound(Edt, PatternCountPerRound, CompressabilityLimit, Verbose, OnlyPatternCount, IdxAdder, BuffAdder, Templates, BaseCubesIds)
            if OnlyPatternCount:
                Patterns += SubPatterns
            else:
                BuffAdder += 1
                try:
                    IdxAdder = SubPatterns[-1].Id
                except:
                    pass
                Patterns._cubes += SubPatterns._cubes
            if Verbose:
                if OnlyPatternCount:
                    print(f"Next round finished. BufferLen: {BuffLenAtTheBeginningOfRound} -> {Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={Patterns}")
                else:
                    print(f"Next round finished. BufferLen: {BuffLenAtTheBeginningOfRound} -> {Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={len(Patterns)}")
            else:
                sleep(0.0005)
        if len(Buffer) > 0:
            if CombinedCompressionChecking:
                SubPatterns, BackTracingCounter, SolverCalls = Buffer._mergingRoundCombined(Edt, len(Buffer), CompressabilityLimit, Verbose, OnlyPatternCount)
                BackTracingCounterSum += BackTracingCounter
                SolverCallsSum += SolverCalls
            else:
                SubPatterns = Buffer._mergingRound(Edt, len(Buffer), CompressabilityLimit, Verbose, OnlyPatternCount, IdxAdder, BuffAdder, Templates, BaseCubesIds)
            if OnlyPatternCount:
                Patterns += SubPatterns
            else:
                Patterns._cubes += SubPatterns._cubes
            if Verbose:
                if OnlyPatternCount:
                    print(f"Last. BufferLen={Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={Patterns}")
                else:
                    print(f"Last. BufferLen={Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={len(Patterns)}")
        if Verbose:
            if OnlyPatternCount:
                print(f"FINISHED BufferLen={Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={Patterns}")
            else:
                print(f"FINISHED BufferLen={Buffer.getWeightedLen()} ({len(Buffer)} items), PatternsLen={len(Patterns)}")
        if CombinedCompressionChecking:
            return Patterns, BackTracingCounterSum, SolverCallsSum
        return Patterns
    
    def removeNotCompressable(self, Edt : EdtStructure, MultiThreading = False, ReturnRemovedCubes : bool = False) -> int:
        ToBeRemoved = []
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver
        if type(Edt) is DecompressorSolver:
            Edt.createEquationBase()
        #if MultiThreading and type(Edt) is not DecompressorSolver:
        #    MultiThreading = False
        import asyncio
        from tqdm import tqdm
        if MultiThreading:        
            def serialRange(Range):
                ToBeRemovedLocal = []
                for i in Range:
                    if not Edt.isCompressable(self.getCube(i)):
                        ToBeRemovedLocal.append(i)
                return ToBeRemovedLocal
            for rl in p_uimap(serialRange, list(Generators().subRanges(0, len(self), 1000, 1)), desc="Removing uncompressable cubes (x1000)"):
                ToBeRemoved += rl
            AioShell.removeLastLine()
            ToBeRemoved.sort()
        else:
            for i in range(len(self)):
                if not Edt.isCompressable(self.getCube(i)):
                    ToBeRemoved.append(i)
        if ReturnRemovedCubes:
            RemovedCubes = []
        for i in reversed(ToBeRemoved):
            if ReturnRemovedCubes:
                RemovedCubes.append(self.getCube(i))
            self.removeCube(i)
        if self.isIdImplemented():
            self.recalculateIndices()
            self.recalculateWeights()
        if ReturnRemovedCubes:
            return RemovedCubes
        return len(ToBeRemoved)
    
    removeUnompressable = removeNotCompressable    # remove this !!!!!!!!!!!!!!!!!!!!!!!
    removeUncompressable = removeNotCompressable
    
    def getCumulativeSpecifiedCellCount(self) ->int:
        return sum([Cube.getSpecifiedCount() for Cube in self._cubes])
    
    def getAverageFillRate(self) -> float:
        RList = [Cube.getFillRate() for Cube in self._cubes]
        return sum(RList) / len(RList)
    
    def getChannelVolume(self, Edt : EdtStructure) -> int:
        return Edt.getTestDataVolume(len(self))
    
    def getCubeVolume(self) -> int:
        Result = 0
        for Cube in self._cubes:
            Result += Cube.getSpecifiedCount()
        return Result
    
    @staticmethod
    def doMergingExperiment(Cubes : TestCubeSet, Edt : EdtStructure, BufferLength : int = None, PatternCountPerRound : int = 1, MinBatteryCharge : float = None, CompressabilityLimit : int = None, Verbose : bool = False, MultiThreading = False, CombinedCompressionChecking : bool = False, AlsoReturnPatterns : bool = False, SkipCubeCOmpressabilityCheck : bool = False, Templates : TestCubeSet = None, BaseCubesIds = set()) -> tuple:
        """Returns 4-element tuple:
        AfterRemovalCubesCount, len(Patterns), TestTime, TestDataVolume, ExecutionTime
        In case of combined method it returns also
        BackTracingCalls, SolverCalls"""
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver    
        if CombinedCompressionChecking and type(Edt) is not DecompressorSolver:
            Aio.printError("Edt must be DecompressorSolver object if CombinedCompressionChecking is set.")
            return None
        CubesCopy = Cubes
        if CombinedCompressionChecking:
            CubesCopy = Cubes.deepCopy()
        else:
            CubesCopy = Cubes.softCopy()
        if BufferLength is not None:
            CubesCopy.BufferSize = BufferLength
        if CompressabilityLimit is not None:
            CubesCopy.CompressionFailLimit = CompressabilityLimit
        edt = Edt.copy()
        if MinBatteryCharge is not None and type(edt) in [EdtStructure, TestDataDecompressor]:
            edt.MinimumBatteryLevel = MinBatteryCharge
        if not SkipCubeCOmpressabilityCheck:
            BeforeRemovalCubesCount = len(CubesCopy)
            if Verbose:
                Aio.print(f"#Cubes before uncompressable removal: {BeforeRemovalCubesCount}")
            RemovedCount = CubesCopy.removeNotCompressable(edt, MultiThreading)
            AfterRemovalCubesCount = len(CubesCopy)
            if Verbose:
                Aio.print(f"#Cubes removed:                       {RemovedCount}")
                Aio.print(f"#Cubes after uncompressable removal:  {AfterRemovalCubesCount}")
        else:
            AfterRemovalCubesCount = len(CubesCopy)
        t0 = time.time()
        if CombinedCompressionChecking:
            Patterns, BackTracingCounterSum, SolverCallsSum = CubesCopy.merge(edt, PatternCountPerRound, Verbose, True, (not AlsoReturnPatterns), Templates, BaseCubesIds)
        else:
            Patterns = CubesCopy.merge(edt, PatternCountPerRound, Verbose, False, (not AlsoReturnPatterns), Templates, BaseCubesIds)
        if AlsoReturnPatterns:
            PatternSet = Patterns
            Patterns = len(PatternSet)
        t1 = time.time()
        TestTime = edt.getTestTime(Patterns)
        TestDataVolume = edt.getTestDataVolume(Patterns)
        ExeTime = (t1 - t0)
        if Verbose:
            Aio.print(f"#Patterns:                            {Patterns}")
            Aio.print(f"Test time [cycles]:                   {TestTime}")
            Aio.print(f"Test data volume [b]:                 {TestDataVolume}")
            Aio.print(f"Execution time [s]:                   {ExeTime}")
        if CombinedCompressionChecking:
            if AlsoReturnPatterns:
                return AfterRemovalCubesCount, Patterns, TestTime, TestDataVolume, ExeTime, BackTracingCounterSum, SolverCallsSum, PatternSet
            else:
                return AfterRemovalCubesCount, Patterns, TestTime, TestDataVolume, ExeTime, BackTracingCounterSum, SolverCallsSum
        if AlsoReturnPatterns:
            return AfterRemovalCubesCount, Patterns, TestTime, TestDataVolume, ExeTime, PatternSet
        else:
            return AfterRemovalCubesCount, Patterns, TestTime, TestDataVolume, ExeTime
        
    doExperiment = doMergingExperiment

    @staticmethod
    def _do_experimentsSingleTry(EdtWithNumber, Cubes, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, CombinedCompressionChecking, SkipCubeCOmpressabilityCheck, CompensatePatternCount, AlsoReturnPatterns : bool = False, Templates : TestCubeSet = None) -> tuple:
        TaskNum = EdtWithNumber[0]
        Edt = EdtWithNumber[1]
        if CompensatePatternCount:
            import gc
            Result = list(TestCubeSet.doMergingExperiment(Cubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, False, CombinedCompressionChecking, SkipCubeCOmpressabilityCheck=SkipCubeCOmpressabilityCheck, AlsoReturnPatterns=True, Templates=Templates))
            Uncompressable = Cubes.copy().removeNotCompressable(Edt, False, ReturnRemovedCubes=True) 
            Comprensator = PatternCountComprensator(Result[-1], Uncompressable, UncompressableCubeUsedOnlyOnce=True)
            Result[1] = Comprensator.getCompensatedPatternCount()
            del Comprensator
            del Uncompressable
            if not AlsoReturnPatterns:
                del Result[-1]
            gc.collect()
            return [TaskNum, Result]
        else:
            return [TaskNum, TestCubeSet.doMergingExperiment(Cubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, False, CombinedCompressionChecking, SkipCubeCOmpressabilityCheck=SkipCubeCOmpressabilityCheck, AlsoReturnPatterns=AlsoReturnPatterns)]

    @staticmethod
    def doExperiments(Cubes : TestCubeSet, EdtList : list, BufferLength : int = None, PatternCountPerRound : int = 1, MinBatteryCharge : float = None, CompressabilityLimit : int = None, CombinedCompressionChecking : bool = False, MultiThreading : bool = True, Verbose : bool = False, SkipCubeCOmpressabilityCheck : bool = False, CompensatePatternCount : bool = False, AlsoReturnPatterns : bool = False, Templates : TestCubeSet = None, UseTrueBaseCubes : bool = True) -> list:
        if type(EdtList) is not list:
            EdtList = [EdtList]
        Result = []
        BaseCubesIds = set()
        if UseTrueBaseCubes:
            PatternIds = set()
            for Cube in Cubes:
                if Cube.PatternId != PatternIds:
                    PatternIds.add(Cube.PatternId)
                    BaseCubesIds.add(Cube.Id)
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver
        def singleTry(Edt) -> tuple:
            SCubes = Cubes.deepCopy()
            Mul = False
            if (not MultiThreading) and (type(Edt) is DecompressorSolver):
                Mul = True
            if CompensatePatternCount:
                Result = list(TestCubeSet.doMergingExperiment(SCubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, Mul, CombinedCompressionChecking, SkipCubeCOmpressabilityCheck=SkipCubeCOmpressabilityCheck, AlsoReturnPatterns=True, Templates=Templates, BaseCubesIds=BaseCubesIds))
                Uncompressable = SCubes.copy().removeNotCompressable(Edt, Mul, ReturnRemovedCubes=True) 
                Comprensator = PatternCountComprensator(Result[-1], Uncompressable, UncompressableCubeUsedOnlyOnce=True)
                Result[1] = Comprensator.getCompensatedPatternCount()
                del Comprensator
                del Uncompressable
                if not AlsoReturnPatterns:
                    del Result[-1]
                return Result
            else:
                return TestCubeSet.doMergingExperiment(SCubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, Mul, CombinedCompressionChecking, SkipCubeCOmpressabilityCheck=SkipCubeCOmpressabilityCheck, AlsoReturnPatterns=AlsoReturnPatterns, Templates=Templates, BaseCubesIds=BaseCubesIds)
        if MultiThreading is None:
            for R in EdtList:
                Result.append(singleTry(R))
        elif MultiThreading:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            from tqdm import tqdm
            from functools import partial
            EdtListWithNumbers = [(i, Edt) for i, Edt in enumerate(EdtList)]
            with ProcessPoolExecutor() as executor:
                Tasks = [executor.submit(partial(TestCubeSet._do_experimentsSingleTry, Cubes=Cubes, BufferLength=BufferLength, PatternCountPerRound=PatternCountPerRound, MinBatteryCharge=MinBatteryCharge, CompressabilityLimit=CompressabilityLimit, Verbose=Verbose, CombinedCompressionChecking=CombinedCompressionChecking, SkipCubeCOmpressabilityCheck=SkipCubeCOmpressabilityCheck, CompensatePatternCount=CompensatePatternCount, AlsoReturnPatterns=AlsoReturnPatterns, Templates=Templates), Edt) for Edt in EdtListWithNumbers]
                for f in tqdm(as_completed(Tasks), total=len(Tasks)):
                    Result.append(f.result())
            Result.sort(key=lambda x: x[0])
            for i, v in enumerate(Result):
                Result[i] = v[1]
            #for R in p_imap(singleTry, EdtList):
            #    Result.append(R)
            AioShell.removeLastLine()
        else:
            import tqdm
            for R in tqdm.tqdm(EdtList):
                Result.append(singleTry(R))
            AioShell.removeLastLine()
        return Result

    def learnMaximumUsedEncodingCapacity(self, TruePatternCount : int, Edt : EdtStructure, Start : float, Stop : float, Step : float = 0.001, UseTemplates : bool = False, CompensatePatternCount : bool = False, UseTrueBaseCubes : bool = False, Verbose : bool = False):
        if _BATTERY_MODEL_TYPE is not BatteryModelType.BASED_ON_USED_ENCODING_CAPACITY:
            Aio.printError("learnMaximumUsedEncodingCapacity is only suitable for BatteryModelType.BASED_ON_USED_ENCODING_CAPACITY.")
            return None
        from functools import lru_cache
        LfsrSize = Edt.getLongestLfsrSize()
        Cubes = self
        if UseTemplates:
            t = self.tryToExtractTemplates(32, Overlapping=1)
            Cubes = self.deepCopy()
            Cubes.removeTemplates(t)
        else:
            t = None
        def sign(x):
            if x < 0:
                return -1
            elif x > 0:
                return 1
            else:
                return 0
        def ternary_search(f, a, b):
            s = (b - a) / 10
            SignChanged = False
            Cntr = 0
            while Cntr < 1:
                Cntr += 1
                x = a
                if Verbose:
                    print(f"Searching for sign change in range: a={a}, b={b}, Step={s}")
                lastval = None
                while x <= b + 1e-12:
                    val = f(x)
                    if lastval is not None:
                        if sign(lastval) != sign(val):
                            a = x - 1 * s
                            b = x + 0.5 * s
                            s = (b - a) / 10
                            SignChanged = True
                            if Verbose:
                                print(f"Sign changed at x={x} -> Err={val}")
                            break
                    lastval = val
                    x += s
                if not SignChanged:
                    if Verbose:
                        print(f"No sign change found!!!")
                    break
            best_x_tmp, best_val_tmp = 1, 10
            while b - a >= 3 * Step:
                if Verbose:
                    print(f"Ternary search step: a={a}, b={b}")
                m1 = a + (b - a) / 3
                m2 = b - (b - a) / 3
                f1, f2 = abs(f(m1)), abs(f(m2))
                if f1 < best_val_tmp:
                    best_x_tmp, best_val_tmp = m1, f1
                if f2 < best_val_tmp:
                    best_x_tmp, best_val_tmp = m2, f2
                if f1 <= f2:
                    b = m2
                else:
                    a = m1
            best_x = a
            best_val = f(a)
            x = a + Step
            while x <= b + 1e-12:
                val = f(x)
                if val < best_val_tmp:
                    best_x_tmp, best_val_tmp = x, val
                if val < best_val:
                    best_x, best_val = x, val
                x += Step
            if best_val > best_val_tmp:
                best_val, best_x = best_val_tmp, best_x_tmp
            return best_x, best_val
        @lru_cache(maxsize=None) 
        def f(x):
            EdtCopied = Edt.copy()
            EdtCopied.MinimumBatteryLevel = x
            Experiments = TestCubeSet.doExperiments(Cubes, [EdtCopied], PatternCountPerRound=1, Verbose=0, CompensatePatternCount=CompensatePatternCount, Templates=t, MultiThreading=None, UseTrueBaseCubes=UseTrueBaseCubes)
            Error = (Experiments[0][1] - TruePatternCount) / TruePatternCount
            if Verbose:
                print(f"UsedEncodingCapacity = {x} -> Err = {Error}    (Estimated {Experiments[0][1]}, True {TruePatternCount})")
            #Error = abs(Error)
            return Error
        MinVars = ternary_search(f, Start, Stop)
        if Verbose:
            print(f"RESULT of UsedEncodingCapacity = {MinVars[0]} -> Err = {MinVars[1]}")
        return MinVars[0]
    
    def learnMinBatteryLevel(self, TruePatternCount : int, Edt : EdtStructure, StartingFromVariables : int = 0, UseTemplates : bool = False, CompensatePatternCount : bool = False, UseTrueBaseCubes : bool = False, Verbose : bool = False):
        if _BATTERY_MODEL_TYPE is not BatteryModelType.NORMAL:
            Aio.printError("learnMinBatteryLevel is only suitable for BatteryModelType.NORMAL.")
            return None
        from functools import lru_cache
        LfsrSize = Edt.getLongestLfsrSize()
        Cubes = self
        if UseTemplates:
            t = self.tryToExtractTemplates(32, Overlapping=1)
            Cubes = self.deepCopy()
            Cubes.removeTemplates(t)
        else:
            t = None
        End = LfsrSize - 1
        def ternary_search(f, a, b):
            while b - a >= 3:
                m1 = a + (b - a) // 3
                m2 = b - (b - a) // 3
                f1, f2 = f(m1), f(m2)
                if f1 < f2:
                    b = m2 - 1
                else:
                    a = m1 + 1
            best_x = a
            best_val = f(a)
            for x in range(a+1, b+1):
                val = f(x)
                if val < best_val:
                    best_x, best_val = x, val
            return best_x, best_val
        @lru_cache(maxsize=None) 
        def f(x):
            EdtCopied = Edt.copy()
            EdtCopied.MinimumBatteryLevel = x / LfsrSize
            Experiments = TestCubeSet.doExperiments(Cubes, [EdtCopied], PatternCountPerRound=1, Verbose=0, CompensatePatternCount=CompensatePatternCount, Templates=t, MultiThreading=None, UseTrueBaseCubes=UseTrueBaseCubes)
            Error = abs((Experiments[0][1] - TruePatternCount) / TruePatternCount)
            if Verbose:
                print(f"Threshold = {x}/{LfsrSize} -> Err = {Error}")
            return Error
        MinVars = ternary_search(f, StartingFromVariables, End)
        if Verbose:
            print(f"RESULT of Threshold = {MinVars[0]/LfsrSize} -> Err = {MinVars[1]}")
        return MinVars[0] / LfsrSize
    
    def learnMinBatteryLevelLinear(self, TruePatternCount : int, Edt : EdtStructure, StartingFromVariables : int = 0, MultiThreading : bool = True, UseTemplates : bool = False, CompensatePatternCount : bool = False, UseTrueBaseCubes : bool = False):
        from libs.utils_list import List
        LfsrSize = Edt.getLongestLfsrSize()
        Cubes = self
        if UseTemplates:
            t = self.tryToExtractTemplates(32, Overlapping=1)
            Cubes = self.deepCopy()
            Cubes.removeTemplates(t)
        else:
            t = None
        edts = []
        for i in range(StartingFromVariables, LfsrSize):
            EdtCopied = Edt.copy()
            EdtCopied.MinimumBatteryLevel = i / LfsrSize
            edts.append(EdtCopied)
        Experiments = TestCubeSet.doExperiments(Cubes, edts, PatternCountPerRound=1, Verbose=0, CompensatePatternCount=CompensatePatternCount, Templates=t, MultiThreading=MultiThreading, UseTrueBaseCubes=UseTrueBaseCubes)
        Errors = [abs((Experiments[i][1] - TruePatternCount) / TruePatternCount) for i in range(len(Experiments))]
        print("Errors = ", Errors)
        Errors = List.MAVFilter(Errors, [0.1, 1, 0.1], 6)
        print("ErrorsF = ", Errors)
        print("PCounts = ", [Experiments[i][1] for i in range(len(Experiments))])
        MinIdx = List.getIndexOfMinimum(Errors)
        print("MinIdx = ", MinIdx)
        return (MinIdx + StartingFromVariables) / LfsrSize


class DecompressorUtils:
    
    @staticmethod
    def getInputConfigForRingGen(LfsrSize : int, InputCount : int, DoubleInjectors : bool = True) -> list:
        Result = []
        from libs.lfsr import Lfsr
        if type(LfsrSize) is Lfsr:
            LfsrSize = len(LfsrSize)
        Adder = LfsrSize / InputCount
        if DoubleInjectors:
            Adder /= 2
        StartPoint = int(round(Adder / 2, 0)) + 1
        UpperIndex = LfsrSize - StartPoint
        LowerIndex = StartPoint - 2
        while LowerIndex < 0:
            LowerIndex += LfsrSize
        for i in range(InputCount):
            if DoubleInjectors:
                Result.append([int(round(UpperIndex, 0)), int(round(LowerIndex, 0))])
                LowerIndex += Adder
            else:
                Result.append(int(round(UpperIndex, 0)))
            UpperIndex -= Adder
        return Result
    
    @staticmethod
    def getDesignInfoFromFIle(FileName : str) -> dict:
        Result = {}
        for Line in Generators().readFileLineByLine(FileName):
            R = re.search(r"FU\s*\(full\)\s*([0-9]+)", Line)
            if R:
                Result["TotalFaults"] = int(R.group(1))
                continue
            R = re.search(r'simulated_patterns\s+([0-9]+)', Line)
            if R:
                Result["SimulatedPatterns"] = int(R.group(1))
                continue
            R = re.search(r"scan_chains\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["ScanChains"] = int(R.group(1))
                continue
            R = re.search(r"scan_length\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["ScanLength"] = int(R.group(1))
                continue
            R = re.search(r"umber\s*of\s*primary\s*inputs\s*=\s*([0-9]+)", Line)
            if R:
                Result["PrimaryInputs"] = int(R.group(1))
                continue
            R = re.search(r"fault[_ ]coverage\s*([0-9.]+)%", Line)
            if R:
                Result["FaultCoverage"] = float(R.group(1)) / 100.0
                continue
            R = re.search(r"test[_ ]coverage\s*([0-9.]+)%", Line)
            if R:
                Result["TestCoverage"] = float(R.group(1)) / 100.0
                continue
            R = re.search(r"atpg[_ ]effectiveness\s*([0-9.]+)%", Line)
            if R:
                Result["AtpgEffectiveness"] = float(R.group(1)) / 100.0
                continue
            R = re.search(r"#test[_ ]patterns\s*([0-9.]+)", Line)
            if R:
                Result["#TestPatterns"] = int(R.group(1))
                continue
            R = re.search(r"AAB\s*\(atpg_abort\)\s+([0-9]+)", Line)
            if R:
                Result["AtpgAborts"] = int(R.group(1))
                continue
            R = re.search(r"EAB\s*\(edt_abort\)\s+([0-9]+)", Line)
            if R:
                Result["EdtAborts"] = int(R.group(1))
                continue
            R = re.search(r"#basic[_ ]patterns\s*([0-9.]+)", Line)
            if R:
                Result["#BasicPatterns"] = int(R.group(1))
                continue
            R = re.search(r"#clock[_ ]sequential[_ ]patterns\s*([0-9.]+)", Line)
            if R:
                Result["#ClockSequentialPatterns"] = int(R.group(1))
                continue
            R = re.search(r"CPU[_ ]time\s+\(secs\)\s*([0-9.]+)", Line)
            if R:
                Result["CpuTime"] = float(R.group(1))
                continue
            R = re.search(r"#gates\s*[:=]\s*([0-9]+)\s+#faults\s*[:=]\s*([0-9]+)", Line)
            if R:
                Result["#Gates"] = int(R.group(1))
                Result["#Faults"] = int(R.group(2))
                continue
        try:
            Result["ScanCells"] = Result["ScanChains"] * Result["ScanLength"]
        except: pass
        return Result
    
    @staticmethod
    def getTableOfDesignInfoFromFiles(FileNames : list, RowTitles : list = None) -> AioTable:
        return AioTable.fromSetOfFiles(FileNames, {
                                    "TotalFaults": r"FU\s*\(full\)\s*([0-9]+)",
                                    "SimulatedPatterns": r'simulated_patterns\s+([0-9]+)',
                                    "ScanChains": r"scan_chains\s*[=:]\s*([0-9]+)",
                                    "ScanLength": r"scan_length\s*[=:]\s*([0-9]+)"
                                }, RowTitles)
        
    @staticmethod
    def getTableOfEdtInfoFromFiles(FileNames : list, RowTitles : list = None) -> AioTable:
        return AioTable.fromSetOfFiles(FileNames, {
                                    "InputChannels": r"input_channels\s*[=:]\s*([0-9]+)",
                                    "lfsr": r"decompressor_size\s*[=:]\s*([0-9]+)",
                                    "ScanChains": r"scan_chains\s*[=:]\s*([0-9]+)",
                                    "ScanLength": r"scan_length\s*[=:]\s*([0-9]+)",
                                    "BufferSize": r"cube\s*pool\s*size\s*[=:]\s*([0-9]+)",
                                    "CompressionFailLimit": r"EDT\s*abort\s*limit\s*[=:]\s*([0-9]+)"
                                }, RowTitles)
    
    @staticmethod
    def getEdtInfoFromFile(FileName : str) -> dict:
        Result = {}
        for Line in Generators().readFileLineByLine(FileName):
            R = re.search(r"input_channels\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["InputChannels"] = int(R.group(1))
                continue
            R = re.search(r"scan_length\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["ScanLength"] = int(R.group(1))
                continue
            R = re.search(r"scan_chains\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["ScanChains"] = int(R.group(1))
                continue
            R = re.search(r"decompressor_size\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["Lfsr"] = int(R.group(1))
                continue
            R = re.search(r"cube\s*pool\s*size\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["BufferSize"] = int(R.group(1))
                continue
            R = re.search(r"EDT\s*abort\s*limit\s*[=:]\s*([0-9]+)", Line)
            if R:
                Result["CompressionFailLimit"] = int(R.group(1))
                continue
            R = re.search(r"After\s*merging", Line)
            if R:
                break
        try:
            Result["ScanCells"] = Result["ScanChains"] * Result["ScanLength"]
        except: pass
        return Result
    
    @staticmethod
    def getDynamicCompactionStatsFromLog(FileName : str) -> list:
        Result = []
        Dict = {}
        for Line in Generators().readFileLineByLine(FileName):
            R = re.search(f'-*\s*Targeting\s*statistics\s*-*', Line)
            if R:
                if len(Dict) > 0:
                    Result.append(Dict)
                    Dict = {}
                continue
            R = re.search(r"number\s*of\s*tested\s*faults\s*[:=]\s*([0-9]+)\s*\(([.0-9]+)%\)", Line)
            if R:
                Dict['tested_faults'] = int(R.group(1))
                Dict['tested_faults_percent'] = float(R.group(2))
                continue
            R = re.search(r"dded\s*per\s*pattern\s*[:=]\s*([.0-9]+)\s*\/\s*([.0-9]+)", Line)
            if R:
                Dict['added_per_pattern'] = float(R.group(1))
                Dict['added_per_pattern_2'] = float(R.group(2))
                continue
            R = re.search(r"number\s*of\s*added\s*scan\s*cells\s*[:=]\s*([0-9]+)\s*\(([.0-9]+)\s*.+,\s*([.0-9]+)", Line)
            if R:
                Dict['added_scan_cells'] = int(R.group(1))
                Dict['added_scan_cells_per_pattern'] = float(R.group(2))
                Dict['added_scan_cells_per_fault'] = float(R.group(2))
                continue
        if len(Dict) > 0:
            Result.append(Dict)
        return Result
    
    @staticmethod
    def preparseLogs(FileNames : list):
        """for each log file writes object, gzipped file <Filename>.preparsed_rs contaning a dictionary:
        {
            "tc": TestCUbeSet,
            "edt": EdtStructure,
            "sol": DecompressorSolver,
            "faults": TotalFaultCount,
            "patterns": PatternCount,
            "scancells": ScanCellsStructure,
            "faultdict": CubeId: Fault dict
            "designinfo": Other data
            "dynamiccompaction": DynamicCompaction <if available in log!!!>
        )"""
        if type(FileNames) is str:
            FileNames = [FileNames]
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver
        from libs.files import File
        def single(FileName):
            try:
                di = DecompressorUtils.getDesignInfoFromFIle(FileName)
                tc, faultdict, eablist, specbitsdict = TestCubeSet.fromFile(FileName, ReturnAlsoFaultsDict=1, ReturnAlsoEABFaultsList=1, ReturnAlsoSpecBitsDict=1)
                Result = {
                    "tc": tc,
                    "edt": EdtStructure.fromFile(FileName),
                    "sol": DecompressorSolver.fromFile(FileName),
                    "scancells": ScanCellsStructure.fromFile(FileName),
                    "faults": di["TotalFaults"],
                    "patterns": di["SimulatedPatterns"],
                    "primaryinputs": di["PrimaryInputs"],
                    "designinfo": di,
                    "faultdict": faultdict,
                    "specbitsdict": specbitsdict,
                    "eablist": eablist
                }
                DynamicCompaction = DecompressorUtils.getDynamicCompactionStatsFromLog(FileName)
                if len(DynamicCompaction) > 0:
                    Result["dynamiccompaction"] = DynamicCompaction
                File.writeObject(FileName + ".preparsed_rs", Result, True)
                return None
            except Exception as e:
                return FileName + " " + str(e)
        for i in p_uimap(single, FileNames):
            if i is not None:
                Aio.printError(i)
        AioShell.removeLastLine()
        
        
        

class PreparsedData:

    __slots__ = ("_data",)

    def __init__(self, FileName : str) -> None:
        try:
            self._data = File.readObject(FileName, 1)
        except:
            self._data = None
            Aio.printError("Error reading preparsed data from file:", FileName)
            
    def getData(self) -> dict:
        return self._data
            
    def getDesignInfoDict(self) -> dict:
        return self._data.get("designinfo", None)
    
    def getUsefullCubes(self, MakeCopy : bool = False) -> TestCubeSet:
        if MakeCopy:
            return self._data.get("tc", TestCubeSet()).deepCopy()
        return self._data.get("tc", TestCubeSet())
    
    def getUsefullCubesIds(self) -> set:
        tc = self._data.get("tc", TestCubeSet())
        Result = set()
        for Cube in tc:
            Result.add(Cube.Id)
        return Result
    
    def getCubeSpecBits(self, Usefull : bool = True, Dropped : bool = False, Aborted : bool = False) -> list:
        UsefullAndDroppedDict = self._data.get("specbitsdict", {})
        UsefullIds = self.getUsefullCubesIds()
        Result = []
        for Id in sorted(UsefullAndDroppedDict.keys()):
            IsUsefull = Id in UsefullIds
            if (Usefull and IsUsefull) or (Dropped and (not IsUsefull)):
                Result.append(UsefullAndDroppedDict[Id])
        if Aborted:
            EABList = self._data.get("eablist", [])
            for Pos in EABList:
                Result.append(Pos[-1])
        return Result
    
    def getCubeFillRates(self, Usefull : bool = True, Dropped : bool = False, Aborted : bool = False) -> list:
        CUbeSpecBits = self.getCubeSpecBits(Usefull, Dropped, Aborted)
        Edt = self.getEdtStructure()
        Result = []
        if Edt is not None:
            SCells = Edt.getScanChainCount() * Edt.getScanLength()
            for SpecBits in CUbeSpecBits:
                Result.append(SpecBits / SCells)
        return Result
    
    def getCubeUsedEncodingCapacity(self, Usefull : bool = True, Dropped : bool = False, Aborted : bool = False) -> list:
        CUbeSpecBits = self.getCubeSpecBits(Usefull, Dropped, Aborted)
        Edt = self.getEdtStructure()
        EncCap = None if Edt is None else Edt.getEncodingCapacity()
        Result = []
        if EncCap is not None:
            for SpecBits in CUbeSpecBits:
                Result.append(SpecBits / EncCap)
        return Result
    
    def getScanCellsStructure(self) -> ScanCellsStructure:
        return self._data.get("scancells", None)
    
    def getDynamicCompactionStats(self) -> list:
        return self._data.get("dynamiccompaction", [])
    
    def getDynamicCompactionAddedCells(self) -> int:
        Stats = self.getDynamicCompactionStats()
        return ListOfDicts.getSumOfField(Stats, 'added_scan_cells')
        
    def getDynamicCompactionAdddedPerPatternData(self) -> list:
        Stats = self.getDynamicCompactionStats()
        return ListOfDicts.getListOfField(Stats, 'added_per_pattern')
    
    def getDynamicCompactionAdddedFaultsData(self) -> list:
        Stats = self.getDynamicCompactionStats()
        return ListOfDicts.getListOfField(Stats, 'tested_faults')
        
    def getEdtStructure(self) -> EdtStructure:
        return self._data.get("edt", None)
    
    def getFaultCount(self) -> int:
        di = self.getDesignInfoDict()
        return di.get("#Faults", 0) if di is not None else 0
    
    def getGateCount(self) -> int:
        di = self.getDesignInfoDict()
        return di.get("#Gates", 0) if di is not None else 0
    
    def getCubeHistogramsAsTable(self, BarWidth, BarWidthAsPartOfScanLength : bool = False) -> AioTable:
        from libs.stats import Histogram
        from libs.utils_float import FloatUtils
        if BarWidthAsPartOfScanLength:
            ScanLen = self.getScanCellsStructure().ScanChainLength
            BarWidth = BarWidth * ScanLen
        UsefulCubeSB = self.getCubeSpecBits(1,0,0)
        DroppedCubeSB = self.getCubeSpecBits(0,1,0)
        AbortedCubeSB = self.getCubeSpecBits(0,0,1)
        UsedCubeH = Histogram(UsefulCubeSB, BarWidth)
        DroppedCubeH = Histogram(DroppedCubeSB, BarWidth)
        AbortedCubeH = Histogram(AbortedCubeSB, BarWidth)
        UsedCubePD = UsedCubeH.getPlotData(0)
        DroppedCubePD = DroppedCubeH.getPlotData(0)
        AbortedCubePD = AbortedCubeH.getPlotData(0)
        Table = AioTable(["SpecBitsRange", "UsefulCount", "DroppedCount", "AbortedCount"])
        Len = max(len(UsedCubePD[1]), len(DroppedCubePD[1]), len(AbortedCubePD[1]))
        for i in range(Len):
            if BarWidthAsPartOfScanLength:
                From = FloatUtils.roundToDecimalPlacesAsInAnotherFloat(i*BarWidth/ScanLen, BarWidth)
                To = FloatUtils.roundToDecimalPlacesAsInAnotherFloat((i+1)*BarWidth/ScanLen, BarWidth)
                Row = [f"{From} - {To}"]
            else:
                Row = [f"{i*BarWidth} - {(i+1)*BarWidth}"]
            if i < len(UsedCubePD[1]):
                Row.append(UsedCubePD[1][i])
            else:
                Row.append(0)
            if i < len(DroppedCubePD[1]):
                Row.append(DroppedCubePD[1][i])
            else:
                Row.append(0)
            if i < len(AbortedCubePD[1]):
                Row.append(AbortedCubePD[1][i])
            else:
                Row.append(0)
            Table.add(Row)
        return Table
    
    def getCubeRangesHistogramAsTable(self, RangeCount : int = 10, Normalised : bool = True) -> AioTable:
        from libs.stats import RangesHistogram
        UsefulCubeSB = self.getCubeSpecBits(1,0,0)
        DroppedCubeSB = self.getCubeSpecBits(0,1,0)
        AbortedCubeSB = self.getCubeSpecBits(0,0,1)
        UsedCubeH = RangesHistogram(UsefulCubeSB, RangeCount)
        DroppedCubeH = RangesHistogram(DroppedCubeSB, RangeCount)
        AbortedCubeH = RangesHistogram(AbortedCubeSB, RangeCount)
        UsedCubeR = UsedCubeH.getRanges(Normalised)
        DroppedCubeR = DroppedCubeH.getRanges(Normalised)
        AbortedCubeR = AbortedCubeH.getRanges(Normalised)
        Table = AioTable(["UsefulRanges", "DroppedRanges", "AbortedRanges"])
        Len = max(len(UsedCubeR), len(DroppedCubeR), len(AbortedCubeR))
        for i in range(Len):
            Row = []
            if i < len(UsedCubeR):
                Row.append(round(UsedCubeR[i], 3))
            else:
                Row.append(0)
            if i < len(DroppedCubeR):
                Row.append(round(DroppedCubeR[i], 3))
            else:
                Row.append(0)
            if i < len(AbortedCubeR):
                Row.append(round(AbortedCubeR[i], 3))
            else:
                Row.append(0)
            Table.add(Row)
        return Table
    
    def getPatternCount(self) -> int:
        return self._data["patterns"]
    
    def getTestDataVolume(self) -> int:
        Edt : EdtStructure = self.getEdtStructure()
        return Edt.getTestDataVolume(self.getPatternCount())
    
    def getTestTime(self) -> int:
        Edt : EdtStructure = self.getEdtStructure()
        return Edt.getTestTime(self.getPatternCount())
    
    def getDataForML(self, EstimatedLfsrLen : int = None, EstimatedChannels : int = None) -> list:
        from libs.utils_list import List, ListOfDicts
        from libs.stats import RangesHistogram
        Result = []
        Edt : EdtStructure = self.getEdtStructure()
        DI : dict = self.getDesignInfoDict()
        UsefulCubeSpecBits = self.getCubeSpecBits(1,0,0)
        DroppedCubeSpecBits = self.getCubeSpecBits(0,1,0)
        AbortedCubeSpecBits = self.getCubeSpecBits(0,0,1)
        UsefulCubesFillRate = self.getCubeFillRates(1,0,0)
        DroppedCubesFillRate = self.getCubeFillRates(0,1,0)
        AbortedCubesFillRate = self.getCubeFillRates(0,0,1)
        UsefulCubesEncCap = self.getCubeUsedEncodingCapacity(1,0,0)
        #DroppedCubesEncCap = self.getCubeUsedEncodingCapacity(0,1,0)
        #AbortedCubesEncCap = self.getCubeUsedEncodingCapacity(0,0,1)
        DynCompPerPattern = self.getDynamicCompactionAdddedPerPatternData()
        TC : TestCubeSet = self.getUsefullCubes(False)
        PatternSpecBits = TC.getPatternSpecBits()
        #Patterns : TestCubeSet = TC.getPatterns()
        #Patterns.getAverageSpecBits()
        ### Compression #######################
        Result.append(Edt.getInputCount())              # #Channels             1   1
        Result.append(Edt.getLongestLfsrSize())         # LFSR size             1   2
        Result.append(Edt.getCompressionRatio())        # Compression ratio     1   3
        Result.append(Edt.getEncodingCapacity())        # Encoding capacity     1   4
        Result.append(Edt.getScanChainCount())          # #Scan chains          1   5   
        Result.append(Edt.getScanLength())              # Scan length           1   6
        ### Circuitry #########################
        Result.append(DI["#Gates"])                     # #Gates                1   7
        Result.append(DI["#Faults"])                    # #Faults               1   8
        ### Useful cubes ######################
        Result.append(len(UsefulCubeSpecBits))           # Count                1   9
        Result.append(List.Avg(UsefulCubeSpecBits))      # AVG                  1  10
        Result.append(List.StdDev(UsefulCubeSpecBits))   # STD DEV              1  11
        Result.append(min(UsefulCubeSpecBits + [0]))     # MIN                  1  12
        Result.append(max(UsefulCubeSpecBits + [0]))     # MAX                  1  13
        Result += RangesHistogram(UsefulCubeSpecBits, 10).getRanges(1)[1:]  # RangesHistogram of SpecBits    9 14-22
        Result.append(sum(UsefulCubesEncCap))            # Used encoding capacity SUM      1  23
        ### Dropped cubes #####################
        Result.append(len(DroppedCubeSpecBits))          # Count                1  24
        Result.append(List.Avg(DroppedCubeSpecBits))     # AVG                  1  25
        Result.append(List.StdDev(DroppedCubeSpecBits))  # STD DEV              1  26
        Result.append(min(DroppedCubeSpecBits + [0]))    # MIN                  1  27
        Result.append(max(DroppedCubeSpecBits + [0]))    # MAX                  1  28
        Result += RangesHistogram(DroppedCubeSpecBits, 10).getRanges(1)[1:]  # RangesHistogram of SpecBits    9 29-37
        Result.append(sum(DroppedCubeSpecBits))          # Used encoding capacity SUM      1  38
        ### Aborted cubes #####################
        Result.append(len(AbortedCubeSpecBits))          # Count                1  39
        Result.append(List.Avg(AbortedCubeSpecBits))     # AVG                  1  40
        Result.append(List.StdDev(AbortedCubeSpecBits))  # STD DEV              1  41
        Result.append(min(AbortedCubeSpecBits + [0]))    # MIN                  1  42
        Result.append(max(AbortedCubeSpecBits + [0]))    # MAX                  1  43
        Result += RangesHistogram(AbortedCubeSpecBits, 10).getRanges(1)[1:]  # RangesHistogram of SpecBits    9 44-52
        Result.append(sum(AbortedCubeSpecBits))          # Used encoding capacity SUM      1  53
        ### Dynamic compaction ################
        Result.append(self.getDynamicCompactionAddedCells())   # Added scan cells SUM     1  54
        Result.append(List.Avg(DynCompPerPattern))      # per pattern AVG       1  55
        Result.append(List.StdDev(DynCompPerPattern))   # per pattern STD DEV   1  56
        Result.append(min(DynCompPerPattern + [0]))     # per pattern MIN       1  57
        Result.append(max(DynCompPerPattern + [0]))     # per pattern MAX       1  58
        Result += RangesHistogram(DynCompPerPattern, 10).getRanges(1)[1:]  # per pattern RangesHistogram    9 59-67
        Result.append(sum(self.getDynamicCompactionAdddedFaultsData()))  # Added faults SUM    1  68
        ### Patterns ##########################
        Result.append(len(PatternSpecBits))             # Count                 1  69
        Result.append(List.Avg(PatternSpecBits))        # AVG                   1  70
        Result.append(List.StdDev(PatternSpecBits))     # STD DEV               1  71
        Result.append(min(PatternSpecBits + [0]))     # per pattern MIN         1  72
        Result.append(max(PatternSpecBits + [0]))     # per pattern MAX         1  73
        Result += RangesHistogram(PatternSpecBits, 10).getRanges(1)[1:]  # per pattern RangesHistogram      9 74-82
        ### ATPG, EDT #########################
        Result.append(self.getTestDataVolume())         # Test data volume      1  83
        Result.append(self.getTestTime())               # Test time             1  84
        Result.append(DI.get("EdtAborts", 0))           # EDT Aborts            1  85
        Result.append(DI.get("AtpgAborts", 0))          # ATPG Aborts           1  86
        Result.append(DI.get("TestCoverage", 0))        # Test coverage         1  87
        ### Estimate point #####################
        if EstimatedLfsrLen is not None and EstimatedChannels is not None:
            EstEdt : EdtStructure = Edt.copy()
            EstEdt.setLfsrs(EstimatedLfsrLen)
            EstEdt.setInputCount(EstimatedChannels)
            Result.append(EstimatedChannels)            # Estimated #Channels
            Result.append(EstimatedLfsrLen)             # Estimated LFSR size
            Result.append(EstEdt.getCompressionRatio()) # Estimated Compression ratio
            Result.append(EstEdt.getEncodingCapacity()) # Estimated Encoding capacity
        return Result
        
        


class TestCubeSetUtils:
    
    preparseLogs = DecompressorUtils.preparseLogs
    
    @staticmethod
    def adaptiveSearchForTemplates(Cubes : TestCubeSet, MinTemplateCount : int = 3, MaxTemplateCount : int = 6, Step : float = 0.00005, MultiThreading : bool = True, CustomCubesForAnalysis : TestCubeSet = None) -> TestCubeSet:
        Span = (0.2+Step)
        Limit = Step + Span
        BestMin = Limit
        print(f"BestMin: {BestMin}, Templates: ?")
        BestFromMaxDistance = len(Cubes)
        CommonCubes = Cubes._tryToExtrctTemplates_phase1(64, False, CustomCubesForAnalysis)
        while Span >= Step * 0.5:
            print(f"Limit: {Limit}...")
            t = Cubes._tryToExtrctTemplates_phase2(CommonCubes, Limit, 1)
            AioShell.removeLastLine()
            if len(t) > MinTemplateCount:
                if abs(MaxTemplateCount - len(t)) < BestFromMaxDistance:
                    BestFromMaxDistance = abs(MaxTemplateCount - len(t))
                    BestMin = Limit
                    AioShell.removeLastLine()
                    print(f"BestMin: {BestMin}, Templates: {len(t)}")
            if len(t) < MaxTemplateCount:
                Limit -= Span
            elif len(t) > MaxTemplateCount:
                Limit += Span
            if Limit < 0:
                Limit = 0
            Span *= 0.51
        Span = (1-BestMin)
        Limit = 1    
        BestMax = Limit
        Middle = (MaxTemplateCount + MinTemplateCount) / 2
        BestFromMiddleDistance = len(Cubes)
        print(f"BestMax: {BestMax}, Templates: ?")
        while Span >= Step * 0.5:
            print(f"Limit: {Limit}...")
            t = Cubes._tryToExtrctTemplates_phase2(CommonCubes, BestMin, Limit)
            AioShell.removeLastLine()
            if abs(Middle - len(t)) <= BestFromMiddleDistance:
                BestFromMiddleDistance = abs(Middle - len(t))
                BestMax = Limit
                AioShell.removeLastLine()
                print(f"BestMax: {BestMax}, Templates: {len(t)}")
            if len(t) > Middle:
                Limit -= Span
            elif len(t) < Middle:
                Limit += Span
            if Limit < 0:
                Limit = 0
            Span *= 0.51
        return Cubes.tryToExtractTemplates(64, BestMin, BestMax, False, CustomCubesForAnalysis)
    
    @staticmethod
    def getBufferSizeListFromFile(FileName : str) -> list:
        if type(FileName) is not str:
            Result = p_map(TestCubeSetUtils.getBufferSizeListFromFile, FileName)
            AioShell.removeLastLine()
            return Result
        Result = []
        Cntr = 0
        LastMask = 1
        for Line in Generators().readFileLineByLine(FileName):
            R = re.search(r"mask\s*=\s*([0-9]+)", Line)
            if R:
                Cntr += 1
                Mask = int(R.group(1))
                if int(Mask) == 1 and LastMask != 1:
                    Result.append(Cntr)
                    Cntr = 0
                LastMask = Mask
        return Result
    
    @staticmethod
    def getBufferDebugData(FileName : str) -> AioTable:
        Result = AioTable(["Mask", "No. Cubes", "Remaining"])
        NumCubes = None
        Remaining = None
        Mask = None
        def write():
            Result.add([Mask, NumCubes, Remaining])
        for Line in Generators().readFileLineByLine(FileName):
            R = re.search(r"pattern\s*=\s*([0-9]+)\s*mask\s*=\s*([0-9]+)", Line)
            if R:
                Mask = int(R.group(2))
                write()
                continue
            R = re.search(r"num_test_cubes\s*[:=]\s*([0-9]+)", Line)
            if R:
                NumCubes = int(R.group(1))
                continue
            R = re.search(r"here\s*are\s*([0-9]+)\s*remaining", Line)
            if R:
                Remaining = int(R.group(1))
                continue
        return Result
    
    @staticmethod
    def getBufferDebugDataForManyDesigns(FileNames : list) -> AioTable:
        Result = AioTable([FileName for FileName in FileNames])
        Data = []
        def single(FileName):
            SingleRes = []
            NumCubes = None
            Remaining = None
            Mask = None
            def write():
                SingleRes.append(NumCubes)
            for Line in Generators().readFileLineByLine(FileName):
                #R = re.search(r"pattern\s*=\s*([0-9]+)\s*mask\s*=\s*([0-9]+)", Line)
                #if R:
                #    Mask = int(R.group(2))
                #    write()
                #    continue
                R = re.search(r"num_test_cubes\s*[:=]\s*([0-9]+)", Line)
                if R:
                    NumCubes = int(R.group(1))
                    write()
                    continue
                #R = re.search(r"here\s*are\s*([0-9]+)\s*remaining", Line)
                #if R:
                #    Remaining = int(R.group(1))
                #    continue
            return SingleRes
        MaxLen = 0
        for R in p_imap(single, FileNames):
            Data.append(R)
            if len(R) > MaxLen:
                MaxLen = len(R)
        AioShell.removeLastLine()
        for i in range(MaxLen):
            Row = []
            for D in Data:
                try:
                    Row.append(D[i])
                except:
                    Row.append("")
            Result.add(Row)
        return Result
    
    @staticmethod
    def getCubeStats(Cubes : TestCubeSet) -> AioTable:
        Result = AioTable(["CUbeId", "BaseCube", "PatternId", "SpecifiedBits"])
        PatternIds = set()
        for Cube in Cubes:
            Pid = Cube.PatternId
            BaseCube = 0
            if Pid not in PatternIds:
                PatternIds.add(Pid)
                BaseCube = 1
            Result.add([Cube.Id, BaseCube, Pid, Cube.getSpecifiedCount()])
        return Result
    
    
class ScanCellsStructure:
    
    __slots__ = ("ScanChainLength", "ScanCount", "_scan_len_dict", "_missing_dict")
    
    def __init__(self, ScanCount : int, ScamChainLength : int):
        self.ScanChainLength = ScamChainLength
        self.ScanCount = ScanCount
        self._scan_len_dict = {i: ScamChainLength for i in range(ScanCount)}
        self._missing_dict = None
        
    def copy(self) -> ScanCellsStructure:
        Result = ScanCellsStructure(self.ScanCount, self.ScanChainLength)
        Result._scan_len_dict = self._scan_len_dict.copy()
        if self._missing_dict is not None:
            Result._missing_dict = self._missing_dict.copy()
        return Result
        
    def __repr__(self) -> str:
        return f"ScanChainStructure({self.ScanChainLength}, {self.ScanCount})"
    
    def __str__(self) -> str:
        return self.__repr__() + f"\n{self._scan_len_dict}"
        
    @staticmethod
    def fromFile(FileName : str) -> ScanCellsStructure:
        ResDict = {}
        ScanLen = 0
        ScanCount = 0
        for Line in Generators().readFileLineByLine(FileName):
            R = re.search(r'Chain\s*=.*chain([0-9]+).*cells\s*[:=]\s*([0-9]+)', Line)
            if R:
                ResDict[int(R.group(1))-1] = int(R.group(2))
                continue
            R = re.search(r'Longest\s*scan\s*chain\s*has\s*([0-9]+).*cells', Line)
            if R:
                ScanLen = int(R.group(1))
                ScanCount = len(ResDict)
                break
        Result = ScanCellsStructure(ScanCount, ScanLen)
        Result._scan_len_dict = ResDict
        return Result
    
    def getMissingCellsDict(self) -> dict:
        if self._missing_dict is None:
            self._missing_dict = {i: self.ScanChainLength - v for i, v in self._scan_len_dict.items()}
        return self._missing_dict.copy()
    
    def getStructureDrawing(self) -> str:
        from libs.asci_drawing import AsciiDrawing_Characters
        Lines = []
        for Scan in range(self.ScanCount-1, -1, -1):
            Line = AsciiDrawing_Characters.EMPTY_RECTANGLE * self._scan_len_dict[Scan]
            if len(Line) < self.ScanChainLength:
                Line = "-" * (self.ScanChainLength - len(Line)) + Line
            Line = Str.toRight(f"{Scan}:|", 6) + Line + "|"
            Lines.append(Line)
        return "\n".join(Lines)
        
    def printStructure(self):
        Aio.print(self.getStructureDrawing())
        
    def getScanChainCount(self, ScanIndex : int) -> int:
        if ScanIndex in self._scan_len_dict:
            return self._scan_len_dict[ScanIndex]
        return None
    
    def __getitem__(self, index : int) -> int:
        if type(index) is slice:
            start, stop, step = index.start, index.stop, index.step
            Result = [self.getScanChainCount(i) for i in range(start, stop, step)]
            return Result
        return self.getScanChainCount(index)
    
    def getScanChainCOunt(self) -> int:
        return self.ScanCount
    
    def getScanChainLength(self) -> int:
        return self.ScanChainLength
    
    
class PatternCountComprensator:
    
    __slots__ = ('_patterns', '_uncompressable', 'UncompressableCubeUsedOnlyOnce')
    
    def __init__(self, Patterns : TestCubeSet, UncompressableCubes : TestCubeSet, UncompressableCubeUsedOnlyOnce : bool = True):
        self._patterns = Patterns
        self._uncompressable = UncompressableCubes
        self.UncompressableCubeUsedOnlyOnce = bool(UncompressableCubeUsedOnlyOnce)
    
    def __repr__(self) -> str:
        return f"MergingResultsComprensator({len(self._patterns)}, {len(self._uncompressable)})"
    
    def __str__(self) -> str:
        return self.__repr__() + f"\nPatterns: {self._patterns}\nUncompressable: {self._uncompressable}"
    
    def getRawPatternCount(self) -> int:
        return len(self._patterns)
    
    def getUncompressableCubesCount(self) -> int:
        return len(self._uncompressable)
    
    def getUncompressableCubesIds(self) -> list:
        return [i.Id for i in self._uncompressable]
    
    def getCubePatternPairs(self) -> list:
        """Returns list of tuples (Cube, Pattern)"""
        Result = []
        for i in self._patterns:
            for j in i.SubCubesIds:
                Result.append((j, i))
        for i in self._uncompressable:
            Result.append((i, None))
        Result.sort(key=lambda x: x[0].Id)
        return Result
    
    def getPatternCubesUncompressableTriplet(self) -> list:
        """Returns list of tuples (Pattern, SubCubeCount, SubCUbesIdSpan, UncompressableCubesCount)"""
        UncompressableIds = set(self.getUncompressableCubesIds())
        Result = []
        for i in self._patterns:
            IdMin = min(i.SubCubesIds)
            IdMax = max(i.SubCubesIds)
            Span = IdMax - IdMin + 1 
            UCubes = [j for j in range(IdMin, IdMax+1) if j in UncompressableIds]
            Result.append((i, len(i.SubCubesIds), Span, len(UCubes)))
            if self.UncompressableCubeUsedOnlyOnce:
                for j in UCubes:
                    UncompressableIds.remove(j)
        return Result
    
    def toTable(self) -> AioTable:
        """Returns table with 4 columns: Pattern, SubCubesCount, UncompressableCubesCount"""
        Result = AioTable(["Pattern", "SubCubesCount", "SubCUbesIdSpan", "UncompressableCubesCount"])
        for i in self.getPatternCubesUncompressableTriplet():
            Result.add([i[0], i[1], i[2], i[3]])
        return Result
    
    def getCompensatedPatternCount(self) -> int:
        Data = self.getPatternCubesUncompressableTriplet()
        Sum = 0.0
        for Row in Data:
            Sum += 1 + Row[3] / Row[1]
        return int(Sum)
    
    def getCompensationAdderPerPattern(self, Cumulative : bool = True) -> list:
        Data = self.getPatternCubesUncompressableTriplet()
        Result = []
        Value = 0
        for Row in Data:
            if Cumulative:
                Value += Row[3] / Row[1]
            else:
                Value = Row[3] / Row[1]
            Result.append(Value)
        return Result
        