from libs.aio import *
from bitarray import *
import bitarray.util as bau
from random import *
from copy import deepcopy
from math import ceil
from functools import partial
from p_tqdm import *


class TestDataDecompressor:
    pass
class TestCube:
    pass
class TestCubeSet:
    pass
class EdtStructure:
    pass

class TestDataDecompressor:
    
    __slots__ = ('InputCount', 'OutputCount', 'LfsrLength', 'ScanLength')
    
    def __init__(self, InputCount : int, OutputCount : int, LfsrLength : int, ScanLength :  int):
        self.InputCount = InputCount
        self.OutputCount = OutputCount
        self.LfsrLength = LfsrLength
        if type(ScanLength) is int:
            self.ScanLength = ScanLength
        elif type(ScanLength) is TestCube:
            self.ScanLength = int(ceil(len(ScanLength) / OutputCount))
            
    def __repr__(self) -> str:
        return f"TestDataDecompressor({self.InputCount}, {self.OutputCount}, {self.LfsrLength}, {self.ScanLength})"
        
    def __str__(self) -> str:
        return f"InputCount={self.InputCount}, OutputCount={self.OutputCount}, LfsrLength={self.LfsrLength}, ScanLength={self.ScanLength}"
        
    def getSpecifiedBitPerCycleDict(self, Cube : TestCube) -> dict:
        Result = {}
        TCPos = Cube.getSpecifiedBitPositions()
        for Pos in TCPos:
            PosInScan = Pos % self.ScanLength
            Result[PosInScan] = Result.get(PosInScan, 0) + 1
        return Result
    
    def getMaximumSpecifiedBitPerCycleToBeCompressable(self) -> int:
        return int(self.LfsrLength + ((self.ScanLength - 1) * self.InputCount))
    
    def getMaximumCubeBitsPerDecompressor(self) -> int:
        return int(self.OutputCount * self.ScanLength)
    
    def isCompressable(self, Cube, MinBatteryCharge : float = 0.1) -> bool:
        SpecifiedBitsPerCycle = self.getSpecifiedBitPerCycleDict(Cube)
        if Cube.getSpecifiedCount() > self.getMaximumSpecifiedBitPerCycleToBeCompressable():
            return False
        # Battery model
        BatteryChrg = self.LfsrLength
        for i in range(self.ScanLength):
            Vars = SpecifiedBitsPerCycle.get(i, 0)
            if Vars > self.LfsrLength:
                return False                
            BatteryChrg -= Vars
            MinChrg = int(ceil(MinBatteryCharge * BatteryChrg))
            if BatteryChrg < MinChrg:
                return False
            BatteryChrg += self.InputCount
        return True


class EdtStructure:
    
    __slots__ = ('_decompressors', '_scan_len')
    
    def __init__(self, Decompressors : list = None):
        self._decompressors = []
        self._scan_len = 0
        if type(Decompressors) is list:
            for Decompressor in Decompressors:
                self.addDecompressor(Decompressor)
        if type(Decompressors) is TestDataDecompressor:
            self.addDecompressor(Decompressors)
                
    def __len__(self) -> int:
        return len(self._decompressors)
    
    def __repr__(self) -> str:
        return f"EdtStructure({self._decompressors})"
    
    def __str__(self):
        Result = "["
        Second = 0
        for Decompressor in self._decompressors:
            if Second:
                Result += ", "
            else:
                Second = 1
            Result += str(Decompressor)
        Result += "]"
        return Result
                
    def getScanLength(self) -> int:
        return self._scan_len
    
    def getDecompressorCount(self) -> int:
        return len(self._decompressors)
    
    def getInputCount(self) -> int:
        return sum([Decompressor.InputCount for Decompressor in self._decompressors])
    
    def getScanChainCount(self) -> int:
        return sum([Decompressor.OutputCount for Decompressor in self._decompressors])
    
    def getFFCount(self) -> int:
        return sum([Decompressor.LfsrLength for Decompressor in self._decompressors])
    
    def getMaximumSpecifiedBitPerCycleToBeCompressable(self) -> int:
        return max([Decompressor.getMaximumSpecifiedBitPerCycleToBeCompressable() for Decompressor in self._decompressors])
    
    def getCubeBitsPerDecompressor(self) -> list:
        return [Decompressor.getMaximumCubeBitsPerDecompressor() for Decompressor in self._decompressors]
        
    def addDecompressor(self, Decompressor : TestDataDecompressor) -> bool:
        if self._scan_len == 0:
            self._scan_len = Decompressor.ScanLength
        elif Decompressor.ScanLength != self._scan_len:
            Aio.printError(f"Decompressor ScanLength must be {self._scan_len}.")
            return False
        self._decompressors.append(Decompressor)
        return True
    
    def isCompressable(self, Cube : TestCube, MinBatteryCharge : float = 0.1) -> bool:
        if Cube.getSpecifiedCount() > self.getMaximumSpecifiedBitPerCycleToBeCompressable():
            return False
        SubCubes = Cube.splitIntoSubCubes(self.getCubeBitsPerDecompressor())
        for i in range(len(self._decompressors)):
            if not self._decompressors[i].isCompressable(SubCubes[i], MinBatteryCharge):
                return False
        return True
    
    def getLongestLfsrSize(self) -> int:
        try:
            return max([Decompressor.LfsrLength for Decompressor in self._decompressors])   
        except:
            return 0
        
    def getTestTime(self, PatternCount : int = 1) -> int:
        Init = 0
        for Decompressor in self._decompressors:
            ThisInit = int(ceil(Decompressor.LfsrLength / Decompressor.InputCount))
            if Init <= ThisInit:
                Init = ThisInit
        return (Init + self.getScanLength()) * PatternCount
    
    def getTestDataVolume(self, PatternCount : int = 1) -> int:
        return self.getTestTime(PatternCount) * self.getInputCount()
        
        
    

