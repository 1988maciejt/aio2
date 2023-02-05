import re
import numpy
#import numba
import random
import multiprocessing
import itertools



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
  
  def randomSelect(List : list):
    if len(List) > 0:
      Max = len(List)-1
      Index = int(round(random.uniform(-0.49, Max+0.49), 0))
      return List[Index]
    return None
  
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