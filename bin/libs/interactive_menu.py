from libs.lfsr import *
from libs.nlfsr import *
from libs.bent_function import *
from libs.programmable_lfsr import *
from prompt_toolkit.shortcuts import *
import ast
import pandas
from libs.pandas_table import *




def _categoryPolynomial_decode():
  Sequence = MainMenu_static.getBinSequence()
  if Sequence is None:
    return
  try:
    Poly = Polynomial.decodeUsingBerlekampMassey(Sequence)
    Aio.print("Decoded polynomial:")
    Aio.print(Poly)
    Is = "This polynomial IS primitibe" if Poly.isPrimitive() else "This polynomial IS NOT primitive."
    message_dialog(title="Decoded polynomial", text=f'{Poly}\n{Is}').run()
  except:
    message_dialog(title="Error", text=f'Incorrect sequence').run()

def _categoryPolynomial_print():
  Degree = MainMenu_static.getPolynomialDegree()
  if Degree is None:
    return
  CoeffsCount = MainMenu_static.getCoeffsCount()
  if CoeffsCount is None:
    return
  Balancing = MainMenu_static.getBalancing()
  if Balancing is None:
    return
  MinDist = MainMenu_static.getMinDistance()
  if MinDist is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  NS = MainMenu_static.getNoSuccess()
  if NS is None:
    return
  Result = Polynomial.listPrimitives(Degree, CoeffsCount, Balancing, MinDistance=MinDist, n=N, NoResultsSkippingIteration=NS)
  String = "Found polynomials:\n\n"
  Aio.print(f'Found primitives({Degree}, {CoeffsCount}, Balancing={Balancing}, MinimumDoistance={MinDist}):')
  for R in Result:
    String += f'{R}\n'
    Aio.print(R)
  message_dialog(title="Result", text=String).run()
    
def _categoryPolynomial_printTiger():
  Degree = MainMenu_static.getPolynomialDegree()
  if Degree is None:
    return
  CoeffsCount = MainMenu_static.getCoeffsCount()
  if CoeffsCount is None:
    return
  Balancing = MainMenu_static.getBalancing()
  if Balancing is None:
    return
  MinDist = MainMenu_static.getMinDistance()
  if MinDist is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  NotMatchingTapsCount = 0
  if N > 1:
    NotMatchingTapsCount = MainMenu_static.getNotMatchingTapsCount()
    if NotMatchingTapsCount is None:
      return
  NS = MainMenu_static.getNoSuccess()
  if NS is None:
    return
  Result = Polynomial.listTigerPrimitives(Degree, CoeffsCount, Balancing, MinDistance=MinDist, n=N, NoResultsSkippingIteration=NS, MinNotMatchingTapsCount=NotMatchingTapsCount)
  String = "Found tiger polynomials:\n\n"
  Aio.print(f'Found tiger primitives({Degree}, {CoeffsCount}, Balancing={Balancing}, MinimumDoistance={MinDist}):')
  for R in Result:
    String += f'{R.toTigerStr()}\n'
    Aio.print(R.toTigerStr())
  message_dialog(title="Result", text=String).run()
  
def _categoryPolynomial_printHybrid():
  Degree = MainMenu_static.getPolynomialDegree()
  if Degree is None:
    return
  CoeffsCount = MainMenu_static.getCoeffsCount()
  if CoeffsCount is None:
    return
  Balancing = MainMenu_static.getBalancing()
  if Balancing is None:
    return
  MinDist = MainMenu_static.getMinDistance()
  if MinDist is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  NotMatchingTapsCount = 0
  if N > 1:
    NotMatchingTapsCount = MainMenu_static.getNotMatchingTapsCount()
    if NotMatchingTapsCount is None:
      return
  NS = MainMenu_static.getNoSuccess()
  if NS is None:
    return
  Result = Polynomial.listHybridPrimitives(Degree, CoeffsCount, Balancing, MinDistance=MinDist, n=N, NoResultsSkippingIteration=NS, MinNotMatchingTapsCount=NotMatchingTapsCount)
  String = "Found hybrid polynomials:\n\n"
  Aio.print(f'Found hybrid primitives({Degree}, {CoeffsCount}, Balancing={Balancing}, MinimumDoistance={MinDist}):')
  for R in Result:
    String += f'{R}\n'
    Aio.print(R)
  message_dialog(title="Result", text=String).run()

