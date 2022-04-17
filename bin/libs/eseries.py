from libs.aio import *
import re

def eng(Number : float, Unit = "", FractionPartDigits = 2) -> str:
  """Returns a string containing a given number displayed using engineering format.
  Args:
      Number (float): input number
      Unit (str, optional): unit. Defaults to "".
      FractionPartDigits (int, optional): fraction part digits count. Defaults to 2.
  """
  prefixes = [(1000000000000.0, "T"),
              (1000000000.0, "G"),
              (100000.0, "M"),
              (1000.0, "k"), 
              (1.0, ""),
              (0.001, "m"),
              (0.000001, "u"),
              (0.000000001, "n"),
              (0.000000000001, "p"),
              (0.000000000000001, "F")]
  for p in prefixes:
    val = p[0]
    prefix = p[1]
    if Number >= val:
      num = Number / val
      return f'{num:.{FractionPartDigits}f} {prefix}{Unit}'    
  return f'{Number:.{FractionPartDigits}f} {prefix}{Unit}'

def getMantissaExponent(Number : float) -> list:
  """Returns a list containing [mantissa, exponent] parts of the given number.
  """
  mantissa = Number
  exponent = 0.0
  while mantissa >= 10.0:
    mantissa /= 10.0
    exponent += 1.0
  while mantissa < 1.0:
    mantissa *= 10.0
    exponent -= 1.0
  return [mantissa, exponent]



class ESeries:
  """A static class containing methods usable to work with E3/E6/E9 series.
  """
  def getESerie(EIndex = 3) -> list:
    if (EIndex == 3):
      return [1.0, 2.2, 4.7, 10.0]
    elif (EIndex == 6):
      return [1.0, 1.5, 2.2, 3.3, 4.7, 6.8, 10.0]
    elif (EIndex == 9):
      return [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2, 10.0]
    return []
  def roundUp(Number : float, EIndex = 3) -> float:
    """Returns a number rounded-up to a number included in E3/E6/E9 serie.

    Args:
        Number (float): input number
        EIndex (int, optional): 3, 6 or 9. Defaults to 3.
    """
    me = getMantissaExponent(Number)
    lst = ESeries.getESerie(EIndex)
    m = me[0]
    e = me[1]
    for i in lst:
      if m <= i:
        m = i
        break
    return m * (10 ** e)
  def roundDown(Number : float, EIndex = 3) -> float:
    """Returns a number rounded-down to a number included in E3/E6/E9 serie.

    Args:
        Number (float): input number
        EIndex (int, optional): 3, 6 or 9. Defaults to 3.
    """
    me = getMantissaExponent(Number)
    lst = ESeries.getESerie(EIndex)
    lst.sort(reverse=True)
    m = me[0]
    e = me[1]
    for i in lst:
      if m >= i:
        m = i
        break
    return m * (10 ** e)
  def round(Number : float, EIndex = 3) -> float:
    """Returns a number rounded to a nearest number included in E3/E6/E9 serie.

    Args:
        Number (float): input number
        EIndex (int, optional): 3, 6 or 9. Defaults to 3.
    """
    up = ESeries.roundUp(Number, EIndex)
    dn = ESeries.roundDown(Number, EIndex)
    if (up - Number) < (Number - dn):
      return up
    return dn



