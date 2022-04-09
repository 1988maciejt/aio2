import re

class List:
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