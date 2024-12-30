from libs.aio import *
from bitarray import *
import bitarray.util as bau
from random import *
from copy import deepcopy

_TEST_CUBE_BITARRAYS = 0
_TEST_CUBE_IMPLEMENTATION_LOCKED = 0

class TestCube:
    pass
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
    
    def __init__(self, SpecifiedBits : str = '', LenIfSpecifiedSDict : int = 0):
        global _TEST_CUBE_BITARRAYS, _TEST_CUBE_IMPLEMENTATION_LOCKED
        _TEST_CUBE_IMPLEMENTATION_LOCKED = 1
        if _TEST_CUBE_BITARRAYS:
            self._specified_bit_positions = bitarray()
            self._specified_bit_values = bitarray()
        else:
            self._specified_bit_positions = {}
            self._specified_bit_values = 0
        self.Age = 0
        if type(SpecifiedBits) is str:
            self.setBits(SpecifiedBits)
        elif type(SpecifiedBits) is dict:
            self.setBits(SpecifiedBits, LenIfSpecifiedSDict)
        elif type(SpecifiedBits) is int:
            self._specified_bit_positions = bau.zeros(SpecifiedBits)
            self._specified_bit_values = bau.zeros(SpecifiedBits)
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
    
    def setBits(self, SpecifiedBits : str, LenIfDict : int = 0):
        global _TEST_CUBE_BITARRAYS
        # 0, 1 - values
        # X - don't care
        if _TEST_CUBE_BITARRAYS:
            if type(SpecifiedBits) is dict:
                self._specified_bit_positions = bau.zeros(LenIfDict)
                self._specified_bit_values = bau.zeros(LenIfDict)
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
                self._specified_bit_values = LenIfDict
            else:
                SpecifiedBits = SpecifiedBits.upper()
                for i in range(len(SpecifiedBits)):
                    if SpecifiedBits[i] == '0':
                        self._specified_bit_positions[i] = 0
                    elif SpecifiedBits[i] == '1':
                        self._specified_bit_positions[i] = 1
                self._specified_bit_values = len(SpecifiedBits)
        
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
    pass
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
    
    def addCube(self, Cube : TestCube):
        self._cubes.append(Cube)
    
    def addRandomCubes(self, Count : int, CubeLen : int, Pspecified : float = 0.1, P1 = 0.5):
        for i in range(Count):
            self.addCube(TestCube.randomCube(CubeLen, Pspecified, P1))
    
    def copy(self) -> TestCubeSet:
        Result = TestCubeSet()
        for Cube in self._cubes:
            Result.addCube(Cube.copy())
        return Result
    
    def resetAge(self):
        for Cube in self._cubes:
            Cube.Age = 0

    def sort(self):
        self._cubes.sort(key = lambda x: x.Age, reverse = True)
    
    def autoMerge(self, PreSort : bool = True):
        if PreSort:
            self.sort()
        DidSomething = True
        while DidSomething:
            DidSomething = False
            for i in range(len(self._cubes)):
                if self._cubes[i].Age < 0:
                    continue
                ThisCube = self._cubes[i].copy()
                for j in range(i + 1, len(self._cubes)):
                    if self._cubes[j].Age < 0:
                        continue
                    ThisCubeAux = ThisCube.copy()
                    if ThisCubeAux.mergeWithAnother(self._cubes[j]):
                        # Check if ThisCubeAux is OK
                        if 1: # if OK
                            ThisCube = ThisCubeAux
                            ThisCube.Age = -2       # Mark as merged
                            self._cubes[j].Age = -1 # Mark as used
                            DidSomething = True
                        else:
                            self._cubes[j].Age += 1 # Age++
                    else:
                        self._cubes[j].Age += 1     # Age++
                self._cubes[i] = ThisCube
            self.sort()

    def splitMergedAndNotmerged(self) -> tuple:
        """Returns two TestCubeSet objects: (Merged_cubes, NotMerged_cubes). Cubes used for merging are ignored."""
        Merged = TestCubeSet()
        NotMerged = TestCubeSet()
        for Cube in self._cubes:
            if Cube.Age == -2:
                Merged.addCube(Cube)
            elif Cube.Age >= 0:
                NotMerged.addCube(Cube)
        return Merged, NotMerged
    
    def splitIntoBufferAndRest(self, BufferLength : int = 100) -> tuple:
        """Returns two TestCubeSet objects: (Buffer, Rest)."""
        Buffer = TestCubeSet()
        Rest = TestCubeSet()
        Buffer._cubes = self._cubes[:BufferLength]
        Rest._cubes = self._cubes[BufferLength:]
        return Buffer, Rest