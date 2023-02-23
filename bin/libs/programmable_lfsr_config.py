from aio import *

import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive

_PROG_LFSR_CONF = None

class ProgrammableLfsrConfiguration:
  __slots__ = ("_taps", "_size")
  def __init__(self, Size : int) -> None:
    self._taps = []
    self._size = Size
  def __bool__(self) -> bool:
    return len(self._taps) > 0
  def __ne__(self, __o: object) -> bool:
    return not (self.__eq__(__o))
  def __eq__(self, __o: object) -> bool:
    if len(self._taps) != len(__o._taps):
      return False
    TheirTaps = __o._taps
    for t in self._taps:
      if t not in TheirTaps:
        return False
    return True
  def remove(self, TapDict : dict) -> None:
    self._taps.remove(TapDict)
  def removeAt(self, TapDictIndex : int) -> None:
    try:
      TapDict = self._taps[TapDictIndex]
      self._taps.remove(TapDict)
    except:
      pass
  def addMandatory(self, From : int, To : int) -> dict:
    Dict = { f'{From}-{To}': [From, To] }
    self._taps.append(Dict)
    return Dict
  def addGated(self, From : int, To : int) -> dict:
    Dict = { f'{From}-{To}_off': None, f'{From}-{To}_on': [From, To] }
    self._taps.append(Dict)
    return Dict
  def addSwitched(self, *Taps) -> dict:
    Dict = {}
    for Tap in Taps:
      if Tap is not None:
        From = Tap[0]
        To = Tap[1]
        Dict[f'{From}-{To}'] = [From, To]
      else:
        Dict['None'] = None
    self._taps.append(Dict)
    return Dict
  addMux = addSwitched
  def addAllCombinationsSwitch(self, SourceList : list, DestinationList : list, IncludeNone = False) -> dict:
    List = []
    if IncludeNone:
      List.append(None)
    for S in SourceList:
      for D in DestinationList:
        List.append([S,D])
    return self.addSwitched(*List)
  addAllCombinationsMux = addAllCombinationsSwitch
  def getTaps(self) -> list:
    return self._taps
  def getSize(self) -> int:
    return self._size
  def print(self):
    for Tap in self._taps:
      Aio.print(Tap)
  def toListOfStrings(self) -> list:
    Result = []
    for Tap in self._taps:
      TapType = "MANDATORY"
      TapPositions = ""
      Values = list(Tap.values())
      if len(Values) == 2 and Values[0] is None and Values[1] is not None:
        TapType = "GATED"
        TapPositions = str(Values[1])
      elif len(Values) > 1:
        TapType = "SWITCHED"
        TapPositions = str(Values)
      else:
        TapPositions = str(Values[0])
      Result.append([TapType, TapPositions])
    return Result


# TUI ===============================================

