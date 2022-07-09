import multiprocessing
from libs.files import *
from libs.aio import *
import re
import plotext
import multiprocess
from libs.binstr import *
import matplotlib.pyplot as plt
#import openpyxl

class PlotTypes:
  Scatter = 1,
  Bar = 2
  
SCATTER = PlotTypes.Scatter,
BAR = PlotTypes.Bar

class Plot:
  Title = ""
  XData = []
  YData = []
  Type = PlotTypes.Scatter
  BarWidth = 1
  XLabel = None
  YLabel = None
  XTicks = None
  YTicks = None
  Width = None
  Height = None
  Colored = None
  Graphical = False
  Lines = True
  def __init__(self, Data=None, Type=PlotTypes.Scatter, Title="", XTicks=None, YTicks=None, XLabel=None, YLabel=None, Grid=False, Width=None, Height=None, Colored=True, Lines=True, Graphical=False) -> None:
    """Initialization of the Plot object

    Args:
        Data (dict data, optional): plot X/Y data. Defaults to None.
        Type (str, optional): Plot type; available: "scatter","bar". Defaults to "scatter".
        Title (str, optional): Plot title. Defaults to "".
        XTicks (list, optional): a list containing X tick values. Defaults to None.
        YTicks (list, optional): a list containing Y tick values. Defaults to None.
        XLabel (str, optional): X-axis label.
        YLabel (str, optional): Y-axis label.
        Grid (bool, optional): whether to plot the grid or not. Defaults to False.
        Width (int, optional): plot width (char count). Defaults to None.
        Height (int, optional): plot height (rows count). Defaults to None.
        Colored (bool, optional): print colored plot or not. Defaults to True.
		Lines (bool, optionsl): whether to connect scatter points by lines (default) or not
		Graphical (bool, optional): default False. If True, then the graphical plot will be created instead of textplot
    """
    self.Title = Title
    if type("") == type(Type):
      if Type.lower == "scatter":
        self.Type = PlotTypes.Scatter
      elif Type.lower == "bar":
        self.Type = PlotTypes.Bar
    else:
      self.Type = Type
    self.Lines = Lines
    self.XTicks = XTicks
    self.YTicks = YTicks
    self.Grid = Grid
    self.Width = Width
    self.Height = Height
    self.Colored = Colored
    self.Graphical = Graphical
    self.XLabel = XLabel
    self.YLabel = YLabel
    if "dict" in str(type(Data)):
      self.importDict(Data)
    elif "list" in str(type(Data)):
      if "list" in str(type(Data[0])):
        self.XData = []
        self.YData = []
        for i in range(len(Data)):
          self.XData.append(Data[i][0])
          self.YData.append(Data[i][1])
      else:
        self.YData = Data
        self.XData = [i for i in range(len(Data))] 
  def importDict(self, dct : dict) -> None:
    """Imports a data dictionary, formatted like this:
    {
      x1: y1,
      x2: y2,
      ...
      xn: yn
    }
    """
    self.XData = []
    self.YData = []
    xs = list(dct.keys())
    xs.sort()
    for x in xs:
      self.XData.append(x)
      self.YData.append(dct[x])
  def exportDataToOpenpyxlSheet(self, Sheet, XColumn=1, YColumn=2, FirstRow=1):
    """Exports the data to a openpyxl Sheet instance

    Args:
        Sheet (openpyxl.Sheet): a Sheet instance in which to place the plot data
        XColumn (int, optional): in which column to place X values. Defaults to 1.
        YColumn (int, optional): in which column to place Y values. Defaults to 2.
        FirstRow (int, optional): first row of the data. Defaults to 1.
    """
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
    """Prints the plot data
    """
    Aio.print("------------------------")
    Aio.print(self.XLabel, "\t", self.YLabel)
    Aio.print("------------------------")
    for i in range(len(self.XData)):
      x = self.XData[i]
      y = self.YData[i]
      Aio.print(x, "\t", y)
    Aio.print("------------------------")
  def print(self) -> None:
    """Prints the plot
    """
    if self.Graphical:
      if self.Lines:
        plt.plot(self.XData, self.YData)
      else:
        plt.plot(self.XData, self.YData, linestyle='None')
      if self.XLabel != None:
        plt.xlabel(self.XLabel)
      if self.YLabel != None:
        plt.ylabel(self.YLabel)
      if self.XTicks != None:
        plt.xticks(self.XTicks)
      if self.YTicks != None:
        plt.yticks(self.YTicks)
      plt.grid(self.Grid)
      if self.Type == PlotTypes.Bar:
        plt.bar(self.XData, self.YData, width = self.BarWidth)
      else:  
        plt.scatter(self.XData, self.YData)
      plt.show()
    else:
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
      if self.Type == PlotTypes.Bar:
        plotext.bar(self.XData, self.YData, width = self.BarWidth)
      else:  
        plotext.scatter(self.XData, self.YData)
      if not self.Colored:
        plotext.colorless()
      Aio.print(plotext.build())