def _categoryPolynomial_printDense():
  Degree = MainMenu_static.getPolynomialDegree()
  if Degree is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  Result = Polynomial.listDensePrimitives(Degree, N)
  String = "Found dense polynomials:\n\n"
  Aio.print(f'Found dense primitives ({Degree}):')
  for R in Result:
    String += f'{R}\n'
    Aio.print(R)
  message_dialog(title="Result", text=String).run()
  
def _categoryPolynomial_printEveryN():
  Degree = MainMenu_static.getPolynomialDegree()
  if Degree is None:
    return
  Section = MainMenu_static.getSectionSize()
  if Section is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  Result = Polynomial.listEveryNTapsPrimitives(Degree, Section, N)
  String = "Found every-N taps polynomials:\n\n"
  Aio.print(f'Found Every-N primitives ({Degree}, {Section}):')
  for R in Result:
    String += f'{R}\n'
    Aio.print(R)
  message_dialog(title="Result", text=String).run()

def _categoryPolynomial_checkPrimitive():
  Poly = -1
  while Poly is not None:
    Poly = MainMenu_static.getPolynomial()
    if Poly is not None:
      IsOrNot = "IS" if Poly.isPrimitive() else "IS NOT"
      message_dialog(title="Result", text=f'Polynomial\n{str(Poly)}\n{IsOrNot} PRIMITIVE!').run()

def _categoryPolynomial():
  SubCategory = -1
  while SubCategory is not None:
    SubCategory = MainMenu_static._prim_polys_menu.run()
    if SubCategory is not None:
      SubCategory()


_GlobalLfsr = Lfsr(16, RING_WITH_SPECIFIED_TAPS, [])

def _categoryLfsrWithManualTaps_subDisplay():
  global _GlobalLfsr
  Text = f'Size: {_GlobalLfsr.getSize()}\nTAPS [\n'
  for Tap in _GlobalLfsr.getTaps():
    Text += f'  {Tap},\n'
  Text += "]"
  message_dialog(
    title="Current Lfsr",
    text=Text
  ).run()
  
def _categoryLfsrWithManualTaps_subInfoDisplay():
  global _GlobalLfsr
  IsMax = "is MAXIMUM" if _GlobalLfsr.isMaximum() else "is NOT MAXIMUM"
  P = Polynomial.decodeUsingBerlekampMassey(_GlobalLfsr)
  PP = "PRIMITIVE" if P.isPrimitive() else "NOT PRIMITIVE"
  Poly = f'Decoded polynomial: {P} ({PP})'
  Text = IsMax + "\n" + Poly
  message_dialog(
    title="Information",
    text=Text
  ).run()
  
def _categoryLfsrWithManualTaps_subCreate():
  global _GlobalLfsr
  Size = MainMenu_static.getLfsrSize()
  if Size is None:
    return
  Taps = MainMenu_static.getTaps()
  if Taps is None:
    return
  del _GlobalLfsr
  _GlobalLfsr = Lfsr(Size, RING_WITH_SPECIFIED_TAPS, Taps)
  _categoryLfsrWithManualTaps_subDisplay()
  
def _categoryLfsrWithManualTaps_subMakeDual():
  global _GlobalLfsr
  _GlobalLfsr = _GlobalLfsr.getDual()
  _categoryLfsrWithManualTaps_subDisplay()
  

def _categoryLfsrWithManualTaps():
  SubCategory = -1
  while SubCategory is not None:
    SubCategory = MainMenu_static._lfsr_manual_taps_menu.run()
    if SubCategory is not None:
      SubCategory()


_GlobalProgrammableRingConfig = ProgrammableLfsrConfiguration(32)
_GlobalProgrammable = None

def _categoryProgrammableRingGenerator_subCreate():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Size = MainMenu_static.getLfsrSize()
  if Size is None:
    return
  _GlobalProgrammableRingConfig = ProgrammableLfsrConfiguration(Size)
  _GlobalProgrammable = None
  
