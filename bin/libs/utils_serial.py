from curses import baudrate
import sys
import glob
import serial
from libs.utils_str import *
from libs.aio import *
from prompt_toolkit.shortcuts import *
import _thread

class Serial(serial.Serial):
  pass
class Serial(serial.Serial):
  def list(pattern=""):
      """ Lists serial port names

          :raises EnvironmentError:
              On unsupported or unknown platforms
          :returns:
              A list of the serial ports available on the system
      """
      if sys.platform.startswith('win'):
          ports = ['COM%s' % (i + 1) for i in range(256)]
      elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
          # this excludes your current terminal "/dev/tty"
          ports = glob.glob('/dev/tty[A-Za-z]*')
      elif sys.platform.startswith('darwin'):
          ports = glob.glob('/dev/tty.*')
      else:
          raise EnvironmentError('Unsupported platform')
      result = []
      for port in ports:
        if pattern in port:
          try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
          except (OSError, serial.SerialException):
            pass
      return result
  def first(pattern=""):
    return Serial.list(pattern)[0]
  def print(self, text):
    self.write(str(text).encode("utf-8"))
  def println(self, text):
    self.print(str(text) + "\n")
  def readln(self) -> str:
    return self.read_until()
  def readUntil(self, string = "\n") -> str:
    return self.read_until().decode()
  def pick(pattern="") -> str:
    Lst = Serial.list(pattern)
    Values = []
    for Item in Lst:
      Values.append((Item, Item))
    Selected = radiolist_dialog(title="Serial", text="Select serial port", values=Values).run()
    return Selected
  
  
class SerialMonitor:
  
  __slots__ = ("_SP", "_Port", "_cbk", "_enabled")
  
  def __init__(self, Port : str = None, Baud : int = 9600, Parity = "N", Callback = None, AutoStart = True):
    if Port is None:
      Port = Serial.pick()
    if Port is None:
      Aio.printError("Undefined serial port name.")
      return
    self._Port = Port
    self._cbk = Callback
    self._enabled = False
    try:
      self._SP = Serial(Port, Baud, 8, Parity, timeout=0.4)
    except:
      Aio.printError("Cannot access the serial port.")
      self._SP = None
      return
    if AutoStart:
      self.start()
    
  def __repr__(self):
    return f"SerialMonitor({self._Port})"
    
  def __str__(self):
    return repr(self)
    
  def __delete__(self):
    if self._SP is not None:
      try:
        self._SP.close()
      except:
        pass
      
  def start(self):
    if self._enabled:
      self.stop()
    self._enabled = True
    _thread.start_new_thread(self._monitor, ())
    
  def stop(self):
    self._enabled = False
    time.sleep(0.5)
    
  def isMonitoring(self):
    return self._enabled
  
  def setCallback(self, Callback = None):
    self._cbk = Callback
    
  def _monitor(self):
    while self._enabled:
      try:
        R = self._SP.readln()
      except:
        continue
      try:
        R = R.decode()
      except:
        try:
          R = R.decode('cp1254')
        except:
          continue
      if len(R) > 0:
        R = R.replace("\n", "")
        R = R.replace("\r", "")
        if self._cbk is None:
          print(f"{Str.color(f'{self._Port}:', 'blue')} {R}")
        else:
          try:
            self._cbk(R)
          except Exception as E:
            Aio.printError(f"Error in callback: {E}")
            
  def print(self, text):
    self._SP.print(text)
    
  def println(self, text):
    self._SP.println(text)
        
    
    