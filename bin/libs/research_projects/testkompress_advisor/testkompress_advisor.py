from libs.aio import *
from bitarray import *
import bitarray.util as bau
from random import *
from copy import deepcopy
from math import ceil
from functools import partial
from p_tqdm import *

_TEST_CUBE_BITARRAYS = 0
_TEST_CUBE_IMPLEMENTATION_LOCKED = 0


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
        MinChrg = int(ceil(MinBatteryCharge * self.LfsrLength))
        BatteryChrg = self.LfsrLength
        for i in range(self.ScanLength):
            BatteryChrg -= SpecifiedBitsPerCycle.get(i, 0)
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
        for Decompressor in self._decompressors:
            Result += str(Decompressor) + "\n"
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
        
        
    

class TestCube:
    
    __slots__ = ('_specified_bit_positions', '_specified_bit_values', "Age")
    
    @staticmethod
    def seImplementation(UseBitarrays : bool = True) -> bool:
        global _TEST_CUBE_BITARRAYS, _TEST_CUBE_IMPLEMENTATION_LOCKED
        if _TEST_CUBE_IMPLEMENTATION_LOCKED:
            Aio.printError("Cannot change TestCube implementation. You can do that before first TestCube object creation.")
            return False
        _TEST_CUBE_BITARRAYS = UseBitarrays
        return True
    
    @staticmethod
    def randomCube(Length : int, Pspecified : float = 0.1, P1 = 0.5) -> TestCube:
        global _TEST_CUBE_BITARRAYS
        if _TEST_CUBE_BITARRAYS:
            StrVal = ""
            for i in range(Length):
                if random() < Pspecified:
                    StrVal += '1' if random() < P1 else '0'
                else:
                    StrVal += 'X'
            return TestCube(StrVal)
        else:
            SDict = {}
            for i in range(Length):
                if random() < Pspecified:
                    SDict[i] = 1 if random() < P1 else 0
            return TestCube(SDict, Length)
    
    def __init__(self, SpecifiedBits : str = '', LenOfTestCubeIfDictImplementation : int = 0):
        global _TEST_CUBE_BITARRAYS, _TEST_CUBE_IMPLEMENTATION_LOCKED
        _TEST_CUBE_IMPLEMENTATION_LOCKED = 1
        if _TEST_CUBE_BITARRAYS:
            self._specified_bit_positions = bitarray()
            self._specified_bit_values = bitarray()
        else:
            self._specified_bit_positions = {}
            self._specified_bit_values = LenOfTestCubeIfDictImplementation
        self.Age = 0
        if type(SpecifiedBits) is str:
            self.setBits(SpecifiedBits)
        elif type(SpecifiedBits) is dict:
            self.setBits(SpecifiedBits, LenOfTestCubeIfDictImplementation)
        elif type(SpecifiedBits) is int:
            if _TEST_CUBE_BITARRAYS:
                self._specified_bit_positions = bau.zeros(SpecifiedBits)
                self._specified_bit_values = bau.zeros(SpecifiedBits)
            else:
                self._specified_bit_values = SpecifiedBits
        elif type(SpecifiedBits) is TestCube:
            self._specified_bit_positions = deepcopy(SpecifiedBits._specified_bit_positions)
            self._specified_bit_values = deepcopy(SpecifiedBits._specified_bit_values)
            self.Age = SpecifiedBits.Age
            
    def __len__(self):
        global _TEST_CUBE_BITARRAYS
        if _TEST_CUBE_BITARRAYS:
            return len(self._specified_bit_positions)
        return self._specified_bit_values
    
    def __str__(self):
        global _TEST_CUBE_BITARRAYS
        if _TEST_CUBE_BITARRAYS:
            Result = f"AGE={self.Age} "
            for i in range(len(self._specified_bit_positions)):
                if not self._specified_bit_positions[i]:
                    Result += 'X'
                else:
                    Result += str(int(self._specified_bit_values[i]))
            return Result
        else:
            return f"AGE={self.Age} " + str(self._specified_bit_positions)
    
    def __repr__(self):
        return f"TestCube(\"{str(self)}\")"
    
    def __getitem__(self, index):
        global _TEST_CUBE_BITARRAYS
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step
            if step is not None:
                Aio.printError("Step is not supported.")
                return None
            if _TEST_CUBE_BITARRAYS:
                Result = TestCube()
                Result._specified_bit_positions = self._specified_bit_positions[start:stop]
                Result._specified_bit_values = self._specified_bit_values[start:stop]
                return Result
            else:
                Result = TestCube(stop - start - 1)
                Result._specified_bit_positions = {i-start: self._specified_bit_positions[i] for i in range(start, stop) if i in self._specified_bit_positions}
                return Result
        else:
            return self.getBit(index)
    
    def __setitem__(self, index, value):
        self.setBit(index, value)
    
    def splitIntoSubCubes(self, SubCubesLen : list) -> list:
        Result = []
        Start = 0
        for SCLen in SubCubesLen:
            Stop = Start + SCLen
            Result.append(self[Start:Stop])
            Start = Stop
        return Result
    
    def setBits(self, SpecifiedBits : str, TestCubeLenIfDictImplementation : int = 0):
        global _TEST_CUBE_BITARRAYS
        # 0, 1 - values
        # X - don't care
        if _TEST_CUBE_BITARRAYS:
            if type(SpecifiedBits) is dict:
                self._specified_bit_positions = bau.zeros(TestCubeLenIfDictImplementation)
                self._specified_bit_values = bau.zeros(TestCubeLenIfDictImplementation)
                for item in SpecifiedBits.items():
                    self._specified_bit_positions[item[0]] = 1
                    self._specified_bit_values[item[0]] = item[1]
            else:
                SpecifiedBits = SpecifiedBits.upper()
                ValuesStr = SpecifiedBits.replace('X', '0')
                SpecifiedStr = SpecifiedBits.replace('0', '1')
                SpecifiedStr = SpecifiedStr.replace('X', '0')
                self._specified_bit_positions = bitarray(SpecifiedStr)
                self._specified_bit_values = bitarray(ValuesStr)
        else:
            if type(SpecifiedBits) is dict:
                self._specified_bit_positions = SpecifiedBits
                self._specified_bit_values = TestCubeLenIfDictImplementation
            else:
                SpecifiedBits = SpecifiedBits.upper()
                for i in range(len(SpecifiedBits)):
                    if SpecifiedBits[i] == '0':
                        self._specified_bit_positions[i] = 0
                    elif SpecifiedBits[i] == '1':
                        self._specified_bit_positions[i] = 1
                self._specified_bit_values = len(SpecifiedBits)
                
    def getFillRate(self) -> float:
        global _TEST_CUBE_BITARRAYS
        if _TEST_CUBE_BITARRAYS:
            return self._specified_bit_positions.count(1) / len(self)
        else:
            return len(self._specified_bit_positions) / len(self)
        
    def getSpecifiedBitPositions(self) -> list:
        global _TEST_CUBE_BITARRAYS
        if _TEST_CUBE_BITARRAYS:
            return [i for i in self._specified_bit_positions.search(1)]
        else:
            return list(self._specified_bit_positions.keys())
        
    def copy(self) -> TestCube:
        Result = TestCube(self)
        return Result
        
    def mergeWithAnother(self, AnotherCute : TestCube) -> bool:
        global _TEST_CUBE_BITARRAYS
        if len(self) != len(AnotherCute):
            return False
        if _TEST_CUBE_BITARRAYS:
            ResPos = bau.zeros(len(self))
            ResVal = bau.zeros(len(self))
            for i in range(len(self)):
                if self._specified_bit_positions[i] and AnotherCute._specified_bit_positions[i]:
                    if self._specified_bit_values[i] != AnotherCute._specified_bit_values[i]:
                        return False
                    ResPos[i] = 1
                    ResVal[i] = self._specified_bit_values[i]
                elif self._specified_bit_positions[i]:
                    ResPos[i] = 1
                    ResVal[i] = self._specified_bit_values[i]
                elif AnotherCute._specified_bit_positions[i]:
                    ResPos[i] = 1
                    ResVal[i] = AnotherCute._specified_bit_values[i]
            self._specified_bit_positions = ResPos
            self._specified_bit_values = ResVal
            return True
        else:
            Result = self._specified_bit_positions.copy()
            for item in AnotherCute._specified_bit_positions.items():
                if Result.get(item[0], None) is not None:
                    if Result[item[0]] != item[1]:
                        return False
                else:
                    Result[item[0]] = item[1]
            self._specified_bit_positions = Result
            return True
    
    def setBit(self, BitIndex : int, BitValue : str) -> bool:
        global _TEST_CUBE_BITARRAYS
        if BitIndex >= len(self):
            return False
        if _TEST_CUBE_BITARRAYS:
            if BitValue in [0, '0']:
                self._specified_bit_positions[BitIndex] = 1
                self._specified_bit_values[BitIndex] = 0
            elif BitValue in [1, '1']:
                self._specified_bit_positions[BitIndex] = 1
                self._specified_bit_values[BitIndex] = 1
            else:
                self._specified_bit_positions[BitIndex] = 0
                self._specified_bit_values[BitIndex] = 0
        else:
            if BitValue in [0, '0']:
                self._specified_bit_positions[BitIndex] = 0
            elif BitValue in [1, '1']:
                self._specified_bit_positions[BitIndex] = 1
            else:
                del self._specified_bit_positions[BitIndex]
        return True
    
    def getBit(self, BitIndex : int) -> int:
        global _TEST_CUBE_BITARRAYS
        if BitIndex >= len(self):
            return -1
        if _TEST_CUBE_BITARRAYS:
            if self._specified_bit_positions[BitIndex]:
                return self._specified_bit_values[BitIndex]
            else:
                return -1
        else:
            if self._specified_bit_positions.get(BitIndex, None) is not None:
                return self._specified_bit_positions[BitIndex]
            else:
                return -1
            
    def getSpecifiedCount(self) -> int:
        global _TEST_CUBE_BITARRAYS
        if _TEST_CUBE_BITARRAYS:
            return self._specified_bit_positions.count(1)
        else:
            return len(self._specified_bit_positions)
            
    
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
    
    def _mergingRound(self, Edt : EdtStructure, PatternCount : int = 64, MinBatteryCharge : float = 0.1, Verbose : bool = False) -> tuple:
        """Returns two TestCubeSet objects: (Patterns, Cubes)."""
        Cubes = self.copy()
        Patterns = TestCubeSet()
        MaximumBitCount = Edt.getMaximumSpecifiedBitPerCycleToBeCompressable()
        while len(Cubes) > 0 and len(Patterns) < PatternCount:
            Cubes.sort()
            Cube = Cubes.getCube(0)
            ToBeRemovedFromBuffer = [0]
            timer0 = time.time()
            for i in range(1, len(Cubes)):
                CubeAux = Cube.copy()
                MergingResult = CubeAux.mergeWithAnother(Cubes._cubes[i])
                if MergingResult and Edt.isCompressable(CubeAux, MinBatteryCharge):
                    Cube = CubeAux
                    ToBeRemovedFromBuffer.append(i)
                    if Cube.getSpecifiedCount()-1 >= MaximumBitCount:
                        break
                else:
                    Cubes._cubes[i].Age += 1
            timer0 = time.time()
            Patterns._cubes.append(Cube)
            for i in reversed(ToBeRemovedFromBuffer):
                del Cubes._cubes[i]
        return Patterns, Cubes
    
    def merge(self, Edt : EdtStructure, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, Verbose : bool = False) -> TestCubeSet:
        self.resetAge()
        Buffer = TestCubeSet()
        Buffer._cubes = self._cubes[0:BufferLength]
        index = BufferLength
        Patterns, Buffer = Buffer._mergingRound(Edt, PatternCountPerRound, MinBatteryCharge, Verbose)
        if Verbose:
            print(f"Furst round finished. BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        while index < len(self):
            HowManyToAdd = BufferLength - len(Buffer)
            Buffer._cubes += self._cubes[index:index+HowManyToAdd]
            index += HowManyToAdd
            SubPatterns, Buffer = Buffer._mergingRound(Edt, PatternCountPerRound, MinBatteryCharge, Verbose)
            Patterns._cubes += SubPatterns._cubes
            if Verbose:
                print(f"Next round finished. BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        if len(Buffer) > 0:
            SubPatterns, Buffer = Buffer._mergingRound(Edt, len(Buffer), MinBatteryCharge, Verbose)
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
    def doExperiment(Cubes : TestCubeSet, Edt : EdtStructure, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, Verbose : bool = False) -> tuple:
        CubesCopy = Cubes.deepCopy()
        BeforeRemovalCubesCount = len(CubesCopy)
        if Verbose:
            print(f"#Cubes before uncompressable removal: {BeforeRemovalCubesCount}")
        RemovedCount = CubesCopy.removeNotCompressable(Edt)
        AfterRemovalCubesCount = len(CubesCopy)
        if Verbose:
            print(f"#Cubes removed:                       {RemovedCount}")
            print(f"#Cubes after uncompressable removal:  {AfterRemovalCubesCount}")
        Patterns = CubesCopy.merge(Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, Verbose)
        TestTime = Edt.getTestTime(len(Patterns))
        if Verbose:
            print(f"#Patterns:                            {len(Patterns)}")
            print(f"Test time [cycles]:                   {TestTime}")
        return AfterRemovalCubesCount, len(Patterns), TestTime
        
    @staticmethod
    def doExperiments(Cubes : TestCubeSet, EdtList : list, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1) -> list:
        Result = []
        def singleTry(Edt : EdtStructure) -> tuple:
            return TestCubeSet.doExperiment(Cubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, False)
        for R in p_imap(singleTry, EdtList):
            Result.append(R)
        AioShell.removeLastLine()
        return Result
    

