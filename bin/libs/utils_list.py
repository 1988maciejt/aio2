import re
import numpy
import numba



class List:
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