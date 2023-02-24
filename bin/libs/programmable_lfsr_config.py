from aio import *

import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive
from libs.asci_drawing import AsciiDrawing_Characters 
import ast

_PROG_LFSR_CONF = None

class ProgrammableLfsrConfiguration:
  pass
class ProgrammableLfsrConfiguration:
  __slots__ = ("_taps", "_size")
  def copy(self) -> ProgrammableLfsrConfiguration:
    Result = ProgrammableLfsrConfiguration(self._size)
    Result._taps = self._taps.copy()
    return Result
  def __init__(self, Size : int) -> None:
    self._taps = []
    self._size = Size
  def __bool__(self) -> bool:
    return len(self._taps) > 0
  def __ne__(self, __o: object) -> bool:
    return not (self.__eq__(__o))
  def __eq__(self, __o: object) -> bool:
    if self._size != __o._size:
      return False
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
  def shiftLeft(self, TapIndex : int):
    if 0 <= TapIndex < len(self._taps):
      TapDict = self._taps[TapIndex]
      self._taps.remove(TapDict)
      if TapIndex == 0:
        self._taps.append(TapDict)
      else:
        self._taps.insert(TapIndex-1, TapDict)
  def shiftRight(self, TapIndex : int):
    if 0 <= TapIndex < len(self._taps):
      TapDict = self._taps[TapIndex]
      self._taps.remove(TapDict)
      if TapIndex == len(self._taps):
        self._taps.insert(0, TapDict)
      else:
        self._taps.insert(TapIndex+1, TapDict)
  def addMandatory(self, From : int, To : int) -> dict:
    DictM = { f'{From}-{To}': [From, To] }
    DictG = { f'{From}-{To}_off': None, f'{From}-{To}_on': [From, To] }
    if DictG in self._taps:
      self._taps.remove(DictG)
    if DictM not in self._taps:
      self._taps.append(DictM)
    return DictM
  def addGated(self, From : int, To : int) -> dict:
    DictM = { f'{From}-{To}': [From, To] }
    DictG = { f'{From}-{To}_off': None, f'{From}-{To}_on': [From, To] }
    if DictM in self._taps:
      self._taps.remove(DictM)
    if DictG not in self._taps:
      self._taps.append(DictG)
    return DictG
  def addSwitched(self, *Taps) -> dict:
    Dict = {}
    for Tap in Taps:
      if Tap is not None:
        From = Tap[0]
        To = Tap[1]
        Dict[f'{From}-{To}'] = [From, To]
      else:
        Dict['None'] = None
    if Dict not in self._taps:
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
  
  def tui(self):
    global _PROG_LFSR_CONF
    _PROG_LFSR_CONF = self.copy()
    ProgrammableLfsrConfigTui().run()
    return _PROG_LFSR_CONF


# TUI ===============================================


class _AddTap(TextualWidgets.Static):
  def compose(self):
    yield TextualWidgets.Label(" \nFrom", id="add_tap_from_lbl")
    yield TextualWidgets.Input(id="add_tap_from")
    yield TextualWidgets.Label(" \nTo", id="add_tap_to_lbl")
    yield TextualWidgets.Input(id="add_tap_to")
    
class _SetSize(TextualWidgets.Static):
  def compose(self):
    global _PROG_LFSR_CONF
    yield TextualWidgets.Label(" \nNew size:", id="set_size_lbl")
    yield TextualWidgets.Input(str(_PROG_LFSR_CONF.getSize()), id="set_size")

