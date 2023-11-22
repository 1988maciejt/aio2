from libs.utils_int import *
from libs.utils_str import *
from libs.lfsr import Polynomial



class GF2Symbol:
  pass
class GF2Symbol:
  
  __slots__ = ("_letter", "_power")

  def copy(self) -> GF2Symbol:
    return GF2Symbol(self)

  def __init__(self, Letter : str  = "x", Power : int = None):
    if type(Letter) is GF2Symbol:
      self._letter = Letter._letter
      self._power = Letter._power
    else:
      _Letter, _Power = Int.splitLettersAndInt(Str.fromSuperScript(Letter), 'x', 1)
      if type(Power) is int:
        self._power = Power
      else:
        self._power = _Power
      self._letter = _Letter
    
  def __repr__(self) -> str:
    return f"GF2Symbol('{self._letter}', {self._power})"
  
  def __str__(self) -> str:
    return f"{self._letter}{Str.toSuperScript(str(self._power))}"
    
  def __hash__(self) -> int:
    return hash(str(self))
  
  def __eq__(self, __value: object) -> bool:
    if self._letter != __value._letter:
      return False
    if self._power != __value._power:
      return False
    return True
  
  def __ne__(self, __value: object) -> bool:
    return not(self == __value)
    
  def getDegree(self) -> int:
    return self._power
  
  def delay(self, Cycles : int):
    self._power += Cycles
    
  def getDelayed(self, Cycles : int) -> GF2Symbol:
    Result = self.copy()
    Result.delay(Cycles)
    return Result
  
  def moduloPowers(self, Modulus : int):
    while self._power < 0:
      self._power += Modulus
    self._power %= Modulus
  
  
class GF2Monomial:
  pass
class GF2Monomial:
  
  __slots__ = ("_symbols")
  
  def copy(self) -> GF2Monomial:
    return GF2Monomial(self)
  
  def __init__(self, *Symbols) -> None:
    _symbols = set()
    for Symbol in Symbols:
      if type(Symbol) is GF2Monomial:
        for Sym in Symbol._symbols:
          _symbols.add(Sym.copy())
      else:
        _symbols.add(GF2Symbol(Symbol))
    self._symbols = list(_symbols)
    self.sort()
  
  @staticmethod
  def fromString(Expression : str) -> GF2Monomial:
    Symbols = []
    Expression.strip()
    Expression = Expression.replace("*", " ")
    Expression = Expression.replace("&", " ")
    while 1:
      Expression2 = Expression.replace("  ", " ")
      if Expression2 == Expression:
        break
      Expression = Expression2
    for E in Expression.split(" "):
      if len(E) > 0:
        Symbols.append(GF2Symbol(E))
    return GF2Monomial(*Symbols)
  
  @staticmethod
  def fromList(Coefficients : list) -> GF2Monomial:
    if type(Coefficients) is int:
      Coefficients = [Coefficients]
    Symbols = set()
    for C in Coefficients:
      Symbols.add(GF2Symbol('x', int(C)))
    return GF2Monomial(*Symbols)
    
  def __len__(self) -> int:
    return len(self._symbols)
  
  def __repr__(self) -> str:
    Result = "GF2Monomial("
    Second = 0
    for Symbol in self._symbols:
      if Second:
        Result += ", "
      else:
        Second = 1
      Result += f"'{str(Symbol)}'"
    Result += ")"
    return Result
  
  def __str__(self) -> str:
    if len(self._symbols) < 1:
      return "0"
    if len(self._symbols) == 1:
      return str(self._symbols[0])
    Result = ""
    Second = 0
    for Symbol in self._symbols:
      if Second:
        Result += " "
      else:
        Second = 1
      Result += f"{str(Symbol)}"
    return Result
  
  def __eq__(self, __value: object) -> bool:
    if len(self) != len(__value):
      return False
    for s1, s2 in zip(self._symbols, __value._symbols):
      if s1 != s2:
        return False
    return True
  
  def __ne__(self, __value: object) -> bool:
    return not(self == __value)
  
  def __mul__(self, Other):
    Symbols = set()
    for s1 in self._symbols:
      for s2 in Other._symbols:
        if s1._letter == s2._letter:
          Symbols.add(GF2Symbol(s1._letter, s1._power + s2._power))
        else:
          Symbols.add(s1.copy())
          Symbols.add(s2.copy())
    return GF2Monomial(*list(Symbols))
  
  def sort(self):
    self._symbols.sort(key = lambda x: x._power, reverse=1)    
  
  def getSymbols(self) -> list:
    return self._symbols.copy()
      
  def getDegree(self) -> int:
    Result = 0
    for Symbol in self._symbols:
      SDeg = Symbol.getDegree()
      if SDeg > Result:
        Result = SDeg
    return Result
  
  def delay(self, Cycles : int):
    for Symbol in self._symbols:
      Symbol.delay(Cycles)
    
  def getDelayed(self, Cycles : int) -> GF2Symbol:
    Result = self.copy()
    Result.delay(Cycles)
    return Result
  
  def rotateLowestTerm(self, Cycles : int):
    if len(self._symbols) > 0:
      self._symbols[-1].delay(Cycles)
      self.sort()
  
  def rotateTermOfGivenPower(self, Cycles : int, Power : int):
    for Symbol in self._symbols:
      if Symbol._power == Power:
        Symbol.delay(Cycles)
        break
    self.sort()
    
  def getLowestPower(self) -> int:
    Result = self.getDegree()
    for Symbol in self._symbols:
      if Symbol._power < Result:
        Result = Symbol._power
    return Result
  
  def moduloPowers(self, Modulus : int):
    for Symbol in self._symbols:
      Symbol.moduloPowers(Modulus)
    self.sort()
    
    

