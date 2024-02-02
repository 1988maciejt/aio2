from libs.aio import *
from libs.lfsr import *
from libs.programmable_lfsr_config import *
from libs.pandas_table import *
import gc
from math import log2
import bitarray.util as bau
import asyncio


import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive


_PROG_LFSR = None
_LFSR = None
_SELECTED_TAPS = None
_LFSR_SIM = []


class ProgrammableLfsr:
  _polys = {}
  _polys_done = 0
  _lfsrs = []
  _lfsrs_done = 0
  _all_taps = []
  _taps_list = []
  _size = 0
  _optimized_lfsrs = []
  _optimized_used_taps = []
  _optimized_unused_taps = []
  _optimized_polys = {}
  _optimized_done = 0
  _non_optimized_done = 0
  _non_optimized_used_taps = []
  _non_optimized_unused_taps = []
  _taps_only = 0
  def __repr__(self) -> str:
    return f'ProgrammableRingGenerator({self._size}, {self._taps_list})'
  def __str__(self) -> str:
    return repr(self)
  def __del__(self):
    self.clear()
  def clear(self):
    self._lfsrs.clear()
    self._polys.clear()
    self._lfsrs_done = 0
    self._polys_done = 0
    self._all_taps.clear()
    self._optimized_lfsrs.clear()
    self._optimized_used_taps.clear()
    self._optimized_unused_taps.clear()
    self._optimized_polys.clear()
    self._optimized_done = 0
    self._non_optimized_done = 0
    self._non_optimized_used_taps.clear()
    self._non_optimized_unused_taps.clear()
  def __init__(self, SizeOrProgrammableLfsrConfiguration : int, TapsList = [], OperateOnTapsOnly=False) -> None:
    if Aio.isType(SizeOrProgrammableLfsrConfiguration, "ProgrammableLfsrConfiguration"):
      Size = SizeOrProgrammableLfsrConfiguration.getSize()
      TapsList = SizeOrProgrammableLfsrConfiguration.getTaps()
    else:
      Size = int(SizeOrProgrammableLfsrConfiguration)
    self._taps_list = TapsList.copy()
    self._size = Size
    self._lfsrs = []
    self._polys = {}
    self._lfsrs_done = 0
    self._polys_done = 0
    self._all_taps = []
    self._optimized_lfsrs = []
    self._optimized_used_taps = []
    self._optimized_unused_taps = []
    self._optimized_polys = {}
    self._optimized_done = 0
    self._non_optimized_done = 0
    self._non_optimized_used_taps = []
    self._non_optimized_unused_taps = []
    self._taps_only = OperateOnTapsOnly
    for Tap in TapsList:
      for TName in Tap.keys():
        if not (Tap[TName] is None):
          self._all_taps.append(Tap[TName])
  def _getLfsrs(self) -> list:
    if not self._lfsrs_done:
      self._lfsrs = Lfsr.listMaximumLfsrsHavingSpecifiedTaps(self._size, self._taps_list, GetTapsOnly=self._taps_only)
      self._lfsrs_done = 1
    return self._lfsrs
  def _polys_dict_calculation(self):
    if not self._polys_done:
      for lfsr in self.getLfsrs(False):
        if self._taps_only:
          poly = Polynomial.decodeUsingBerlekampMassey(Lfsr(self._size, RING_WITH_SPECIFIED_TAPS, lfsr.copy()).getSequence(Length=self._size*2+2))
        else:
          poly = Polynomial.decodeUsingBerlekampMassey(lfsr.getSequence(Length=lfsr._size*2+2))   
        if poly in self._polys:
          self._polys[poly].append(lfsr)
        else:
          self._polys[poly] = [lfsr]
      self._polys_done = 1    
      gc.collect()
  def getSize(self) -> int:
    return self._size
  def getPolynomialsAndLfsrsDictionary(self, Optimization=False) -> dict:
    if Optimization:
      self._optimized_calculations()
      return self._optimized_polys
    else:
      self._polys_dict_calculation()
      return self._polys
  def getPolynomials(self) -> list:
    return list(self.getPolynomialsAndLfsrsDictionary(False).keys())
  def getAllPosssibleTaps(self) -> list:
    return self._all_taps.copy()
  def _optimized_calculations(self):
    if not self._optimized_done:      
      dict = self.getPolynomialsAndLfsrsDictionary(False)
      polys = dict.keys()
      if len(polys) < 1:
        self._optimized_done = 1
        return
      MinimumCount = 0
      MinimumPoly = None
      for p in polys:
        if (MinimumPoly is None) or (len(dict[p]) < MinimumCount):
          MinimumCount = len(dict[p])
          MinimumPoly = p
      MinimumUsedTaps = None
      MinimumUsedLfsrs = None
      for lfsr0 in dict[MinimumPoly]:
        if self._taps_only:
          UsedTaps = lfsr0.copy()
        else:
          UsedTaps = lfsr0.getTaps().copy()
        UsedLfsrs = [lfsr0]
        Polys = {}
        for p in polys:
          if p == MinimumPoly:
            Polys[p] = lfsr0
            continue
          MinimumCount = -1
          MinimumLfsr = None
          for lfsr in dict[p]:
            NewCntr = 0
            if self._taps_only:
              XTaps = lfsr
            else:
              XTaps = lfsr.getTaps()
            for Tap in XTaps:
              if not (Tap in UsedTaps):
                NewCntr += 1
            if (MinimumLfsr is None) or (NewCntr < MinimumCount):
              MinimumCount = NewCntr
              MinimumLfsr = lfsr
          UsedLfsrs.append(MinimumLfsr)
          Polys[p] = MinimumLfsr
          if self._taps_only:
            XTaps = MinimumLfsr
          else:
            XTaps = MinimumLfsr.getTaps()
          for Tap in XTaps:
            if not (Tap in UsedTaps):
              UsedTaps.append(Tap)
        if (MinimumUsedTaps is None) or (len(UsedTaps) < len(MinimumUsedTaps)):
          MinimumUsedTaps = UsedTaps
          MinimumUsedLfsrs = UsedLfsrs
      UnusedTaps = []
      for Tap in self._all_taps:
        if not (Tap in MinimumUsedTaps):
          UnusedTaps.append(Tap)
      self._optimized_used_taps = MinimumUsedTaps
      self._optimized_lfsrs = MinimumUsedLfsrs
      self._optimized_unused_taps = UnusedTaps
      self._optimized_polys = Polys
      self._optimized_done = 1
      gc.collect()
  def _non_optimized_calculations(self):
    if not self._non_optimized_done:
      UsedTaps = []
      dict = self.getPolynomialsAndLfsrsDictionary(False)
      polys = dict.keys()
      if len(polys) <= 1:
        self._non_optimized_done = 1
        return
      for p in polys:
        for lfsr in dict[p]:
          if self._taps_only:
            XTaps = lfsr
          else:
            XTaps = lfsr.getTaps()
          for Tap in XTaps:
            if not (Tap in UsedTaps):
              UsedTaps.append(Tap)
      UnusedTaps = []
      for Tap in self._all_taps:
        if not (Tap in UsedTaps):
          UnusedTaps.append(Tap)
      self._non_optimized_used_taps = UsedTaps
      self._non_optimized_unused_taps = UnusedTaps
      self._non_optimized_done = 1
      gc.collect()
  def getUnusedTaps(self, optimization=True) -> list:
    if optimization:
      self._optimized_calculations()
      return self._optimized_unused_taps
    else:
      self._non_optimized_calculations()
      return self._non_optimized_unused_taps
  def getUsedTaps(self, optimization=True) -> list:
    if optimization:
      self._optimized_calculations()
      return self._optimized_used_taps
    else:
      self._non_optimized_calculations()
      return self._non_optimized_used_taps
  def getLfsrs(self, Optimization=False) -> list:
    if Optimization:
      self._optimized_calculations()
      return self._optimized_lfsrs
    else:
      return self._getLfsrs()
  def toVerilog(self, ModuleName : str, InjectorIndexesList = []):
    ConfigDict = {}
    ConfigBits = 0
    MandatoryTaps = []
    ValIndex = 0
    for tap in self._taps_list:
      Bits = ceil(log2(len(tap)))
      ConfigBits += Bits
      if Bits == 0:
        mtap = list(tap.values())[0]
        MandatoryTaps.append([f"O[{mtap[0]}]", mtap[1]])
        continue
      Bus = (ConfigBits-1, ConfigBits-Bits)
      Keys = list(tap.keys())
      Sources = {}
      Destinations = {}
      for i in range(len(Keys)):
        Condition = f"{Bits}'d{i}"
        Key = Keys[i]
        Connection = tap[Key]
        if Connection is None:
          #Sources[Condition] = "1'b0"
          continue
        Sources[Condition] = f"O[{Connection[0]}]"
        Destinations[Condition] = Connection[1]
      Value = f"T{ValIndex}"
      ValIndex += 1
      TapConfig = {}
      TapConfig["bus"] = Bus
      if Bus[0] == Bus[1]:
        TapConfig["configbus"] = f"config_vector[{Bus[0]}]"
      else:
        TapConfig["configbus"] = f"config_vector[{Bus[0]}:{Bus[1]}]"
      TapConfig["sources"] = Sources
      TapConfig["destinations"] = Destinations
      ConfigDict[Value] = TapConfig
    Wires = ""
    Always = ""
    DestSignalsConditions = {}
    DestSignalsSources = {}
    ConfiguredTaps = {}
    SignalsLowLevelDict = {}
    for Key in ConfigDict.keys():
      Sources = ConfigDict[Key]["sources"]
      Destinations = ConfigDict[Key]["destinations"]
      ConfigBus = ConfigDict[Key]["configbus"]
      Wires += f"reg {Key};\n"
      Always += f"\nalways @ (*) begin\n"
      Always += f"  {Key} <= 1'b0;\n"
      UsedConfigValues = []
      for Source in Sources.keys():
        ConfigValue = Source
        if ConfigValue not in UsedConfigValues:
          SourceFlop = Sources[Source]
          Always += f"  if ({ConfigBus} == {ConfigValue}) begin\n"
          Always += f"    {Key} <= {SourceFlop};\n"
          Always += f"  end\n"
          UsedConfigValues.append(ConfigValue)
      Always += f"end\n"
      DestFlops = []
      for Dest in Destinations.keys():
        ConfigValue = Dest
        DestFlop = Destinations[Dest]
        SignalName = f"{Key}_{DestFlop}"
        SignalsLowLevelDict[SignalName] = Key
        Aux = ConfiguredTaps.get(DestFlop, [])
        if SignalName not in Aux:
          Aux.append(SignalName)
        ConfiguredTaps[DestFlop] = Aux
        if DestFlop not in DestFlops:
          Wires += f"reg {SignalName};\n"
          DestFlops.append(DestFlop)
        Aux = DestSignalsConditions.get(SignalName, [])
        Condition = f"{ConfigBus} == {ConfigValue}"
        Aux.append(Condition)
        DestSignalsConditions[SignalName] = Aux
        DestSignalsSources[SignalName] = Key
    for Key in DestSignalsConditions.keys():
      Conditions = DestSignalsConditions[Key]
      FullCondition = ""
      for i in range(len(Conditions)):
        if i > 0:
          FullCondition += " || "
        FullCondition += f"({Conditions[i]})"
      Always += f"\nalways @ (*) begin\n"
      Always += f"  {Key} <= 1'b0;\n"
      Always += f"  if ({FullCondition}) begin\n"
      Always += f"    {Key} <= {SignalsLowLevelDict[Key]};\n"
      Always += f"  end\n"
      Always += f"end\n"
    for Tap in MandatoryTaps:
      Aux = ConfiguredTaps.get(Tap[1], [])
      Aux.append(Tap[0])
      ConfiguredTaps[Tap[1]] = Aux
    for i in range(len(InjectorIndexesList)):
      Source = f"injectors[{i}]"
      Aux = ConfiguredTaps.get(InjectorIndexesList[i], [])
      Aux.append(Source)
      ConfiguredTaps[InjectorIndexesList[i]] = Aux
    Module = \
