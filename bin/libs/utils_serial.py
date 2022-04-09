from curses import baudrate
import sys
import glob
import serial

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
    return str(self.read_until())
  def readUntil(self, string = "\n") -> str:
    return str(self.read_until(string.encode("utf-8")))