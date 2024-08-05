
from sympy import *
#from sympy.logic import SOPform
import sympy.logic.boolalg as SympyBoolalg
import sympy.parsing

class SymPy:
    
    @staticmethod
    def isThereAFunctionInExpression(expr, func) -> bool:
        if expr.func == func:
            return True
        for arg in expr.args:
            if SymPy.isThereAFunctionInExpression(arg, func):
                return True
        return False
        
    @staticmethod
    def isANFLinear(expr) -> bool:
        try:
            anf = expr.to_anf()
            return not SymPy.isThereAFunctionInExpression(anf, And)
        except:
            return True
        
    @staticmethod
    def getAnfVariablesCount(expr) -> int:
        try:
            Literls = set()
            anf = expr.to_anf()
            for arg in anf.args:
                if type(arg) is Symbol:
                    Literls.add(arg)
                elif type(arg) is And:
                    for aarg in arg.args:
                        Literls.add(aarg)
            return len(Literls)
        except:
            return 0
        
    @staticmethod
    def getAnfLiteralsCount(expr) -> int:
        try:
            Counter = 0
            anf = expr.to_anf()
            for arg in anf.args:
                if type(arg) is Symbol:
                    Counter += 1
                elif type(arg) is And:
                    for aarg in arg.args:
                        Counter += 1
            return Counter
        except:
            return 0
        
    @staticmethod
    def getAnfDegree(expr) -> int:
        try:
            Degree = 0
            anf = expr.to_anf()
            for arg in anf.args:
                if type(arg) is Symbol:
                    if Degree < 1:
                        Degree = 1
                elif type(arg) is And:
                    if Degree < len(arg.args):
                        Degree = len(arg.args)
            return Degree
        except:
            return 0
        
    @staticmethod
    def getAnfMonomialsCount(expr) -> int:
        try:
            Result = 0
            anf = expr.to_anf()
            for arg in anf.args:
                if type(arg) in [Symbol, And]:
                    Result += 1
            return Result
        except:
            return 0
    
    @staticmethod
    def anf(expr : str):
        try:
            expr = expr.replace("+", "^")
            expr = expr.replace("*", "&")
            return sympy.parsing.parse_expr(expr).to_anf()
        except:
            return None
        
    @staticmethod
    def cnf(expr : str):
        try:
            expr = expr.replace("+", "^")
            expr = expr.replace("*", "&")
            return SympyBoolalg.simplify_logic(sympy.parsing.parse_expr(expr), 'cnf', 1, 1)
        except:
            return None
        
    @staticmethod
    def dnf(expr : str):
        try:
            expr = expr.replace("+", "^")
            expr = expr.replace("*", "&")
            return SympyBoolalg.simplify_logic(sympy.parsing.parse_expr(expr), 'dnf', 1, 1)
        except:
            return None
    
    @staticmethod
    def anfsAND(expr1, expr2):
        try:
            anf1 = expr1.to_anf()
        except:
            anf1 = expr1
        try:
            anf2 = expr2.to_anf()
        except:
            anf2 = expr2
        not1 = 0
        not2 = 0
        try:
            if anf1.func == Not:
                not1 = 1
                anf1 = anf1.args[0]
        except:
            pass
        try:
            if anf2.func == Not:
                not2 = 1
                anf2 = anf1.args[0]
        except:
            pass
        Result = False
        Terms1 = tuple([True])
        if type(anf1) == Xor:
            Terms1 = anf1.args
            if not1:
                Terms1 += tuple([True])
        else:
            Terms1 = tuple([anf1])
        Terms2 = tuple([True])
        if type(anf2) == Xor:
            Terms2 = anf2.args
            if not2:
                Terms2 += tuple([True])
        else:
            Terms2 = tuple([anf2])       
        for T1 in Terms1:
            for T2 in Terms2:
                #print(T1, "   AND   ", T2)
                Result ^= T1 & T2
        return Result
    
    def substDict(expr, Dict : dict):
        R = expr
        for i in Dict.items():
            R = R.subs(*i)
        return R