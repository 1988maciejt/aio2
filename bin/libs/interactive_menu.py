from libs.lfsr import *
from libs.programmable_lfsr import *
from prompt_toolkit.shortcuts import *
import ast

class MainMenu_static:
  _main_menu = radiolist_dialog(
    title="Main menu",
    text="Choose category",
    values=[
      (1, "Primitive polynomials"),
      (2, "Maximum Rungs")
    ]
  )
  _prim_polys_menu = radiolist_dialog(
    title="Primitive polynomials",
    text="What you want to do:",
    values=[
      (1, "Check if a given polynomial is primitive"),
      (2, "Print dense primitives")
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
    SubCategory = -1
    Poly = -1
    Degree = -1
    while Category is not None:
      Category = MainMenu_static._main_menu.run()
      if Category == 1:
        while SubCategory is not None:
          SubCategory = MainMenu_static._prim_polys_menu.run()
          if SubCategory == 1:
            while Poly is not None:
              Poly = MainMenu_static.getPolynomial()
              if Poly is not None:
                IsOrNot = "IS" if Poly.isPrimitive() else "IS NOT"
                message_dialog(title="Result", text=f'Polynomial\n{str(Poly)}\n{IsOrNot} PRIMITIVE!').run()
          if SubCategory == 2:
            Degree = MainMenu_static.getPolynomialDegree()
            if Degree is not None:
              Polynomial.printDensePrimitives(Degree)
              return
            
          
      
      
      

def menu():
  MainMenu_static.run()