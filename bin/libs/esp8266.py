from libs.files import *
from libs.utils_serial import *
from libs.aio import *
from simple_term_menu import TerminalMenu
import subprocess
import re

class Esp8266:
  Port = ""
  _WasErased = False
  _ChipParamsFetched = False
  _FlashParamsFetched = False
  _Params = {}
  def __init__(self, Port = None) -> None:
    if Aio.isType(Port, None):
      SerialList = Serial.list()
      PortMenu = TerminalMenu(SerialList, title="Select serial port")
      Port = SerialList[PortMenu.show()]
    self.Port = Port
  def getChipId(self):
    return Aio.shellExecute(f'esptool.py --port {self.Port} chip_id')
  def chipId(self):
    subprocess.call(["esptool.py", "--port", self.Port, "chip_id"])
  def getFlashId(self):
    return Aio.shellExecute(f'esptool.py --port {self.Port} flash_id')
  def flashId(self):
    subprocess.call(["esptool.py", "--port", self.Port, "flash_id"])
  def getParams(self):
    if not self._FlashParamsFetched:
      self.fetchFlashParams()
    if not self._ChipParamsFetched:
      self.fetchChipParams()
    return self._Params.copy()
  def fetchChipParams(self):
    FlashText = self.getFlashId()
    m = re.search(r'Crystal\sis\s(\S+)', FlashText)
    if m:
      self._Params["crystal"] = m[1]
    m = re.search(r'Chip\sis\s(\S+)', FlashText)
    if m:
      self._Params["chip"] = m[1]
    m = re.search(r'MAC:\s(\S+)', FlashText)
    if m:
      self._Params["mac"] = m[1]
    m = re.search(r'ID:\s(\S+)', FlashText)
    if m:
      self._Params["chip_id"] = m[1]
    self._FlashParamsFetched = True
  def fetchFlashParams(self):
    FlashText = self.getFlashId()
    m = re.search(r'flash\ssize:\s(\S+)', FlashText)
    if m:
      self._Params["flash_size"] = m[1]
    self._ChipParamsFetched = True
  def getFlashSize(self):
    if not self._FlashParamsFetched:
      self.fetchFlashParams()
    return self._Params["flash_size"]
  def eraseFlash(self):
    subprocess.call(["esptool.py", "--port", self.Port, "erase_flash"])
    self._WasErased = True
  def writeFlash(self, File = None):
    if Aio.isType(File, None):
      File =  pickFile(Aio.getPath()+"../utils/esp8266_firmware")
    if not self._WasErased:
      self.eraseFlash()
    subprocess.call(["esptool.py", "--port", self.Port, "--baud", "921600", 
                    "write_flash", "--flash_size=detect", "-fm", "dout", "0", File])