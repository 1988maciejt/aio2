"""
BINARY POLYNOMIAL ARITHMETIC
These functions operate on binary polynomials (Z/2Z[x]), expressed as coefficient bitmasks, etc:
  0b100111 -> x^5 + x^2 + x + 1
As an implied precondition, parameters are assumed to be *nonnegative* integers unless otherwise noted.
This code is time-sensitive and thus NOT safe to use for online cryptography.
"""

from typing import Tuple

# descriptive aliases (assumed not to be negative)
Natural = int
BPolynomial = int

def p_mul(a: BPolynomial, b: BPolynomial) -> BPolynomial:
    """ Binary polynomial multiplication (peasant). """
    result = 0
    while a and b:
        if a & 1: result ^= b
        a >>= 1; b <<= 1
    return result

def p_mod(a: BPolynomial, b: BPolynomial) -> BPolynomial:
    """ Binary polynomial remainder / modulus.
        Divides a by b and returns resulting remainder polynomial.
        Precondition: b != 0 """
    bl = b.bit_length()
    while True:
        shift = a.bit_length() - bl
        if shift < 0: return a
        a ^= b << shift

def p_divmod(a: BPolynomial, b: BPolynomial) -> Tuple[BPolynomial, BPolynomial]:
    """ Binary polynomial division.
        Divides a by b and returns resulting (quotient, remainder) polynomials.
        Precondition: b != 0 """
    q = 0; bl = b.bit_length()
    while True:
        shift = a.bit_length() - bl
        if shift < 0: return (q, a)
        q ^= 1 << shift; a ^= b << shift

def p_mod_mul(a: BPolynomial, b: BPolynomial, modulus: BPolynomial) -> BPolynomial:
    """ Binary polynomial modular multiplication (peasant).
        Returns p_mod(p_mul(a, b), modulus)
        Precondition: modulus != 0 and b < modulus """
    result = 0; deg = p_degree(modulus)
    assert p_degree(b) < deg
    while a and b:
        if a & 1: result ^= b
        a >>= 1; b <<= 1
        if (b >> deg) & 1: b ^= modulus
    return result

def p_exp(a: BPolynomial, exponent: Natural) -> BPolynomial:
    """ Binary polynomial exponentiation by squaring (iterative).
        Returns polynomial `a` multiplied by itself `exponent` times.
        Precondition: not (x == 0 and exponent == 0) """
    factor = a; result = 1
    while exponent:
        if exponent & 1: result = p_mul(result, factor)
        factor = p_mul(factor, factor)
        exponent >>= 1
    return result

def p_gcd(a: BPolynomial, b: BPolynomial) -> BPolynomial:
    """ Binary polynomial euclidean algorithm (iterative).
        Returns the Greatest Common Divisor of polynomials a and b. """
    while b: a, b = b, p_mod(a, b)
    return a

def p_egcd(a: BPolynomial, b: BPolynomial) -> tuple:
    """ Binary polynomial Extended Euclidean algorithm (iterative).
        Returns (d, x, y) where d is the Greatest Common Divisor of polynomials a and b.
        x, y are polynomials that satisfy: p_mul(a,x) ^ p_mul(b,y) = d
        Precondition: b != 0
        Postcondition: x <= p_div(b,d) and y <= p_div(a,d) """
    a = (a, 1, 0)
    b = (b, 0, 1)
    while True:
        q, r = p_divmod(a[0], b[0])
        if not r: return b
        a, b = b, (r, a[1] ^ p_mul(q, b[1]), a[2] ^ p_mul(q, b[2]))

def p_mod_inv(a: BPolynomial, modulus: BPolynomial) -> BPolynomial:
    """ Binary polynomial modular multiplicative inverse.
        Returns b so that: p_mod(p_mul(a, b), modulus) == 1
        Precondition: modulus != 0 and p_coprime(a, modulus)
        Postcondition: b < modulus """
    d, x, y = p_egcd(a, modulus)
    assert d == 1 # inverse exists
    return x