def _categoryProgrammableRingGenerator_subStore():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Filename = input_dialog(
    title="Store programmable ring config to file",
    text="Enter file name"
  ).run()
  if Filename is None:
    return
  writeObjectToFile(Filename, _GlobalProgrammableRingConfig)
    
def _categoryProgrammableRingGenerator_subRestore():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Filename = pickFile()
  try:
    Obj = readObjectFromFile(Filename)
    if Aio.isType(Obj, _GlobalProgrammableRingConfig):
      _GlobalProgrammableRingConfig = Obj
      _categoryProgrammableRingGenerator_subDisplay()
    else:
      message_dialog(
        title="Error",
        text=f'File "{Filename}" does not include programmable ring config.'
      ).run()
  except:
    message_dialog(
      title="Error",
      text=f'Loading error.'
    ).run()
  
def _categoryProgrammableRingGenerator_subDisplay():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Text = f'SIZE: {_GlobalProgrammableRingConfig.getSize()}\n'
  for TapD in _GlobalProgrammableRingConfig.getTaps():
    TapValues = list(TapD.values())
    if len(TapValues) == 1: #<amdatory
      Tap = TapValues[0]
      Text += f'- Mandatory tap    : {Tap}\n'
    elif len(TapValues) == 2 and None in TapValues: #gated
      TapValues.remove(None)
      Tap = TapValues[0]
      Text += f'- Gated tap        : {Tap}\n'
    elif None in TapValues: #muxed with off
      TapValues.remove(None)
      Text += f'- (de)mux with off : {TapValues}\n'
    else: #muxed
      Text += f'- (de)mux          : {TapValues}\n'
  message_dialog(title="Programmable ring config", text=Text).run()
  
def _categoryProgrammableRingGenerator_subRemove():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  RemList = []
  for TapD in _GlobalProgrammableRingConfig.getTaps():
    TapValues = list(TapD.values())
    if len(TapValues) == 1: #<amdatory
      Tap = TapValues[0]
      RemList.append( (TapD, f'Mandatory tap    : {Tap}') )
    elif len(TapValues) == 2 and None in TapValues: #gated
      TapValues.remove(None)
      Tap = TapValues[0]
      RemList.append( (TapD, f'Gated tap        : {Tap}') )
    elif None in TapValues: #muxed with off
      TapValues.remove(None)
      RemList.append( (TapD, f'(de)mux with off : {TapValues}') )
    else: #muxed
      RemList.append( (TapD, f'(de)mux          : {TapValues}') )
  RT = radiolist_dialog(
    title="Tap removing",
    text="Which tap to remove?",
    values=RemList
  ).run()
  if RT is None:
    return
  _GlobalProgrammableRingConfig.remove(RT)
  _GlobalProgrammable = None
  _categoryProgrammableRingGenerator_subDisplay()
  
def _categoryProgrammableRingGenerator_subAddMandatory():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Taps = MainMenu_static.getTaps(1)
  if Taps is None:
    return
  for Tap in Taps:
    _GlobalProgrammableRingConfig.addMandatory(Tap[0], Tap[1])
  _GlobalProgrammable = None
  _categoryProgrammableRingGenerator_subDisplay()
  
def _categoryProgrammableRingGenerator_subAddGated():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Taps = MainMenu_static.getTaps(1)
  if Taps is None:
    return
  for Tap in Taps:
    _GlobalProgrammableRingConfig.addGated(Tap[0], Tap[1])
  _GlobalProgrammable = None
  _categoryProgrammableRingGenerator_subDisplay()
  
def _categoryProgrammableRingGenerator_subAddMuxed():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Taps = MainMenu_static.getTaps(1)
  if Taps is None:
    return
  _GlobalProgrammableRingConfig.addMux(*Taps)
  _GlobalProgrammable = None
  _categoryProgrammableRingGenerator_subDisplay()
  
def _categoryProgrammableRingGenerator_subAddMuxedWithOff():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  Taps = MainMenu_static.getTaps(1)
  if Taps is None:
    return
  _GlobalProgrammableRingConfig.addMux(None, *Taps)
  _GlobalProgrammable = None
  _categoryProgrammableRingGenerator_subDisplay()
  