f'''module {ModuleName} (
  input wire clk,
  input wire enable,
  input wire reset,
  input wire [{ConfigBits-1}:0] config_vector,
'''
    if len(InjectorIndexesList) > 0:
      Module += f"  input wire [{len(InjectorIndexesList)-1}:0] injectors,\n"
    Module += \
f'''  output reg [{self.getSize()-1}:0] O
);

{Wires}
{Always}
always @ (posedge clk or posedge reset) begin
  if (reset) begin
    O <= {self.getSize()}'d0;
  end else begin
    if (enable) begin
'''
    for i in range(self.getSize()):
      DestFlop = f"O[{i}]"
      SourceFlop = f"O[{(i+1)%self._size}]"
      Line = f"      {DestFlop} <= {SourceFlop}"
      for S in ConfiguredTaps.get(i, []):
        Line += f" ^ {S}"
      Line += ";\n"
      Module += Line;
    Module += \
f'''    end
  end
end
    
endmodule'''
    return Module
  
  def getSize(self) -> int:
    return self._size
  
  def getConfig(self) -> ProgrammableLfsrConfiguration:
    Result = ProgrammableLfsrConfiguration(self._size)
    Result._taps = self._taps_list
    return Result
  
  def getLfsr(self, Config):
    try:
      TapsList = []
      if Aio.isType(Config, []):
        for i in range(len(self._taps_list)):
          tap = self._taps_list[i]
          conf = Config[i]
          iTap = tap[conf]
          if iTap is not None:
            TapsList.append(iTap)
      else:
        ConfLen = self.getConfigVectorLength()
        if ConfLen <= 0:
          return Lfsr(self._size, RING_WITH_SPECIFIED_TAPS, [])
        if Aio.isType(Config, 0):
          Config = bau.int2ba(Config, self.getConfigVectorLength(), endian='little')
        elif Aio.isType(Config, "str"):
          Config = bitarray(Config)
        B0 = 0
        for tap in self._taps_list:
          Bits = ceil(log2(len(tap)))
          B1 = B0 + Bits
          if Bits == 0:
            iTap = list(tap.values())[0]
            if iTap is not None:
              TapsList.append(iTap)
            continue
          S = Config[B0:B1]
          B0 += Bits
          S.reverse()
          keys = list(tap.keys())
          Index = bau.ba2int(S)
          iTap = tap[keys[Index]]
          if iTap is not None:
            TapsList.append(iTap)
      return Lfsr(self._size, RING_WITH_SPECIFIED_TAPS, TapsList)
    except Exception as inst:
      Aio.printError(inst)
      return None
    
  def getConfigVectorLength(self) -> int:
    Result = 0
    for tap in self._taps_list:
      Result += ceil(log2(len(tap)))
    return Result
  
  def printConfigVectorReport(self):
    PT = PandasTable(["CONTROL_VECTOR_BITS", "CONTROL_VALUE", "CONTROL_NAME", "TAP"], AutoId=1, AddVerticalSpaces=0)
    B0 = 0
    for tap in self._taps_list:
      Bits = ceil(log2(len(tap)))
      B1 = B0 + Bits
      BitsStr = f"[{B0}:{B1}]"
      B0 += Bits
      IndexStr = ""
      NameStr = ""
      ValStr = ""
      Second = 0
      Index = 0
      for key in tap.keys():
        val = tap[key]
        istr = str(bau.int2ba(Index, Bits, endian='little'))[9:-1]
        if Second:
          IndexStr += "\n"
          NameStr += "\n"
          ValStr += "\n"
        else:
          Second = 1
        IndexStr += f"{istr}"
        NameStr += f"{key}"
        ValStr += f"{val}"
        Index += 1
      PT.add([BitsStr, IndexStr, NameStr, ValStr])
    PT.print()
    
  def tui(self):
    global _PROG_LFSR, _LFSR, _SELECTED_TAPS
    _PROG_LFSR = self
    _LFSR = self.getLfsr(0)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tui = _ProgrammableLfsrTui()
    tui.run()
    if tui.EXE == "ok":
      return _LFSR
    return None
  
  def tuiEdit(self):
    Config = self.getConfig().tui()
    if Config is not None:
      self.__init__(Config)
    
  @staticmethod
  def tuiCreate(Size = 32):
    Config = ProgrammableLfsrConfiguration(Size).tui()
    if Config is None:
      return None
    return ProgrammableLfsr(Config)
  
  
