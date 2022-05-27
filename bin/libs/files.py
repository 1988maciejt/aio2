import os
import ast
import pickle
import gzip
import pathlib
import random
import shutil
from tempfile import tempdir

FS = pathlib.Path(".")

def cd(dirname : str):
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

def writeFile(FileName : str, Data, GZip = False):
  if GZip:
    f = gzip.open(FileName, "w")
  else:
    f = open(FileName, "w")
  f.write(str(Data))
  f.close()
  

def writeObjectToFile(FileName : str, Obj, GZip = False):
  if GZip:
    f = gzip.open(FileName, "wb")
  else:
    f = open(FileName, "wb")
  pickle.dump(Obj, f)
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
    f.close()
    
    
def writeBinary(FileName : str, Data : bytes):
  f = open(FileName, "wb")
  f.write(bytes(Data))
  f.close()
  
def readBinary(FileName : str) -> bytes:
  f = open(FileName, 'rb')
  d = bytes(f.read())
  f.close()
  return d
  
def cat(FileName : str):
  print(readFile(FileName))


class TempDir:
  _name = ""
  _path = ""
  def __del__(self) -> None:
    shutil.rmtree(self._path, ignore_errors=True)
  def __init__(self) -> None:
    oncemore = True
    while oncemore:
      self._name = "aio" + str(int(random.uniform(1000000000, 9999999999)))
      self._path = os.path.expanduser("~/temp/" + self._name)
      oncemore = os.path.isdir(self._path)
    os.makedirs(self._path)
  def name(self) -> str:
    return self._name
  def path(self) -> str:
    return self._path
    
    
    