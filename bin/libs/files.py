import os
import ast

def getAioPath() -> str:
  return os.path.dirname(os.path.dirname(__file__)) + "/"

def readFile(FileName : str) -> str:
  f = open(FileName, 'r')
  return f.read()

def writeFile(FileName : str, data):
  f = open(FileName, "w")
  f.write(str(data))
  
def writeDictionary(FileName : str, dictionary : dict):
  f = open(FileName, "w")
  f.write("{\n")
  for key, value in dictionary.items():
    f.write(" " + str(key) + ":\t" + str(value) + ",\n")
  f.write("}")
  
def readDictionary(FileName : str) -> dict:
  f = open(FileName, 'r')
  return ast.literal_eval(f.read())
  