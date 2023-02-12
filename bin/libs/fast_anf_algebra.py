from libs.aio import *
from bitarray import *
from functools import partial
from p_tqdm import *
from tqdm import tqdm
import bitarray.util as bau
import itertools


class FastANFSpace:
    pass

class FastANFExpression:
    pass


class FastANFExpression:
    
    __slots__ = ("_MySpace", "_MonomialSize", "_Table")
    
    def __init__(self, MySpace : FastANFSpace, VarCount : int) -> None:
        self._MySpace = MySpace
        self._MonomialSize = VarCount
        self._Table = MySpace._Zero.copy()
        
    def __str__(self) -> str:
        return self.toStr()
        
    def __repr__(self) -> str:
        return self.toStr()
    
    def __xor__(self, other):
        New = self.copy()
        New.add(other)
        return New
    
    def __and__(self, other):
        New = self.copy()
        New.mul(other)
        return New
    
    def __invert__(self):
        New = self.copy()
        New.negate()
        return New
    
    def __len__(self):
        return self.getMonomialCount()
    
    def copy(self) -> FastANFExpression:
        New = FastANFExpression(self._MySpace, self._MonomialSize)
        New._Table = self._Table.copy()
        return New
        
    def addMonomial(self, Monomial : int):
        if Monomial is not None:
            self._Table[Monomial] ^= 1
                   
    def getMonomials(self):
        return self._Table.search(1)
    
    def getMonomialCount(self):
        return len(self._Table.search(1))
    
    def clear(self):
        self._Table.setall(0)

    def add(self, Another : FastANFExpression):
        self._Table ^= Another._Table
            
    def _mul_par(self, M1, Monomials2) -> bitarray:
        Result = bau.zerps(1 << self._MonomialSize)
        for M2 in Monomials2:
            Result[M1 | M2] ^= 1
        return Result
        
    def mul(self, Another : FastANFExpression, Parallel = 0):
        Monomials1 = self._Table.search(1)
        Monomials2 = Another._Table.search(1)
        self._Table.setall(0)
        if Parallel:
            if len(Monomials1) < len(Monomials2):
                for Table in p_uimap(partial(self._mul_par, Monomials2=Monomials2), Monomials1, desc="FastANF MUL PAR"):
                    self._Table ^= Table            
            else:
                for Table in p_uimap(partial(self._mul_par, Monomials2=Monomials1), Monomials2, desc="FastANF MUL PAR"):
                    self._Table ^= Table            
        else:
            for M1 in Monomials1:
                for M2 in Monomials2:
                    self._Table[M1 | M2] ^= 1
                
    def negate(self):
        self._Table[0] ^= 1

    def toStr(self) -> str:
        if self.getMonomialCount() == 0:
            return "0"
        Result = ""
        Second = 0
        for M in self.getMonomials():
            if Second:
                Result += " + "
            else:
                Second = 1
            VL = self._MySpace.getMonomialStr(M)
            if "&" in VL:
                Result += f"({VL})"
            else:
                Result += f"{VL}"
        return Result

    def getMonomialsHistogram(self, MinMonomial = None, MaxMonomial = None) -> list:
        if MinMonomial is None:
            MinMonomial = 0
        if MaxMonomial is None:
            MaxMonomial = 1 << self._MonomialSize
        Result = [0 for _ in range(self._MonomialSize + 1)]
        for M in self.getMonomials():
            if MinMonomial <= M <= MaxMonomial:
                Result[bau.int2ba(M, self._MonomialSize).count(1)] += 1        
        return Result
    
        
        

class FastANFSpace:
    
    __slots__ = ("_Variables", "_Zero")
    
    def __init__(self, Variables : list) -> None:
        self._Variables = Variables.copy()
        self._Zero = bitarray(1 << len(Variables))
        self._Zero.setall(0)
        
    def getVariableByIndex(self, Index : int):
        return self._Variables[Index]
        
    def getVariables(self, Monomial = None) -> list:
        if Monomial is None:
            return self._Variables.copy()
        if Monomial == 0:
            return 1
        BAMonomial = bau.int2ba(Monomial, len(self._Variables), 'little')
        IntVars = BAMonomial.search(1)
        Result = []
        for IntV in IntVars:
            Result.append(self._Variables[IntV])
        return Result
    
    def getMonomialStr(self, Monomial : int) -> str:
        Vars = self.getVariables(Monomial)
        try:
            if Vars == 1:
                return "1"
        except:
            pass
        Result = ""
        Second = 0
        for V in Vars:
            if Second:
                Result += " & "
            else:
                Second = 1
            Result += str(V)
        return Result            
    
    def createExpression(self, setOne = 0, InitValue = None):
        E = FastANFExpression(self, len(self._Variables))
        if setOne:
            E._Table[0] = 1
        if InitValue is not None:
            E.addMonomial(self.getMonomial(InitValue))
        return E
    
    def getVariableIndex(self, Variable) -> int:
        try:
            return self._Variables.index(Variable)
        except:
            return None
        
    def getMonomial(self, Variables) -> int:
        if Variables is None:
            return None
        try:
            if Variables == 1:
                return 0
        except:
            pass
        if not Aio.isType(Variables, []):
            Variables = [Variables]
        Result = 0
        for V in Variables:
            I = self.getVariableIndex(V)
            if I is not None:
                Result |= (1 << I)
        return Result
    
    def multiplyList(self, ListOfExpressions : list) -> FastANFExpression:
        if len(ListOfExpressions) < 1:
            return self.createExpression()
        Result = ListOfExpressions[0].copy()
        for i in range(1, len(ListOfExpressions)):
            Result.mul(ListOfExpressions[i])
        return Result