def _categoryProgrammableRingGenerator_subDoCalculations():
  global _GlobalProgrammableRingConfig, _GlobalProgrammable
  if _GlobalProgrammable is None:
    _GlobalProgrammable = ProgrammableRingGenerator(_GlobalProgrammableRingConfig.getSize(), _GlobalProgrammableRingConfig.getTaps(), 1)
  Text  = f'Full count of maximum LFSRs       : {len(_GlobalProgrammable.getLfsrs(False))}\n'
  Text += f'Full count of maximum polynomials : {len(_GlobalProgrammable.getPolynomials())}\n'
  Text += f'OPTIMIZATION:\n'
  Text += f'  Count of used taps   : {len(_GlobalProgrammable.getUsedTaps(True))}\n'
  Text += f'       - used taps     : {_GlobalProgrammable.getUsedTaps(True)}\n'
  Text += f'  Count of unused taps : {len(_GlobalProgrammable.getUnusedTaps(True))}\n'
  Text += f'       - unused taps   : {_GlobalProgrammable.getUnusedTaps(True)}\n'
  Aio.print(Text)
  message_dialog(
    title="Programmable ring generator stats",
    text=Text
  ).run()
  
def _categoryProgrammableRingGenerator():
  SubCategory = -1
  while SubCategory is not None:
    SubCategory = MainMenu_static._programmable_ring_generator_menu.run()
    if SubCategory is not None:
      SubCategory()
      

def _categoryHybridRingGenerator_subDecodePolynomial():
  HPoly = MainMenu_static.getPolynomial()
  if HPoly is None:
    return
  Poly = Polynomial.decodeUsingBerlekampMassey(Lfsr(HPoly, HYBRID_RING))
  Result = f"""Hybrid Polynomial: 
  {Polynomial(HPoly)}
decoded characteristic polynomial:
  {Poly}
"""
  print(Result)
  message_dialog(title="Result", text=Result).run()

def _categoryTigerRingGenerator_subDecodePolynomial():
  TIgerPoly = MainMenu_static.getTigerPolynomial()
  if TIgerPoly is None:
    return
  Poly = Polynomial.decodeUsingBerlekampMassey(Lfsr(TIgerPoly, TIGER_RING))
  Result = f"""Tiger Polynomial: 
  {Polynomial(TIgerPoly).toTigerStr()}
decoded characteristic polynomial:
  {Poly}
"""
  print(Result)
  message_dialog(title="Result", text=Result).run()
  
def _categoryTigerRingGenerator():
  SubCategory = -1
  while SubCategory is not None:
    SubCategory = MainMenu_static._tiger_ring_generator_menu.run()
    if SubCategory is not None:
      SubCategory()
  
  
_GlobalNlfsr = Nlfsr(8, [])
  
def _categoryNlfsrs_createNlfsr():
  global _GlobalNlfsr
  Size = MainMenu_static.getRegisterSize()
  if Size is None:
    return
  Config = MainMenu_static.getNlfsrTaps()
  if Config is None:
    return
  _GlobalNlfsr = Nlfsr(Size, Config)
  _categoryNlfsrs_info()
  
def _categoryNlfsrs_check_period():
  global _GlobalNlfsr
  Period = _GlobalNlfsr.getPeriod()
  MaxPeriod = Int.mersenne(_GlobalNlfsr._size)
  IsMaximum = "MAXIMUM" if Period == MaxPeriod else f'NOT MAXIMUM ({round(Period * 100. / MaxPeriod, 2)}% of max)'
  Text = f'Period:  {Period}\n\n'
  Text += f'  {IsMaximum}\n'
  if Int.isPrime(Period):
    Text += f'  IS PRIME\n'
  message_dialog(title="Nlfsr - period", text=Text).run()
  
