from libs.aio import *
from libs.lfsr import *
from libs.programmable_lfsr_config import *
import gc

class ProgrammableRingGenerator:
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
          print ("HERE!", UsedLfsrs)
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
  def getUnusedTaps(self, Optimization=True) -> list:
    if Optimization:
      self._optimized_calculations()
      return self._optimized_unused_taps
    else:
      self._non_optimized_calculations()
      return self._non_optimized_unused_taps
  def getUsedTaps(self, Optimization=True) -> list:
    if Optimization:
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
    
    