class GF2Polynomial:
  pass
class GF2Polynomial:
  
  __slots__ = ("_monomials", "_inv")
  
  def copy(self) -> GF2Polynomial:
    return GF2Polynomial(self)
  
  def __init__(self, *Monomials, Inverted=False) -> None:
    self._monomials = []
    self._inv = Inverted 
    if len(Monomials) > 0:
      if type(Monomials[0]) is GF2Polynomial:
        self._inv = Monomials[0]._inv
        for Monomial in Monomials[0]._monomials:
          self._monomials.append(Monomial.copy())
      else:
        for Monomial in Monomials:
          Monomial = GF2Monomial(Monomial)
          if Monomial in self._monomials:
            self._monomials.remove(Monomial)
          else:
            self._monomials.append(Monomial)
    self.sort()
  
  @staticmethod
  def fromString(Expression : str) -> GF2Polynomial:
    Monomials = []
    Expression.strip()
    Expression = Expression.replace("^", "+")
    Expression = Expression.replace(",", "+")
    Expression = Expression.replace(";", "+")
    while 1:
      Expression2 = Expression.replace("  ", " ")
      if Expression2 == Expression:
        break
      Expression = Expression2
    for E in Expression.split("+"):
      if len(E) > 0:
        Monomials.append(GF2Monomial.fromString(E))
    return GF2Polynomial(*Monomials)
  
  @staticmethod
  def fromList(Coefficients : list) -> GF2Polynomial:
    if type(Coefficients) is int:
      Coefficients = [Coefficients]
    Monomials = []
    for C in Coefficients:
      Monomial = GF2Monomial.fromList(C)
      if Monomial in Monomials:
        Monomials.remove(Monomial)
      else:
        Monomials.append(Monomial)
    return GF2Polynomial(*Monomials)
  
  @staticmethod
  def fromPolynomial(Poly : Polynomial) -> GF2Polynomial:
    return GF2Polynomial.fromList(Poly.getCoefficients())
  
  def __len__(self) -> int:
    return len(self._monomials)
    
  def __repr__(self) -> str:
    return str(self)
  
  def __str__(self) -> str:
    Second = 0
    Result = ""
    if len(self._monomials) < 1:
      Result = "0"
    else:
      for Monomial in self._monomials:
        if Second:
          Result += " + "
        else:
          Second = 1
        Result += str(Monomial)
    if self._inv:
      Result = f"NOT( {Result} )"
    return Result
  
  def __eq__(self, __value: object) -> bool:
    if self._inv != __value._inv:
      return False
    if len(self) != len(__value):
      return False
    for m1, m2 in zip(self._monomials, __value._monomials):
      if m1 != m2:
        return False
    return True
  
  def __ne__(self, __value: object) -> bool:
    return not(self == __value)
  
  def __invert__(self):
    return self.getInverted()
  
  def __add__(self, Other):
    Result = self.copy()
    for Monomial in Other._monomials:
      if Monomial in Result._monomials:
        Result._monomials.remove(Monomial)
      else:
        Result._monomials.append(Monomial)
    Result.sort()
    if Other._inv:
      Result.invert()
    return Result
  
  def __mul__(self, Other):
    Monomials = []
    for m1 in self._monomials:
      for m2 in Other._monomials:
        Mul = m1 * m2
        if Mul in Monomials:
          Monomials.remove(Mul)
        else:
          Monomials.append(Mul)
    return GF2Polynomial(*Monomials, Inverted=self._inv & Other._inv)
        
  def __mod__(self, Modulus):
    _, m = self.divmod(Modulus)
    return m
  
  def __lshift__(self, Cycles):
    Result = self.copy()
    Result.delay(int(Cycles))
    return Result
  
  def __rshift__(self, Cycles):
    Result = self.copy()
    Result.delay(int(-Cycles))
    return Result
            
  def sort(self):
    self._monomials.sort(key = lambda x: (len(x) << 32) + x.getDegree(), reverse=1)
    
  def invert(self):
    self._inv = not self._inv
    
  def getInverted(self) -> GF2Polynomial:
    Result = self.copy()
    Result.invert()
    return Result
    
  def getInversion(self) -> bool:
    return self._inv
  
  def setInversion(self, Inversion=True):
    self._inv = bool(Inversion)
    
  def getDegree(self) -> int:
    Result = 0
    for Monomial in self._monomials:
      MD = Monomial.getDegree()
      if MD > Result:
        Result = MD
    return Result
  
  def getMonomials(self) -> list:
    return self._monomials.copy()
  
  def getSymbols(self) -> list:
    All = set()
    for Monomial in self._monomials:
      for Symbol in Monomial.getSymbols():
        Symbol = Symbol.copy()
        All.add(Symbol)
    return list(All)
  
  def delay(self, Cycles : int):
    for Monomial in self._monomials:
      Monomial.delay(Cycles)
      
  def getDelayed(self, Cycles : int) -> GF2Polynomial:
    Result = self.copy()
    Result.delay(Cycles)
    return Result
    
  def getLowestPower(self) -> int:
    Result = self.getDegree()
    for Monomial in self._monomials:
      MLP = Monomial.getLowestPower()
      if MLP < Result:
        Result = MLP
    return Result
  
  def rotateLowestTerm(self, Cycles : int):
    LP = self.getLowestPower()
    for Monomial in self._monomials:
      Monomial.rotateTermOfGivenPower(Cycles, LP)
    self.sort()
  
  def moduloPowers(self, Modulus : int):
    for Monomial in self._monomials:
      Monomial.moduloPowers(Modulus)
    self.sort()
    
  def subst(self, Substitution : GF2Polynomial, Letter : str = "x") -> GF2Polynomial:
    Result = GF2Polynomial(Inverted=self._inv)
    for Monomial in self._monomials:
      First = 1
      for Symbol in Monomial._symbols:
        if Symbol._letter == Letter:
          Subst = Substitution << Symbol._power
        else:
          ## FIX THAT!
          print("FIX THAT!")
          Subst = GF2Polynomial(Symbol)
        if First:
          Poly = Subst
          First = 0
        else:
          Poly *= Subst
      Result += Poly
    return Result
  
  def divmod(self, Modulus : GF2Polynomial, Debug = False) -> tuple:
    myDeg = self.getDegree()
    modDeg = Modulus.getDegree()
    Div = GF2Polynomial()
    Result = self
    while myDeg > modDeg:
      Div += GF2Polynomial(GF2Symbol('0')) << (myDeg-modDeg)
      ToAdd = Modulus << (myDeg-modDeg)
      Result = Result + ToAdd
      myDeg = Result.getDegree()
      if Debug:
        print("Div =",Div, ", \tRest =", Result)
    return Div, Result    
  
  def getSeparation(self, Characteristic : GF2Polynomial, SequenceLength : int = None) -> int:
    Char = Characteristic.copy()
    Normaliser = -Char.getLowestPower()
    Char <<= Normaliser
    if SequenceLength is None:
      SequenceLength = (1 << (Char.getDegree()))-1
    MaxSteps = len(self.getSymbols())
    Self = self.copy()
    Self <<= Normaliser
    while Self.getLowestPower() < 0:
      Self.rotateLowestTerm(SequenceLength)
    for i in range(MaxSteps):
      Delay = Self.getLowestPower()
      if (Self >> Delay) == Char:
        Delay2 = SequenceLength-Delay
        return Delay if Delay < Delay2 else -Delay2
      Self.rotateLowestTerm(SequenceLength)
    return None
      
    