from libs.aio import *
from libs.files import *
from random import uniform
import importlib
import os

class AioCython:
  
  @staticmethod
  def getModuleFromPyxFile(FileName : str):
    ModuleName = (os.path.splitext(FileName)[0]).replace("/",".")
    Result = Aio.shellExecute(f"cythonize -i {FileName}", 0, 1)
    Result.strip()
    if "Error" in Result:
      Aio.printError(f"AioCython: {Result}")
      return None
    return importlib.import_module(ModuleName)
  
  @staticmethod
  def getModuleFromString(PyxString : str, CleanFiles = True):
    RndStr = hash(PyxString)
    FileTitle = f"tmp_cython_{RndStr}"
    FileName = f"{FileTitle}.pyx"
    if not os.path.isfile(FileName):
      writeFile(FileName, PyxString)
    Module = AioCython.getModuleFromPyxFile(FileName)
    try:
      os.remove(FileName)
    except: pass
    if CleanFiles:
      removeFile(FileTitle + "*")
    return Module