def p_mod_pow(x: BPolynomial, exponent: Natural, modulus: BPolynomial) -> BPolynomial:
    """ Binary polynomial modular exponentiation by squaring (iterative).
        Returns: p_mod(p_exp(x, exponent), modulus)
        Precondition: modulus > 0
        Precondition: not (x == 0 and exponent == 0) """
    factor = x = p_mod(x, modulus); result = 1
    while exponent:
        if exponent & 1:
            result = p_mod_mul(result, factor, modulus)
        factor = p_mod_mul(factor, factor, modulus)
        exponent >>= 1
    return result

def p_degree(a: BPolynomial) -> int:
    """ Returns degree of a. """
    return a.bit_length() - 1

def p_congruent(a: BPolynomial, b: BPolynomial, modulus: BPolynomial) -> bool:
    """ Checks if a is congruent with b under modulus.
        Precondition: modulus > 0 """
    return p_mod(a^b, modulus) == 0

def p_coprime(a: BPolynomial, b: BPolynomial) -> bool:
    """ Checks if a and b are coprime. """
    return p_gcd(a, b) == 1
  
def p_trace(a : BPolynomial, p : BPolynomial) -> BPolynomial:
    """ Computes the Trace of polynomial a with respect to
        irreducible polynomial p.. """
    n = p_degree(p)
    ai = a
    result = ai
    #print(f'{bin(ai)}     {bin(result)}')
    for i in range(1,n):
      ai = p_mod_pow(ai, 2, p)
      result ^= ai
    #  print(f'{bin(ai)}     {bin(result)}')
    return result
  
def p_get_next_trace1(a : BPolynomial, p : BPolynomial, infinite = False) -> BPolynomial:
  n0 = p_degree(a)
  result = a+1
  while infinite or (p_degree(result) == n0):
    try:
      if p_trace(result, p) == 1:
        return result
    except:
      pass
    result += 1
  return 0

def p_get_prev_trace1(a : BPolynomial, p : BPolynomial) -> BPolynomial:
  n0 = p_degree(a)
  result = a-1
  while result >= 0:
    try:
      if p_trace(result, p) == 1:
        return result
    except:
      pass
    result -= 1
  return 0

def p_derivative(a : BPolynomial) -> BPolynomial:
  n = p_degree(a)
  result = a;
  mask = (1 << (n+1)) - 2
  for i in range(0,n,2):
    result &= mask
    mask = (mask << 2) + 0b11
  return result>>1

  
"""
UTILITIES
"""

from typing import Iterator, Iterable

def to_bits(n: int) -> Iterator[int]:
    """ Generates the bits of n that are 1, in ascending order. """
    bit = 0
    while n:
        if n & 1: yield bit
        bit += 1
        n >>= 1

def from_bits(bits: Iterable[int], strict=False) -> int:
    """ Assembles a series of bits into an integer with these bits set to 1.
        If a bit is negative, ValueError is raised.
        If strict=True and there are duplicate bits, ValueError is raised. """
    n = 0
    for bit in bits:
        mask = 1 << bit
        if strict and (n & mask):
            raise ValueError('duplicated bit')
        n |= mask
    return n

def polynomial_str(n: int, variable: str="x", unicode: bool=False, separator: str=" + ", constant: str="1") -> str:
    """ Formats binary polynomial 'n' as a nice string, i.e. "x^10 + x^4 + x + 1".
        If unicode=True, then superscript digits will be used instead of ^n notation. """
    sup = lambda s: "".join("⁰¹²³⁴⁵⁶⁷⁸⁹"[ord(c) & 0xF] for c in s)
    power = lambda s: variable + sup(s) if unicode else variable + "^" + s
    term = lambda bit: constant if bit == 0 else ( \
        variable if bit == 1 else power(str(bit)) )
    return separator.join(map(term, sorted(to_bits(n), reverse=True)))

bits = lambda *bits: from_bits(bits, strict=True)
bit_str = lambda n, width=0: "{:b}".format(abs(n)).rjust(width, "0")
