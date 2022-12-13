from libs.utils_array import *
from libs.aio import *

class AsciiDrawing_Characters:
  HORIZONTAL = '\U00002500'
  VERTICAL = '\U00002502'
  HORIZONTAL_BOLD = '\U00002501'
  VERTICAL_BOLD = '\U00002503'
  HORIZONTAL_UP = '\U00002534'
  HORIZONTAL_DOWN = '\U0000252C'
  VERTICAL_LEFT = '\U00002524'
  VERTICAL_RIGTH = '\U0000251C'
  UPPER_LEFT = '\U0000250C'
  UPPER_RIGHT = '\U00002510'
  LOWER_LEFT = '\U00002514'
  LOWER_RIGHT = '\U00002518'
  UPPER_LEFT_BOLD = '\U0000250F'
  UPPER_RIGHT_BOLD = '\U00002513'
  LOWER_LEFT_BOLD = '\U00002517'
  LOWER_RIGHT_BOLD = '\U0000251B'
  LOWER_LEFT_TO_UPPER_RIGHT = '\U00002571'
  UPPER_LEFT_TO_LOWER_RIGHT = '\U00002572'
  CROSS = '\U0000253C'
  DIAGONAL_CROSS = '\U00002573'
  LEFT_ARROW = '\U0001F868'
  RIGHT_ARROW = '\U0001F86A'
  UP_ARROW = '\U0001F869'
  DOWN_ARROW = '\U0001F86B'
  CIRCLED_PLUS = '\U00002A01'

class AsciiDrawing_Direction:
  Left = 8
  Up = 4
  Down = 2
  Right = 1
  SpecialXor = 16
  
AD_DIRECTION_LEFT = AsciiDrawing_Direction.Left 
AD_DIRECTION_RIGHT = AsciiDrawing_Direction.Right
AD_DIRECTION_UP = AsciiDrawing_Direction.Up
AD_DIRECTION_DOWN = AsciiDrawing_Direction.Down
AD_DIRECTION_SPECIAL_XOR = AsciiDrawing_Direction.SpecialXor
  
class AsciiDrawing_Alignment:
  def left(Text, Len : int) -> str:
    T = str(Text)
    if len(T) < Len:
      return T + (' ' * (Len - len(T)))
    return T[0:Len]
  def right(Text, Len : int) -> str:
    T = str(Text)
    if len(T) < Len:
      return (' ' * (Len - len(T))) + T
    return T[-Len::]
  def center(Text, Len : int) -> str:
    T = str(Text)
    if len(T) >= Len:
      return T[0:Len]
    Rest = Len - len(T)
    RestR = Rest//2
    RestL = Rest - RestR
    return (' ' * RestL) + T + (' ' * RestR)
    
      
  
class AsciiDrawing_WiringNode:
  _Directions = 0
  def __init__(self, Directions = 0) -> None:
    self.addDirection(Directions)
  def __str__(self) -> str:
    d = self._Directions & 0xF
    special = self._Directions & 0xF0
    if special == AD_DIRECTION_SPECIAL_XOR:
      return AsciiDrawing_Characters.CIRCLED_PLUS
    if d == 0b1001:
      return AsciiDrawing_Characters.HORIZONTAL
    if d == 0b1000:
      return AsciiDrawing_Characters.LEFT_ARROW
    if d == 0b0001:
      return AsciiDrawing_Characters.RIGHT_ARROW
    if d == 0b0110:
      return AsciiDrawing_Characters.VERTICAL
    if d == 0b0100:
      return AsciiDrawing_Characters.UP_ARROW
    if d == 0b0010:
      return AsciiDrawing_Characters.DOWN_ARROW
    if d == 0b0011:
      return AsciiDrawing_Characters.UPPER_LEFT
    if d == 0b1010:
      return AsciiDrawing_Characters.UPPER_RIGHT
    if d == 0b0101:
      return AsciiDrawing_Characters.LOWER_LEFT
    if d == 0b1100:
      return AsciiDrawing_Characters.LOWER_RIGHT
    if d == 0b1101:
      return AsciiDrawing_Characters.HORIZONTAL_UP
    if d == 0b1011:
      return AsciiDrawing_Characters.HORIZONTAL_DOWN
    if d == 0b1110:
      return AsciiDrawing_Characters.VERTICAL_LEFT
    if d == 0b0111:
      return AsciiDrawing_Characters.VERTICAL_RIGTH
    if d == 0b1111:
      return AsciiDrawing_Characters.CROSS
    return " "
  def __repr__(self) -> str:
    s = str(self)
    return f'AsciiDrawing_WiringNode({s})'
  def addDirection(self, Directions : AsciiDrawing_Direction) -> None:
    self._Directions |= Directions

