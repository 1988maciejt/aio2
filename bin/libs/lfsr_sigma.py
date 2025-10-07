from libs.lfsr import *


class SigmaLfsr (Lfsr):

    _value = []
    _bits_per_pos = 0
    _modulus = 0
    
    def tui():
        Aio.printError("SigmaLfsr has no TUI")
        return None
    
    def __str__(self) -> str:
        width = len(str(self._modulus - 1))
        Result = ""
        for V in reversed(self._value):
            Result +=  f"{V:0{width}d} "
        return Result
    
    def __repr__(self) -> str:
        result = "SigmaLfsr("
        if self._type == LfsrType.Galois:
            result += str(self._my_poly) + ", " + str(self._bits_per_pos) + ", LfsrType.Galois"
        if self._type == LfsrType.Fibonacci:
            result += str(self._my_poly) + ", " + str(self._bits_per_pos) + ", LfsrType.Fibonacci"
        if self._type == LfsrType.RingGenerator:
            result += str(self._my_poly) + ", " + str(self._bits_per_pos) + ", LfsrType.RingGenerator"
        if self._type == LfsrType.RingWithSpecifiedTaps:
            result += str(self._size) + ", " + str(self._bits_per_pos) + ", LfsrType.RingWithSpecifiedTaps, " + str(self._taps)
            result += ")"
        return result

    def __init__(self, polynomial, BitsPerPosition : int = 1, lfsr_type = LfsrType.Fibonacci, manual_taps = []):
        try:
            super().__init__(polynomial, lfsr_type, manual_taps)
        except:
            pass
        if "SigmaLfsr" in str(type(polynomial)):
            self._value = copy.deepcopy(polynomial._value)
            self._bits_per_pos = polynomial._bits_per_pos
            self._modulus = polynomial._modulus
            return
        if type(Polynomial([0])) != type(polynomial):
            self._value = [0 for _ in range(self._size)]
            self._bits_per_pos = BitsPerPosition
            self._modulus = (1 << self._bits_per_pos)
        else:
            Aio.printError("SigmaLfsr polynomial must be a Polynomial of SigmaLfsr object")
            return
        self.reset()

    def reset(self) -> list:
        for i in range(self._size):
            self._value[i] = 0
        self._value[0] = 1
        return self._value
    
    def getValue(self) -> list:
        return self._value

    def setValue(self, Value : list):
        Value = list(Value)
        if len(Value) != len(self._value):
            Aio.printError(f"The new value is {len(Value)} bit length while should be {len(self._value)}.")
        self._value = Value

    def _next1(self):
        if self._type == LfsrType.Fibonacci:
            Feedback = 0
            for Pos in self._bamask.search(1):
                Feedback += self._value[Pos]
            Feedback = Feedback % self._modulus
            self._value = self._value[1:] + [Feedback]
            return self._value
        elif self._type == LfsrType.Galois:
            lbit = self._value[0]
            self._value = self._value[1:] + [0]
            if lbit != 0:
                for Pos in self._bamask.search(1):
                    self._value[Pos] = (self._value[Pos] + lbit) % self._modulus
            return self._value
        elif self._type == LfsrType.RingGenerator or self._type == LfsrType.RingWithSpecifiedTaps:
            lbit = self._value[0]
            nval = self._value[1:] + [lbit]
            for tap in self._taps:
                nval[tap[1]] = (nval[tap[1]] + self._value[tap[0]]) % self._modulus
            self._value = nval
            return self._value
        return [0 for _ in range(self._size)]
    
    def next(self, steps=1) -> list:
        for _ in range(steps):
            self._next1()
        return self._value
    
    def getPeriod(self) -> int:
        MaxResult = Int.mersenne(self._size) * self._bits_per_pos
        #if self.isMaximum():
        #    return MaxResult
        self.reset()
        value0 = self._value.copy()
        valuebefore = self._value.copy()
        valuex = self.next().copy()
        for i in range(MaxResult+1):
            if valuex == value0:
                return i+1
            elif valuex == valuebefore:
                return 1
            valuebefore = valuex
            valuex = self.next().copy()  
        return -1      
    
    def printValues(self, n = 0, step = 1, reset = True) -> None:
        if n <= 0:
            val0 = self._value.copy()
            n = self.getPeriod()
            self._value = val0
        if reset:
            self.reset()
        for i in range(n):
            Aio.print(self)
            self.next(step)