# TUI ===========================================================  
  
def _lfsr_sim_refresh(n = 32):
    global _LFSR, _LFSR_SIM
    Lst2 = []
    Lst1 = _LFSR.getValues(n)
    for I in Lst1:
      Lst2.append([Bitarray.toString(I), I.count(1)])
    _LFSR_SIM = Lst2

def _lfsr_sim_append():
    global _LFSR_SIM
    _lfsr_sim_refresh(len(_LFSR_SIM)<<1)
  
class _TTap(TextualWidgets.DataTable):
  TAP_DICT = {}
  TAP_INDEX = 0
  def on_mount(self):
    self.add_columns(f"Switch {self.TAP_INDEX}", "Connection")
    for Switch in self.TAP_DICT.keys():
      self.add_row(Switch, self.TAP_DICT[Switch])
  def on_data_table_cell_selected(self, event: TextualWidgets.DataTable.CellSelected) -> None:
    global _SELECTED_TAPS, _LFSR, _PROG_LFSR
    TapValue = event.coordinate.row
    TapSwitch = list(self.TAP_DICT.keys())[TapValue]
    _SELECTED_TAPS[self.TAP_INDEX] = TapSwitch
    _LFSR = _PROG_LFSR.getLfsr(_SELECTED_TAPS)
    _lfsr_sim_refresh()
  
