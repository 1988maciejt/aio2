from libs.files import *
from libs.utils_serial import *
from libs.aio import *
from simple_term_menu import TerminalMenu
import subprocess

class Esp32:
  Port = ""
  _WasErased = False
  def __init__(self, Port = None) -> None:
    if Aio.isType(Port, None):
      SerialList = Serial.list()
      PortMenu = TerminalMenu(SerialList, title="Select serial port")
      Port = SerialList[PortMenu.show()]
    self.Port = Port
  def eraseFlash(self):
    subprocess.call(["esptool.py", "--chip", "esp32", "--port", self.Port, "erase_flash"])
    self._WasErased = True
  def WriteFlash(self, File = None):
    if Aio.isType(File, None):
      File =  pickFile(Aio.getPath()+"../utils/esp32_firmware")
    if not self._WasErased:
      self.eraseFlash()
    subprocess.call(["esptool.py", "--chip", "esp32", "--port", self.Port, "--baud", "460800", 
                    "write_flash", "-z", "0x1000", File])