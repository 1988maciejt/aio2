import os
import ast
import pickle
import gzip

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
      f.write(str(i))
    f.close()