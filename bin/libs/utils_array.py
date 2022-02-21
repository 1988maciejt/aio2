from array import *

def create2DArray(rows : int, cols : int) -> array:
    return [[0 for i in range(rows)] for j in range(cols)]