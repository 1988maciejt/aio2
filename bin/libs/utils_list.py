import re
import random
import multiprocessing
import itertools
from libs.aio import *
from libs.files import *



class List:
  
  def getCombinations(List, k : int) -> list:
    Result = []
    for subset in itertools.combinations(List, k):
      if subset is None:
        break
      Result.append(subset)
    return Result
  
  def getPermutationsPfManyListsCount(lists) -> int:
    Result = 1
    for L in lists:
      Result *= len(L)
    return Result
  
  def getPermutationsPfManyLists(lists, MaximumNonBaseElements = 0) -> list:
    """gets some lists and returns a list of lists containing
    all possible permutations of elements of those lists.
    
    Examplecall:
    List.getPermutationsPfManyLists( [ [1,2], ['a', 'b', 'c'] ] )
    
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
  
  
  def getPermutationsPfManyListsGenerator(lists, MaximumNonBaseElements = 0, UseAsGenerator_Chunk = 1) -> list:
    """gets some lists and returns a list of lists containing
    all possible permutations of elements of those lists.
    
    Examplecall:
    List.getPermutationsPfManyLists( [ [1,2], ['a', 'b', 'c'] ] )
    
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
  
  def randomSelect(List : list, HowMany = 1):
    if len(List) < HowMany:
      Aio.printError("List length is < than HowMany")
      return None
    RList = List.copy()
    Result = []
    Max = len(RList)-1
    for i in range(HowMany):
      Index = random.randint(i, Max)
      Result.append(RList[Index])
      if Index > i:
        RList[Index] = RList[i]
    if len(Result) == 1:
      return Result[0]
    return Result
  
  def mathDelta(List : list) -> list:
    left = List[0]
    result = []
    for i in range(1, len(List)):
      this = List[i]
      result.append(this - left)
      left = this
    return result
  
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
    result = []
    for i in list1:
      if (not (i in list2)) and (not (i in result)):
        result.append(i)
    for i in list2:
      if (not (i in list1)) and (not (i in result)):
        result.append(i)
    return result
  
  def removeByString(lst : list, pattern) -> list:
    result = []
    for i in lst:
      if not re.search(pattern, str(i)):
        result.append(i)
    return result
  
  def splitIntoSublists(lst : list, SublistSize : int) -> list:
    result = []
    for i in range(0, len(lst), SublistSize):
      result.append(lst[i:(i+SublistSize)])
    return result
  
  def toString(lst : list, indent = 0) -> str:
    result = ""
    ind = " " * indent
    for i in lst:
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
    return [value for value in lst1 if value in lst2]
  
  def search(lst : list, item) -> list:
    indices = []
    for idx, value in enumerate(lst):
        if value == item:
            indices.append(idx)
    return indices
  
  def circularDiff(ListOfNumbers : list, Modulus : int) -> list:
    Result = []
    for i in range(len(ListOfNumbers)):
      D = ListOfNumbers[i] - ListOfNumbers[i-1]
      if i == 0:
        D += Modulus
      Result.append(D)
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
        self._user_dir = None
        self._list = []
        self._gz = GZipped
        self._file_i = 1
    else:
      self._td = TempDir()
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
  
  