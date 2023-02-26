from libs.aio import *
from bitarray import *
from functools import partial
from p_tqdm import *
from tqdm import tqdm
import bitarray.util as bau
import itertools
import numpy as np
from libs.simple_threading import *


class FastANFSpace:
    pass

class FastANFExpression:
    pass


class FastANFExpression:
    
    __slots__ = ("_MySpace", "_MonomialSize", "_Table", "_Empty")
    
    def __init__(self, MySpace : FastANFSpace, VarCount : int) -> None:
        self._MySpace = MySpace
        self._MonomialSize = VarCount
        self._Table = np.zeros((1<<self._MonomialSize), dtype=np.bool_)
        self._Empty = True
        
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
        New._Empty = self._Empty
        return New
        
    def addMonomial(self, Monomial : int):
        self._Empty = False
        if Monomial is not None:
            self._Table[Monomial] ^= 1
    
    def getMonomials(self):
        return [np.int64(i) for i in range(len(self._Table)) if self._Table[i]] 
    
    def getMonomialCount(self):
        return len(self.getMonomials())
    
    def clear(self):
        self._Empty = True
        self._Table = np.zeros((1<<self._MonomialSize), dtype=np.bool_)

    def add(self, Another : FastANFExpression):
        self._Table ^= Another._Table
        self._Empty = False

    @staticmethod
    def _mulArrays(A : bytes, B : bytes) -> bytes:
        a = pickle.loads(A)
        b = pickle.loads(B)
        r = np.zeros(len(a), dtype=np.bool_)
        Monomials1 = [np.int64(i) for i in range(len(a)) if a[i]] 
        Monomials2 = [np.int64(i) for i in range(len(b)) if b[i]] 
        for M1 in Monomials1:
            for M2 in Monomials2:
                r[M1 | M2] ^= 1
        return pickle.dumps(r)        

    def _mul(self, M1, Monomials2) -> list:
        Result = np.zeros(len(Monomials2), dtype=np.int64)
        for i in range(len(Monomials2)):
            Result[i] = M1 | Monomials2[i]
        return Result
    
    def mul(self, Another : FastANFExpression):
        if self.isZero():
            return
        if Another.isZero():
            self.clear()
            return
        Monomials1 = self.getMonomials()
        Monomials2 = Another.getMonomials()
        self.clear()
        if 0:
            for R in SimpleThread.uimap(partial(self._mul, Monomials2=Monomials2), Monomials1):
                for N in R:
                    self._Table[N] ^= 1
        else:
            for M1 in Monomials1:
                for M2 in Monomials2:
                    self._Table[M1 | M2] ^= 1
        self._Empty = False
                
    def negate(self):
        self._Table[0] ^= 1
        self._Empty = False

    def isZero(self):
        return self._Empty

    def toStr(self) -> str:
        Monomials = self.getMonomials()
        if len(Monomials) == 0:
            return "0"
        Result = ""
        Second = 0
        for M in Monomials:
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
        for npM in self.getMonomials():
            M = int(npM)
            if MinMonomial <= M <= MaxMonomial:
                Result[bau.int2ba(M, self._MonomialSize).count(1)] += 1        
        return Result
    
        
        

class FastANFSpace:
    
    __slots__ = ("_Variables")
    
    def __init__(self, Variables : list) -> None:
        if len(Variables) > 64:
            Aio.printError("FastANF can operate on 64 variables max")
        self._Variables = Variables.copy()
        
    def getVariableByIndex(self, Index : int):
        return self._Variables[Index]
        
    def getVariables(self, Monomial = None) -> list:
        if Monomial is None:
            return self._Variables.copy()
        if Monomial == 0:
            return 1
        BAMonomial = bau.int2ba(int(Monomial), len(self._Variables), 'little')
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