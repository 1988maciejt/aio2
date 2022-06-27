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
  CIRVLED_PLUS = '\U00002A01'

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
      return AsciiDrawing_Characters.CIRVLED_PLUS
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