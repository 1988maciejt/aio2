import zlib
import pickle
import ast
import base64

_superscript_map = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹", "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ",
    "e": "ᵉ", "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ᶦ", "j": "ʲ", "k": "ᵏ",
    "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "q": "۹", "r": "ʳ",
    "s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ",
    "z": "ᶻ", "A": "ᴬ", "B": "ᴮ", "C": "ᶜ", "D": "ᴰ", "E": "ᴱ", "F": "ᶠ",
    "G": "ᴳ", "H": "ᴴ", "I": "ᴵ", "J": "ᴶ", "K": "ᴷ", "L": "ᴸ", "M": "ᴹ",
    "N": "ᴺ", "O": "ᴼ", "P": "ᴾ", "Q": "Q", "R": "ᴿ", "S": "ˢ", "T": "ᵀ",
    "U": "ᵁ", "V": "ⱽ", "W": "ᵂ", "X": "ˣ", "Y": "ʸ", "Z": "ᶻ", "+": "⁺",
    "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾"}
_subscript_map = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆",
    "7": "₇", "8": "₈", "9": "₉", "a": "ₐ", "b": "♭", "c": "꜀", "d": "ᑯ",
    "e": "ₑ", "f": "բ", "g": "₉", "h": "ₕ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ",
    "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "q": "૧", "r": "ᵣ",
    "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "w": "w", "x": "ₓ", "y": "ᵧ",
    "z": "₂", "A": "ₐ", "B": "₈", "C": "C", "D": "D", "E": "ₑ", "F": "բ",
    "G": "G", "H": "ₕ", "I": "ᵢ", "J": "ⱼ", "K": "ₖ", "L": "ₗ", "M": "ₘ",
    "N": "ₙ", "O": "ₒ", "P": "ₚ", "Q": "Q", "R": "ᵣ", "S": "ₛ", "T": "ₜ",
    "U": "ᵤ", "V": "ᵥ", "W": "w", "X": "ₓ", "Y": "ᵧ", "Z": "Z", "+": "₊",
    "-": "₋", "=": "₌", "(": "₍", ")": "₎"}
r'[⁰-⁹]'
_super_trans = str.maketrans(
    ''.join(_superscript_map.keys()),
    ''.join(_superscript_map.values()))
_sub_trans = str.maketrans(
    ''.join(_subscript_map.keys()),
    ''.join(_subscript_map.values()))
_super_retrans = str.maketrans(
    ''.join(_superscript_map.values()),
    ''.join(_superscript_map.keys()))
_sub_retrans = str.maketrans(
    ''.join(_subscript_map.values()),
    ''.join(_subscript_map.keys()))

  
class Str:
  
  @staticmethod
  def toSuperScript(Text : str) -> str:
    return str(Text).translate(_super_trans)
  
  @staticmethod
  def toSubScript(Text : str) -> str:
    return str(Text).translate(_sub_trans)
  
  @staticmethod
  def fromSuperScript(Text : str) -> str:
    return str(Text).translate(_super_retrans)
  
  @staticmethod
  def fromSubScript(Text : str) -> str:
    return str(Text).translate(_sub_retrans)
  
  @staticmethod
  def color(Text : str, Color : int) -> str:
    Code = 0
    if type(Color) == type(0):
      Code = Color
    elif type(Color) == type(""):
      color = str(Color).lower()
      if 'brig' in color:
        Code = 90
      else:
        Code = 30
      if 'red' in color:
        Code += 1
      elif 'gree' in color:
        Code += 2
      elif 'yell' in color:
        Code += 3
      elif 'blue' in color:
        Code += 4
      elif 'magen' in color:
        Code += 5
      elif 'cya' in color:
        Code += 6
      elif 'whi' in color:
        Code += 7
    return f'\033[{Code}m{Text}\033[0m'
  
  @staticmethod
  def objectToString(object) -> str:
    message_bytes = pickle.dumps(object)
    base64_bytes = base64.b64encode(message_bytes)
    txt = base64_bytes.decode('ascii')
    return txt
    
  @staticmethod 
  def stringToObject(string):
    base64_bytes = string.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    obj = pickle.loads(message_bytes)
    return obj