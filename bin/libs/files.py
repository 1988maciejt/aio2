import os
import ast
import pickle
import glob
import gzip
import pathlib
import random
import shutil
from tempfile import tempdir
from prompt_toolkit.shortcuts import *

FS = pathlib.Path(".")

def cd(dirname = None):
  global FS
  if dirname == None:
    dirname = pickDirectory()
  os.chdir(dirname)
  FS = pathlib.Path(os.getcwd())    

def pwd() -> str:
  return os.getcwd()

def ls(DirsOnly = False) -> str:
  res = []
  for e in FS.iterdir():
    if DirsOnly:
      if not pathlib.Path.is_dir(e):
        continue
    res.append(str(e))
  return res
def mkdir(dirname : str):
  os.mkdir(dirname)
    
def getAioPath() -> str:
  return os.path.dirname(os.path.dirname(__file__)) + "/"


def readFile(FileName : str, GZip = False) -> str:
  if GZip:
    f = gzip.open(FileName, "r")
  else:
    f = open(FileName, 'r')
  d = f.read()
  f.close()
  return d

def writeFile(FileName : str, Data, GZip = False, Append = False):
  if Append:
    o = "a"
  else:
    o = "w"
  if GZip:
    f = gzip.open(FileName, o)
  else:
    f = open(FileName, o)
  f.write(str(Data))
  f.flush()
  os.fsync(f.fileno())
  f.close()
  

def writeObjectToFile(FileName : str, Obj, GZip = False):
  if GZip:
    f = gzip.open(FileName, "wb")
  else:
    f = open(FileName, "wb")
  pickle.dump(Obj, f)
  f.flush()
  os.fsync(f.fileno())
  f.close()
  
def readObjectFromFile(FileName : str, GZip = False):
  if GZip:
    f = gzip.open(FileName, "rb")
  else:
    f = open(FileName, "rb")
  r = pickle.load(f)
  f.close()
  return r


def writeDictionary(FileName : str, dictionary : dict, GZip = False):
  if GZip:
    f = gzip.open(FileName, "w")
  else:
    f = open(FileName, "w")
  f.write("{\n")
  for key, value in dictionary.items():
    f.write(" " + str(key) + ":\t" + str(value) + ",\n")
  f.write("}")
  f.flush()
  os.fsync(f.fileno())
  f.close()
  
def readDictionary(FileName : str, GZip = False) -> dict:
  if GZip:
    f = gzip.open(FileName, "r")
  else:
    f = open(FileName, 'r')
  r = ast.literal_eval(f.read())
  f.close()
  return r

  
def writeLinesFromList(FileName : str, List : list):
  f = open(FileName, "w")
  for i in List:
    f.write(str(i) + "\n")
  f.flush()
  os.fsync(f.fileno())
  f.close()
    
    
def writeBinary(FileName : str, Data : bytes):
  f = open(FileName, "wb")
  f.write(bytes(Data))
  f.flush()
  os.fsync(f.fileno())
  f.close()
  
def readBinary(FileName : str) -> bytes:
  f = open(FileName, 'rb')
  d = bytes(f.read())
  f.close()
  return d
  
def cat(FileName : str):
  print(readFile(FileName))
    
def pickFile(Path = "", Title = "Choose a file:", Preview = False) -> str:
  Result = os.path.abspath(Path)
  if os.path.isfile(Result):
    Result = os.path.dirname(Result)
  while os.path.isdir(Result):
    Items = [".."] + os.listdir(Result)
    Values = []
    for I in Items:
      Values.append((I, I))
    Selected = radiolist_dialog(title=Title, text="", values=Values).run()
    if Selected is None:
      return None
    elif Selected == "..":
      Result = os.path.dirname(Result)
    else:
      Result += "/" + Selected
  return Result

def pickDirectory(Path = "", Title = "Choose a directory:", Preview = False) -> str:
  Result = os.path.abspath(Path)
  if os.path.isfile(Result):
    Result = os.path.dirname(Result)
  Choosen = False
  while not Choosen:
    AllItems = os.listdir(Result)
    Values = [(0, "CHOOSE THIS"), ("..", "..")]
    for Item in AllItems:
      if os.path.isdir(Result + "/" + Item):
        Values.append((Item, Item))
    Selected = radiolist_dialog(title=Title, text=f'[{Result}]', values=Values).run()
    if Selected is None:
      return None
    elif Selected == "..":
      Result = os.path.dirname(Result)
    elif Selected == 0:
      return Result
    else:
      Result += "/" + Selected
      
def removeFile(FileName: str) -> bool:
  try:
    os.remove(FileName)
    return True
  except:
    return False

