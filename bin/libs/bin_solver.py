from libs.aio import *
from bitarray import *
import bitarray.util as bau

class BinSolverEquation:
    
    __slots__ = ('_variables', '_value', '_first_one')
    
    def __init__(self, Equation : bitarray, Value : int = None):
        if type(Equation) is BinSolverEquation:
            self._variables = Equation._variables.copy()
            self._value = Equation._value
            self._first_one = Equation._first_one
            return
        if type(Equation) is str:
            Equation = bitarray(Equation) 
        if Value is None:
            self._variables = Equation[:-1]
            self._value = Equation[-1]
        else:
            self._variables = Equation.copy()
            self._value = Value
        self._lookForFirstOne()
        
    def copy(self) -> "BinSolverEquation":
        return BinSolverEquation(self)
            
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
        return f"BinSolverEquation('{str(self._variables)[10:-2]}', {str(self._value)})"
            
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
    
    def xorWith(self, Another : "BinSolverEquation"):
        self._xorWith(Another)
        
    def _xorWith(self, Another : "BinSolverEquation", RecalculateFirst : bool = True):
        self._variables ^= Another._variables
        self._value ^= Another._value
        if RecalculateFirst:
            self._lookForFirstOne()
    
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
        if type(Equations) is list:
            self._equations = Equations.copy()
        elif type(Equations) in [set, tuple]:
            self._equations = list(Equations.copy())
        elif type(Equations) is BinSolver:
            self._equations = Equations._equations.copy()
        else:
            Aio.printError(f"{type(Equations)} is not a valid type for equations")
        self._gauss_done = False
        
    def copy(self) -> "BinSolver":
        Result = BinSolver([])
        for Eq in self._equations:
            Result._equations.append(Eq.copy())
        Result._gauss_done = self._gauss_done
        return Result
        
    def addEquation(self, Equation : BinSolverEquation):
        if type(Equation) is BinSolverEquation:
            self._equations.append(Equation)
            self._gauss_done = False
        elif type(Equation) in [list, tuple, set]:
            for Eq in Equation:
                self.addEquation(Eq)
        else:
            Aio.printError(f"{type(Equation)} is not a valid type for an equation")
        
    def __len__(self):
        return len(self._equations)
        
    def __str__(self):
        return '\n'.join([str(Eq) for Eq in self._equations])
    
    def __repr__(self):
        return f"BinSolver({[repr(Eq)+',' for Eq in self._equations]})"
    
    def sortEquations(self):
        self._equations.sort(key=lambda Eq: Eq._first_one)
        
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
        # NEW
        if Verbose:
            print(f"Before elimination: ----------")
            print(self)
        DidSomething = True
        while DidSomething:
            self.sortEquations()
            DidSomething = False
            NewPivots = set()
            ToBeRemoved = []
            if Verbose:
                print(f"Before iteration: ----------")
                print(self)
            for i, Eq0 in enumerate(self._equations):
                if (i in NewPivots):
                    continue
                if Eq0.isNotEmpty():
                    for j in range(i+1, len(self._equations)):
                        Eq1 = self._equations[j]
                        if Eq1._first_one == Eq0._first_one:
                            Eq1._xorWith(Eq0,1)
                            DidSomething = True
                            NewPivots.add(j)
                            if self._equations[j].isInconsistent():
                                if Verbose:
                                    print(f"INCONSISTENCY FOUND in equation {j}: {self._equations[j]}")
                                self._gauss_done = False
                                return False
                        else:
                            break
                else:
                    ToBeRemoved.append(i)
            if Verbose:
                print(f"Before cleaning: ----------")
                print(self)
            for i in reversed(ToBeRemoved):
                del self._equations[i]
            if Verbose:
                print(f"After iteration: ----------")
                print(self)
        if not self.removeEmptyAndCheckInconsistencies():
            if Verbose:
                print(f"INCONSISTENCY FOUND")
            self._gauss_done = False
            return False
        if Verbose:
            print(f"After elimination: ----------")
            print(self)
            print(f"GAUSS End =======================")
        self._gauss_done = True
        return True
    
    def removeEmptyAndCheckInconsistencies(self) -> bool:
        toDelete = []
        for i, Eq in enumerate(self._equations):
            if Eq._first_one < 0:
                if Eq._value:
                    return False
                toDelete.append(i)
        for i in reversed(toDelete):
            del self._equations[i]
        return True
            
    def removeEmpty(self):
        toDelete = []
        for i, Eq in enumerate(self._equations):
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
                RefEqI = VarToEqDict.get(Var, None)
                if RefEqI is not None:
                    if Verbose:
                        print(f"    Var: {Var}")
                    RefEq = self._equations[RefEqI]
                    #self._equations[i] = Eq0 + RefEq
                    Eq0._xorWith(RefEq, 0)
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
            
                
                
        