from libs.aio import *
from bitarray import *
import bitarray.util as bau
from random import *


class TestCube:
    pass
class TestCube:
    
    __slots__ = ('_specified_bit_positions', '_specified_bit_values', "Age")
    
    @staticmethod
    def randomCube(Length : int, Pspecified : float = 0.1, P1 = 0.5) -> TestCube:
        StrVal = ""
        for i in range(Length):
            if random() < Pspecified:
                StrVal += '1' if random() < P1 else '0'
            else:
                StrVal += 'X'
        return TestCube(StrVal)
    
    def __init__(self, SpecifiedBits : str = ''):
        self._specified_bit_positions = bitarray()
        self._specified_bit_values = bitarray()
        self.Age = 0
        if type(SpecifiedBits) is str:
            self.setBits(SpecifiedBits)
        elif type(SpecifiedBits) is int:
            self._specified_bit_positions = bau.zeros(SpecifiedBits)
            self._specified_bit_values = bau.zeros(SpecifiedBits)
        elif type(SpecifiedBits) is TestCube:
            self._specified_bit_positions = SpecifiedBits._specified_bit_positions.copy()
            self._specified_bit_values = SpecifiedBits._specified_bit_values.copy()
            self.Age = SpecifiedBits.Age
            
    def __len__(self):
        return len(self._specified_bit_positions)
    
    def __str__(self):
        Result = ""
        for i in range(len(self._specified_bit_positions)):
            if not self._specified_bit_positions[i]:
                Result += 'X'
            else:
                Result += str(int(self._specified_bit_values[i]))
        return Result
    
    def __repr__(self):
        return f"TestCube(\"{str(self)}\")"
    
    def setBits(self, SpecifiedBits : str):
        # 0, 1 - values
        # X - don't care
        SpecifiedBits = SpecifiedBits.upper()
        ValuesStr = SpecifiedBits.replace('X', '0')
        SpecifiedStr = SpecifiedBits.replace('0', '1')
        SpecifiedStr = SpecifiedStr.replace('X', '0')
        self._specified_bit_positions = bitarray(SpecifiedStr)
        self._specified_bit_values = bitarray(ValuesStr)
        
    def copy(self) -> TestCube:
        Result = TestCube(self)
        return Result
        
    def mergeWithAnother(self, AnotherCute : TestCube) -> bool:
        if len(self) != len(AnotherCute):
            return False
        ResPos = bau.zeros(len(self))
        ResVal = bau.zeros(len(self))
        Result = False
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
        return f"TestCubeSet()"
    
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
    
    def autoMerge(self):
        pass