class File:
  remove = removeFile
  pick = pickFile
  cat = cat
  read = readFile
  readBinary = readBinary
  readDict = readDictionary
  readObject = readObjectFromFile
  write = writeFile
  writeBinary = writeBinary
  writeDict = writeDictionary
  writeObject = writeObjectToFile
  
  @staticmethod
  def writeLines(FileName : str, Iterator):
    if type(Iterator) is not list:
      Iterator = [i for i in Iterator]
    writeLinesFromList(FileName, Iterator)
    
  @staticmethod
  def list(Pattern : str) -> list:
    return glob.glob(Pattern)
  
  @staticmethod
  def replaceText(FileNamePattern : str, OldText : str, NewText : str) -> int:
    FileNames = glob.glob(FileNamePattern)
    Counter = 0
    for FileName in FileNames:
      Text = readFile(FileName)
      Text = Text.replace(OldText, NewText)
      try:
        writeFile(FileName, Text)
        Counter += 1
      except:
        from libs.aio import Aio
        Aio.printError(f"Couldn't write '{FileName}'.")
    return Counter
  
  @staticmethod
  def readLineByLineGenerator(FileName : str):
    """Reads a file line by line and returns a generator.

    Args:
        FileName (str): File name to read.

    Yields:
        str: Line read from the file.
    """
    from libs.generators import Generators
    for Line in Generators().readFileLineByLine(FileName):
      yield Line
  
  @staticmethod
  def getRandomTempFileName() -> str:
    return f"/tmp/aio_tmp_{int(random.uniform(1000000000, 9999999999))}"
  
  @staticmethod
  def parseValues(FileName : str, RegExpressionDict : dict, ReportLastValueIfMany : bool = False) -> dict:
    """Reads file line-by-line and uses regular expressions passed by the second argument to extract values from the lines.

    Args:
        RegExpressionDict (dict): {key1: 'rregex1(group1)', key2: 'rregex2(group1)', ...}
          Group count is unlimited.
        ReportLastValueIfMany (bool, optional): If True, then if many lines matches the regex then the last value is stored in the resultant dict. Defaults to False.

    Returns:
        dict: Dictionary similar to the one provided by the argument, but regexpressions are replaced by the extracted values.
    """
    from libs.generators import Generators
    from re import search
    ToList = 0
    if type(RegExpressionDict) is list:
      ToList = len(RegExpressionDict)
      AuxDict = {}
      for i in range(len(RegExpressionDict)):
        AuxDict[i] = RegExpressionDict[i]
      RegExpressionDict = AuxDict
    Gen = Generators()
    Result = {}
    RegExpressionDictC = RegExpressionDict.copy()
    for Line in Gen.readFileLineByLine(FileName):
      if len(RegExpressionDictC) > 0:
        KeysToRemove = []
        for key, value in RegExpressionDictC.items():
          R = search(value, Line)
          if R:
            Val = R.groups()
            if len(Val) == 1:
              Val = Val[0]
            Result[key] = Val
            KeysToRemove.append(key)
        if not ReportLastValueIfMany:
          for key in KeysToRemove:
            del RegExpressionDictC[key]
      else:
        continue
    for key in RegExpressionDictC:
      Result[key] = None
    if ToList > 0:
      AuxList = []  
      for i in range(ToList):
        AuxList.append(Result[i])
      Result = AuxList
    return Result
  
  
  
class Dir:
  pick = pickDirectory
  make = mkdir
  mkdir = mkdir
  getAioPath = getAioPath
  pwd = pwd
  getCurrent = pwd
  
  @staticmethod
  def forceRemove_Linux(DirName: str) -> bool:
    import subprocess
    from time import sleep
    if not os.path.isdir(DirName):
      return True
    try:
        for root, dirs, files in os.walk(DirName):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    result = subprocess.run(['fuser', '-a', file_path], capture_output=True, text=True)
                    if result.returncode == 0:
                        pids = [
                            int(pid)
                            for pid in result.stdout.strip().split()
                            if pid.isdigit()
                        ]
                        for pid in pids:
                            print(f"Killing PID {pid} locking {file_path}")
                            subprocess.run(['kill', '-9', str(pid)])
                except Exception as e:
                    pass
        sleep(1)
        shutil.rmtree(DirName)
        return True
    except Exception as e:
        return False
  
  

class TempDir:
  __slots__ = ("_name", "_path", "_pwd", "DontDelete")
  def __repr__(self) -> str:
    return f"TempDir('{self._path}')"
  def __str__(self) -> str:
    return self._path
  def __del__(self) -> None:
      from libs.aio_auto import AioAuto
      if not self.DontDelete:
        shutil.rmtree(self._path, ignore_errors=True)
      AioAuto.unregisterDirToClean(self._path)
  def __init__(self) -> None:
    from libs.aio_auto import AioAuto
    self.DontDelete = False
    oncemore = True
    self._pwd = pwd()
    while oncemore:
      self._name = "aio_tmp" + str(int(random.uniform(1000000000, 9999999999)))
      #self._path = "/tmp/" + self._name
      self._path = os.path.abspath(f"./{self._name}")
      oncemore = os.path.isdir(self._path)
    os.makedirs(self._path)
    AioAuto.registerDirToClean(self._path)
  def getName(self) -> str:
    return self._name
  def getPath(self) -> str:
    return self._path
  def go(self):
    cd(self._path)
  def goBack(self):
    cd(self._pwd)