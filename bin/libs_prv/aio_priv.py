# auto install missing libs
_required_libs = [
  "pvlib",
  "suncalc"
]
def _isModuleAvailable(LibName : str) -> bool:
  try:
    x = __import__(LibName)
    return True
  except:
    return False
def _filterUnavailableModules(LibNamesList : list) -> list:
  Result = []
  for LibName in LibNamesList:
    if not _isModuleAvailable(LibName):
      Result.append(LibName)
  return Result
def _installPythonLib(LibName : str):
  import os
  os.system(f"python3 -m pip install --upgrade {LibName}")
def _installMissingModules(LibNamesList : list) -> list:
  for LibName in LibNamesList:
    if type(LibName) in [list, tuple]:
      PDef = LibName[1]
      LibName = LibName[0]
    else:
      PDef = LibName
    if not _isModuleAvailable(PDef):
      print(f"INSTALLING MISSING '{LibName}' MODULE:")
      _installPythonLib(LibName)

_installMissingModules(_required_libs)

from libs_prv.music import *
from libs_prv.pv import *