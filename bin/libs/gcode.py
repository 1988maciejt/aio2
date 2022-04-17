import serial


class GCodePoint:
  _x = 0.0
  _y = 0.0
  _z = 0.0
  _rel = True
  def __init__(self, X = 0.0, Y = 0.0, Z = 0.0, Relative = True) -> None:
    self._x = X
    self._y = Y
    self._z = Z
    self._rel = Relative
  def __repr__(self) -> str:
    return "GCodePoint(" + str(self._x) + ", " + str(self._y) + ", " + str(self._z) + ")"
  def __str__(self) -> str:
    result = ""
    if not self._rel or (self._rel and self._x != 0):
      result += "X" + f'{self._x:.3f}'
    if not self._rel or (self._rel and self._y != 0):
      result += "Y" + f'{self._y:.3f}'
    if not self._rel or (self._rel and self._z != 0):
      result += "Z" + f'{self._z:.3f}'
    return result
  def move(self, X = 0.0, Y = 0.0, Z = 0.0) -> str:
    self._x += X
    self._y += Y
    self._z += Z
    return str(self)


class GCode:
  _my_serial = serial.Serial()
  _history = ""
  _history_store = False
  def __init__(self, SerialName : str, Baud = 115200) -> None:
    self._my_serial.baudrate = Baud
    self._my_serial.port = SerialName
    self._my_serial.timeout = 500
  def __repr__(self) -> str:
    return "GCode(" + self._my_serial.port + ")"
  def __str__(self) -> str:
    return "GCode: " + str(self._my_serial)
  def __bool__(self) -> bool:
    return self._my_serial.is_open()
  def open(self) -> None:
    self._my_serial.open()
  def close(self) -> None:
    self._my_serial.close()
  def flush(self) -> None:
    self._my_serial.flush()
  def print(self, Text = "") -> None:
    if self._history_store:
      self._history += Text + "\n"
    self._my_serial.write(Text)
  def println(self, Text = "") -> None:
    if self._history_store:
      self._history += Text + "\n"
    self._my_serial.write(Text + "\n")
  def readLine(self) -> str:
    result = self._my_serial.readline()
    if self._history_store:
      self._history += "RECV: " + result + "\n"
    return result
  def sendRec(self, Text : str) -> str:
    self.flush()
    self.println(Text)
    return self.readLine()
  def history(self, Enabled : bool) -> None:
    self._history_store = Enabled
  def getHistory(self) -> str:
    return self._history
  def clearHistory(self) -> None:
    self._history = ""
  


  
class Grbl(GCode):
  def __repr__(self) -> str:
    return "Grbl(" + self._my_serial.port + ")"
  def __str__(self) -> str:
    return "Grbl: " + str(self._my_serial)
  def getSetting(self, Index : int) -> str:
    return self.sendRec("$" + str(Index))
  def printlnOk(self, Text : str) -> bool:
    result = self.sendRec(Text)
    if "ok" in result:
      return True
    return False
  def setSetting(self, Index : int, Value : str) -> bool:
    return self.printlnOk("$" + str(Index) + "=" + Value)
  def getBuildInfo(self) -> str:
    return self.sendRec("$I")
  def getGcodeMode(self) -> str:
    return self.sendRec("$C")
  def getUnlock(self) -> str:
    return self.sendRec("$X")
  def getParserState(self) -> str:
    return self.sendRec("$G")
  def homing(self) -> bool:
    return self.printlnOk("$H")
  def setSpindleSpeed(self, Speed : int) -> bool:
    return self.printlnOk("S" + str(Speed))
      