from curses.ascii import SP
from libs.utils_array import *
from libs.utils_int import *
from libs.database import *
from libs.aio import *
from libs.lfsr import *
from libs.PolynomialsArithmetic import *
from bitarray import *
import bitarray.util as bau
import copy
from libs.lfsr import *

class Ca(Lfsr):
  """Cellular automata object.
  """
  _ba_my_rules = bitarray(0)
  _baValue = bitarray(0)
  _size : int
  _ba_fast_sim_array = None

  def copy(self):
    return Ca(self)
  
  def __del__(self):
    pass

  def __init__(self, Rules : bitarray):
    """Initializes the CA object.

    Args:
        Rules (bitarray): rules vector. Bit==1 means 150 rule, Bit==0 means 90 rule.
                          If rules is of type of Polynomial, then it calls Ca.fromPolynomial() method.
    """
    if type(Rules) is Ca:
      self._ba_my_rules = Rules._ba_my_rules.copy()
      self._size = Rules._size
      self._baValue = Rules._baValue.copy()
    else:
      if type(Rules) in [Polynomial, list]:
        if type(Rules) is list:
           Rules = Polynomial(Rules)
        Aux = Ca.fromPolynomial(Rules)
        if Aux is None:
          self._ba_my_rules = bitarray("0")
        else:
           self._ba_my_rules = Aux._ba_my_rules
      elif Aio.isType(Rules, "bitarray"):
        self._ba_my_rules = Rules.copy()
      else:
        self._ba_my_rules = bitarray(Rules)
      self._size = len(self._ba_my_rules)
      self._baValue = bitarray(self._size)
      self.reset()

  def __repr__(self) -> str:
    result = "Ca(" + str(self._size) + ", " + self._ba_my_rules.to01() + ")"
    return result
  
  def __str__(self) -> str:
    return self._baValue.to01()
  
  def _next1(self) -> bitarray:
    middle = self._baValue & self._ba_my_rules
    left = self._baValue << 1
    right = self._baValue >> 1
    self._baValue = left ^ middle ^ right
    return self._baValue
  
  @staticmethod
  def _polynomial_to_ca90_150(poly: int) -> tuple[bitarray, bitarray]:
      """
      Cattell-Muzio synthesis.

      Input:
          poly: irreducible GF(2) polynomial as an integer.
                Bit i represents the coefficient of x**i.

      Returns:
          Two reversed CA rule vectors:
          0 = rule 90, 1 = rule 150.

      Convention:
          Vectors are ordered from the leftmost to the rightmost cell.
      """
      if poly < 0 or poly.bit_length() < 3 or not (poly & 1):
          raise ValueError(
              "Expected a degree >= 2 polynomial with constant term 1"
          )
      n = poly.bit_length() - 1
      x = 0b10
      # a = (x^2 + x) * P'(x) mod P(x)
      derivative = IntPolynomialUtils.gf2_derivative(poly)
      a = IntPolynomialUtils.gf2_mul_mod(0b110, derivative, poly)
      if a == 0:
          raise ValueError("Invalid auxiliary coefficient")
      # Solve z^2 + z = 1/a^2 in GF(2^n).
      a_inv = IntPolynomialUtils.gf2_pow_mod(a, (1 << n) - 2, poly)
      c = IntPolynomialUtils.gf2_mul_mod(a_inv, a_inv, poly)

      z = IntPolynomialUtils.solve_z2_z(c, poly, n)
      if z is None:
          raise ValueError(
              "No solution found; input may not be irreducible"
          )
      # g = a*z. The two solutions differ by a.
      g = IntPolynomialUtils.gf2_mul_mod(a, z, poly)
      if g.bit_length() != n:
          g2 = IntPolynomialUtils.gf2_mul_mod(a, z ^ 1, poly)
          if g2.bit_length() == n:
              g = g2
          else:
              raise ValueError("Could not construct auxiliary polynomial")
      # Euclidean divisions recover x + d_n, ..., x + d_1.
      A, B = poly, g
      reversed_rules = []
      for _ in range(n):
          quotient, remainder = IntPolynomialUtils.gf2_divmod(A, B)
          if quotient not in (0b10, 0b11):
              raise ValueError(
                  "Unexpected quotient; check irreducibility and conventions"
              )
          reversed_rules.append(quotient & 1)
          A, B = B, remainder
      rules = bitarray(reversed(reversed_rules))
      return rules, rules[::-1]
  
  def fromPolynomial(P : Polynomial) -> "Ca":
    if P.isReducible():
       Aio.printError(f"Polynomial '{P}' is reducible so that it cannot be converted to CA rules.")
       return None
    r1, r2 = Ca._polynomial_to_ca90_150(P.toInt())
    return Ca(r1)
