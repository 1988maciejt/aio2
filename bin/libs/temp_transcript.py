import glob
from libs.files import *
import os
import time
from prompt_toolkit.shortcuts import *

_OPEN_TEMP_FILES = set()

class TempTranscript:
  
  __slots__ = ("_filename", "_file", "_len")
  
  @staticmethod
  def listStoredFiles() -> list:
    Result = glob.glob("/tmp/*.aio2tmptr")
    Result.sort()
    return Result
  
  @staticmethod
  def menu(ReturnTrueIfPrinted = False):
    while 1:
      lst = TempTranscript.listStoredFiles()
      if len(lst) < 1:
        message_dialog(title="Temporary Transcripts",text="No temporary transcripts found")
        return None
      FirstMenu = [(0,'print temp transcript...'),(1,"Remove selected transcript..."),(2,'Remove all temp transcripts')]
      Selected = radiolist_dialog(title="Temporary Transcripts", text="", values=FirstMenu).run()
      if Selected is None:
        return None
      if Selected == 2:
        TempTranscript.removeAllFiles(True)
        continue
      elif Selected == 1:
        SecondMenu = []
        for Item in lst:
          if Item not in _OPEN_TEMP_FILES:
            SecondMenu.append((Item, Item[5:-10]))
        Selected = radiolist_dialog(title="Remove transcript...", text="", values=SecondMenu).run()
        if Selected is not None:
          removeFile(Selected)
      elif Selected == 0:
        SecondMenu = []
        for Item in lst:
          SecondMenu.append((Item, Item[5:-10]))
        Selected = radiolist_dialog(title="Select transcript...", text="", values=SecondMenu).run()
        if Selected is not None:
          print("------------{",Selected[5:-10],"}------------")
          print("")
          cat(Selected)
          print("--------------" + ("-"*(len(Selected)-15)) + "--------------")
          return (True if ReturnTrueIfPrinted else None)
      
  
  tui = menu
  
  @staticmethod
  def removeAllFiles(ExceptOpened = True):
    global _OPEN_TEMP_FILES
    for f in TempTranscript.listStoredFiles():
      if ExceptOpened and (f in _OPEN_TEMP_FILES):
        continue
      removeFile(f)
  
  def __repr__(self) -> str:
    return f"TempTranscript({self._filename})"
  
  def __str__(self) -> str:
    return repr(self)
  
  def __len__(self) -> int:
    return self._len
  
  def __init__(self, TaskName : str):
    global _OPEN_TEMP_FILES
    T = time.localtime()
    self._filename = f"/tmp/{T[0]}-{T[1]}-{T[2]}_{T[3]}:{T[4]}:{T[5]}_{TaskName}.aio2tmptr"
    self._len = 0
    self._file = None
    self.open()
    
  def print(self, *args) -> bool:
    if self._file is None:
      return False
    Text = ""
    Second = 0
    for arg in args:
      if Second:
        Text += " "
      else:
        Second = 1
      Text += str(arg)
    Text += "\n"
    self._file.write(Text)
    self._file.flush()
    os.fsync(self._file.fileno())
    self._len += len(Text)
    return True
  
  def open(self):
    global _OPEN_TEMP_FILES
    if self._file is not None:
      try:
        self._file.close()
      except:
        pass
    self._file = open(self._filename, "w")
    self._len = 0
    _OPEN_TEMP_FILES.add(self._filename)
    
  reopen = open
  
  def close(self):
    global _OPEN_TEMP_FILES
    _OPEN_TEMP_FILES.remove(self._filename)
    if self._file is None:
      return False
    try:
      self._file.close()
    except:
      pass
    removeFile(self._filename)
    self._file = None
    