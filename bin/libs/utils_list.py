import re
import numpy
#import numba
import random
import multiprocessing



class List:
  def randomSelect(List : list):
    if len(List) > 0:
      Max = len(List)-1
      Index = int(round(random.uniform(0, Max), 0))
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
  def join(list1 : list, list2 : list) -> list:
    result = []
    for i in list1:
      if (not (i in result)):
        result.append(i)
    for i in list2:
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
  def toString(lst : list) -> str:
    result = ""
    for i in lst:
      result += str(i) + "\n"
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
    
  