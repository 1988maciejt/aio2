from bitarray import *
from libs.aio import *

class PhaseShifter:
    _xors = [] # reversed
    _my_source = None
    _size = 0
    _bavalue = None
    def __init__(self, SourceObject, XorList : list) -> None:
        self.setSourceObject(SourceObject)
        self._size = len(XorList)
        self._bavalue = bitarray(self._size)
        self.reset()
        self._xors = []
        for Xor in reversed(XorList):
            if Aio.isType(Xor, 0):
                Xor = [Xor]
            Xor2 = []
            for Input in Xor:
                Xor2.append(-Input-1)
            self._xors.append(Xor2)
        self.update()
    def __str__(self) -> str:
        return str(self._bavalue)[10:-2]   
    def __repr__(self) -> str:
        return f'PhaseShifter({repr(self._my_source)}, {self._size})'     
    def reset(self) -> bitarray:
        self._bavalue.setall(0)
        return self._bavalue
    def getValue(self) -> bitarray:
        return self._bavalue
    def update(self) -> bitarray:
        self._bavalue.setall(0)
        ival = self._my_source.getValue()
        for i in range(self._size):
            Xor = self._xors[i]
            V = 0
            for Input in Xor:
                V ^= ival[Input]
            self._bavalue[i] = V
        return self._bavalue
    def next(self, steps = 1) -> bitarray:
        self._my_source.next(steps)
        return self.update()
    def setSourceObject(self, SourceObject) -> bool:
        try:
            test = SourceObject.getValue()
            self._my_source = SourceObject
            return True
        except:
            Aio.printError("The source object must have getValue() method giving bitarray object")
        return False
    def getSourceObject(self):
        return self._my_source
    def getValues(self, n = 0, step = 1, reset = True) -> list:
        """Returns a list containing consecutive values of the LFSR.

        Args:
            n (int, optional): How many steps to simulate for. If M= 0 then maximum period is obtained. Defaults to 0.
            step (int, optional): steps (clock pulses) per iteration. Defaults to 1.
            reset (bool, optional): If True, then the source is resetted to the 0x1 value before simulation. Defaults to True.

        Returns:
            list of bitarrays.
        """
        if n <= 0:
            n = self._my_source.getPeriod()
        if reset:
            self._my_source.reset()
        result = []
        for i in range(n):
            result._my_source.append(self._bavalue.copy())
            self.next(step)
        return result
    def printValues(self, n = 0, step = 1, reset = True, IncludeSource = False) -> None:
        """Prints the consecutive binary values of the LFSR.

        Args:
            n (int, optional): How many steps to simulate for. If M= 0 then maximum period is obtained. Defaults to 0.
            step (int, optional): steps (clock pulses) per iteration. Defaults to 1.
            reset (bool, optional): If True, then the source is resetted to the 0x1 value before simulation. Defaults to True.
        """
        if n <= 0:
            n = self._my_source.getPeriod()
        if reset:
            self._my_source.reset()
        for i in range(n):
            if IncludeSource:
                Aio.print(self._my_source, self)
            else:
                Aio.print(self)
            self.next(step)
