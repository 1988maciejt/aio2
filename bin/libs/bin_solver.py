from libs.aio import *
from bitarray import *
import bitarray.util as bau

class BinSolverEquation:
    
    __slots__ = ('_variables', '_value', '_first_one')
    
    def __init__(self, Equation : bitarray, Value : int = None):
        if type(Equation) is str:
            Equation = bitarray(Equation) 
        if Value is None:
            self._variables = Equation[:-1]
            self._value = Equation[-1]
        else:
            self._variables = Equation.copy()
            self._value = Value
        self._lookForFirstOne()
            
    def _lookForFirstOne(self):
        try:
            self._first_one = self._variables.index(1)
        except:
            self._first_one = -1
        
            
    def __len__(self):
        return len(self._variables)
            
    def __str__(self):
        return f"{str(self._variables)[10:-2]}={str(self._value)}"
    
    def __repr__(self):
        return f"BinSolverEquation('{str(self._variables)[10:-2]}{str(self._value)}')"
            
    def isInconsistent(self) -> bool:
        return True if ((self._first_one == -1) and (self._value)) else False
    
    def isEmpty(self) -> bool:
        return True if ((self._first_one == -1) and (not self._value)) else False
    
    def isNotEmpty(self) -> bool:
        return True if ((self._first_one > -1) or (self._value)) else False
    
    def __add__(self, Other):
        if len(self) != len(Other):
            Aio.printError("Both equations must have the same number of variables")
            return None
        return BinSolverEquation(self._variables ^ Other._variables, (self._value ^ Other._value))
    
    def firstOne(self) -> int:
        return self._first_one
    
    def getVariableIteratorBesidesFirst(self):
        return self._variables.search(1, self._first_one+1)
    
    def getSecondVarIndex(self, StartFrom : int = None):
        if StartFrom is None:
            return self._variables.find(1, self._first_one+1)
        return self._variables.find(1, StartFrom)
    
    
    
class BinSolver:
    
    __slots__ = ('_equations', '_gauss_done')
    
    def __init__(self, Equations : list):
        """Equations must be a list of BinSolverEquation objects, having the same num of variables"""
        self._equations = Equations.copy()
        self._gauss_done = False
        
    def __len__(self):
        return len(self._equations)
        
    def __str__(self):
        return '\n'.join([str(Eq) for Eq in self._equations])
    
    def __repr__(self):
        return f"BinSolver({[repr(Eq)+',' for Eq in self._equations]})"
        
    def getIndexesOfEquationsHavingSpecifiedFirstOne(self) -> list:
        if len(self._equations) < 1:
            return None
        VarCount = len(self._equations[0])
        Result = [[] for i in range(VarCount+1)]
        for i in range(len(self._equations)):
            Eq = self._equations[i]
            Result[Eq.firstOne()].append(i)   
        return Result     
        
    def gauss(self, Verbose : bool = False) -> bool:
        if len(self._equations) < 2:
            self._gauss_done = False
            return False
        if Verbose:
            print(f"GAUSS Start =======================")
        VarCount = len(self._equations[0])
        for VarIdx in range(VarCount):
            Reference = self.getIndexesOfEquationsHavingSpecifiedFirstOne()
            for EI in range(len(Reference[-1])):
                if not self._equations[EI].isInconsistent():
                    if Verbose:
                        print(f"INCONSISTENCY FOUND in equation {EI}: {self._equations[EI]}")
                    self._gauss_done = False
                    return False
            if Verbose:
                print(f"Var: {VarIdx} ------------------")
                print(f"Reference: {Reference}")
            ThisVarFirst = Reference[VarIdx]
            if len(ThisVarFirst) < 2:
                continue
            EqsToBeRemoved = []
            BaseEq = self._equations[ThisVarFirst[0]]
            for i in range(1, len(ThisVarFirst)):
                EqIdx = ThisVarFirst[i]
                self._equations[EqIdx] = self._equations[EqIdx] + BaseEq
                if self._equations[EqIdx].isEmpty():
                    EqsToBeRemoved.append(EqIdx)
                if self._equations[EqIdx].isInconsistent():
                    if Verbose:
                        print(f"INCONSISTENCY FOUND in equation {EqIdx}: {self._equations[EqIdx]}")
                    self._gauss_done = False
                    return False
            if Verbose:
                print(self)
                print(f"EqsToBeRemoved: {EqsToBeRemoved}")
            for ir in reversed(EqsToBeRemoved):
                del self._equations[ir]
            if Verbose:
                print(self)
        if Verbose:
            print(f"Fater elimination: ----------")
            print(self)
            print(f"GAUSS End =======================")
        self._gauss_done = True
        return True
            
    def solve(self, Verbose : bool = False) -> list:
        GaussResult = True
        if not self._gauss_done:
            GaussResult = self.gauss(Verbose=Verbose)
        if not GaussResult:
            if Verbose:
                print(f"GAUSS FAILED!")
            return None
        if Verbose:
            print(f"SOLVE Start =======================")
            print(self)
        VarCount = len(self._equations[0])
        Solution = [None for _ in range(VarCount)]
        Reference = self.getIndexesOfEquationsHavingSpecifiedFirstOne()
        if Verbose:
            print(f"Reference: {Reference}")
        for EqI in range(len(self._equations)):
            Eq = self._equations[EqI]
            if Verbose:
                print(f"EqIndex: {EqI} ------------------")
                print(f"Eq: {Eq}") 
            VarToEliminate = Eq.getSecondVarIndex()
            while VarToEliminate > -1:
                if Verbose:
                    print(f"VarToEliminate: {VarToEliminate}")
                CandidList = Reference[VarToEliminate]
                if len(CandidList) < 1:
                    if Verbose:
                        print(f"NO CANDIDATES!")
                    VarToEliminate = Eq.getSecondVarIndex(VarToEliminate+1)
                    continue
                    #return None
                Candidate = CandidList[0]
                if Verbose:
                    print(f"Eq used to eleiminate this var: {Candidate} {self._equations[Candidate]}")
                Eq = Eq + self._equations[Candidate]
                VarToEliminate = Eq.getSecondVarIndex()
                if Verbose:
                    print(f"Eq after elimination: {Eq}") 
            if Verbose:
                print(f"Eq system at the end of this step")
                print(self) 
                print(f"VAR {Eq._first_one} = {Eq._value}")
            if Solution[Eq._first_one] is None:
                Solution[Eq._first_one] = Eq._value
            else:
                if Verbose:
                    print("No solution - INCONSISTENCY")
                return None
            self._equations[EqI] = Eq
        if Verbose:
            print(f"SOLVE End =======================")
        for i in range(len(Solution)):
            if Solution[i] is None:
                Solution[i] = 0
        return Solution
            
                
                
        