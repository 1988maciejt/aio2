from libs.files import *
from libs.aio import *
import re
import plotext
#import openpyxl

class Plot:
  Title = ""
  XData = []
  YData = []
  Type = "scatter"
  BarWidth = 1
  XLabel = None
  YLabel = None
  XTicks = None
  YTicks = None
  Width = None
  Height = None
  Colored = None
  def __init__(self, Data=None, Type="scatter", Title="", XTicks=None, YTicks=None, Grid=False, Width=None, Height=None, Colored=True) -> None:
    self.Title = Title
    self.Type = Type
    self.XTicks = XTicks
    self.YTicks = YTicks
    self.Grid = Grid
    self.Width = Width
    self.Height = Height
    self.Colored = Colored
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
  def exportDataToOpenpyxlSheet(self, Sheet, XColumn=1, YColumn=1, FirstRow=1):
    if self.XLabel != None:
      Sheet.cell(FirstRow, XColumn).value = str(self.XLabel)
    if self.YLabel != None:
      Sheet.cell(FirstRow, YColumn).value = str(self.YLabel)
    if self.XLabel != None or self.YLabel != None:
      FirstRow += 1 
    for i in range(len(self.XData)):
      x = self.XData[i]
      y = self.YData[i]
      Sheet.cell(FirstRow+i, XColumn).value = x
      Sheet.cell(FirstRow+i, YColumn).value = y
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
    if self.XTicks != None:
      plotext.xticks(self.XTicks)
    if self.YTicks != None:
      plotext.yticks(self.YTicks)
    if self.XLabel != None:
      plotext.xlabel(self.XLabel)
    if self.YLabel != None:
      plotext.ylabel(self.YLabel)
    plotext.grid(self.Grid)
    plotext.plot_size(self.Width, self.Height)
    if "bar" in self.Type.lower():
      plotext.bar(self.XData, self.YData, width = self.BarWidth)
    else:  
      plotext.scatter(self.XData, self.YData)
    if not self.Colored:
      plotext.colorless()
    Aio.print(plotext.build())

class BinStrings:
  def probOf1Histogram(BinStrings : list, IncludeAll = False) -> dict:
    result = dict()
    if IncludeAll:
      for i in range(len(BinStrings[0])):
        result[i] = 0
    for word in BinStrings:
      for index in range(len(word)):
        bit = word[index]
        if bit == "1": 
          result[index] = result.get(index, 0) + 1
    N = len(BinStrings)
    for key in result.keys():
      result[key] = result[key] * 1.0 / N
    return result
  def seriesHistogram(BinString : str, IncludeAll = False) -> dict:
    result = dict()
    if IncludeAll:
      for i in range(len(BinString)):
        result[i] = 0
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
  def seriesCount(BinString : str) -> int:
    result = 0
    cPrev = "X"
    for c in BinString:
      if c != cPrev:
          result += 1
          cPrev = c
    return result
  def countOf1s(BinString : str) -> int:
    result = 0
    for c in BinString:
      if c == "1":
        result += 1
    return result
  

class Stats:
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
  def deviation(DictData : dict, Expected : float):
    sum = 0
    values = DictData.values()
    for val in values:
      sum += abs(val-Expected)
    return sum / len(values)
  def chi2(DictData : dict, Expected : float):
    sum = 0
    values = DictData.values()
    for val in values:
      sum += (val-Expected) ** 2
    return sum / Expected
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
    