class TestCube:
    
    __slots__ = ('_specified_bit_dict', '_len', "Age")
        
    @staticmethod
    def randomCube(Length : int, Pspecified : float = 0.1, P1 = 0.5) -> TestCube:
        SDict = {}
        Count = randint(1, Pspecified*Length*2)
        for i in range(Count):
            SDict[randint(0, Length-1)] = 1 if random() < P1 else 0
        return TestCube(SDict, Length)
    
    def __init__(self, SpecifiedBits : str = '', TestCubeLen : int = 0):
        self._specified_bit_dict = {}
        self._len = TestCubeLen
        self.Age = 0
        if type(SpecifiedBits) is str:
            self.setBits(SpecifiedBits)
        elif type(SpecifiedBits) is dict:
            self.setBits(SpecifiedBits, TestCubeLen)
        elif type(SpecifiedBits) is int:
            self._len = SpecifiedBits
        elif type(SpecifiedBits) is TestCube:
            self._specified_bit_dict = deepcopy(SpecifiedBits._specified_bit_dict)
            self._len = deepcopy(SpecifiedBits._len)
            self.Age = SpecifiedBits.Age
            
    def __len__(self):
        return self._len
    
    def __str__(self):
        return f"AGE={self.Age} " + str(self._specified_bit_dict)
    
    def __repr__(self):
        return f"TestCube(\"{str(self)}\")"
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step
            if step is not None:
                Aio.printError("Step is not supported.")
                return None
            Result = TestCube(stop - start - 1)
            Result._specified_bit_dict = {i-start: self._specified_bit_dict[i] for i in range(start, stop) if i in self._specified_bit_dict}
            return Result
        else:
            return self.getBit(index)
    
    def __setitem__(self, index, value):
        self.setBit(index, value)
        
    def getSpecifiedScanCellValues(self, ScanCount : int, ScanLength : int) -> list:
        Result = []
        for item in self._specified_bit_dict.items():
            Index = item[0]
            Value = item[1]
            Cycle = Index % ScanLength
            Scan = Index // ScanLength
            if Scan < ScanCount:
                Result.append([Scan, Cycle, Value])
            else:
                Aio.printError(f"Scan index {Scan} is out of range.")
        return Result
    
    def splitIntoSubCubes(self, SubCubesLen : list) -> list:
        Result = []
        Start = 0
        for SCLen in SubCubesLen:
            Stop = Start + SCLen
            Result.append(self[Start:Stop])
            Start = Stop
        return Result
    
    def setBits(self, SpecifiedBits : str, TestCubeLenIfDictImplementation : int = 0):
        # 0, 1 - values
        # X - don't care
        if type(SpecifiedBits) is dict:
            self._specified_bit_dict = SpecifiedBits
            self._len = TestCubeLenIfDictImplementation
        else:
            SpecifiedBits = SpecifiedBits.upper()
            for i in range(len(SpecifiedBits)):
                if SpecifiedBits[i] == '0':
                    self._specified_bit_dict[i] = 0
                elif SpecifiedBits[i] == '1':
                    self._specified_bit_dict[i] = 1
            self._len = len(SpecifiedBits)
                
    def getFillRate(self) -> float:
        return len(self._specified_bit_dict) / len(self)
        
    def getSpecifiedBitPositions(self) -> list:
        return list(self._specified_bit_dict.keys())
        
    def copy(self) -> TestCube:
        Result = TestCube(self)
        return Result
        
    def mergeWithAnother(self, AnotherCute : TestCube) -> bool:
        if len(self) != len(AnotherCute):
            return False
        Result = self._specified_bit_dict.copy()
        for item in AnotherCute._specified_bit_dict.items():
            if Result.get(item[0], None) is not None:
                if Result[item[0]] != item[1]:
                    return False
            else:
                Result[item[0]] = item[1]
        self._specified_bit_dict = Result
        return True
    
    def setBit(self, BitIndex : int, BitValue : str) -> bool:
        if BitIndex >= len(self):
            return False
        if BitValue in [0, '0']:
            self._specified_bit_dict[BitIndex] = 0
        elif BitValue in [1, '1']:
            self._specified_bit_dict[BitIndex] = 1
        else:
            del self._specified_bit_dict[BitIndex]
        return True
    
    def getBit(self, BitIndex : int) -> int:
        if BitIndex >= len(self):
            return -1
        if self._specified_bit_dict.get(BitIndex, None) is not None:
            return self._specified_bit_dict[BitIndex]
        else:
            return -1
            
    def getSpecifiedCount(self) -> int:
        return len(self._specified_bit_dict)
            
    