class _Table(TextualWidgets.Static):
  Config = TextualReactive.reactive([])
  Size = TextualReactive.reactive(-1)
  def compose(self):
    yield TextualWidgets.Static("  Size of the register:", id="section_name1")
    yield TextualWidgets.Static(" ", id="size_widget")
    yield TextualWidgets.Static(" ")
    yield TextualWidgets.Static("  Configurable taps list:", id="section_name2")
    yield TextualWidgets.DataTable(id="config", zebra_stripes=1)
  def on_mount(self):
    self.set_interval(0.2, self.refresh_variables)
    ConfTable = self.query_one(TextualWidgets.DataTable)
    ConfTable.add_columns("Type", "Connections", ".", ".", ".")
  def refresh_variables(self):
    global _PROG_LFSR_CONF
    self.Config = _PROG_LFSR_CONF.toListOfStrings()
    self.Size = _PROG_LFSR_CONF.getSize()
  def watch_Config(self):
    ConfTable = self.query_one("#config", TextualWidgets.DataTable)
    ConfTable.clear()
    for Tap in self.Config:
      ConfTable.add_row(Tap[0], Tap[1], "[REMOVE]", AsciiDrawing_Characters.UP_ARROW, AsciiDrawing_Characters.DOWN_ARROW)
  def watch_Size(self):
    SizeWidget = self.query_one("#size_widget", TextualWidgets.Static)
    SizeWidget.update(f"       {self.Size}")
  def on_data_table_cell_selected(self, event: TextualWidgets.DataTable.CellSelected) -> None:
    global _PROG_LFSR_CONF
    TapIndex = event.coordinate.row
    Command = event.coordinate.column
    if Command == 2:
      _PROG_LFSR_CONF.removeAt(TapIndex)
    elif Command == 3:
      _PROG_LFSR_CONF.shiftLeft(TapIndex)
    elif Command == 4:
      _PROG_LFSR_CONF.shiftRight(TapIndex)
    
class _Config(TextualWidgets.Static):
  def compose(self):
    yield TextualWidgets.Static("  LFSR SIZE ", id="section_name1")
    yield _SetSize()
    yield TextualWidgets.Button("Set LFSR size", id="btn_set_size")
    yield TextualWidgets.Static("  SIMPLE TAPS", id="section_name2")
    yield _AddTap()
    yield TextualWidgets.Button("Add mandatory tap", id="btn_add_mandatory")
    yield TextualWidgets.Button("Add gated tap", id="btn_add_gated")
    yield TextualWidgets.Static("  SWITCHED TAPS ", id="section_name3")
    yield TextualWidgets.Label(
"""To add switched tap, define taps i.e.:
  [1,2], [5,6], [3,6]
To add all combinations switch enter sources and destinations lists, i.e.:
  [1,2,3], [6,7,8]
""")
    yield TextualWidgets.Input("[<from>, <to>], ...", id="input_switched")
    yield TextualWidgets.Button("Add switched taps", id="btn_add_switched")
    yield TextualWidgets.Button("Add All-Combinations switch", id="btn_add_all_switched")
  def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
    global _PROG_LFSR_CONF
    id = event.button.id
    try:
      if id == "btn_set_size":
        SizeW = self.query_one(_SetSize)
        Size = int(SizeW.query_one("#set_size").value)
        if Size > 0:
          _PROG_LFSR_CONF._size = Size
      elif id == "btn_add_mandatory":
        ATap = self.query_one(_AddTap)
        From = int(ATap.query_one("#add_tap_from").value)
        To = int(ATap.query_one("#add_tap_to").value)
        _PROG_LFSR_CONF.addMandatory(From, To)
      elif id == "btn_add_gated":
        ATap = self.query_one(_AddTap)
        From = int(ATap.query_one("#add_tap_from").value)
        To = int(ATap.query_one("#add_tap_to").value)
        _PROG_LFSR_CONF.addGated(From, To)
      elif id == "btn_add_switched":
        Val = list(ast.literal_eval(self.query_one("#input_switched", TextualWidgets.Input).value))
        _PROG_LFSR_CONF.addSwitched(*Val)
      elif id == "btn_add_all_switched":
        Val = list(ast.literal_eval(self.query_one("#input_switched", TextualWidgets.Input).value))
        if len(Val) == 2:
          _PROG_LFSR_CONF.addAllCombinationsSwitch(*Val)
    except:
      pass
  
class _HLayout(TextualWidgets.Static):
  def compose(self):
    yield _Config()
    yield _Table()
  
class ProgrammableLfsrConfigTui(TextualApp.App):
  BINDINGS = [("q", "quit", "Quit")]
  CSS_PATH = "tui/programmable_lfsr_config.css"
  def compose(self):
    yield TextualWidgets.Header()
    yield _HLayout()
    yield TextualWidgets.Footer()
  def on_mount(self):
    self.dark = False