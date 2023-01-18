from aio import *

class ProgrammableLfsrConfiguration:
  __slots__ = ("_taps", "_size")
  def __init__(self, Size : int) -> None:
    self._taps = []
    self._size = Size
  def remove(self, TapDict : dict) -> None:
    self._taps.remove(TapDict)
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