def _categoryNlfsrs_info():
  global _GlobalNlfsr
  Text =  f'Polynomial:          {_GlobalNlfsr.toBooleanExpressionFromRing(Shorten=1)}\n'
  Text += f'Polynomial REV:      {_GlobalNlfsr.toBooleanExpressionFromRing(Reversed=1, Shorten=1)}\n'
  Text += f'Polynomial COMP:     {_GlobalNlfsr.toBooleanExpressionFromRing(Complementary=1, Shorten=1)}\n'
  Text += f'Polynomial REV,COMP: {_GlobalNlfsr.toBooleanExpressionFromRing(Complementary=1, Reversed=1, Shorten=1)}\n'
  Text += f'CROSSING-FREE: {_GlobalNlfsr.isCrossingFree()}\n'
  Text += _GlobalNlfsr.getFullInfo()
  message_dialog(title="Nlfsr - info", text=Text).run()
  
def _categoryNlfsrs_searchForMaximum():
  Degree = MainMenu_static.getPolynomialDegree()
  if Degree is None:
    return
  CoeffsCount = MainMenu_static.getCoeffsCount()
  if CoeffsCount is None:
    return
  Balancing = MainMenu_static.getBalancing()
  if Balancing is None:
    return
  MinDist = MainMenu_static.getMinDistance()
  if MinDist is None:
    return
  AndShift = MainMenu_static.getAndShift()
  if AndShift is None:
    return
  MaxAndCount = MainMenu_static.getMaxAndCount()
  if MaxAndCount is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  Details = radiolist_dialog(
    title="Details",
    text="",
    values=[
      (2, "Maximum periods, beautifull only"),
      (0, "Maximum periods - all (takes more time!)"),
      (3, "Prime periods > 50%, beautifull only)"),
      (1, "Prime periods > 50% - all (takes more time!)"),
    ]
  ).run()
  if Details is None:
    return
  Poly0 = Polynomial.createPolynomial(Degree, CoeffsCount, Balancing, MinDistance=MinDist)
  Results = []
  if Details == 0:
    Results = Nlfsr.findNLRGsWithSpecifiedPeriod(Poly0, AndShift, InvertersAllowed=1, Filter=1, Iterate=1, n=N, MaxAndCount=MaxAndCount)
  elif Details == 2:
    Results = Nlfsr.findNLRGsWithSpecifiedPeriod(Poly0, AndShift, InvertersAllowed=1, BeautifullOnly=1, Filter=1, Iterate=1, n=N, MaxAndCount=MaxAndCount)
  elif Details == 1:
    Results = Nlfsr.findNLRGsWithSpecifiedPeriod(Poly0, AndShift, InvertersAllowed=1, OnlyPrimePeriods=1, PeriodLengthMinimumRatio=0.5, Iterate=1, n=N, MaxAndCount=MaxAndCount)
  elif Details == 3:
    Results = Nlfsr.findNLRGsWithSpecifiedPeriod(Poly0, AndShift, InvertersAllowed=1, BeautifullOnly=1, OnlyPrimePeriods=1, PeriodLengthMinimumRatio=0.5, Iterate=1, n=N, MaxAndCount=MaxAndCount)
  Canonical = "Canonical"
  NlfsrObject = "Python Object"
  Equations = "Taps"
  RC = "Rev/Compl"
  SmallPT = PandasTable([Canonical, NlfsrObject], AutoId=1)
  FullPT = PandasTable([RC, Canonical, Equations, NlfsrObject], AutoId=1, AddVerticalSpaces=1)
  for R in Results:
    SmallPT.add([
      R.toBooleanExpressionFromRing(Shorten=1),
      repr(R)
    ])    
    FullPT.add([
      f'  \nComplement\nReversed\nRev.,Compl.',
      f'{R.toBooleanExpressionFromRing(Shorten=1)}\n\
{R.toBooleanExpressionFromRing(Complementary=1, Shorten=1)}\n\
{R.toBooleanExpressionFromRing(Reversed=1, Shorten=1)}\n\
{R.toBooleanExpressionFromRing(Reversed=1, Complementary=1, Shorten=1)}',
      R.getFullInfo(Header=0),
      repr(R)
    ])
  Aio.print()
  FullPT.print()
  Aio.print()
  message_dialog(title="Found NLFSRs", text=SmallPT.toString()).run()

def _categoryNlfsrs():
  SubCategory = -1
  while SubCategory is not None:
    SubCategory = MainMenu_static._nlfsrs_menu.run()
    if SubCategory is not None:
      SubCategory()
  
  