class _VTop(TextualWidgets.Static):
  LfsrDraw = TextualReactive.reactive("")
  Lbl = None
  def compose(self):
    self.Lbl = TextualWidgets.Label()
    yield self.Lbl 
  def on_mount(self):
    self.set_interval(0.2, self.update_LfsrDraw)
  def update_LfsrDraw(self):
    global _LFSR
    self.LfsrDraw = _LFSR.getDraw()
  def watch_LfsrDraw(self):
    self.Lbl.update(self.LfsrDraw)

class _VMiddle(TextualWidgets.Static):
  LfsrPoly = TextualReactive.reactive(Polynomial([1,0]))
  def on_mount(self):
    self.set_interval(0.2, self.update_LfsrPoly)
  def update_LfsrPoly(self):
    global _LFSR
    self.LfsrPoly = Polynomial.decodeUsingBerlekampMassey(_LFSR)
  def watch_LfsrPoly(self):
    global _LFSR
    l = _LFSR.copy()
    Max = "IS MAXIMUM" if l.isMaximum() else "is NOT maximum"
    Prim = "IS PRIMITIVE" if self.LfsrPoly.isPrimitive() else "Is NOT primitive"
    self.update(f"This LFSR {Max}.\nCharacteristic polynomial {Prim}: {self.LfsrPoly}")

