import multiprocessing
from libs.files import *
from libs.aio import *
import re
import plotext
import multiprocess
from libs.binstr import *
import matplotlib.pyplot as plt
#import openpyxl


class Histogram:
  
  __slots__ = ("_data_dict", "_bar_width", "_bar_count", "_min", "_max")
  
  
  def __init__(self, Data = [], BarWidth : float = None, BarCount : int = 10):
    if type(BarWidth) in [float, int]:
      self._bar_width = BarWidth
      self._bar_count = None
    else:
      self._bar_count = int(BarCount)
      self._bar_width = None
    self._data_dict = {}
    self._min = None
    self._max = None
    self.addData(Data)
  
  def addData(self, Data):
    from libs.utils_float import FloatUtils
    if type(Data) in [int, float]:
      Data = [Data]
    for D in Data:
      if type(D) is list:
        D = D[0]
      D = float(D)
      if self._bar_width is not None:
        D = FloatUtils.roundToDecimalPlacesAsInAnotherFloat(D, self._bar_width)
      cnt = self._data_dict.get(D, 0)
      self._data_dict[D] = cnt + 1
      if self._min is None:
        self._min = D
        self._max = D
      else:
        if D < self._min: 
          self._min = D
        if D > self._max:
          self._max = D
          
  addDataPoint = addData
          
  def clearData(self):
    self._data_dict.clear()
    self._min = None
    self._max = None
    
  def setBarWidth(self, BarWidth : float):
    self._bar_width = BarWidth
    self._bar_count = None
  
  def setBarCount(self, BarCount : int):
    self._bar_width = None
    self._bar_count = BarCount
    
  def getPlotData(self, Min : float = None, Max : float = None) -> dict:
    from libs.utils_float import FloatUtils
    if Min is None:
      Min = self._min
    if Max is None:
      Max = self._max
    if self._bar_width is not None:
      BarWidth = self._bar_width
      BarCnt = None
    else:
      BarWidth = (Max - Min) / float(self._bar_count)
      BarCnt = self._bar_count
    Bars = []
    Barsp1 = []
    Vals = []
    Bar = FloatUtils.roundToDecimalPlacesAsInAnotherFloat(Min, BarWidth)
    if Bar is None or Max is None:
      return []
    Cnt = 0
    while Bar < Max:
      if BarCnt is not None:
        if Cnt >= BarCnt and BarCnt is not None:
          break
      Cnt += 1
      Bars.append(Bar)
      Barsp1.append(Bar)
      Vals.append(0)
      Bar = FloatUtils.roundToDecimalPlacesAsInAnotherFloat(Bar + BarWidth, BarWidth)
    Barsp1.append(Bar)
    for D in self._data_dict.keys():
      if Min <= D <= Max:
        Count = self._data_dict[D]
        for i in range(1, len(Barsp1)):
          if D < Barsp1[i]:
            Vals[i-1] += Count
            break
    return [Bars, Vals]
  
  
class RangesHistogram:
  
  __slots__ = ("_data", "_data_dict", "_range_count", "_min", "_max", "_data_cnt")
  
  def __init__(self, Data = [], RangeCount : int = 10):
    self._data_dict = {}
    self._min = None
    self._max = None
    self._data_cnt = 0
    self._range_count = RangeCount
    self.addData(Data)
  
  def addData(self, Data):
    if type(Data) in [int, float]:
      Data = [Data]
    for D in Data:
      if type(D) is list:
        D = D[0]
      D = float(D)
      cnt = self._data_dict.get(D, 0)
      self._data_dict[D] = cnt + 1
      self._data_cnt += 1
      if self._min is None:
        self._min = D
        self._max = D
      else:
        if D < self._min: 
          self._min = D
        if D > self._max:
          self._max = D
          
  addDataPoint = addData
          
  def clearData(self):
    self._data_dict.clear()
    self._min = None
    self._max = None
    self._data_cnt = 0
    
  def getRanges(self, Normalise : bool = False):
    BinVolume = self._data_cnt / float(self._range_count)
    Ranges = [self._min]
    Sum = 0
    MustAdd = True
    for i in sorted(self._data_dict.keys()):
      Sum += self._data_dict[i]
      MustAdd = True
      if Sum >= BinVolume:
        Ranges.append(i)
        Sum -= BinVolume
        MustAdd = False
    if MustAdd:
      Ranges.append(self._max)
    if Normalise:
      RangesNorm = []
      for r in Ranges:
        rn = (r - self._min) / (self._max - self._min)
        RangesNorm.append(rn)
      return RangesNorm
    return Ranges
  
  def getMinMax(self) -> tuple:
    return (self._min, self._max)
      
  def getPlotData(self) -> dict:
    y = self.getRanges()
    x = [i for i in range(len(y))]
    return [x, y]


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
    if type(Data) is dict:
      self.importDict(Data)
    elif type(Data) in [list, tuple]:
      if "list" in str(type(Data[0])):
        self.XData = Data[0].copy()
        self.YData = Data[1].copy()
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
    
  def getDraw(self) -> str:
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
      plotext.clear_figure()
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
        try:
          plotext.colorless()
        except:
          plotext.clear_color()
      Text = plotext.build()
      if not self.Colored:
        Text = Str.removeEscapeCodes(Text)
      return Text
      
  def print(self) -> None:
      Aio.print(self.getDraw())
      
    

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
    
