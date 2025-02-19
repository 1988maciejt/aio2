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


class TestDataDecompressor:
    pass
class TestCube:
    pass
class TestCubeSet:
    pass
class EdtStructure:
    pass

class TestDataDecompressor:
    
    __slots__ = ('InputCount', 'OutputCount', 'LfsrLength', 'ScanLength', "MinimumBatteryLevel")
    
    def __init__(self, InputCount : int, OutputCount : int, LfsrLength : int, ScanLength :  int, MinBatteryLevel : float = None):
        self.MinimumBatteryLevel = MinBatteryLevel
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
    
    def getTestDataVolume(self) -> int:
        return (self.ScanLength + self.getInitialPhaseLength()) * self.getInputCount()
    
    def getCompressionRatio(self) -> float:
        return self.getPatternLength() / self.getTestDataVolume()
    
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
        BatteryMax = self.LfsrLength
        BatteryMin = int(ceil(MinBatteryCharge * BatteryMax))
        BatteryChrg = BatteryMax
        for i in range(self.ScanLength):
            Vars = SpecifiedBitsPerCycle.get(i, 0)
            BatteryChrg -= Vars
            if BatteryChrg < BatteryMin:
                return False
            BatteryChrg += self.InputCount
            if BatteryChrg > BatteryMax:
                BatteryChrg = BatteryMax
        return True


