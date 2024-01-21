import zlib
import pickle
import ast
import base64
import re
import difflib

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
  def removeSingleChars(Text : str, Chars) -> str:
    Result = str(Text)
    for Char in Chars:
      Result = Result.replace(str(Char), "")
    return Result
  
  @staticmethod
  def splitIntoSections(Text : str, SectionSize : int = 1024, Overlap : int = 256) -> list:
    B = 0
    E = SectionSize
    Result = []
    R = 'X'
    while len(R) > 0:
      if B >= len(Text):
        break
      R = Text[B:E]
      if len(R) > 0:
        Result.append(R)
      if E == len(Text):
        break
      B = E-Overlap
      E = B + SectionSize
    return Result
  
  @staticmethod
  def removePunctuation(Text : str) -> str:
    Result = Str.removeSingleChars(Text, "\r\t\\/,./<>?;':\"[]{}()*&^%$#@!")
    Result = Result.replace("\n", " ")
    Result = Result.replace("  ", " ")
    return Result
  
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
  
  @staticmethod
  def similarity(a : str, b : str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()
  
  @staticmethod
  def toLeft(Text : str, Width : int) -> str:
    Result = ""
    Second = 0
    for Line in Text.split("\n"):
      Line.replace("\r", "")
      Line.replace("\t", " ")
      Line = Line[:Width]
      if len(Line) < Width:
        Line += " " * (Width - len(Line))
      if Second:
        Result += "\n"
      else:
        Second = 1
      Result += Line
    return Result
  
  @staticmethod
  def toRight(Text : str, Width : int) -> str:
    Result = ""
    Second = 0
    for Line in Text.split("\n"):
      Line.replace("\r", "")
      Line.replace("\t", " ")
      Line = Line[-Width:]
      if len(Line) < Width:
        Line = " " * (Width - len(Line)) + Line
      if Second:
        Result += "\n"
      else:
        Second = 1
      Result += Line
    return Result
  
  @staticmethod
  def toCenter(Text : str, Width : int) -> str:
    Result = ""
    Second = 0
    for Line in Text.split("\n"):
      Line.replace("\r", "")
      Line.replace("\t", " ")
      WDelta = Width - len(Line)
      DLeft = (WDelta >> 1)
      DRight = WDelta - DLeft
      if DLeft < 0:
        Line = Line[-DLeft:]
      elif DLeft > 0:
        Line = " " * (DLeft) + Line
      if DRight < 0:
        Line = Line[:DRight]
      elif DRight > 0:
        Line += " " * (DRight)
      if Second:
        Result += "\n"
      else:
        Second = 1
      Result += Line
    return Result
  
  @staticmethod
  def removeEscapeCodes(Text) -> str:
    Result = re.sub(r'(\033\[[^m]*m)', '', Text)
    return Result
  
  @staticmethod
  def getAligned(Text : str, Width : int, LeftRightCenter : str) -> str:
    LeftRightCenter = str(LeftRightCenter).strip()
    LeftRightCenter = LeftRightCenter.lower()
    if len(LeftRightCenter) > 0:
      if LeftRightCenter[0] == 'r':
        return Str.toRight(Text, Width)
      if LeftRightCenter[0] == 'c':
        return Str.toCenter(Text, Width)
    return Str.toLeft(Text, Width)
  
  @staticmethod
  def getWidth(Text : str) -> int:
    Result = 0
    for Line in Text.split("\n"):
      Line.replace("\r", "")
      Line.replace("\t", " ")
      if len(Line) > Result:
        Result = len(Line)
    return Result