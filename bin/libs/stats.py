from math import *
from libs.files import *
import re
import plotext
from libs.aio import *

class Plot:
  Title = ""
  XData = []
  YData = []
  Type = "scatter"
  BarWidth = 1
  XLabel = "X"
  YLabel = "Y"
  def __init__(self, Data = None, Type = "scatter", Title = "") -> None:
    self.Title = Title
    self.Type = Type
    if "dict" in str(type(Data)):
      self.importDict(Data)
  def importDict(self, dct : dict) -> None:
    self.XData = []
    self.YData = []
    xs = list(dct.keys())
    xs.sort()
    for x in xs:
      self.XData.append(x)
      self.YData.append(dct[x])
  def printTable(self) -> None:
    Aio.print("------------------------")
    Aio.print(self.XLabel, "\t", self.YLabel)
    Aio.print("------------------------")
    for i in range(len(self.XData)):
      x = self.XData[i]
      y = self.YData[i]
      Aio.print(x, "\t", y)
    Aio.print("------------------------")
  def print(self) -> None:
    plotext.clear_plot()
    plotext.title(self.Title)
    if "bar" in self.Type.lower():
      plotext.bar(self.XData, self.YData, width = self.BarWidth)
      plotext.xlabel = self.XLabel
      plotext.ylabel = self.YLabel
    else:  
      plotext.scatter(self.XData, self.YData)
      plotext.xlabel = self.XLabel
      plotext.ylabel = self.YLabel
    plotext.colorless()
    Aio.print(plotext.build())
def readDieharder(FileName : str) -> list:
  fdata = readFile(FileName)
  l = fdata.split("\n")
  result = []
  tp = "d"
  for n in l:
    m = re.search(r'type:\s*(\S+)', n)
    if m:
      tp = m.group(1)
    elif ":" not in n:
      if tp == "b":
        result.append(int(n, 2))
      elif tp == "h":
        result.append(int(n, 16))
      else:
        result.append(int(n))
  return result

class Stats:
  def seriesHistogram_BinString(BinString : str) -> list:
    result = dict()
    cntr = 0
    cPrev = "X"
    for c in BinString:
      cntr += 1
      if c != cPrev:
        if cntr > 0:
          result[cntr] = result.get(cntr, 0) + 1
        cPrev = c
        cntr = 0
    return result
        
  def repeatedNumbers(data : list) -> dict:
    result = {}
    aux = {}
    for d in data:
      ThisNum = aux.get(d, 0)
      aux[d] = ThisNum + 1
    for k in aux.keys():
      num = k
      rep = aux[k]
      ThisRep = result.get(rep, 0)
      result[rep] = ThisRep + 1
    return result
  def repeatedSequence(data : list, seqLen = 2) -> dict:
    dlen = len(data)
    aux = {}
    result = {}
    for i in range(dlen - seqLen + 1):
      dli = 0
      for j in range(i, i + seqLen):
        dli = (dli * 7) + data[j]  
      ThisList = aux.get(dli, 0)
      aux[dli] = ThisList + 1
    for k in aux.keys():
      num = k
      rep = aux[k]
      ThisRep = result.get(rep, 0)
      result[rep] = ThisRep + 1
    return result
    