class EdtStructure:
    
    __slots__ = ('_decompressors', '_scan_len', '_len_sets', "MinimumBatteryLevel")
    
    def __init__(self, Decompressors : list = None, MinBatteryLevel : float = None):
        self.MinimumBatteryLevel = MinBatteryLevel
        self._decompressors = []
        self._scan_len = 0
        self._len_sets = []
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver
        if type(Decompressors) is list:
            for Decompressor in Decompressors:
                self.addDecompressor(Decompressor)
        elif type(Decompressors) in [TestDataDecompressor, DecompressorSolver]:
            self.addDecompressor(Decompressors)
        else:
            Aio.printError(f"Illegal type of decompressor '{type(Decompressor)}'")
                
    def __len__(self) -> int:
        return len(self._decompressors)
    
    def __repr__(self) -> str:
        return f"EdtStructure({self._decompressors})"
    
    @staticmethod
    def fromFile(FileName : str) -> EdtStructure:
        InCount, OutCount, LfsrLen, ScanLen = 0, 0, 0, 0
        Cntr = 0
        Gen = Generators()
        for Line in Generators().readFileLineByLine(FileName):
            if Cntr >= 4:
                Gen.disable()
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
        return EdtStructure(TestDataDecompressor(InCount, OutCount, LfsrLen, ScanLen))
    
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
        return sum([Decompressor.getInputCount() for Decompressor in self._decompressors])
    
    def getScanChainCount(self) -> int:
        return sum([Decompressor.getScanChainCount() for Decompressor in self._decompressors])
    
    def getFFCount(self) -> int:
        return sum([Decompressor.getLfsrLength() for Decompressor in self._decompressors])
    
    def getMaximumSpecifiedBitPerCycleToBeCompressable(self) -> int:
        return max([Decompressor.getMaximumSpecifiedBitPerCycleToBeCompressable() for Decompressor in self._decompressors])
    
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
    
    def isCompressable(self, Cube : TestCube, MinBatteryCharge : float = 0.1) -> bool:
        if Cube.getSpecifiedCount() > self.getMaximumSpecifiedBitPerCycleToBeCompressable():
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
    
    __slots__ = ('_len', '_ones_set', '_zeros_set', '_primary_zeros_set', '_primary_ones_set')
        
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
    
    def __init__(self, SpecifiedBits : str = '', TestCubeLenIfDictImplementation : int = 0):
        self._ones_set = set()
        self._zeros_set = set()
        self._primary_ones_set = set()
        self._primary_zeros_set = set()
        self._len = TestCubeLenIfDictImplementation
        if type(SpecifiedBits) is str and len(SpecifiedBits) > 0:
            self.setBits(SpecifiedBits)
        elif type(SpecifiedBits) is dict:
            self.setBits(SpecifiedBits, TestCubeLenIfDictImplementation)
        elif type(SpecifiedBits) is int:
            self._len = SpecifiedBits
        elif type(SpecifiedBits) is TestCube:
            self._ones_set = SpecifiedBits._ones_set.copy()
            self._zeros_set = SpecifiedBits._zeros_set.copy()
            self._primary_ones_set = SpecifiedBits._primary_ones_set.copy()
            self._primary_zeros_set = SpecifiedBits._primary_zeros_set.copy()
            self._len = SpecifiedBits._len
            
    def __len__(self):
        return self._len
    
    def __str__(self):
        return f"ONES: " + str(self._ones_set) + ", ZEROS: " + str(self._zeros_set) + ", PRIMARY ONES: " + str(self._primary_ones_set) + ", PRIMARY ZEROS: " + str(self._primary_zeros_set)
    
    def __repr__(self):
        return f"TestCube(\"{str(self)}\")"
    
    def __getitem__(self, index):
        if type(index) is slice:
            start, stop, step = index.start, index.stop, index.step
            if step is None:
                step = 1
            Result = TestCube("", self._len)
            AuxSet = set(range(start, stop, step))
            Result._ones_set = self._ones_set & AuxSet
            Result._zeros_set = self._zeros_set & AuxSet
            return Result
        return self.getBit(index)
    
    def __setitem__(self, index, value):
        self.setBit(index, value)
        
    def getSpecifiedScanCellValues(self, ScanCount : int, ScanLength : int) -> list:
        Result = []
        for Index in self._ones_set:
            Cycle = Index % ScanLength
            Scan = Index // ScanLength
            if Scan < ScanCount:
                Result.append([Scan, Cycle, 1])
            else:
                Aio.printError(f"Scan index {Scan} is out of range.")
        for Index in self._zeros_set:
            Cycle = Index % ScanLength
            Scan = Index // ScanLength
            if Scan < ScanCount:
                Result.append([Scan, Cycle, 0])
            else:
                Aio.printError(f"Scan index {Scan} is out of range.")
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
            Split._primary_ones_set = self._primary_ones_set
            Split._primary_zeros_set = self._primary_zeros_set
            Result.append(Split)
            Start = Stop
        return Result
    
    def splitIntoSubCubesBasingOnSets(self, SubCubesLenSets : list) -> list:
        Result = []
        for SCLenSet in SubCubesLenSets:
            TC = TestCube("", len(SCLenSet))
            TC._ones_set = self._ones_set & SCLenSet
            TC._zeros_set = self._zeros_set & SCLenSet
            Result.append(TC)
        return Result
    
    def setBits(self, SpecifiedBits : str, TestCubeLenIfDictImplementation : int = 0):
        # 0, 1 - values
        # X - don't care
        if type(SpecifiedBits) is dict:
            for item in SpecifiedBits.items():
                if item[1]:
                    self._ones_set.add(item[0])
                    try:
                        self._zeros_set.remove(item[0])
                    except:
                        pass
                else:
                    self._zeros_set.add(item[0])
                    try:
                        self._ones_set.remove(item[0])
                    except:
                        pass
            self._len = TestCubeLenIfDictImplementation
        else:
            SpecifiedBits = SpecifiedBits.upper()
            for i in range(len(SpecifiedBits)):
                if SpecifiedBits[i] == '0':
                    self._zeros_set.add(i)
                    try:
                        self._ones_set.remove(i)
                    except:
                        pass
                elif SpecifiedBits[i] == '1':
                    self._ones_set.add(i)
                    try:
                        self._zeros_set.remove(i)
                    except:
                        pass
            self._len = len(SpecifiedBits)
            
    def setPrimaryBits(self, SpecifiedBits : str):
        # 0, 1 - values
        # X - don't care
        if type(SpecifiedBits) is dict:
            for item in SpecifiedBits.items():
                if item[1]:
                    self._primary_ones_set.add(item[0])
                    try:
                        self._primary_zeros_set.remove(item[0])
                    except:
                        pass
                else:
                    self._primary_zeros_set.add(item[0])
                    try:
                        self._primary_ones_set._ones_set.remove(item[0])
                    except:
                        pass
        else:
            SpecifiedBits = SpecifiedBits.upper()
            for i in range(len(SpecifiedBits)):
                if SpecifiedBits[i] == '0':
                    self._primary_zeros_set.add(i)
                    try:
                        self._primary_ones_set.remove(i)
                    except:
                        pass
                elif SpecifiedBits[i] == '1':
                    self._primary_ones_set.add(i)
                    try:
                        self._primary_zeros_set.remove(i)
                    except:
                        pass
                    
    def clearPrimaryBits(self):
        self._primary_ones_set.clear()
        self._primary_zeros_set.clear()
        
    def clearScanBits(self):
        self._ones_set.clear()
        self._zeros_set.clear()
        
    def clear(self):
        self.clearScanBits()
        self.clearPrimaryBits()
                
    def getFillRate(self) -> float:
        return (len(self._ones_set) + len(self._zeros_set)) / len(self)
        
    def getSpecifiedBitPositions(self) -> list:
        return list(self._ones_set | self._zeros_set)
    
    def getSpecifiedPrimaryBitPositions(self) -> list:
        return list(self._primary_ones_set | self._primary_zeros_set)
        
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
        
    def mergeWithAnother(self, AnotherCube : TestCube) -> bool:
        if len(self) != len(AnotherCube):
            return False
        if len(self._ones_set & AnotherCube._zeros_set) > 0 or len(self._zeros_set & AnotherCube._ones_set) > 0:
            return False
        if len(self._primary_ones_set & AnotherCube._primary_zeros_set) > 0 or len(self._primary_zeros_set & AnotherCube._primary_ones_set) > 0:
            return False
        self._ones_set |= AnotherCube._ones_set
        self._zeros_set |= AnotherCube._zeros_set
        self._primary_ones_set |= AnotherCube._primary_ones_set
        self._primary_zeros_set |= AnotherCube._primary_zeros_set
        return True
    
    def canBeMergedWithAnother(self, AnotherCube : TestCube) -> bool:
        if len(self) != len(AnotherCube):
            return False
        if len(self._ones_set & AnotherCube._zeros_set) > 0 or len(self._zeros_set & AnotherCube._ones_set) > 0:
            return False
        if len(self._primary_ones_set & AnotherCube._primary_zeros_set) > 0 or len(self._primary_zeros_set & AnotherCube._primary_ones_set) > 0:
            return False
        return True
    
    def _forceMergeWithAnother(self, AnotherCube : TestCube):
        self._ones_set |= AnotherCube._ones_set
        self._zeros_set |= AnotherCube._zeros_set
        self._primary_ones_set |= AnotherCube._primary_ones_set
        self._primary_zeros_set |= AnotherCube._primary_zeros_set
    
    def setPrimaryBit(self, BitIndex : int, BitValue : str) -> bool:
        if BitValue in [0, '0']:
            self._primary_zeros_set.add(BitIndex)
            try:
                self._primary_ones_set.remove(BitIndex)
            except:
                pass
        elif BitValue in [1, '1']:
            self._primary_ones_set.add(BitIndex)
            try:
                self._primary_zeros_set.remove(BitIndex)
            except:
                pass
        else:
            try:
                self._primary_zeros_set.remove(BitIndex)
            except:
                pass
            try:
                self._primary_ones_set.remove(BitIndex)
            except:
                pass
        return True
    
    def setBit(self, BitIndex : int, BitValue : str) -> bool:
        if BitIndex >= len(self):
            return False
        if BitValue in [0, '0']:
            self._zeros_set.add(BitIndex)
            try:
                self._ones_set.remove(BitIndex)
            except:
                pass
        elif BitValue in [1, '1']:
            self._ones_set.add(BitIndex)
            try:
                self._zeros_set.remove(BitIndex)
            except:
                pass
        else:
            try:
                self._zeros_set.remove(BitIndex)
            except:
                pass
            try:
                self._ones_set.remove(BitIndex)
            except:
                pass
        return True
    
    def getBit(self, BitIndex : int) -> int:
        if BitIndex >= len(self):
            return -1
        if BitIndex in self._ones_set:
            return 1
        if BitIndex in self._zeros_set:
            return 0
        return -1
    
    def getPrimaryBit(self, BitIndex : int) -> int:
        if BitIndex in self._primary_ones_set:
            return 1
        if BitIndex in self._primary_zeros_set:
            return 0
        return -1
            
    def getSpecifiedCount(self) -> int:
        return len(self._zeros_set) + len(self._ones_set)
    
    def getPrimarySpecifiedCount(self) -> int:
        return len(self._primary_zeros_set) + len(self._primary_ones_set)
            
    
