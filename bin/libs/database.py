from libs.files import *

def getPrimitiveTestingCyclesList(index : int) -> list:
  global primitive_testing_dict
  if "primitive_testing_dict" not in globals():
    primitive_testing_dict = readDictionary(getAioPath()+"data/primitive_testing.dict")
  return primitive_testing_dict[index]