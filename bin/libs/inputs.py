from libs.aio import *
from bitarray import *
import bitarray.util as bau


class Inputs:
  pass
class Inputs:

  __slots__ = ('_config')

  def __init__(self, Config = None):
    self._config = []
    if type(Config) is Inputs:
      self._config = Config._config.copy()
    elif type(Config) in [int, tuple]:
      self.addInput(Config)
    elif type(Config) is list:
      for Input in Config:
        self.addInput(Input)

  def __len__(self):
    return len(self._config)
  
  def __repr__(self):
    return f"Inputs({self._config})"
  
  def __str__(self):
    return str.join('\n', [f"Injector {i} \t: {self._config[i]}" for i in range(len(self._config))])
 
  def addInput(self, Input):
    """Input may be an int or a list of ints. Each number means a pin index to which the injector goes."""
    if type(Input) is int:
      self._config.append(tuple([Input]))
    elif type(Input) in [list, tuple]:
      self._config.append(tuple(Input))
    else:
      Aio.printError('Invalid input type. Allowed types: int, list, tuple.')

  def applyByXor(self, InputData : bitarray, Value : bitarray) -> bitarray:
    """Apply the input data, according to the Input configuration, to the Value."""
    if type(InputData) is str:
      InputData = bitarray(InputData)
    if len(InputData) != len(self._config):
      Aio.printError(f'Invalid input data length. Must be {len(self)} bits.')
      return None
    if type(Value) is str:
      Result = bitarray(Value)
    else:
      Result = Value.copy()
    for i in range(len(self)):
      if InputData[i]:
        for j in self._config[i]:
          Result[j] ^= 1
    return Result
    
  def applyByOr(self, InputData : bitarray, Value : bitarray) -> bitarray:
    """Apply the input data, according to the Input configuration, to the Value."""
    if type(InputData) is str:
      InputData = bitarray(InputData)
    if len(InputData) != len(self._config):
      Aio.printError(f'Invalid input data length. Must be {len(self)} bits.')
      return None
    if type(Value) is str:
      Result = bitarray(Value)
    else:
      Result = Value.copy()
    for i in range(len(self)):
      if InputData[i]:
        for j in self._config[i]:
          Result[j] = 1
    return Result

  def applyByAnd(self, InputData : bitarray, Value : bitarray) -> bitarray:
    """Apply the input data, according to the Input configuration, to the Value."""
    if type(InputData) is str:
      InputData = bitarray(InputData)
    if len(InputData) != len(self._config):
      Aio.printError(f'Invalid input data length. Must be {len(self)} bits.')
      return None
    if type(Value) is str:
      Result = bitarray(Value)
    else:
      Result = Value.copy()
    for i in range(len(self)):
      if not InputData[i]:
        for j in self._config[i]:
          Result[j] = 0
    return Result
  
  def clear(self):
    self._config = []

  def copy(self) -> Inputs:
    return Inputs(self)

  @staticmethod
  def createInputsForLfsr(LfsrSize : int, InputCount : int, DoubleInjectors : bool = True) -> Inputs:
    Result = Inputs()
    from libs.lfsr import Lfsr
    if type(LfsrSize) is Lfsr:
      LfsrSize = len(LfsrSize)
    Adder = LfsrSize / InputCount
    if DoubleInjectors:
        Adder /= 2
    StartPoint = int(round(Adder / 2, 0)) + 1
    UpperIndex = LfsrSize - StartPoint
    LowerIndex = StartPoint - 2
    while LowerIndex < 0:
        LowerIndex += LfsrSize
    for i in range(InputCount):
        if DoubleInjectors:
            Result.addInput(tuple([int(round(UpperIndex, 0)), int(round(LowerIndex, 0))]))
            LowerIndex += Adder
        else:
            Result.addInput(tuple([int(round(UpperIndex, 0))]))
        UpperIndex -= Adder
    return Result
