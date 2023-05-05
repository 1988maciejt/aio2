from libs.files import *
import re


class DB:
  
  def getPrimitiveTestingCyclesList(index : int) -> list:
    global primitive_testing_dict
    if "primitive_testing_dict" not in globals():
      primitive_testing_dict = readDictionary(getAioPath()+"data/primitive_testing.dict")
    return primitive_testing_dict.get(index, None)
  
  def getReducibleToAExpressionsList(VarCount : int, MonomnialCount : int, OnlyThoseHavingSingleVariableMonomial = None, RandomlySelectOneExpression = False) -> list:
    global reducible_to_a_dict
    if "reducible_to_a_dict" not in globals():
      reducible_to_a_dict = readDictionary(getAioPath()+"data/reducible_to_a.dict")
    Result = reducible_to_a_dict.get((VarCount, MonomnialCount), [])
    if OnlyThoseHavingSingleVariableMonomial is not None:
      ResFilt = []
      for E in Result:
        R = re.search(r'\((~|)[b-z]\)', E)
        if (OnlyThoseHavingSingleVariableMonomial and R) or (not(OnlyThoseHavingSingleVariableMonomial) and not(R)):
          ResFilt.append(E)
      Result = ResFilt
    if RandomlySelectOneExpression:
      if len(Result) <= 1:
        return None
      if len(Result) == 1:
        return Result[0]
      else:
        return Result[random.randint(0, len(Result)-1)]    
    else:
      return Result