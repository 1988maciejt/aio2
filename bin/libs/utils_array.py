from array import *

def create2DArray(rows : int, cols : int, val = 0, copy = 0) -> array:
    if copy:
        return [[val.copy() for i in range(rows)] for j in range(cols)]        
    return [[val] * rows for j in range(cols)]