from libs.lfsr import *
from libs.printing import *
import copy


def createPolynomial(degree : int, coeffs_count : int, balancing = 0) -> Polynomial:
  if coeffs_count < 1:
    print_error ("'oefficients_count' must be >= 1")
    return Polynomial([])
  if degree < (coeffs_count-1):
    print_error ("'coefficients_count - 1' must be <= 'degree'")
    return Polynomial([])  
  result = [degree]
  if balancing > 0:
    avg = float(degree) / float(coeffs_count - 1)
    halfbal = float(balancing) / 2.0
    bmin = avg - halfbal
    bmax = avg + halfbal
    result.insert(0,0);
    if bmin < 1.0:
      bmin = 1.0
      bmax = float(balancing + 1)
    c = 0.0
    for i in range(3, coeffs_count):
      c += bmin
      result.insert(0, int(round(c)))
    max_c = int(round(float(degree) - bmax))
    while max_c in result:
      max_c += 1
    result.insert(0, max_c)
  else:
    for i in range(coeffs_count-1):
      result.insert(0,i)
  return Polynomial(result, balancing)

def findPrimitivePolynomials(degree : int, coeffs_count : int, balancing = 0, n = 0) -> list:
  result = []
  poly = createPolynomial(degree, coeffs_count, balancing)
  if poly.isPrimitive():
    poly2 = copy.copy(poly)
    result.insert(0,poly2)
    print("Found prim. poly:", poly.getCoefficients())
    if n == 1:
      return result
  while poly.nextPrimitive():
    poly2 = copy.deepcopy(poly)
    result.insert(0,poly2)
    print("Found prim. poly:", poly.getCoefficients())
    if n > 0:
      if len(result) >= n:
        break
  return result