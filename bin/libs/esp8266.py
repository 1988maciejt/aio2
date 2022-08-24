from libs.files import *
from libs.utils_serial import *
from libs.aio import *
from simple_term_menu import TerminalMenu
import subprocess

class Esp8266:
  Port = ""
  _WasErased = False
  def __init__(self, Port = None) -> None:
    if Aio.isType(Port, None):
      SerialList = Serial.list()
      PortMenu = TerminalMenu(SerialList, title="Select serial port")
      Port = SerialList[PortMenu.show()]
    self.Port = Port
  def eraseFlash(self):
    subprocess.call(["esptool.py", "--port", self.Port, "erase_flash"])
    self._WasErased = True
  def WriteFlash(self, File = None):
    if Aio.isType(File, None):
      File =  pickFile(Aio.getPath()+"../utils/esp8266_firmware")
    if not self._WasErased:
      self.eraseFlash()
    subprocess.call(["esptool.py", "--port", self.Port, "--baud", "921600", 
                    "write_flash", "--flash_size=detect", "-fm", "dout", "0", File])