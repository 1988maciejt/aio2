from libs.lfsr import *
from libs.programmable_lfsr import *
from prompt_toolkit.shortcuts import *
import ast




def _categoryPolynomial_decode():
  Sequence = MainMenu_static.getBinSequence()
  if Sequence is None:
    return
  try:
    Poly = Polynomial.decodeUsingBerlekampMassey(Sequence)
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
  MinDist = MainMenu_static.getMinDistance()
  if MinDist is None:
    return
  N = MainMenu_static.getN()
  if N is None:
    return
  Result = Polynomial.listPrimitives(Degree, CoeffsCount, MinimumDIstance=MinDist, n=N)
  String = "Found dense polynomials:\n\n"
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





class MainMenu_static:
  _main_menu = radiolist_dialog(
    title="Main menu",
    text="Choose category",
    values=[
      (_categoryPolynomial,                 "Primitive polynomials"),
      (_categoryLfsrWithManualTaps,         "Ring generators with manually specified taps")
    ]
  )
  _prim_polys_menu = radiolist_dialog(
    title="Primitive polynomials",
    text="What you want to do:",
    values=[
      (_categoryPolynomial_checkPrimitive,  "Check if a given polynomial is primitive"),
      (_categoryPolynomial_print,           "Print primitives"),
      (_categoryPolynomial_printDense,      "Print dense primitives"),
      (_categoryPolynomial_decode,          "Decode using Berlekamp-Massey algorithm")
    ]
  )
  _lfsr_manual_taps_menu = radiolist_dialog(
    title="Ring generators with manually specified taps",
    text="What you want to do:",
    values=[
      (_categoryLfsrWithManualTaps_subDisplay,  "Display ring generator"),
      (_categoryLfsrWithManualTaps_subCreate,   "Define ring generator"),
      (_categoryLfsrWithManualTaps_subInfoDisplay, "is maximum? What is the polynomial?"),
      (_categoryLfsrWithManualTaps_subMakeDual,   "Make dual ring")
    ]
  )
  _input_polynomial = input_dialog(
    title="Polynomial input",
    text="Enter a list of polynomial coefficients, i.e.\n[5,4,0]\nIs it also possible to enter an integer number representing a polynomial, i.e.\n0b110001",
  )
  _input_polynomial_degree = input_dialog(
    title="Polynomial degree",
    text="Enter polynomial degree:"
  )
  _input_n_results = input_dialog(
    title="How many results?",
    text="Enter the required count of results (0 = no limit):"
  )
  _input_polynomial_minimum_distance = input_dialog(
    title="Minimum distance",
    text="What is the required minimum distance between successive coefficients?\nDefault : 1"
  )
  _input_polynomial_coeffs_count = input_dialog(
    title="Coefficients count",
    text="Coefficients count?\nDefault : 3"
  )
  _input_bin_sequence = input_dialog(
    title="Sequence?", 
    text="Enter a sequence of 1s and 0s:"
  )
  _input_lfsr_size = input_dialog(
    title="Lfsr size",
    text="Enter size of the Lfsr:"
  )
  _input_taps = input_dialog(
    title="Taps list",
    text="""Enter taps. Example string:
    [3,6], [6,2]
    ..which means two taps: from FF3 output to the XOR at FF6 input and the second tap from FF6 output to the XOR at FF2 input."""
  )
  
  def getTaps() -> list:
    while 1:
      Result = MainMenu_static._input_taps.run()
      if Result is None:
        return None
      try:
        R = list(ast.literal_eval(f'[{Result}]'))
        return R
      except:
        continue
    
  
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
        message_dialog(title="Error", text=f'The given text "{Result}" is not an integer number.').run()

  def run():
    Category = -1
    while Category is not None:
      Category = MainMenu_static._main_menu.run()
      if Category is not None:
        Category()
          
      

      

def menu():
  MainMenu_static.run()