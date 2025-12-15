import re
import random
import multiprocessing
import itertools
from libs.aio import *
from libs.files import *



class List:
  
  @staticmethod
  def Sum(Numbers : list) -> float:
    Sum = 0.0
    for n in Numbers:
      try:
        Sum += float(n)
      except:
        pass
    return Sum
  
  @staticmethod
  def Avg(Numbers : list) -> float:
    Sum = 0.0
    Count = 0
    for n in Numbers:
      try:
        Sum += float(n)
        Count += 1
      except:
        pass
    if Count == 0:
      return 0.0
    return Sum / Count
  
  @staticmethod
  def StdDev(Numbers : list) -> float:
    from statistics import pstdev
    Values = []
    for n in Numbers:
      try:
        v = float(n)
        Values.append(v)
      except:
        pass
    if len(Values) < 2:
      return 0.0
    return pstdev(Values)
  
  @staticmethod
  def getIndexOfMinimum(Numbers : list) -> int:
    from statistics import median_low
    Min = min(Numbers)
    Indices = []
    for i, n in enumerate(Numbers):
      if n == Min:
        Indices.append(i)
    if len(Indices) < 1:
      return -1
    return median_low(Indices)
  
  @staticmethod
  def MAVFilter(Numbers : list, WindowSize : int, Round = None) -> list:
    WFilter = None
    if type(WindowSize) in [list, tuple]:
      WFilter = WindowSize
      WindowSize = len(WindowSize)
    if WindowSize < 2:
      Result = Numbers
    else:
      Result = []
      if WFilter is None:
        for i in range(len(Numbers)):
          Start = i - (WindowSize // 2)
          End = i + (WindowSize // 2) + (WindowSize % 2)
          if Start < 0:
            Start = 0
          if End > len(Numbers):
            End = len(Numbers)
          Sum = 0
          Count = 0
          for j in range(Start, End):
            Sum += Numbers[j]
            Count += 1
          Result.append(Sum / Count)
      else:
        for i in range(len(Numbers)):
          Start = i - (WindowSize // 2)
          End = i + (WindowSize // 2) + (WindowSize % 2)
          Idx = 0
          if Start < 0:
            Start = 0
          if End > len(Numbers):
            Idx = End - len(Numbers)
            End = len(Numbers)
          Sum = 0
          Div = 0
          for j in range(Start, End):
            Div += WFilter[Idx]
            Sum += Numbers[j] * WFilter[Idx]
            Idx += 1
          Result.append(Sum / Div)
    if Round is not None:
      for i in range(len(Result)):
        Result[i] = round(Result[i], Round)
    return Result
  
  def getCombinations(List, k : int) -> list:
    Result = []
    for subset in itertools.combinations(List, k):
      if subset is None:
        break
      Result.append(subset)
    return Result
  
  def getPermutationsOfManyListsCount(lists) -> int:
    Result = 1
    for L in lists:
      Result *= len(L)
    return Result
  getPermutationsPfManyListsCount = getPermutationsOfManyListsCount
  
  def getPermutationsOfManyLists(lists, MaximumNonBaseElements = 0) -> list:
    """gets some lists and returns a list of lists containing
    all possible permutations of elements of those lists.
    
    Examplecall:
    List.getPermutationsOfManyLists( [ [1,2], ['a', 'b', 'c'] ] )
    
    Result:
    [[1, 'a'], [2, 'a'], [1, 'b'], [2, 'b'], [1, 'c'], [2, 'c']]
    """
    MaxValues = []
    for L in lists:
      MaxValues.append(len(L))
    Size = len(MaxValues)
    Zeros = [0 for _ in range(Size)]
    Counter = Zeros.copy()
    N = len(MaxValues)
    Results = []
    while 1:
      Result = []
      ZeroElements = 0
      for c in Counter:
        if c == 0:
          ZeroElements += 1
      NonZeroElements = Size - ZeroElements
      if MaximumNonBaseElements <= 0 or NonZeroElements <= MaximumNonBaseElements:
        for i in range(N):
          Result.append(lists[i][Counter[i]])
        Results.append(Result)
      for i in range(N):
        Counter[i] += 1
        if Counter[i] < MaxValues[i]:
          break
        else:
          Counter[i] = 0
      if Counter == Zeros:
        break
    return Results
  getPermutationsPfManyLists = getPermutationsOfManyLists
  
  
  def getPermutationsOfManyListsGenerator(lists, MaximumNonBaseElements = 0, UseAsGenerator_Chunk = 1):
    """gets some lists and returns a list of lists containing
    all possible permutations of elements of those lists.
    
    Examplecall:
    List.getPermutationsOfManyListsGenerator( [ [1,2], ['a', 'b', 'c'] ] )
    
    Result:
    [[1, 'a'], [2, 'a'], [1, 'b'], [2, 'b'], [1, 'c'], [2, 'c']]
    """
    Chunk = 1
    if UseAsGenerator_Chunk > 0:
      Chunk = UseAsGenerator_Chunk
    MaxValues = []
    for L in lists:
      MaxValues.append(len(L))
    Size = len(MaxValues)
    Zeros = [0 for _ in range(Size)]
    Counter = Zeros.copy()
    N = len(MaxValues)
    Results = []
    while 1:
      Result = []
      ZeroElements = 0
      for c in Counter:
        if c == 0:
          ZeroElements += 1
      NonZeroElements = Size - ZeroElements
      if MaximumNonBaseElements <= 0 or NonZeroElements <= MaximumNonBaseElements:
        for i in range(N):
          Result.append(lists[i][Counter[i]])
        Results.append(Result)
        if len(Results) >= Chunk:
          yield Results
          Results.clear()
      for i in range(N):
        Counter[i] += 1
        if Counter[i] < MaxValues[i]:
          break
        else:
          Counter[i] = 0
      if Counter == Zeros:
        break
    if len(Results) >= 0:
      yield Results
      Results.clear()
    return None
  getPermutationsPfManyListsGenerator = getPermutationsOfManyListsGenerator
  
  def randomSelect(List : list, HowMany = 1) -> list:
    if len(List) < HowMany:
      Aio.printError("List length is < than HowMany")
      return None
    return random.sample(List, HowMany)
  
  def mathDelta(List : list) -> list:
    left = List[0]
    result = []
    for i in range(1, len(List)):
      this = List[i]
      result.append(this - left)
      left = this
    return result
  
  def shuffle(lst : list) -> list:
    result = lst.copy()
    random.shuffle(result)
    return result
  
  def onlyUniquesAreIncluded(Lst : list) -> bool:
    return len(set(Lst)) == len(Lst)
  
  def join(*lists) -> list:
    """Concatenates two lists without repetitions

    Returns:
        list: _description_
    """
    result = []
    for L in lists:
      for i in L:
        if (not (i in result)):
          result.append(i)
    return result
  
  def xor(list1 : list, list2 : list) -> list:
    return list(set(list1) ^ set(list2))
  
  def removeByString(lst : list, pattern) -> list:
    return list(filter(lambda x: not re.search(pattern, str(x)), lst))
  
  def splitIntoSublists(lst : list, SublistSize : int, Overlaping : int= 0) -> list:
    result = []
    if Overlaping < 0:
      Overlaping = 0
    LastIncluded = 0
    for i in range(0, len(lst), SublistSize-Overlaping):
      Sublist = lst[i:(i+SublistSize)]
      if LastIncluded:
        if len(Sublist) < SublistSize:
          break
      else:
        if i+SublistSize >= len(lst):
          LastIncluded = 1
      result.append(Sublist)
    return result
  
  def toString(lst : list, indent = 0, IncludeIndices = False) -> str:
    result = ""
    ind = " " * indent
    for i in lst:
      if IncludeIndices:
        result += f"Idx={i}: \t"
      result += ind + str(i) + "\n"
    return result
  
  def toBytes(lst : list) -> bytes:
    lstlen = len(lst)
    if lstlen <= 512:      
      result = bytes(0)
      for item in lst:
        result += bytes(item)
      return result
    sublists = List.splitIntoSublists(lst, 512)
    pool = multiprocessing.Pool()
    reslist = pool.map(List.toBytes, sublists)
    pool.close()
    pool.join()
    result = bytes(0)
    for r in reslist:
      result += r
    return result
    
  def intersection(lst1 : list, lst2 : list) -> list:
    return list(set(lst1) & set(lst2))
  
  def search(lst : list, item) -> list:
    return [i for i, x in enumerate(lst) if x == item]
  
  def circularDiff(ListOfNumbers : list, Modulus : int) -> list:
    Result = []
    valim1 = ListOfNumbers[-1]
    for i, vali in enumerate(ListOfNumbers):
      D = vali - valim1
      if i == 0:
        D += Modulus
      Result.append(D)
      valim1 = vali
    return Result
  
  def circularIterator(lst : list, FromIndex : int, ToIndex : int):
    Modulus = len(lst)
    while FromIndex < 0:
      FromIndex += Modulus
    while ToIndex < FromIndex:
      ToIndex += Modulus
    for i in range(FromIndex, ToIndex+1):
      yield lst[i % Modulus]
      
  def circularShift(lst, IndexOfFirstItem : int)-> list:
    Modulus = len(lst)
    while IndexOfFirstItem < 0:
      IndexOfFirstItem += Modulus
    IndexOfFirstItem = (IndexOfFirstItem % Modulus)
    return lst[IndexOfFirstItem:] + lst[:IndexOfFirstItem]
  
  def circularAlign(ListOfNumbers) -> list:
    Min = min(ListOfNumbers)
    MinIndices = List.search(ListOfNumbers, Min)
    Dict = {}
    for i in range(len(MinIndices)):
      Num = 0
      for CItem in List.circularIterator(ListOfNumbers, MinIndices[i-1], MinIndices[i]-1):
        Num = (Num * 10) + CItem
      Dict[MinIndices[i-1]] = Num
    MaxIndex = -1
    MaxValue = -1
    for k in Dict.keys():
      v = Dict[k]
      if v > MaxValue:
        MaxValue = v
        MaxIndex = k
    return List.circularShift(ListOfNumbers, MaxIndex)
  
  def getDifferentItems(a : list, b : list) -> list:
    return list(set(a) ^ set(b))
  
  


class BufferedList:
  
  __slots__ = ("_list", "_td", "_gz", "_iter_i", "_file_i", "_user_dir", "SaveData")
  
  def __init__(self, OtherObject = None, UserDefinedDirPath : str = None, GZipped : bool = False):
    if type(UserDefinedDirPath) is str:
      try:
        UserDefinedDirPath = os.path.abspath(UserDefinedDirPath)
        if not os.path.exists(UserDefinedDirPath):
          os.makedirs(UserDefinedDirPath)
        self._user_dir = UserDefinedDirPath
        FTest = self._getFileName(0)
        writeFile(FTest, "")
        removeFile(FTest)
        self._td = None
        try:
          fl = readObjectFromFile(f'{self._user_dir}/index')
          self._list = fl[0]
          self._gz = fl[1]
          self._file_i = fl[2]
        except:
          self._list = []
          self._gz = GZipped
          self._file_i = 1
      except:
        Aio.printError(f"Cannot use '{UserDefinedDirPath}' as a writable directory.")
        self._td = TempDir()
        self._td.DontDelete = True
        self._user_dir = None
        self._list = []
        self._gz = GZipped
        self._file_i = 1
    else:
      self._td = TempDir()
      self._td.DontDelete = True
      self._user_dir = None
      self._list = []
      self._gz = GZipped
      self._file_i = 1
    self._iter_i = 0
    self.SaveData = False
    if type(OtherObject) in [list, set]:
      for Item in OtherObject:
        self.append(Item)
    elif type(OtherObject) is BufferedList:
      self._gz = OtherObject._gz
      self._file_i = OtherObject._file_i
      OtherDir = OtherObject.getDirPath()
      SelfDir = self.getDirPath()
      for OtherFileName in OtherObject._list:
        SelfFilename = OtherFileName.replace(OtherDir, SelfDir)
        self._list.append(SelfFilename)
        shutil.copy(OtherFileName, SelfFilename)
        
  def copy(self):
    return BufferedList(self)
        
  def __del__(self) -> None:
    if (self._td is not None):
      if self.SaveData:
        self._td.DontDelete = True
      else:
        self._td.DontDelete = False
        del self._td
        
    
  def __len__(self) -> int:
    return len(self._list)
  
  def __repr__(self) -> str:
    return f"BufferedList('{self.getDirPath()}')"
  
  def __str__(self) -> str:
    return repr(self)
  
  def __iter__(self):
    self._iter_i = 0
    return self
  
  def __next__(self):
    if self._iter_i >= len(self._list):
      raise StopIteration  
    else:
      index = self._iter_i
      self._iter_i += 1
      return self[index]
  
  def _getFileName(self, Index : int) -> str:
    if self._user_dir is None:
      return f"{self._td.getPath()}/{Index}"
    return f"{self._user_dir}/{Index}"
  
  def append(self, Item):
    FileName = self._getFileName(self._file_i)
    self._file_i += 1
    self._list.append(FileName)
    writeObjectToFile(FileName, Item, self._gz)
    if self._user_dir is not None:
      writeObjectToFile(f'{self._user_dir}/index', [self._list, self._gz, self._file_i])
    
  def __getitem__(self, i):
    if type(i) is slice:
      Result = []
      for it in self._list.__getitem__(i):
        Result.append(readObjectFromFile(it, self._gz))
      return Result
    else:
      return readObjectFromFile(self._list.__getitem__(i), self._gz)
    
  def __setitem__(self, i, item):
    if type(i) is slice:
      for Index, Obj in zip(range(*i.indices(len(self._list))), item):
        FileName = self._list[Index]
        writeObjectToFile(FileName, Obj, self._gz)
    else:
      FileName = self._list[i]
      writeObjectToFile(FileName, item, self._gz)
      
  def getUnbuffered(self):
    return self[0:]
      
  def getDirPath(self):
    if self._user_dir is not None:
      return self._user_dir
    return self._td.getPath()
  
  def clear(self):
    for FileName in self._list:
      removeFile(FileName)
    self._list.clear()
    self._file_i = 1
  


class ListOfDicts:
  
  @staticmethod
  def isListOfDicts(Object) -> bool:
    if type(Object) is not list:
      return False
    for D in Object:
      if type(D) is not dict:
        return False
    return True
  
  @staticmethod
  def getSumOfField(ListOfDicts : list, FieldName : str) -> float:
    Sum = 0.0
    for D in ListOfDicts:
      if FieldName in D:
        try:
          Sum += float(D[FieldName])
        except:
          pass
    return Sum
  
  @staticmethod
  def getAvgOfField(ListOfDicts : list, FieldName : str) -> float:
    Sum = 0.0
    Count = 0
    for D in ListOfDicts:
      if FieldName in D:
        try:
          Sum += float(D[FieldName])
          Count += 1
        except:
          pass
    if Count == 0:
      return 0.0
    return Sum / Count
  
  @staticmethod
  def getCountOfField(ListOfDicts : list, FieldName : str) -> int:
    Count = 0
    for D in ListOfDicts:
      if FieldName in D:
        Count += 1
    return Count
  
  @staticmethod
  def getStdDevOfField(ListOfDicts : list, FieldName : str) -> float:
    from statistics import pstdev
    Values = []
    for D in ListOfDicts:
      if FieldName in D:
        try:
          v = float(D[FieldName])
          Values.append(v)
        except:
          pass
    if len(Values) < 2:
      return 0.0
    return pstdev(Values)
  
  @staticmethod
  def getMaxOfField(ListOfDicts : list, FieldName : str) -> float:
    Max = None
    for D in ListOfDicts:
      if FieldName in D:
        try:
          v = float(D[FieldName])
          if Max is None or v > Max:
            Max = v
        except:
          pass
    return Max
  
  @staticmethod
  def getMinOfField(ListOfDicts : list, FieldName : str) -> float:
    Min = None
    for D in ListOfDicts:
      if FieldName in D:
        try:
          v = float(D[FieldName])
          if Min is None or v < Min:
            Min = v
        except:
          pass
    return Min
  
  @staticmethod
  def getListOfField(ListOfDicts : list, FieldName : str, NoneIfNoField : bool = False) -> list:
    Result = []
    for D in ListOfDicts:
      if FieldName in D:
        Result.append(D[FieldName])
      else:
        if NoneIfNoField:
          Result.append(None)
    return Result
  
  