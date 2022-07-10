from libs.lfsr import *
from simple_term_menu import TerminalMenu

_menu_ppolys_degree = 64
_menu_ppolys_coeffs = 5
_menu_ppolys_balancing = 0
_menu_ppolys_n = 0

def menu_ppoly_settings(OnlyDegree = False):
  global _menu_ppolys_degree, _menu_ppolys_coeffs, _menu_ppolys_balancing, _menu_ppolys_n
  while True:
    PPS = [ "OK", 
            "Degree    : " + str(_menu_ppolys_degree)
          ]
    if not OnlyDegree:
      PPS += [
              "#Coeffs   : " + str(_menu_ppolys_coeffs),
              "Balancing : " + str(_menu_ppolys_balancing)
            ]
    PPS += ["#Results  : " + str(_menu_ppolys_n)]
    PPSMenu = TerminalMenu(PPS, title="Polynomials settings")
    Res = PPSMenu.show()
    if Res == 0:
      return
    elif Res == 1:
      ans = input("Degree >> ")
      try:
        _menu_ppolys_degree = int(ans)
      except:
        pass
    elif Res == 2 and not OnlyDegree:
      ans = input("# Coefficients >> ")
      try:
        _menu_ppolys_coeffs = int(ans)
      except:
        pass
    elif Res == 3:
      ans = input("Balancing >> ")
      try:
        _menu_ppolys_balancing = int(ans)
      except:
        pass
    elif Res == 4 or (Res == 2 and OnlyDegree):
      ans = input("# Results (0 means 'no limit') >> ")
      try:
        _menu_ppolys_n = int(ans)
      except:
        pass

def menu():
  global _menu_ppolys_degree, _menu_ppolys_coeffs, _menu_ppolys_balancing, _menu_ppolys_n
  Categories = ["Cancel", "Primitive polynomials over GF(2)"]
  CatMenu = TerminalMenu(Categories, title="Select category")
  CatSelected = CatMenu.show()
  if CatSelected == 1:
    PrimPolys = ["Cancel", "Find any", "Find dense"]
    PrimMenu = TerminalMenu(PrimPolys, title="Primitive polynomials over GF(2):")
    sel = PrimMenu.show()
    if sel == 0:
      return None
    elif sel == 1:
      menu_ppoly_settings()
      return Polynomial.listPrimitives(_menu_ppolys_degree, _menu_ppolys_coeffs, _menu_ppolys_balancing, False, _menu_ppolys_n)
    elif sel == 2:
      menu_ppoly_settings(True)
      return Polynomial.listDense(_menu_ppolys_degree, _menu_ppolys_n)
  return None
  