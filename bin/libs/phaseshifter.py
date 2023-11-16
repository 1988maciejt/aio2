from bitarray import *
from libs.aio import *
from sympy import *
from sympy.logic import *
from libs.fast_anf_algebra import *
from random import Random

# TUI =====================================================

import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive
import textual.containers as TextualContainers

class PhaseShifter:
    pass

class PhaseShifter:
    _xors = [] # reversed
    _my_source = None
    _size = 0
    _bavalue = None
    
    def createRandom(SourceObject, OutputsCount : int, MinXorInputs : int, MaxXorInputs : int) -> PhaseShifter:
        InputSize = SourceObject.getSize()    
        R = Random()
        Xors = []
        while OutputsCount > 0:
            XorInputs = R.randint(MinXorInputs, MaxXorInputs)
            Xor = []
            while XorInputs > 0:
                x = R.randint(0, InputSize-1)
                if x not in Xor:
                    Xor.append(x)
                    XorInputs -= 1
            Xor.sort()
            if Xor not in Xors:
                Xors.append(Xor)
                OutputsCount -= 1
        return PhaseShifter(SourceObject, Xors)
    
    def __init__(self, SourceObject, XorList : list) -> None:
        self.setSourceObject(SourceObject)
        self._size = len(XorList)
        self._bavalue = bitarray(self._size)
        self._xors = XorList.copy()
        self.update()
    def __str__(self) -> str:
        return str(self._bavalue)[10:-2]   
    def __repr__(self) -> str:
        return f'PhaseShifter({repr(self._my_source)}, {self._size})'     
    def __iter__(self):
        self._my_source.reset()
        self._v0 = self._my_source._baValue.copy()
        self._next_iteration = False
        return self
    def __next__(self):
        val = self._my_source._baValue
        self.next()
        if self._next_iteration:    
            if val == self._v0:
                raise StopIteration
        else:
            self._next_iteration = True
        return self._bavalue
    def __len__(self) -> int:
        return self.getSize()
    def getSize(self) -> int:
        return len(self._xors)
    def getXors(self) -> list:
        return self._xors
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
    
    def symbolicValues(self, SourceValues : list) -> list:
        Result = []
        for Xor in self._xors:
            Val = False
            for I in Xor:
                Val ^= SourceValues[I]
            Result.append(Val)
        return Result
    
    def fastANFValues(self, ANFSpace : FastANFSpace,  SourceValues : list) -> list:
        Result = []
        for Xor in self._xors:
            Val = ANFSpace.createExpression()
            for I in Xor:
                Val ^= SourceValues[I]
            Result.append(Val)
        return Result
        
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
    
    def getSequences(self, Length=0) -> list:
        Values = self.getValues(n = Length)
        if len(Values) < 1:
            return []
        SequenceLength = len(Values)
        Result = [bitarray() for i in range(self._size)]
        for word_index in range(SequenceLength):
            Word = Values[word_index]
            for flop_index in range(self._size):
                Result[flop_index].append(Word[flop_index])
        return Result
        
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
            self.update()
            result.append(self._bavalue.copy())
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
            
    def toVerilog(self, ModuleName : str):
        Inputs = self._my_source.getSize()
        Outputs = len(self._xors)
        Result = f"""module {ModuleName} (
  input wire [{Inputs-1}:0] I,
  output wire [{Outputs-1}:0] O
);
"""
        for i in range(len(self._xors)):
            Expr = f"assign O[{i}] = "
            Second = 0
            for Input in self._xors[i]:
                if Second:
                    Expr += " ^ "
                else:
                    Second = 1
                Expr += f"I[{Input}]"
            Expr += ";"
            Result += "\n" + Expr
        Result += "\n\nendmodule"
        return Result

    def tui(self):
        TUI = _PhaseShufter_tui()
        TUI.OBJ = self
        TUI.run()






class _PhaseShufter_tui(TextualApp.App):
  BINDINGS = [("q", "quit", "Quit")]
  CSS_PATH = "tui/seqreport.css"
  OBJ = None
  def compose(self) -> TextualApp.ComposeResult:
    self.dark=False
    tbl = TextualWidgets.DataTable()
    tbl.add_columns("XOR inputs", "# 1s", "Linear complexity", "# n-bit tuples")
    for i in range(len(self.OBJ._xors)):
        Row = [self.OBJ._xors[i]]
        try:
            Row.append(self.OBJ.OnesCount[i])
        except:
            Row.append("-")
        try:
            Row.append(self.OBJ.LinearComplexity[i])
        except:
            Row.append("-")
        try:
            Row.append(self.OBJ.SeqStats[i])
        except:
            Row.append("-")
        tbl.add_row(*Row)
    Primitive = "Yes" if self.OBJ._my_source.isMaximum() else "No"
    yield TextualWidgets.Header()
    yield TextualContainers.Horizontal(
      TextualContainers.Vertical(
        TextualWidgets.Static(self.OBJ._my_source.getDraw()),
        TextualWidgets.Label(f" \n   Is maximum: {Primitive}\n\n"),
        TextualWidgets.Button("OK", id="btn_ok", variant="success"),
        id="left_block"
      ),
      TextualWidgets.Static("  ", id="sep1"),
      tbl
    )
    yield TextualWidgets.Footer()
  def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
    if event.button.id == "btn_ok":
      self.app.exit()