class BinStringStats:
  """Static class containing BinString object related stats.
  """
  def _p1_mproc(index):
    BinStringStats._p1res[index] = 0
    bsum = 0
    for bs in BinStringStats._data:
      bsum += bs[index]
    BinStringStats._p1res[index] = float(bsum) / BinStringStats._p1n
    Aio.print(index,"\t",BinStringStats._p1res[index])
  def probOf1Histogram(BinStrings : list) -> dict:
    """Returns a dict containing a histogram: P(1) for each bit in a sequence.

    Args:
        BinStrings (list): a list of BinString objects

    Returns:
        dict: usable for Plot
    """
    N = len(BinStrings)
    result = dict()
    for i in range(len(BinStrings[0])):
      result[i] = 0
    for word in BinStrings:
      for index in range(len(word)):
        bit = word[index]
        if bit == 1: 
          result[index] = result.get(index, 0) + 1
    for key in result.keys():
      result[key] = result[key] * 1.0 / N
    return result
  def seriesHistogram(data : BinString, IncludeAll = False) -> dict:
    """Returns a dict containing a series length histogram.

    Args:
        BinString (BinString): input data
        IncludeAll (bool, optional): Whether tp include series lengths appearing 0 times. Defaults to False.

    Returns:
        dict: usable for Plot
    """
    result = dict()
    if IncludeAll:
      for i in range(len(data)):
        result[i] = 0
    cntr = 0
    cPrev = -1
    for c in data:
      cntr += 1
      if c != cPrev:
        if cntr > 0:
          result[cntr] = result.get(cntr, 0) + 1
          cPrev = c
          cntr = 0
    return result
  def seriesCount(data : BinString) -> int:
    """Returns count of series in the given binary string

    Args:
        BinString (BinString): input data
    """
    result = 0
    cPrev = -1
    for c in data:
      if c != cPrev:
          result += 1
          cPrev = c
    return result
  def countOf1s(data : str) -> int:
    """Returns the count of 1s in the given binary string
    """
    result = 0
    for c in data:
      if c == 1:
        result += 1
    return result
  

class Stats:
  """A static class containing statistical methods
  """
  def readDieharder(FileName : str) -> list:
    """Reads the Dieharder-like data file.

    Args:
        FileName (str): dieharder-like data file

    Returns:
        list: list of integers
    """
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
  def deviation(DictData : dict, Expected : float) -> float:
    """Calculates a parameter non-officially called 'deviation':
    SUM ( abs(Pi - Expected) )

    Args:
        DictData (dict): dict-like data
        Expected (float): expected probavility value (0-1)
    """
    sum = 0
    values = DictData.values()
    for val in values:
      sum += abs(val-Expected)
    return sum / len(values)
  def chi2(DictData : dict, Expected : float) -> float:
    """Calculates chi-squared stat for a given dict data value

    Args:
        DictData (dict): input data
        Expected (float): expected probability
    """
    sum = 0
    values = DictData.values()
    for val in values:
      sum += (val-Expected) ** 2
    return sum / Expected
  def repeatedNumbers(data : list) -> dict:
    """Returns a stat showing repeated numbers in the given set

    Args:
        data (list): input data list

    Returns:
        dict: dictionary structure:
        {
          number: how_many_times_appeared,
          ...
        }
    """
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
    """Returns a stat showing series of repeated numbers in the given set

    Args:
        data (list): input data list

    Returns:
        dict: dictionary structure:
        {
          serie: how_many_times_appeared,
          ...
        }
    """
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
    
