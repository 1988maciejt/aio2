from bitarray import *



class Bitarray:
    
    def rotl(BitArrayValue : bitarray) -> bitarray:
        NewValue = BitArrayValue << 1
        NewValue[-1] = BitArrayValue[0]
        return NewValue
    
    def rotr(BitArrayValue : bitarray) -> bitarray:
        NewValue = BitArrayValue >> 1
        NewValue[0] = BitArrayValue[-1]
        return NewValue
        
    def getShiftBetweenSequences(A : bitarray, B : bitarray) -> int:
        if len(A) == len(B):
            B2 = B + B
            Res = B2.find(A)
            if Res >= 0:
                if Res > (len(A) >> 1):
                    return Res - len(A)
                return Res
        return None
    
    def toString(X : bitarray) -> str:
        Result = ""
        for b in reversed(X):
            Result += str(b)
        return Result
    
    def mapBits(Source : bitarray, IndexesList : list) -> bitarray:
        Result = bitarray(len(IndexesList), endian='little')
        for i in range(len(IndexesList)):
            Result[i] = Source[IndexesList[i]]
        return Result
    
    def setSeriesOfBits(Var : bitarray, Value, SerieLength : int, EveryNBit : int, StartFrom = 0):
        Len = len(Var)
        for i in range(StartFrom, Len, EveryNBit):
            for j in range(0, SerieLength):
                try:
                    Var[i + j] = Value
                except:
                    pass
    
    def resetSeriesOfBits(Var : bitarray, SerieLength : int, EveryNBit : int, StartFrom = 0):
        Len = len(Var)
        for i in range(StartFrom, Len, EveryNBit):
            for j in range(0, SerieLength):
                try:
                    Var[i + j] = 0
                except:
                    pass