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
        if len(self._equations) == 1:
            self._gauss_done = True
            return True
        elif len(self._equations) < 1:
            self._gauss_done = False
            return False
        if Verbose:
            print(f"GAUSS Start =======================")
        ########## NEW ########
        DidSomething = True
        IIndices = [i for i in range(len(self._equations))]
        while DidSomething:
            DidSomething = False
            NewIIndices = set()
            #for i in range(len(self._equations)):
            for i in IIndices:
                Eq0 = self._equations[i]
                if Eq0.isNotEmpty():
                    #for j in range(len(self._equations)):
                    for j, Eq1 in enumerate(self._equations):
                        if i == j:
                            continue
                        #Eq1 = self._equations[j]
                        if Eq1._first_one == Eq0._first_one:
                            self._equations[j] = Eq0 + Eq1
                            DidSomething = True
                            NewIIndices.add(j)
                            if self._equations[j].isInconsistent():
                                if Verbose:
                                    print(f"INCONSISTENCY FOUND in equation {j}: {self._equations[j]}")
                                self._gauss_done = False
                                return False
            IIndices = NewIIndices
        self.removeEmpty()
        if Verbose:
            print(f"Fater elimination: ----------")
            print(self)
            print(f"GAUSS End =======================")
        self._gauss_done = True
        return True
    
    def removeEmpty(self):
        toDelete = []
        for i in range(len(self._equations)):
            Eq = self._equations[i]
            if Eq.isEmpty():
                toDelete.append(i)
        for i in reversed(toDelete):
            del self._equations[i]
            
    def solve(self, Verbose : bool = False) -> list:
        if len(self._equations) == 1:
            Eq = self._equations[0]
            Solution = [0 for _ in range(len(Eq))]
            if Eq._value:
                if Eq._first_one < 0:
                    return None
                Solution[Eq._first_one] = 1
            return Solution                
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
        VarToEqDict = {}
        for EqI, Eq in enumerate(self._equations):
            VarToEqDict[Eq._first_one] = EqI
        if Verbose:
            print(f"VarToEqDict: {VarToEqDict}")
        for i, Eq0 in enumerate(self._equations):
            Var = Eq0._variables.find(1, Eq0._first_one+1)
            if Verbose:
                print(f"Eq0: {Eq0}")
                print(f"  FirstOne: {Eq0._first_one}")
            while Var > 0:
                if Verbose:
                    print(f"    Var: {Var}")
                RefEqI = VarToEqDict.get(Var, None)
                if RefEqI is not None:
                    RefEq = self._equations[RefEqI]
                    self._equations[i] = Eq0 + RefEq
                    if self._equations[i].isInconsistent():
                        if Verbose:
                            print(f"INCONSISTENCY (1) FOUND in equation {i}: {self._equations[i]}")
                        return None
                else:
                    Solution[Var] = 0
                Var = Eq0._variables.find(1, Var+1)
        if Verbose:
            print(f"Equations after solving:\n{self}")
            print(f"Addint first var to solution...")
        for i, Eq in enumerate(self._equations):
            if Solution[Eq._first_one] is None:   
                Solution[Eq._first_one] = Eq._value
            elif Solution[Eq._first_one] != Eq._value:
                if Verbose:
                    print(f"INCONSISTENCY (2) FOUND in equation {i}: {self._equations[i]}")
                return None
        if Verbose:
            print(f"ActualSolution: {Solution}")
        for i, v in enumerate(Solution):
            if v is None:
                Solution[i] = 0
        if Verbose:
            print(f"Final solution: {Solution}")
            print(f"SOLVE End ========================")
        return Solution
            
                
                
        