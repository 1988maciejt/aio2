import zlib
import pickle
import ast
import base64
import re
import difflib
import textwrap
from libs.asci_drawing import *

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
  def wrap(Text : str, Width : int) -> str:
    Result = ""
    Second = 0
    for Line in Text.split("\n"):
      if len(Line) <= Width:
        NewLines = [Line]
      else:
        NewLines = textwrap.wrap(Line, width=Width)
      for NewLine in NewLines:
        if Second: Result += "\n"
        else: Second = 1
        Result += NewLine
    return Result
  
  @staticmethod
  def booble(Text : str, Width : int, BackColor = 'blue', ForeColor = 'white', FrameIncluding : bool = False) -> str:
    InternalWidth = Width-2 if FrameIncluding else Width
    Aux = Str.wrap(Text, InternalWidth)
    Result = ""
    Second = 0
    for Line in Aux.split("\n"):
      Line = Str.toLeft(Line, InternalWidth)
      if FrameIncluding:
        Line = AsciiDrawing_Characters.VERTICAL + Line + AsciiDrawing_Characters.VERTICAL
      Line = Str.color(Str.color(Line, ForeColor), "back " + BackColor)
      if Second:
        Result += "\n"
      else:
        Second = 1
        if FrameIncluding:
          Result = Str.color(Str.color(AsciiDrawing_Characters.UPPER_LEFT + AsciiDrawing_Characters.HORIZONTAL * InternalWidth + AsciiDrawing_Characters.UPPER_RIGHT + "\n", ForeColor), "back " + BackColor)
      Result += Line
    if FrameIncluding:
      Result += "\n" + Str.color(Str.color(AsciiDrawing_Characters.LOWER_LEFT + AsciiDrawing_Characters.HORIZONTAL * InternalWidth + AsciiDrawing_Characters.LOWER_RIGHT, ForeColor), "back " + BackColor)
    return Result
  
  @staticmethod
  def indent(Text : str, SpacesCount : int) -> str:
    Result = ""
    Second = 0
    for Line in Text.split("\n"):
      if Second:
        Result += "\n"
      else:
        Second = 1
      Result += " " * SpacesCount + Line
    return Result
  
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
      Code = 30
      if 'brig' in color:
        if "bg" in color or "bac" in color:
          Code = 100
        else:
          Code = 90
      else:
        if "bg" in color or "bac" in color:
          Code = 40
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
  
  @staticmethod
  def mustEndWith(Text : str, Ending : str, CaseSensitive : bool = True) -> str:
    if CaseSensitive:
      if Text.endswith(Ending):
        return Text
    else:
      if Text.lower().endswith(Ending.lower()):
        return Text
    return Text + Ending
  
  @staticmethod
  def latexToPlainText(Text : str) -> str:
    Result = Text
    Result = Result.replace("\r", "")
    Result = re.sub(r'\$(\\\S+)\$', r"'\1'", Result)
    Result = re.sub(r'\$([a-zA-Z0-9]+)\$', r"'\1'", Result)
    Result = re.sub(r'(\S)\_(\S+)', r'\1\2', Result)
    Result = re.sub(r'\\(begin|end)\{\S+\}', r'', Result)
    Result = Result.replace("&=", "=")
    Result = Result.replace("$$", "")
    Result = Result.replace("\\oplus", "^")
    Result = Result.replace("\\wedge", "&")
    Result = Result.replace("\\\\\n", "\n")
    Result = Result.replace("**", "")
    Result = Result.replace("\n\n\n", "\n")
    return Result
  
  @staticmethod
  def objectToString(Object) -> str:
    from libs.utils_zlib import Zlib
    Compressed = Zlib.compressObject(Object)
    return base64.b85encode(Compressed).decode('ascii')
  
  @staticmethod  
  def objectFromString(StrObject):
    from libs.utils_zlib import Zlib
    try:
      ByteString = base64.b85decode(StrObject)
      return Zlib.uncompressObject(ByteString)
    except:
      return None
    

class StrHex:
  
  __slots__ = ('_data', 'Width', '_otype')
  
  def __init__(self, Object, Width : int = 8):
    self._otype = str(type(Object))
    self._data = pickle.dumps(Object)
    self.Width = Width
    
  def __repr__(self) -> str:
    return f'StrHex({self._otype})'
    
  def __str__(self):
    return self.toString()
    
  def toString(self):
    from libs.generators import Generators
    Idx = 0
    HeaderLine = "+" + "-" * 20 + "+-" + "-" * (self.Width * 3) + "+" + "-" * (self.Width + 2) + "+"
    Lines = [HeaderLine]
    for DataLine in Generators().subLists(self._data, self.Width):
      LW = 22 + self.Width * 3
      Line = f"| {Idx:08X}-{(Idx+self.Width-1):08X}: | "
      Line += (" ".join([f"{x:02X}" for x in DataLine]))
      Line = Str.toLeft(Line, LW)
      Line += " | "
      for Char in DataLine:
        if Char < 32 or Char > 126:
          Line += "."
        else:
          Line += chr(Char)
      Line = Str.toLeft(Line, LW + 4 + self.Width)
      Line += "|"
      Lines.append(Line)
      Idx += self.Width
    Lines.append(HeaderLine)
    return "\n".join(Lines)
  
  def print(self):
    from libs.aio import Aio
    Aio.print(self.toString())