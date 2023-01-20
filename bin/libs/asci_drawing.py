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
  LEFT_ARROW = '\U000025C0'
  RIGHT_ARROW = '\U000025B6'
  UP_ARROW = '\U000025B2'
  DOWN_ARROW = '\U000025BC'
  UP_LEFT_ARROW = '\U00002196'
  UP_RIGHT_ARROW = '\U00002197'
  DOWN_LEFT_ARROW = '\U00002199'
  DOWN_RIGHT_ARROW = '\U00002198'
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
      
  def isChar(self, Char : str):
    return (self._char == Char)
      
  
  
  
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
        
  def drawXor(self, X : int, Y : int) -> None:
    self._array[X][Y].setChar(AsciiDrawing_Characters.CIRCLED_PLUS)
    
  def drawChar(self, X : int, Y : int, Char : str) -> None:
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
      MaxTextLen = Width-1
      AlignedText = AsciiDrawing_Alignment.center(Text, MaxTextLen)
      ix = X+1
      for Char in AlignedText:
        self._array[ix][TextY].setChar(Char)
        ix += 1
      
  def drawConnectorVV(self, X1 : int, Y1 : int, X2 : int, Y2 : int) -> None:
    MidDirection = ""
    Direction = "U"
    if (Y2 > Y1):
      Direction = "D"
    StartX = X1
    if X2 < X1:
      MidDirection = "L"
      StopX = X2 -1
      StepX = -1
      if Direction == "D":
        MidBChar = AsciiDrawing_Characters.LOWER_RIGHT
        MidEChar = AsciiDrawing_Characters.UPPER_LEFT
      else:
        MidBChar = AsciiDrawing_Characters.UPPER_RIGHT
        MidEChar = AsciiDrawing_Characters.LOWER_LEFT
    elif X2 > X1:
      MidDirection = "R"
      StopX = X2 +1
      StepX = +1
      if Direction == "D":
        MidBChar = AsciiDrawing_Characters.LOWER_LEFT
        MidEChar = AsciiDrawing_Characters.UPPER_RIGHT
      else:
        MidBChar = AsciiDrawing_Characters.UPPER_LEFT
        MidEChar = AsciiDrawing_Characters.LOWER_RIGHT
    MidY = (Y2 + Y1) >> 1
    StartY = Y1
    if Direction == "D":
      StopY = Y2 +1
      StepY = 1
    else:
      StopY = Y2 -1
      StepY = -1
    ix = X1
    for iy in range(StartY, StopY, StepY):
      if iy == MidY:
        if MidDirection == "":
          self._array[ix][iy].setChar(AsciiDrawing_Characters.VERTICAL)
        else:
          for jx in range(StartX, StopX, StepX):
            if jx == X1:
              self._array[jx][iy].setChar(MidBChar)
            elif jx == X2:
              self._array[jx][iy].setChar(MidEChar)
            else:
              self._array[jx][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
          ix = X2
      else:
        self._array[ix][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
      
  def drawConnectorHH(self, X1 : int, Y1 : int, X2 : int, Y2 : int) -> None:
    MidDirection = ""
    Direction = "L"
    if (X2 > X1):
      Direction = "R"
    StartY = Y1
    if Y2 > Y1:
      MidDirection = "D"
      StopY = Y2 +1
      StepY = 1
      if Direction == "R":
        MidBChar = AsciiDrawing_Characters.UPPER_RIGHT
        MidEChar = AsciiDrawing_Characters.LOWER_LEFT
      else:
        MidBChar = AsciiDrawing_Characters.UPPER_LEFT
        MidEChar = AsciiDrawing_Characters.LOWER_RIGHT
    elif Y2 < Y1:
      MidDirection = "U"
      StopY = Y2 -1
      StepY = -1
      if Direction == "R":
        MidBChar = AsciiDrawing_Characters.LOWER_RIGHT
        MidEChar = AsciiDrawing_Characters.UPPER_LEFT
      else:
        MidBChar = AsciiDrawing_Characters.LOWER_LEFT
        MidEChar = AsciiDrawing_Characters.UPPER_RIGHT
    MidX = (X2 + X1) >> 1
    StartX = X1
    if Direction == "R":
      StopX = X2 +1
      StepX = 1
    else:
      StopX = X2 -1
      StepX = -1
    iy = Y1
    for ix in range(StartX, StopX, StepX):
      if ix == MidX:
        if MidDirection == "":
          self._array[ix][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
        else:
          for jy in range(StartY, StopY, StepY):
            if jy == Y1:
              self._array[ix][jy].setChar(MidBChar)
            elif jy == Y2:
              self._array[ix][jy].setChar(MidEChar)
            else:
              self._array[ix][jy].setChar(AsciiDrawing_Characters.VERTICAL)
          iy = Y2
      else:
        self._array[ix][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
    
  def drawConnectorVH(self, X1 : int, Y1 : int, X2 : int, Y2 : int) -> None:
    BDirection = "D"
    StartY = Y1
    StopY = Y2
    StepY = 1
    if Y2 < Y1:
      BDirection = "U"
      StepY = -1
    EDirection = "R"
    StartX = X2
    StopX = X1
    StepX = -1
    if X2 < X1:
      EDirection = "L"
      StepX = 1
    if BDirection == "U" and EDirection == "L":
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
    elif BDirection == "U" and EDirection == "R":
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.UPPER_LEFT)
    elif BDirection == "D" and EDirection == "L":
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
    else:
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.LOWER_LEFT)
    iy = Y2  
    for ix in range(StartX, StopX, StepX):
      self._array[ix][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
    ix = X1  
    for iy in range(StartY, StopY, StepY):
      self._array[ix][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
        
  def drawConnectorHV(self, X1 : int, Y1 : int, X2 : int, Y2 : int) -> None:
    BDirection = "R"
    StartX = X2
    StopX = X1
    StepX = -1
    if X2 < X1:
      BDirection = "L"
      StepX = 1
    EDirection = "D"
    StartY = Y1
    StopY = Y2
    StepY = 1
    if Y2 < Y1:
      EDirection = "U"
      StepY = -1
    if BDirection == "L" and EDirection == "U":
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
    elif BDirection == "L" and EDirection == "D":
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
    elif BDirection == "R" and EDirection == "U":
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.UPPER_LEFT)
    else:
      self._array[X1][Y2].setChar(AsciiDrawing_Characters.LOWER_LEFT)
    iy = Y2  
    for ix in range(StartX, StopX, StepX):
      self._array[ix][iy].setChar(AsciiDrawing_Characters.HORIZONTAL)
    ix = X1  
    for iy in range(StartY, StopY, StepY):
      self._array[ix][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
      
  def drawConnectorVUV(self, X1 : int, Y1 : int, X2 : int, Y2 : int, dY = 2) -> None:
    MidY = Y1 - abs(dY)
    if Y2 < Y1:
      MidY = Y2 - abs(dY)
    for iy in range(Y1, MidY, -1):
      self._array[X1][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    for iy in range(Y2, MidY, -1):
      self._array[X2][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    if X2 < X1:
      for ix in range(X2, X1):
        self._array[ix][MidY].setChar(AsciiDrawing_Characters.HORIZONTAL)
      self._array[X1][MidY].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
      self._array[X2][MidY].setChar(AsciiDrawing_Characters.UPPER_LEFT)
    else:
      for ix in range(X1, X2):
        self._array[ix][MidY].setChar(AsciiDrawing_Characters.HORIZONTAL)
      self._array[X1][MidY].setChar(AsciiDrawing_Characters.UPPER_LEFT)
      self._array[X2][MidY].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
      
  def drawConnectorVDV(self, X1 : int, Y1 : int, X2 : int, Y2 : int, dY = 2) -> None:
    MidY = Y1 + abs(dY)
    if Y2 > Y1:
      MidY = Y2 + abs(dY)
    for iy in range(Y1, MidY, 1):
      self._array[X1][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    for iy in range(Y2, MidY, 1):
      self._array[X2][iy].setChar(AsciiDrawing_Characters.VERTICAL)
    if X2 < X1:
      for ix in range(X2, X1):
        self._array[ix][MidY].setChar(AsciiDrawing_Characters.HORIZONTAL)
      self._array[X1][MidY].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
      self._array[X2][MidY].setChar(AsciiDrawing_Characters.LOWER_LEFT)
    else:
      for ix in range(X1, X2):
        self._array[ix][MidY].setChar(AsciiDrawing_Characters.HORIZONTAL)
      self._array[X1][MidY].setChar(AsciiDrawing_Characters.LOWER_LEFT)
      self._array[X2][MidY].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
      
  def drawConnectorHRH(self, X1 : int, Y1 : int, X2 : int, Y2 : int, dX = 2) -> None:
    MidX = X1 + abs(dX)
    if X2 > X1:
      MidX = X2 + abs(dX)
    for ix in range(X1, MidX, 1):
      self._array[ix][Y1].setChar(AsciiDrawing_Characters.HORIZONTAL)
    for ix in range(X2, MidX, 1):
      self._array[ix][Y2].setChar(AsciiDrawing_Characters.HORIZONTAL)
    if Y2 < Y1:
      for iy in range(Y2, Y1):
        self._array[MidX][iy].setChar(AsciiDrawing_Characters.VERTICAL)
      self._array[MidX][Y1].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
      self._array[MidX][Y2].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
    else:
      for iy in range(Y1, Y2):
        self._array[MidX][iy].setChar(AsciiDrawing_Characters.VERTICAL)
      self._array[MidX][Y1].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
      self._array[MidX][Y2].setChar(AsciiDrawing_Characters.LOWER_RIGHT)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
    
  def drawConnectorHLH(self, X1 : int, Y1 : int, X2 : int, Y2 : int, dX = 2) -> None:
    MidX = X1 - abs(dX)
    if X2 < X1:
      MidX = X2 - abs(dX)
    for ix in range(X1, MidX, -1):
      self._array[ix][Y1].setChar(AsciiDrawing_Characters.HORIZONTAL)
    for ix in range(X2, MidX, -1):
      self._array[ix][Y2].setChar(AsciiDrawing_Characters.HORIZONTAL)
    if Y2 < Y1:
      for iy in range(Y2, Y1):
        self._array[MidX][iy].setChar(AsciiDrawing_Characters.VERTICAL)
      self._array[MidX][Y1].setChar(AsciiDrawing_Characters.LOWER_LEFT)
      self._array[MidX][Y2].setChar(AsciiDrawing_Characters.UPPER_LEFT)
    else:
      for iy in range(Y1, Y2):
        self._array[MidX][iy].setChar(AsciiDrawing_Characters.VERTICAL)
      self._array[MidX][Y1].setChar(AsciiDrawing_Characters.UPPER_LEFT)
      self._array[MidX][Y2].setChar(AsciiDrawing_Characters.LOWER_LEFT)
    self.fixLinesAtPoint(X1, Y1)
    self.fixLinesAtPoint(X2, Y2)
    
  def _neighbours(self, X : int, Y : int):
    L = 0
    R = 0
    U = 0
    D = 0
    if X > 0:
      if self._array[X-1][Y].isChar(AsciiDrawing_Characters.HORIZONTAL): L = 1
      if self._array[X-1][Y].isChar(AsciiDrawing_Characters.LOWER_LEFT): L = 1
      if self._array[X-1][Y].isChar(AsciiDrawing_Characters.UPPER_LEFT): L = 1
      if self._array[X-1][Y].isChar(AsciiDrawing_Characters.VERTICAL_RIGTH): L = 1
    if X < self._width-1:
      if self._array[X+1][Y].isChar(AsciiDrawing_Characters.HORIZONTAL): R = 1
      if self._array[X+1][Y].isChar(AsciiDrawing_Characters.LOWER_RIGHT): R = 1
      if self._array[X+1][Y].isChar(AsciiDrawing_Characters.UPPER_RIGHT): R = 1
      if self._array[X+1][Y].isChar(AsciiDrawing_Characters.VERTICAL_LEFT): R = 1
    if Y > 0:
      if self._array[X][Y-1].isChar(AsciiDrawing_Characters.VERTICAL): U = 1
      if self._array[X][Y-1].isChar(AsciiDrawing_Characters.UPPER_LEFT): U = 1
      if self._array[X][Y-1].isChar(AsciiDrawing_Characters.UPPER_RIGHT): U = 1
      if self._array[X][Y-1].isChar(AsciiDrawing_Characters.HORIZONTAL_DOWN): U = 1
    if Y < self._height-1:
      if self._array[X][Y+1].isChar(AsciiDrawing_Characters.VERTICAL): D = 1
      if self._array[X][Y+1].isChar(AsciiDrawing_Characters.LOWER_LEFT): D = 1
      if self._array[X][Y+1].isChar(AsciiDrawing_Characters.LOWER_RIGHT): D = 1
      if self._array[X][Y+1].isChar(AsciiDrawing_Characters.HORIZONTAL_UP): D = 1
    return L, R, U, D
      
  def fixLinesAtPoint(self, X : int, Y : int) -> None:
    L, R, U, D = self._neighbours(X, Y)
    if L and R and U and D:
      self._array[X][Y].setChar(AsciiDrawing_Characters.CROSS)
    elif L and R and D:
      self._array[X][Y].setChar(AsciiDrawing_Characters.HORIZONTAL_DOWN)
    elif L and U and D:
      self._array[X][Y].setChar(AsciiDrawing_Characters.VERTICAL_LEFT)
    elif L and R and U:
      self._array[X][Y].setChar(AsciiDrawing_Characters.HORIZONTAL_UP)
    elif R and U and D:
      self._array[X][Y].setChar(AsciiDrawing_Characters.VERTICAL_RIGTH)
    elif R and L:
      self._array[X][Y].setChar(AsciiDrawing_Characters.HORIZONTAL)
    elif U and D:
      self._array[X][Y].setChar(AsciiDrawing_Characters.VERTICAL)
    elif U and R:
      self._array[X][Y].setChar(AsciiDrawing_Characters.LOWER_LEFT)
    elif R and D:
      self._array[X][Y].setChar(AsciiDrawing_Characters.UPPER_LEFT)
    elif D and L:
      self._array[X][Y].setChar(AsciiDrawing_Characters.UPPER_RIGHT)
    elif L and U:
      self._array[X][Y].setChar(AsciiDrawing_Characters.LOWER_RIGHT)

    
    