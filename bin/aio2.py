# auto install missing libs
_required_libs = [
  "setuptools",
  "ptpython",
  "plotext",
  "percol",
  "tqdm",
  "line_profiler",
  "openpyxl",
  "xlsxwriter",
  "ansi2html",
  "pathos",
  "multiprocess",
  "sympy",
  "matplotlib",
  "latex",
  "bitarray",
  "p_tqdm",
  "pandas",
  "netifaces",
  "pint",
  "textual",
  "hyperloglog",
  "cython",
  "scipy",
  ("python-docx", "docx"),
  ("PyMuPDF", "fitz"),
  ("pillow", "PIL"),
  "g4f",
  "gensim",
  "nltk",
  "galois",
  "pysnooper",
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

from aio_config import *
from aio import *

shell_config.printHeader()


if len(sys.argv) > 1:
  os.chdir(sys.argv[1])


def _tc(filename="driver.py"):
  SFile = filename
  if "driver.py" in SFile:
    try:
      shutil.rmtree("results", ignore_errors=True)
    except:
      Aio.printError("Error removing 'results' directory.")
      exit()
    try:
      os.makedirs("results")
    except:
      Aio.printError("Error creating 'results' directory.")
      exit()
#    Aio.shellExecute("mkdir -p references")
    os.chdir("results")
    SFile = "../" + SFile
    sys.path.append("../data")
    sys.path.append("../")
    Aio.print ("Testcase mode. Output redirected to 'transcript.txt'.\n")
    Aio.printTranscriptEnable()
  if os.path.isfile(SFile):
#    exec(open(SFile).read())
#    from driver import *
#    try:
    with open(SFile) as src:
      imp.load_module('__MAIN__', src, SFile, (".py", "r", imp.PY_SOURCE))
#    except:
#      Aio.printError("TC processing error!")
  else:
    Aio.printError("No file '" + SFile + "'")    
  os.chdir("../")
  print("==== TC FINISHED ====")

def _run_binding_thread():
  import libs.key_bindings as _key_binds
  _key_binds.startKeyBindingThread()
  
def _run_tc():
  if len(sys.argv) > 2:
    _tc(str(sys.argv[2]))
    
    
_run_tc()
#_run_binding_thread()
      
class Shell:
  def getUserObjects():
    result = List.xor(globals(), Cache.recall("globals", []))
    result = List.removeByString(result, r'^_+[0-9]*$')
    result = List.removeByString(result, r'^_+i+[0-9]*$')
    result = List.removeByString(result, r'^_+\Sh$')
    result = List.removeByString(result, r'^_+i+$')
    result = List.removeByString(result, r'^run$')
    result = List.removeByString(result, r'^get_ptpython$')
    result = List.removeByString(result, r'^get_ipython$')
    result = List.removeByString(result, r'^In$')
    result = List.removeByString(result, r'^Out$')
    result = List.removeByString(result, r'^exit$')
    result = List.removeByString(result, r'^quit$')
    result = List.removeByString(result, r'^__.*__$')
    return result
  def startHistoryLogging(filename="aio2_history", append=True):      
    from ptpython.repl import embed
    history_path = os.path.expanduser(filename)
    if not append:
      try:
        os.remove(history_path)
      except:
        pass
    embed(globals(), locals(), history_filename=history_path)
  def importHistory(filename="aio2_history"):
    try:
      exec(open(filename).read())
      print("History loaded.")
    except:
      print("History loading error!")
      
      
Cache.store("globals", list(globals().keys()).copy())
#========================================================