class TestCubeSet:
    
    __slots__ = ('_cubes')
    
    def __init__(self):
        self._cubes = []
        
    def __len__(self):
        return len(self._cubes)
    
    def __str__(self):
        Result = ""
        Second = 0
        for Cube in self._cubes:
            if Second:
                Result += "\n"
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
            return Result
        else:
            return self._cubes[index]
        
    @staticmethod
    def fromFile(FileName : str, ScanChainCount : int, ScanChainLength : int, FilterAfterMerging : bool = False) -> TestCubeSet:
        CubeLength = ScanChainLength * ScanChainCount
        Cube = None
        Result = TestCubeSet()
        IgnoreThis = False
        for Line in Generators().readFileLineByLine(FileName):
            if FilterAfterMerging:
                R = re.search(r"After merging", Line)
                if R:
                    IgnoreThis = False # True
                    continue
            R = re.search(r"TDVE[:]*\s*Cube\s*[0-9]", Line)
            if R:
                if Cube is not None:
                    if not IgnoreThis:
                        Result.addCube(Cube)
                    IgnoreThis = False
                Cube = TestCube(CubeLength)
                continue
            R = re.search(r"TDVE[:]*\s*([-0-9]+)\s+([0-9]+)\s([0-9]+)", Line)
            if R:
                Chain = int(R.group(1))
                BitIndex = int(R.group(2))
                BitVal = int(R.group(3))
                if Chain < 0: # primary
                    Cube.setPrimaryBit(BitIndex, BitVal)
                else:                
                    CubeBitIndex = Chain * ScanChainLength + BitIndex
                    Cube.setBit(CubeBitIndex, BitVal)
        if Cube is not None:
            if not IgnoreThis:
                Result.addCube(Cube)
            IgnoreThis = False
        return Result

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
    
    def softCopy(self) -> TestCubeSet:
        Result = TestCubeSet()
        Result._cubes = self._cubes
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
    
    def _mergingRound(self, Edt : EdtStructure, PatternCount : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 3, Verbose : bool = False, OnlyPatternCount : bool = False) -> tuple:
        """Returns two TestCubeSet objects: (Patterns, Cubes)."""
        Cubes = self
        if OnlyPatternCount:
            Patterns = 0
        else:
            Patterns = TestCubeSet()
        MaximumBitCount = Edt.getMaximumSpecifiedBitPerCycleToBeCompressable()
        while len(Cubes) > 0 and (Patterns < PatternCount if OnlyPatternCount else len(Patterns) < PatternCount):
            Cube = Cubes._cubes[0]
            del Cubes._cubes[0]
            ToBeRemovedFromBuffer = []
            CompressionCounter = 0
            for ANotherCube in Cubes._cubes:
                MergingResult = Cube.canBeMergedWithAnother(ANotherCube)
                if MergingResult: 
                    CubeAux = Cube.copy()
                    CubeAux._forceMergeWithAnother(ANotherCube)
                    if Edt.isCompressable(CubeAux, MinBatteryCharge):
                        Cube = CubeAux
                        ToBeRemovedFromBuffer.append(ANotherCube)
                        if Cube.getSpecifiedCount()-1 >= MaximumBitCount:
                            break
                    else:
                        CompressionCounter += 1
                        if CompressionCounter > CompressabilityLimit:
                            break
            if OnlyPatternCount:
                Patterns += 1
            else:
                Patterns._cubes.append(Cube)
            for i in ToBeRemovedFromBuffer:
                Cubes._cubes.remove(i)
        return Patterns
    
    def _mergingRoundCombined(self, Edt, PatternCount : int = 64, MinBatteryCharge : float = 0.05, CompressabilityLimit : int = 3, Verbose : bool = False, OnlyPatternCount : bool = False) -> tuple:
        """Returns two TestCubeSet objects: (Patterns, Cubes)."""
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
                            if EdtBattery.isCompressable(CubeAux, MinBatteryCharge):
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
    
    def merge(self, Edt : EdtStructure, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 3, Verbose : bool = False, CombinedCompressionChecking : bool = False, OnlyPatternCount : bool = False) -> TestCubeSet:
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver     
        if CombinedCompressionChecking and type(Edt) is not DecompressorSolver:
            Aio.printError("Edt must be DecompressorSolver object if CombinedCompressionChecking is set.")
            return None
        elif type(Edt) is DecompressorSolver:
            MinBatteryCharge = 0
        elif type(Edt) is TestDataDecompressor:
            MBL = Edt.MinimumBatteryLevel
            Edt = EdtStructure(Edt)
            Edt.MinimumBatteryLevel = MBL
        if type(Edt) is EdtStructure:
            if Edt.MinimumBatteryLevel is not None:
                MinBatteryCharge = Edt.MinimumBatteryLevel
        Buffer = TestCubeSet()
        if type(BufferLength) is int:
            BufferLength = [BufferLength]
        if len(BufferLength) < 1:
            BufferLength = [512]
        Buffer._cubes = self._cubes[0:BufferLength[0]]
        index = BufferLength[0]
        if CombinedCompressionChecking:
            Patterns, BackTracingCounterSum, SolverCallsSum = Buffer._mergingRoundCombined(Edt, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, OnlyPatternCount)
        else:
            Patterns = Buffer._mergingRound(Edt, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, OnlyPatternCount)
        BufferLenIndex = 0
        if Verbose:
            if OnlyPatternCount:
                print(f"Furst round finished. BufferLen: {BufferLength[0]} -> {len(Buffer)}, PatternsLen={Patterns}")
            else:
                print(f"Furst round finished. BufferLen: {BufferLength[0]} -> {len(Buffer)}, PatternsLen={len(Patterns)}")
        while index < len(self):
            BufferLenIndex += 1 
            if BufferLenIndex >= len(BufferLength):
                BufferLenIndex = len(BufferLength) - 1
            HowManyToAdd = BufferLength[BufferLenIndex] - len(Buffer)
            Buffer._cubes += self._cubes[index:index+HowManyToAdd]
            if Verbose:
                BuffLenAtTheBeginningOfRound = len(Buffer)
            index += HowManyToAdd
            if CombinedCompressionChecking:
                SubPatterns, BackTracingCounterSum, SolverCallsSum = Buffer._mergingRoundCombined(Edt, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, OnlyPatternCount)
            else:
                SubPatterns = Buffer._mergingRound(Edt, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, OnlyPatternCount)
            if OnlyPatternCount:
                Patterns += SubPatterns
            else:
                Patterns._cubes += SubPatterns._cubes
            if Verbose:
                if OnlyPatternCount:
                    print(f"Next round finished. BufferLen: {BuffLenAtTheBeginningOfRound} -> {len(Buffer)}, PatternsLen={Patterns}")
                else:
                    print(f"Next round finished. BufferLen: {BuffLenAtTheBeginningOfRound} -> {len(Buffer)}, PatternsLen={len(Patterns)}")
        if len(Buffer) > 0:
            if CombinedCompressionChecking:
                SubPatterns, BackTracingCounter, SolverCalls = Buffer._mergingRoundCombined(Edt, len(Buffer), MinBatteryCharge, CompressabilityLimit, Verbose, OnlyPatternCount)
                BackTracingCounterSum += BackTracingCounter
                SolverCallsSum += SolverCalls
            else:
                SubPatterns = Buffer._mergingRound(Edt, len(Buffer), MinBatteryCharge, CompressabilityLimit, Verbose, OnlyPatternCount)
            if OnlyPatternCount:
                Patterns += SubPatterns
            else:
                Patterns._cubes += SubPatterns._cubes
            if Verbose:
                if OnlyPatternCount:
                    print(f"Last. BufferLen={len(Buffer)}, PatternsLen={Patterns}")
                else:
                    print(f"Last. BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        if Verbose:
            if OnlyPatternCount:
                print(f"FINISHED BufferLen={len(Buffer)}, PatternsLen={Patterns}")
            else:
                print(f"FINISHED BufferLen={len(Buffer)}, PatternsLen={len(Patterns)}")
        if CombinedCompressionChecking:
            return Patterns, BackTracingCounterSum, SolverCallsSum
        return Patterns
    
    def removeNotCompressable(self, Edt : EdtStructure, MultiThreading = False) -> int:
        ToBeRemoved = []
        if MultiThreading:        
            def serial(Indices):
                ToBeRemovedLocal = []
                for i in Indices:
                    if not Edt.isCompressable(self.getCube(i)):
                        ToBeRemovedLocal.append(i)
                return ToBeRemovedLocal
            AllIndices = [i for i in range(len(self))]
            for rl in p_uimap(serial, List.splitIntoSublists(AllIndices, 1000), desc="Removing uncompressable cubes (x1000)"):
                ToBeRemoved += rl
            AioShell.removeLastLine()
            ToBeRemoved.sort()
        else:
            for i in range(len(self)):
                if not Edt.isCompressable(self.getCube(i)):
                    ToBeRemoved.append(i)
        for i in reversed(ToBeRemoved):
            self.removeCube(i)
        return len(ToBeRemoved)
    
    removeUnompressable = removeNotCompressable
    
    @staticmethod
    def doMergingExperiment(Cubes : TestCubeSet, Edt : EdtStructure, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 10, Verbose : bool = False, MultiThreading = False, CombinedCompressionChecking : bool = False) -> tuple:
        """Returns 4-element tuple:
        AfterRemovalCubesCount, len(Patterns), TestTime, TestDataVolume, ExecutionTime
        In case of combined method it returns also
        BackTracingCalls, SolverCalls"""
        from libs.research_projects.testkompress_advisor.edt_solver import DecompressorSolver     
        if CombinedCompressionChecking and type(Edt) is not DecompressorSolver:
            Aio.printError("Edt must be DecompressorSolver object if CombinedCompressionChecking is set.")
            return None
        if CombinedCompressionChecking:
            CubesCopy = Cubes.deepCopy()
        else:
            CubesCopy = Cubes.softCopy()
        BeforeRemovalCubesCount = len(CubesCopy)
        if Verbose:
            Aio.print(f"#Cubes before uncompressable removal: {BeforeRemovalCubesCount}")
        RemovedCount = CubesCopy.removeNotCompressable(Edt, MultiThreading)
        AfterRemovalCubesCount = len(CubesCopy)
        if Verbose:
            Aio.print(f"#Cubes removed:                       {RemovedCount}")
            Aio.print(f"#Cubes after uncompressable removal:  {AfterRemovalCubesCount}")
        t0 = time.time()
        if CombinedCompressionChecking:
            Patterns, BackTracingCounterSum, SolverCallsSum = CubesCopy.merge(Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, True, True)
        else:
            Patterns = CubesCopy.merge(Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, Verbose, False, True)
        t1 = time.time()
        TestTime = Edt.getTestTime(Patterns)
        TestDataVolume = Edt.getTestDataVolume(Patterns)
        ExeTime = (t1 - t0)
        if Verbose:
            Aio.print(f"#Patterns:                            {Patterns}")
            Aio.print(f"Test time [cycles]:                   {TestTime}")
            Aio.print(f"Test data volume [b]:                 {TestDataVolume}")
            Aio.print(f"Execution time [s]:                   {ExeTime}")
        if CombinedCompressionChecking:
            return AfterRemovalCubesCount, Patterns, TestTime, TestDataVolume, ExeTime, BackTracingCounterSum, SolverCallsSum
        return AfterRemovalCubesCount, Patterns, TestTime, TestDataVolume, ExeTime
        
    doExperiment = doMergingExperiment
    
    @staticmethod
    def doExperiments(Cubes : TestCubeSet, EdtList : list, BufferLength : int = 512, PatternCountPerRound : int = 64, MinBatteryCharge : float = 0.1, CompressabilityLimit : int = 10, CombinedCompressionChecking : bool = False) -> list:
        Result = []
        def singleTry(Edt : EdtStructure) -> tuple:
            return TestCubeSet.doMergingExperiment(Cubes, Edt, BufferLength, PatternCountPerRound, MinBatteryCharge, CompressabilityLimit, False, False, CombinedCompressionChecking)
#        for x in EdtList:
#            Result.append(singleTry(x))
        for R in p_imap(singleTry, EdtList):
            Result.append(R)
        AioShell.removeLastLine()
        return Result
    
    


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
    
    
class TestCubeSetUtils:
    
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