class _VBottom(TextualWidgets.Static):
    SimROws = TextualReactive.reactive([])
    def compose(self):
        self.Data = TextualWidgets.DataTable()
        yield TextualWidgets.DataTable()
        yield TextualWidgets.Label("")
    def on_mount(self):
        _lfsr_sim_refresh()
        self.set_interval(0.5, self.update_simdata)
        table = self.query_one(TextualWidgets.DataTable)
        table.add_columns("#Cycle", "Value (n-1, ..., 0)", "#1s")
    def update_simdata(self):
        global _LFSR_SIM
        self.SimROws = _LFSR_SIM
    def watch_SimROws(self):
        global _LFSR_SIM
        table = self.query_one(TextualWidgets.DataTable)
        table.clear()
        for i in range(len(_LFSR_SIM)):
          v = _LFSR_SIM[i]
          table.add_row(i, v[0], v[1])
  
class _LeftMenu(TextualWidgets.Static):
  def compose(self):
    global _SELECTED_TAPS, _PROG_LFSR
    _SELECTED_TAPS = []
    TapsDicts = _PROG_LFSR._taps_list
    yield TextualWidgets.Button("Append sim table", id="asim")
    for i in range(len(TapsDicts)):
      TapsDict = TapsDicts[i]
      _SELECTED_TAPS.append(list(TapsDict.keys())[0])
      TTap = _TTap()
      TTap.TAP_DICT = TapsDict
      TTap.TAP_INDEX = i
      yield TTap
    yield TextualWidgets.Label(" ")
    yield TextualWidgets.Button("OK", id="btn_ok", variant="success")
    yield TextualWidgets.Button("Cancel", id="btn_cancel", variant="error")
  def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
    global _LFSR, _LFSR_SIM
    if event.button.id == "asim":
      _lfsr_sim_append()
    elif event.button.id == "btn_ok":
      self.app.EXE = "ok"
      self.app.exit()
    elif event.button.id == "btn_cancel":
      self.app.EXE = "cancel"
      self.app.exit()
      
class _HRight(TextualWidgets.Static):
  def compose(self) -> None:
    yield _VTop()
    yield _VMiddle()
    yield _VBottom()
  
class _HLayout(TextualWidgets.Static):
  def compose(self) -> None:
    yield _LeftMenu()
    yield _HRight()

class _ProgrammableLfsrTui(TextualApp.App):
  BINDINGS = [("q", "quit", "Quit"), ('a', 'asim', 'Append values')]
  CSS_PATH = "tui/programmable_lfsr.css"
  def compose(self) -> None:
    self.dark=False
    self.EXE = ""
    yield TextualWidgets.Header()
    yield _HLayout()
    yield TextualWidgets.Footer()
  def action_asim(self):
    _lfsr_sim_append()