def _categoryBent_printLuts():
  InputCount = MainMenu_static.getBentInputs()
  if InputCount is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  pt = PandasTable(["Sequence (LUT)"], AutoId=1)
  for x in BentFunction.listBentFunctionLuts(InputCount, N):
    pt.add([x.to01()])
  S = pt.toString()
  Aio.print(S)
  if len(pt) <= 100:
    message_dialog(title="Found bent sequences (LUTs)", text=S).run()
  else:
    message_dialog(title="Found bent sequences (LUTs)", text="Too many results.\nClose the menu to see all results.").run()

def _categoryBent():
  SubCategory = -1
  while SubCategory is not None:
    SubCategory = MainMenu_static._bent_menu.run()
    if SubCategory is not None:
      SubCategory()
  


class MainMenu_static:
  _main_menu = radiolist_dialog(
    title="Main menu",
    text="Choose category",
    values=[
      (_categoryPolynomial,                 "Primitive polynomials"),
      (_categoryLfsrWithManualTaps,         "Ring generators with manually specified taps"),
      (_categoryProgrammableRingGenerator,  "Programmable ring renegrator"),
      (_categoryTigerRingGenerator,         "Hybrid/Tiger Ring Generators"),
      (_categoryNlfsrs,                     "Nonlinear shift registers"),
      (_categoryBent,                       "Bent functions"),
    ]
  )
  _prim_polys_menu = radiolist_dialog(
    title="Primitive polynomials",
    text="What do you want to do:",
    values=[
      (_categoryPolynomial_checkPrimitive,  "Check if a given polynomial is primitive"),
      (_categoryPolynomial_print,           "Print primitives"),
      (_categoryPolynomial_printEveryN,     "Print Every-N primitives"),
      (_categoryPolynomial_printDense,      "Print dense primitives"),
      (_categoryPolynomial_printTiger,      "Print Tiger polynomials"),
      (_categoryPolynomial_printHybrid,     "Print Hybrid polynomials"),
      (_categoryPolynomial_decode,          "Decode using Berlekamp-Massey algorithm")
    ]
  )
  _lfsr_manual_taps_menu = radiolist_dialog(
    title="Ring generators with manually specified taps",
    text="What do you want to do:",
    values=[
      (_categoryLfsrWithManualTaps_subDisplay,  "Display ring generator"),
      (_categoryLfsrWithManualTaps_subCreate,   "Define ring generator"),
      (_categoryLfsrWithManualTaps_subInfoDisplay, "Is maximum? What is the polynomial?"),
      (_categoryLfsrWithManualTaps_subMakeDual,   "Make dual ring")
    ]
  )
  _programmable_ring_generator_menu = radiolist_dialog(
    title="Programmable ring generators",
    text="What do you want to do:",
    values=[
      (_categoryProgrammableRingGenerator_subDisplay,         "Display programmable ring"),
      (_categoryProgrammableRingGenerator_subCreate,          "Create new (set size)"),
      (_categoryProgrammableRingGenerator_subRestore,         "Read config from file"),
      (_categoryProgrammableRingGenerator_subStore,           "Save config to file"),
      (_categoryProgrammableRingGenerator_subAddMandatory,    "Add mandatory taps"),
      (_categoryProgrammableRingGenerator_subAddGated,        "Add gated taps"),
      (_categoryProgrammableRingGenerator_subAddMuxed,        "Add (de)muxed taps"),
      (_categoryProgrammableRingGenerator_subAddMuxedWithOff, "Add (de)muxed taps with off"),
      (_categoryProgrammableRingGenerator_subRemove,          "Remove tap"),
      (_categoryProgrammableRingGenerator_subDoCalculations,  "Stats"),
    ]
  )
  _tiger_ring_generator_menu = radiolist_dialog(
    title="Hybrid/Tiger ring generators",
    text="What do you want to do:",
    values=[
      (_categoryPolynomial_printTiger,    "Search for maximum tiger ring generators"),
      (_categoryPolynomial_printHybrid,   "Search for maximum hybrid ring generators"),
      (_categoryTigerRingGenerator_subDecodePolynomial, "Decode characteristic polynomial of Tiger Ring"),
      (_categoryHybridRingGenerator_subDecodePolynomial, "Decode characteristic polynomial o Hybrid Ring"),
    ]
  )
  _nlfsrs_menu = radiolist_dialog(
    title="Programmable ring generators",
    text="What do you want to do:",
    values=[
      (_categoryNlfsrs_createNlfsr,          "Create NLFSR"),
      (_categoryNlfsrs_info,                 "Show info"),
      (_categoryNlfsrs_check_period,         "Check period of the NLFSR"),
      (_categoryNlfsrs_searchForMaximum,     "Search for maximum NLFSRs"),
    ]
  )
  _bent_menu = radiolist_dialog(
    title="Bent functions",
    text="What do you want to do:",
    values=[
      (_categoryBent_printLuts,             "Search for bent sequences (LUTs)"),
    ]
  )
  _input_bent_inputs = input_dialog(
    title="Bent function inputs",
    text="How many inpits? (Must be even; default: 2)",
  )
  _input_tiger_polynomial = input_dialog(
    title="Tiger polynomial",
    text="Enter coefficients of a Tiger Polynomial.\n\nAttention: '-' chars may be omitted. The results is always considered as Tiger Polynomial.\nExample inputs (both describe the same, identical Tiger Ring):\n7, 5, 3, 1, 0\n7, -5, 3, -1, 0",
  )
  _input_polynomial = input_dialog(
    title="Polynomial input",
    text="Enter a list of polynomial coefficients, i.e.\n[5,4,0]\nIt is also possible to enter an integer representing a polynomial, i.e.\n0b110001",
  )
  _input_not_matching_taps_count = input_dialog(
    title="Various taps",
    text="What is the minimum required count of not matching (various) taps in results? Default is 0 (does not matter)",
  )
  _input_polynomial_degree = input_dialog(
    title="Polynomial degree",
    text="Enter polynomial degree:"
  )
  _input_register_size = input_dialog(
    title="Register size",
    text="Enter register size:"
  )
  _input_section_size = input_dialog(
    title="Section size",
    text="Enter section size (FFs between taps. Default: 4):"
  )
  _input_n_results = input_dialog(
    title="How many results?",
    text="Enter the required count of results (0 = no limit):"
  )
  _input_max_and_count = input_dialog(
    title="Max AND count?",
    text="Enter the required maximum count of AND gates (default: 0 = no limit):"
  )
  _input_polynomial_minimum_distance = input_dialog(
    title="Minimum distance",
    text="What is the required minimum distance between successive coefficients?\nDefault : 1"
  )
  _input_polynomial_balancing = input_dialog(
    title="Balancing",
    text="What is the required maximum balancing?\nBalancing means the difference between furthest and closest distance between successive coefficients.\nDefaul is 0 (does not matter)."
  )
  _input_polynomial_coeffs_count = input_dialog(
    title="Coefficients count",
    text="Coefficients count? (#taps = #coefficients - 2)\nDefault : 3"
  )
  _input_bin_sequence = input_dialog(
    title="Sequence?", 
    text="Enter a sequence of 1s and 0s:",
  )
  _input_lfsr_size = input_dialog(
    title="Lfsr size",
    text="Enter size of the Lfsr:"
  )
  _input_nlfsr_and_shift = input_dialog(
    title="AND gates",
    text="Allowed left/right shift for the second AND input (default:1):"
  )
  _input_no_success = input_dialog(
    title="Break if no result??",
    text="Enter number of iterations after which it breaks if no result (default: 0 = no limit):"
  )
  _input_taps = input_dialog(
    title="Taps list",
    text="""Enter taps. Example string:
    [3,6], [6,2]
    ..which means two taps: from FF3 output to the XOR at FF6 input and the second tap from FF6 output to the XOR at FF2 input."""
  )
  _input_nlfsr_taps = input_dialog(
    title="Taps list",
    text="""Enter non-linear taps. Each tap is a list: [<Destination> [Source0>, <Source1>, ..., <SourceN>]]
    [4, 6]     - simple tap: output of the FF6 goes to the XOR at the input of FF4
    [3, [1,2]]   - AND(FF1, FF2) goes to the XOR at FF3 input
    [-8, [2,-3]] - NOT(AND(2, NOT(3))) goes to the XOR at FF8 input
    Example string of taps:
    [1, [6,7]], [4, [4,-5]]
    """
  )
  
  def getNoSuccess() -> list:
    while 1:
      Result = MainMenu_static._input_no_success.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(f'{Result}'))
        if R >= 0:
          return R
      except:
        return 0
      
  def getBentInputs() -> list:
    while 1:
      Result = MainMenu_static._input_bent_inputs.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(f'{Result}'))
        if R > 0 and (R & 1) == 0:
          return R
      except:
        continue
  
  def getTigerPolynomial() -> list:
    while 1:
      Result = MainMenu_static._input_tiger_polynomial.run()
      if Result is None:
        return None
      try:
        R = list(ast.literal_eval(f'[{Result}]'))
        return R
      except:
        continue
      
  def getTaps(Reset = False) -> list:
    if Reset:
      MainMenu_static._input_taps.reset()
    while 1:
      Result = MainMenu_static._input_taps.run()
      if Result is None:
        return None
      try:
        R = list(ast.literal_eval(f'[{Result}]'))
        return R
      except:
        continue
  
  def getNlfsrTaps() -> list:
    while 1:
      Result = MainMenu_static._input_nlfsr_taps.run()
      if Result is None:
        return None
      try:
        R = list(ast.literal_eval(f'[{Result}]'))
        return R
      except:
        continue
  
  def getNotMatchingTapsCount() -> list:
    while 1:
      Result = MainMenu_static._input_not_matching_taps_count.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        return R
      except:
        return 0
    
  def getBinSequence() -> str:
    Result = MainMenu_static._input_bin_sequence.run()
    return Result
  
  def getCoeffsCount() -> int:
    while 1:
      Result = MainMenu_static._input_polynomial_coeffs_count.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        if R < 2: 
          R = 2
        return R
      except:
        return 3
  
  def getAndShift() -> int:
    while 1:
      Result = MainMenu_static._input_nlfsr_and_shift.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        if R < 1: 
          R = 1
        return R
      except:
        return 1
      
  def getSectionSize() -> int:
    while 1:
      Result = MainMenu_static._input_section_size.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        if R < 1: 
          R = 1
        return R
      except:
        return 4

  def getMaxAndCount() -> int:
    while 1:
      Result = MainMenu_static._input_max_and_count.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        return R
      except:
        return 0
    
  def getMinDistance() -> int:
    while 1:
      Result = MainMenu_static._input_polynomial_minimum_distance.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        if R < 1: 
          R = 1
        return R
      except:
        return 1
      

  def getBalancing() -> int:
    while 1:
      Result = MainMenu_static._input_polynomial_balancing.run()
      if Result is None:
        return None
      try:
        R = int(ast.literal_eval(Result))
        R = abs(R)
        return R
      except:
        return 0
    
  def getN() -> int:
    Result = MainMenu_static._input_n_results.run()
    if Result is None:
      return None
    try:
      return int(ast.literal_eval(Result))
    except:
      return 0
      
  def getLfsrSize() -> int:
    while 1:
      Result = MainMenu_static._input_lfsr_size.run()
      if Result is None:
        return None
      try:
        return int(ast.literal_eval(Result))
      except:
        continue
  
  def getPolynomial() -> Polynomial:
    while 1:
      Result = MainMenu_static._input_polynomial.run()
      if Result is None:
        return None
      try:
        return Polynomial(ast.literal_eval(Result))
      except:
        message_dialog(title="Error", text=f'The given text "{Result}" is not a polynomial.').run()

  def getPolynomialDegree() -> int:
    while 1:
      Result = MainMenu_static._input_polynomial_degree.run()
      if Result is None:
        return None
      try:
        return int(ast.literal_eval(Result))
      except:
        message_dialog(title="Error", text=f'The given text "{Result}" is not an integer.').run()

  def run():
    Category = -1
    while Category is not None:
      Category = MainMenu_static._main_menu.run()
      if Category is not None:
        Category()
          
      

      

def menu():
  MainMenu_static.run()