class TestCubeSet:
    
    __slots__ = ('_cubes')
    
    def __init__(self):
        self._cubes = []
        
    def __len__(self):
        return len(self._cubes)
    
    def __str__(self):
        Result = ""
        for Cube in self._cubes:
            Result += str(Cube) + "\n"
        return Result
    
    def __repr__(self):
        return "TestCubeSet()"
    
    def __getitem__(self, index) -> TestCube:
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step
            Result = TestCubeSet()
            Result._cubes = self._cubes[start:stop:step]
            return Result
        else:
            return self._cubes[index]
        
    @staticmethod
    def randomCubeSet(CubeCount : int, Length : int, Pspecified : float = 0.1, P1 = 0.5) -> TestCubeSet:
        Result = TestCubeSet()
        def single(args):
            return TestCube.randomCube(Length, Pspecified, P1)
        for C in p_uimap(single, range(CubeCount), desc="Generating random cubes"):
            Result.addCube(C)
        AioShell.removeLastLine()
        return Result
    
    def addCube(self, Cube : TestCube):
        self._cubes.append(Cube)
    
    def addRandomCubes(self, Count : int, CubeLen : int, Pspecified : float = 0.1, P1 = 0.5):
        for i in range(Count):
            self.addCube(TestCube.randomCube(CubeLen, Pspecified, P1))
    
    def copy(self) -> TestCubeSet:
        Result = TestCubeSet()
        Result._cubes = self._cubes.copy()
        return Result
    
    def deepCopy(self) -> TestCubeSet:
        Result = TestCubeSet()
        for Cube in self._cubes:
            Result._cubes.append(Cube.copy())
        return Result
    
    def resetAge(self):
        for Cube in self._cubes:
            Cube.Age = 0

    def sort(self):
        self._cubes.sort(key = lambda x: x.Age, reverse = True)

    def removeCube(self, CubeIndex : int) -> bool:
        try:
            del self._cubes[CubeIndex]
            return True
        except:
            return False
    
    def autoMerge(self, PreSort : bool = True):
        pass
    
    def getCube(self, index : int) -> TestCube:
        return self._cubes[index]
    
    def getSubCubeSets(self, SubSetSize : int) -> list:
        Result = []
        for i in range(0, len(self), SubSetSize):
            TestCubeSubset = TestCubeSet()
            TestCubeSubset._cubes = self._cubes[i:i+SubSetSize]
            Result.append(TestCubeSubset)
        return Result
    
    def _mergingRound(self, Edt : EdtStructure, PatternCount : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 3, Verbose : bool = False) -> tuple:
        """Returns two TestCubeSet objects: (Patterns, Cubes)."""
        Cubes = self.copy()
        Patterns = TestCubeSet()
        MaximumBitCount = Edt.getMaximumSpecifiedBitPerCycleToBeCompressable()
        while len(Cubes) > 0 and len(Patterns) < PatternCount:
            #Cubes.sort()
            Cube = Cubes.getCube(0)
            ToBeRemovedFromBuffer = [0]
            CompressionCounter = 0
            for i in range(1, len(Cubes)):
                CubeAux = Cube.copy()
                MergingResult = CubeAux.mergeWithAnother(Cubes._cubes[i])
                if MergingResult: 
                    if Edt.isCompressable(CubeAux, MinBatteryCharge):
                        Cube = CubeAux
                        ToBeRemovedFromBuffer.append(i)
                        if Cube.getSpecifiedCount()-1 >= MaximumBitCount:
                            break
                    else:
                        CompressionCounter += 1
                        if CompressionCounter > CompressabilityLimit:
                            break
                #else:
                #    Cubes._cubes[i].Age += 1
            Patterns._cubes.append(Cube)
            for i in reversed(ToBeRemovedFromBuffer):
                del Cubes._cubes[i]
        return Patterns, Cubes
    
    def merge(self, Edt : EdtStructure, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 3, Verbose : bool = False) -> TestCubeSet:
        #self.resetAge()
        Buffer = TestCubeSet()
        if type(BufferLength) is int:
            BufferLength = [BufferLength]
        if len(BufferLength) < 1:
            BufferLength = [512]
        Buffer._cubes = self._cubes[0:BufferLength[0]]
        index = BufferLength[0]
        Patterns, Buffer = Buffer._mergingRound(Edt, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose)
        BufferLenIndex = 0
        if Verbose:
            print(f"Furst round finished. BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        while index < len(self):
            BufferLenIndex += 1
            if BufferLenIndex >= len(BufferLength):
                BufferLenIndex = -1
            HowManyToAdd = BufferLength[BufferLenIndex] - len(Buffer)
            Buffer._cubes += self._cubes[index:index+HowManyToAdd]
            index += HowManyToAdd
            SubPatterns, Buffer = Buffer._mergingRound(Edt, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose)
            Patterns._cubes += SubPatterns._cubes
            if Verbose:
                print(f"Next round finished. BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        if len(Buffer) > 0:
            SubPatterns, Buffer = Buffer._mergingRound(Edt, len(Buffer), MinBatteryCharge, CompressabilityLimit, Verbose)
            Patterns._cubes += SubPatterns._cubes
            if Verbose:
                print(f"Last. BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        if Verbose:
            print(f"FINISHED BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        return Patterns
    
    def removeNotCompressable(self, Edt : EdtStructure) -> int:
        ToBeRemoved = []
        for i in range(len(self)):
            if not Edt.isCompressable(self.getCube(i)):
                ToBeRemoved.append(i)
        for i in reversed(ToBeRemoved):
            self.removeCube(i)
        return len(ToBeRemoved)
    
    @staticmethod
    def doExperiment(Cubes : TestCubeSet, Edt : EdtStructure, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 3, Verbose : bool = False) -> tuple:
        CubesCopy = Cubes.deepCopy()
        BeforeRemovalCubesCount = len(CubesCopy)
        if Verbose:
            Aio.print(f"#Cubes before uncompressable removal: {BeforeRemovalCubesCount}")
        RemovedCount = CubesCopy.removeNotCompressable(Edt)
        AfterRemovalCubesCount = len(CubesCopy)
        if Verbose:
            Aio.print(f"#Cubes removed:                       {RemovedCount}")
            Aio.print(f"#Cubes after uncompressable removal:  {AfterRemovalCubesCount}")
        Patterns = CubesCopy.merge(Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose)
        TestTime = Edt.getTestTime(len(Patterns))
        TestDataVolume = Edt.getTestDataVolume(len(Patterns))
        if Verbose:
            Aio.print(f"#Patterns:                            {len(Patterns)}")
            Aio.print(f"Test time [cycles]:                   {TestTime}")
            Aio.print(f"Test data volume [b]:                 {TestDataVolume}")
        return AfterRemovalCubesCount, len(Patterns), TestTime, TestDataVolume
        
    @staticmethod
    def doExperiments(Cubes : TestCubeSet, EdtList : list, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 3) -> list:
        Result = []
        def singleTry(Edt : EdtStructure) -> tuple:
            return TestCubeSet.doExperiment(Cubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, False)
        for R in p_imap(singleTry, EdtList):
            Result.append(R)
        AioShell.removeLastLine()
        return Result
    