class Stats:
  
  @staticmethod
  def chiSquared(Data) -> float:
    N = 0
    Avg = 0
    for I in Data:
      N += 1
      Avg += I
    Avg /= N
    Chi2 = 0
    for I in Data:
      Chi2 += ((I - Avg) / Avg)
    return Chi2
  
  def predictLinear(x : float, x1 : float, y1 : float, x2 : float, y2 : float) -> float:
    if x1 == x2:
      x2 += (y2 - y1)
    a = (y1 - y2) / (x1 - x2)
    b = y1 - a * x1
    y = x * a + b
    return y
  
  def predict(x : float, xPoints : list, yPoints : list) -> float:
    Points = [(xp, yp) for xp, yp in zip(xPoints, yPoints)]
    if len(Points) < 1:
      return None
    if len(Points) == 1:
      return Points[0][1]
    Points.sort(key = lambda x: x[0])
    if len(Points) == 2:
      return Stats.predictLinear(x, Points[0][0], Points[0][1], Points[1][0], Points[1][1])
    if len(Points) == 3:
      return Stats.predictLinear(x, Points[0][0], Points[0][1], Points[1][0], Points[1][1], Points[2][0], Points[2][1])
    if x <= Points[1][0]:
      return Stats.predictLinear(x, Points[0][0], Points[0][1], Points[1][0], Points[1][1])
    if x >= Points[-1][0]:
      return Stats.predictLinear(x, Points[-2][0], Points[-2][1], Points[-1][0], Points[-1][1])
    for i in range(len(Points)-1):
      if Points[i][0] <= x <= Points[i+1][0]:
        return Stats.predictLinear(x, Points[i][0], Points[i][1], Points[i+1][0], Points[i+1][1])
    return None
  
  def revertFunction(InXValues : list, InYValues : list, OutXStart : float, OutXStop : float, OutXStep : float) -> tuple:
    OutXValues, OutYValues = [], []
    X = OutXStart
    while X <= OutXStop:
      OutXValues.append(X)
      OutYValues.append(Stats.predict(X, InYValues, InXValues))
      X += OutXStep
    return (OutXValues, OutYValues)
  
  def interAndExtrapolate(XValues : list, YValues : list, XStart : float, XStop : float, XStep : float) -> tuple:
    OutXValues, OutYValues = [], []
    X = XStart
    while X <= XStop:
      OutXValues.append(X)
      OutYValues.append(Stats.predict(X, XValues, YValues))
      X += XStep
    return (OutXValues, OutYValues)
  
  
class MovingAverageFilter:
  
  slots = ('_samples', '_size', '_value')
  
  def __init__(self, Size : int = 10):
    if Size < 1:
      raise ValueError("MAV filter size must be a positive integer")
    self._samples = []
    self._size = Size
    self._value = 0.0
    
  def __len__(self):
    return len(self._samples)
  
  def filter(self, Value : float) -> float:
    """Filters the given value and returns the filtered value.
    
    Args:
        Value (float): input value
    
    Returns:
        float: filtered value
    """
    if len(self._samples) == self._size:
      self._samples.pop(0)
    self._samples.append(Value)
    self._value = sum(self._samples) / len(self._samples)
    return self._value
  
  add = filter
  
  def __call__(self, Value : float) -> float:
    return self.filter(Value)
  
  def getValue(self) -> float:
    """Returns the current filtered value.
    
    Returns:
        float: current filtered value
    """
    return self._value if hasattr(self, '_value') else 0.0
  
  def reset(self) -> None:
    """Resets the filter, clearing all samples.
    """
    self._samples.clear()
    self._value = 0.0
    
    