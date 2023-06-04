from bitarray import *
from random import randint
import bitarray.util as bau
import hashlib
import pickle
from libs.utils_list import *
import hyperloglog
from libs.generators import *


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
                
    def rand(Size : int) -> bitarray:
        return bau.int2ba(randint(0, (1<<Size)-1), Size)
    
    def countNotMatchingBits(A : bitarray, B : bitarray):
        return bau.count_xor(A, B)
    
    def getAllBitarrayWithSingleBitFlipped(Word : bitarray):
        Results = []
        Len = len(Word)
        for i in range(Len):
            Result = Word.copy()
            Result[i] ^= 1
            Results.append(Result)
        return Results
    
    def movingWindowIterator(Word : bitarray, WindowSize : int):
        W = Word.copy()
        Steps = len(Word)
        while len(W) < WindowSize:
            W += W
        W += W[:WindowSize]
        for i in range(Steps):
            yield W[i:i+WindowSize]
            
    def fromStringOfHex(Text : str, GroupSize=32) -> bitarray:
        Result = bitarray()
        for Group in Text.strip().split(" "):
            Result += bau.int2ba(int(Group, 16), GroupSize)
        return Result
    
    def getRotationInsensitiveSignature(Word : bitarray, BlockSize) -> int:
        WLen = len(Word)
        W = Word + Word[0:BlockSize-1]
        Z = bau.zeros(BlockSize)
        Z[0] = 1
        Z[BlockSize-1] = 1
        Zeros = W.search(Z)
        if len(Zeros) == 0:
            RZeros = -1
        elif len(Zeros) == 1:
            RZeros = 0
        else:
            RZeros = List.circularAlign(List.circularDiff(Zeros, WLen))
        #print(RZeros)
        #HZ = hashlib.sha1(pickle.dumps(RZeros)).hexdigest()
        HZ = hash(pickle.dumps(RZeros))
        return HZ
    
    def getHyperLogLogCardinality(Word : bitarray, TupleSize : int, Error = 0.01) -> int:
        hll = hyperloglog.HyperLogLog(Error)
        for t in Bitarray.movingWindowIterator(Word, TupleSize):
            hll.add(t)
        return len(hll)
    
    def getCardinality(Word : bitarray, TupleSize : int) -> int:
        Res = bau.zeros(1<<TupleSize)
        for t in Bitarray.movingWindowIterator(Word, TupleSize):
            Res[bau.ba2int(t)] = 1
        return Res.count(1)
    
    def getTuplesHistogram(Word : bitarray, TupleSize : int) -> int:
        Res = [0 for i in range(1<<TupleSize)]
        for i in range(1<<TupleSize):
            Res[i] = 0
        for t in Bitarray.movingWindowIterator(Word, TupleSize):
            Res[bau.ba2int(t)] += 1
        return Res
    
    def getMissingTuples(Word : bitarray, TupleSize : int) -> list:
        Missing = []
        Res = bau.zeros(1<<TupleSize)
        for t in Bitarray.movingWindowIterator(Word, TupleSize):
            Res[bau.ba2int(t)] = 1
        Indices = Res.search(0)
        for i in Indices:
            Missing.append(bau.int2ba(i, TupleSize))
        return Missing
    
    def getTuples(Word : bitarray, TupleSize : int) -> list:
        Tuples = []
        Res = bau.zeros(1<<TupleSize)
        for t in Bitarray.movingWindowIterator(Word, TupleSize):
            Res[bau.ba2int(t)] = 1
        Indices = Res.search(1)
        for i in Indices:
            Tuples.append(bau.int2ba(i, TupleSize))
        return Tuples
    
    def getHammingDistance(A : bitarray, B : bitarray) -> int:
        return bau.count_xor(A, B)

    def getHammingSimilarity(A : bitarray, B : bitarray) -> float:
        return 1.0 - (Bitarray.getHammingDistance(A, B) / len(A))
    
    def getBestHammingSimilarity(A : bitarray, B : bitarray, ReturnAlsoShift = False) -> float:
        BestSHift = 0
        BestValue = 0.0
        Brot = B.copy()
        for i in range(len(A)):
            S = Bitarray.getHammingSimilarity(A, Brot)
            if S > BestValue:
                BestValue = S
                BestSHift = i
            Brot = Bitarray.rotl(Brot)
        if ReturnAlsoShift:
            return BestValue, BestSHift
        return BestValue
    
    def getLinearComplexity(Word : bitarray) -> int:
        from libs.lfsr import Polynomial
        return Polynomial.decodeUsingBerlekampMassey(Word).getDegree()