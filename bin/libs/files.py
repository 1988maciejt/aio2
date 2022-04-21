import os
import ast
import pickle

def getAioPath() -> str:
  return os.path.dirname(os.path.dirname(__file__)) + "/"

def readFile(FileName : str) -> str:
  f = open(FileName, 'r')
  d = f.read()
  f.close()
  return d

def writeFile(FileName : str, Data):
  f = open(FileName, "w")
  f.write(str(Data))
  f.close()

def writeObjectToFile(FileName : str, Obj):
  f = open(FileName, "wb")
  pickle.dump(Obj, f)
  f.close()
  
def readObjectFromFile(FileName : str):
  f = open(FileName, "rb")
  r = pickle.load(f)
  f.close()
  return r

def writeDictionary(FileName : str, dictionary : dict):
  f = open(FileName, "w")
  f.write("{\n")
  for key, value in dictionary.items():
    f.write(" " + str(key) + ":\t" + str(value) + ",\n")
  f.write("}")
  f.close()
  
def readDictionary(FileName : str) -> dict:
  f = open(FileName, 'r')
  r = ast.literal_eval(f.read())
  f.close()
  return r
  