class AsciiDrawing_HorizontalFF:
  HorizontalSize = 5
  Label = ""
  def __init__(self, Label = "", HorizontalSize = 5) -> None:
    self.Label = Label
    self.HorizontalSize = HorizontalSize
  def __str__(self) -> str:
    return "[{self.Label}]"
  def __repr__(self) -> str:
    s = str(self)
    return f'AsciiDrawing_HorizontalFF({s})'
  def toString(self, LineIndex_0_to_2) -> str:
    if LineIndex_0_to_2 == 0:
      L = AsciiDrawing_Characters.UPPER_LEFT
      M = AsciiDrawing_Characters.HORIZONTAL * (self.HorizontalSize-2)
      R = AsciiDrawing_Characters.UPPER_RIGHT
    elif LineIndex_0_to_2 == 2:
      L = AsciiDrawing_Characters.LOWER_LEFT
      M = AsciiDrawing_Characters.HORIZONTAL * (self.HorizontalSize-2)
      R = AsciiDrawing_Characters.LOWER_RIGHT
    else:      
      L = AsciiDrawing_Characters.VERTICAL_LEFT
      M = AsciiDrawing_Alignment.center(self.Label, self.HorizontalSize-2) 
      R = AsciiDrawing_Characters.VERTICAL_RIGTH
    return L + M + R
  
def ADTest():
  UL = AsciiDrawing_Characters.UPPER_LEFT
  UR = AsciiDrawing_Characters.UPPER_RIGHT
  LL = AsciiDrawing_Characters.LOWER_LEFT
  LR = AsciiDrawing_Characters.LOWER_RIGHT
  LN = AsciiDrawing_Characters.VERTICAL_LEFT
  RN = AsciiDrawing_Characters.VERTICAL_RIGTH
  H = AsciiDrawing_Characters.HORIZONTAL
  lbl = AsciiDrawing_Alignment.center("0", 4)
  print(f'{UL}{H*4}{UR}')
  print(f'{LN}{lbl}{RN}\U00002790\U00002790')
  print(f'{LL}{H*4}{LR}')
  
  
  
class AsciiDrawingPoint:
  
  __slots__ = ("_char", "_reservation")
  
  def __init__(self) -> None:
    self._char = " "
    self._reservation = 0
    
  def __str__(self):
    return self._char
  
  def setChar(self, Char : str):
    if len(Char) > 0:
      self._char = Char
      self._reservation = 1
    else:
      self._char = " "
      self._reservation = 0
      
  def setHLine(self):
    pass
  
  def setVLine(self):
    pass
  
  
  
class AsciiDrawingCanvas:
  
  __slots__ = ("_width", "_height", "_array")
  
  def __init__(self, Width : int, Height : int) -> None:
    self._width = int(Width)
    self._height = int(Height)
    self._array = create2DArray(self._height, self._width, None)
    self.clear()
    
  def __str__(self) -> str:
    Result = ""
    Second = 0
    for y in range(self._height):
      Line = ""
      for x in range(self._width):
        Line += str(self._array[x][y])  
      if Second:
        Result += "\n"
      else:
        Second = 1
      Result += Line
    return Result
  
  def print(self) -> None:
    Aio.print(str(self))
      
  def clear(self) -> None:
    for x in range(self._width):
      for y in range(self._height):
        self._array[x][y] = AsciiDrawingPoint()
        
  def setChar(self, X : int, Y : int, Char : str) -> None:
    if 0 <= X < self._width and 0 <= Y < self._height:
      self._array[X][Y].setChar(Char)
        
  def drawBox(self, X : int, Y : int, Width : int, Height : int, Text = "") -> None:
    X2 = X + Width 
    Y2 = Y + Height
    XBoumd = X2 
    if XBoumd > self._width-1:
      XBoumd = self._width-1
    YBoumd = Y2 
    if YBoumd > self._height-1:
      YBoumd = self._height-1
    for ix in range(X, XBoumd+1):
      for iy in range(Y, YBoumd+1):
        if iy==Y:
          if ix==X:
            self._array[ix][iy].setChar(AsciiDrawing_Characters.UPPER_LEFT)
          elif ix==X2: 
            self._array[ix][iy].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
          else:
            self._array[ix][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
        elif iy==Y2:
          if ix==X:
            self._array[ix][iy].setChar(AsciiDrawing_Characters.LOWER_LEFT)
          elif ix==X2: 
            self._array[ix][iy].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
          else:
            self._array[ix][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
        else:
          if ix==X or ix==X2:
            self._array[ix][iy].setChar(AsciiDrawing_Characters.VERTICAL)
          else:
            self._array[ix][iy].setChar(" ")
    if len(Text) > 0 and Height >= 2:
      TextY = Y + (Height // 2)
      MaxTextLen = Width-2
      AlignedText = AsciiDrawing_Alignment.center(Text, MaxTextLen)
      ix = X+1
      for Char in AlignedText:
        self._array[ix][TextY].setChar(Char)
        ix += 1
      
  def drawConnector(self, X1 : int, Y1 : int, X2 : int, Y2 : int) -> None:
    pass