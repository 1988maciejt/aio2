from bitarray import *
from random import randint
import bitarray.util as bau
import hashlib
import pickle
from libs.utils_list import *
import hyperloglog
from libs.generators import *
from p_tqdm import *
from functools import partial
from tqdm import *
from libs.stats import *


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
                
    def rand(Size : int, P1 = 0) -> bitarray:
        if (1 > P1 > 0):
            Result = bau.zeros(Size)
            for i in range(Size):
                if random.uniform(0, 1) <= P1:
                   Result[i] = 1
        else:
            Result = bau.int2ba(randint(0, (1<<Size)-1), Size)
        return Result
    
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
    
    def movingWindowIterator(Word : bitarray, WindowSize : int, Cyclic = True):
        if Cyclic:
            W = Word.copy()
            while len(W) < WindowSize:
                W += W
            W += W[:WindowSize-1]
            Steps = len(Word)
            for i in range(Steps):
                yield W[i:i+WindowSize]
            W.clear()
        else:
            if WindowSize <= len(Word):
                Steps = len(Word) - WindowSize + 1
                for i in range(Steps):
                    yield Word[i:i+WindowSize]
    
    def movingWindowIteratorInt(Word : bitarray, WindowSize : int, Cyclic = True):
        if Cyclic:
            W = Word.copy()
            while len(W) < WindowSize:
                W += W
            W += W[:WindowSize-1]
            Initial = WindowSize-1
            Res = 0
            Mask = (1 << WindowSize) -1
            for b in W:
                Res <<= 1
                Res += b
                if Initial:
                    Initial -= 1
                else:
                    Res &= Mask
                    yield Res
            W.clear()
        else:
            Initial = WindowSize-1
            Res = 0
            Mask = (1 << WindowSize) -1
            for b in Word:
                Res <<= 1
                Res += b
                if Initial:
                    Initial -= 1
                else:
                    Res &= Mask
                    yield Res
                
            
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
    
    def getCardinality(Word : bitarray, TupleSize : int, ParallelTuplesPerChunk = 0, ThisIsSubStepForParallelImplementation = False) -> int:
        if ParallelTuplesPerChunk > 1:
            Res = bau.zeros(1<<TupleSize)
            BList = Bitarray.divideIntoSubArraysToIterateThroughAllTuples(Word,TupleSize,ParallelTuplesPerChunk,True)
            BList.SaveData = True
            Iter = p_uimap(partial(Bitarray.getCardinality, TupleSize=TupleSize, ThisIsSubStepForParallelImplementation=True), BList, desc="Cardinality computing")
            for I in Iter:
                Res |= I
            BList.SaveData = False
            del BList
            return Res.count(1)
        else:
            Res = bau.zeros(1<<TupleSize)
            for t in Bitarray.movingWindowIteratorInt(Word, TupleSize, Cyclic=(not ThisIsSubStepForParallelImplementation)):
                Res[t] = 1
            if ThisIsSubStepForParallelImplementation:
                return Res
            return Res.count(1)
    
    def getTuplesHistogram(Word : bitarray, TupleSize : int) -> int:
        Res = [0 for i in range(1<<TupleSize)]
        for i in range(1<<TupleSize):
            Res[i] = 0
        for t in Bitarray.movingWindowIteratorInt(Word, TupleSize):
            Res[t] += 1
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
    
    def getLinearComplexity(Word : bitarray, Course = False) -> int:
        from libs.lfsr import Polynomial
        if Course:
            return Polynomial.decodeUsingBerlekampMassey(Word).getDegree()
        else:
            return Polynomial.decodeUsingBerlekampMassey(Word).getDegree()
        
    def divideIntoSubArraysToIterateThroughAllTuples(Word : bitarray, TupleSize : int, MaxTuplesCountPerSubArray : int = 1000000, UseBufferedList = False) -> list:
        if UseBufferedList:
            Result = BufferedList()
        else:
            Result = []
        W = Word.copy()
        W += W[:(TupleSize-1)]
        BlockSize = MaxTuplesCountPerSubArray + TupleSize - 1
        Start = 0
        Stop = BlockSize
        All = 0
        while Stop <= len(W):
            Result.append(W[Start:Stop])
            if (Stop == len(W)):
                All = 1
            Start += MaxTuplesCountPerSubArray
            Stop += MaxTuplesCountPerSubArray
        if not All:
            Result.append(W[Start:])
        W.clear()
        return Result
    
    def transpose(ListOfBitarrays : list) -> list:
        if len(ListOfBitarrays) == 0:
            return []
        WLen = len(ListOfBitarrays[0])
        WCount = len(ListOfBitarrays)
        Result = [bitarray(WCount) for _ in range(WLen)]
        for sbit, Word in zip(range(WCount), ListOfBitarrays):
            for sid, Bit in zip(range(WLen), Word):
                Result[sid][sbit] = Bit
        return Result
    
    
class TuplesReport:
    
    __slots__ = ("_histo_dict", "_tmin", "_tmax", "_stats", "_pass")
    
    def __init__(self, Word : bitarray, FromTupleSize : int = 2, ToTupleSize : int = 8, Significance=0.05):
        self._histo_dict = {}
        self._tmin = FromTupleSize
        self._tmax = ToTupleSize
        self._stats = {}
        self._pass = {}
        from scipy.stats import chisquare
        from scipy.stats import chi2
        for TSize in tqdm(range(FromTupleSize, ToTupleSize+1), desc="Counting tuples"):
            H = Bitarray.getTuplesHistogram(Word, TSize)
            self._histo_dict[TSize] = H
            self._stats[TSize] = chisquare(H)
            Critical = chi2.isf(Significance, (1<<TSize)-1)
            self._pass[TSize] = True if self._stats[TSize].statistic <= Critical else False
            
    def getReport(self, FromTupleSize : int = None, ToTupleSize : int = None, Colored = False, HidePlot = False) -> str:
        if FromTupleSize is None:
            FromTupleSize = self._tmin
        elif FromTupleSize < self._tmin:
            FromTupleSize = self._tmin
        if ToTupleSize is None:
            ToTupleSize = self._tmax
        elif ToTupleSize > self._tmax:
            ToTupleSize = self._tmax
        if ToTupleSize < FromTupleSize:
            Aio.printError("ToTupleSize must be >= FromTupleSize.")
            return ""
        Result = ""
        for TSize in range(FromTupleSize, ToTupleSize+1):
            H = self._histo_dict[TSize]
            HValues = H
            Min = min(HValues)
            Max = max(HValues)
            PDiv = self._stats[TSize]
            Pass = self._pass[TSize]
            Result += f"=================================[ Tuple size: {TSize} ]====================================\n\n"
            Result += f"Min: {Min}, \tMax: {Max}, \tChi{Str.toSuperScript('2')}: {PDiv.statistic}, \tPval: {PDiv.pvalue}  \t->  {'PASSED' if Pass else 'FAILED'}\n\n"
            if not HidePlot:
                Result += Plot(H, PlotTypes.Bar, Width=80, Height=16, Colored=Colored).getDraw()
            Result += "HistogramValues = " + str(H)
            Result += "\n\n"
        return Result
        
    def toHtmlFile(self, HtmlFileName : str, FromTupleSize : int = None, ToTupleSize : int = None, Colored = False, HidePlot = False):
        FileText = self.getReport(FromTupleSize, ToTupleSize, Colored, HidePlot)
        conv = Ansi2HTMLConverter(escaped=False, dark_bg=0, title="TuplesReport", line_wrap=1, linkify=0)
        html = conv.convert(FileText)
        html = re.sub(r'(\.ansi2html-content\s+)(\{)', '\g<1>{ font-family: "Lucida Console", Cascadia, Consolas, Monospace;', html)
        html = re.sub(r'(\*\s+)(\{)', '\g<1>{ font-family: "Lucida Console", Cascadia, Consolas, Monospace;', html)
        html = re.sub(r'.body_background { background-color: #AAAAAA; }', '.body_background { background-color: #FFFFFF; }', html)
        HtmlFile = open(HtmlFileName, "w")
        HtmlFile.write(html)
        HtmlFile.close()
    
    def printReport(self, FromTupleSize : int = None, ToTupleSize : int = None, Colored = True, HidePlot = False) -> None:
        Aio.print(self.getReport(FromTupleSize, ToTupleSize, Colored, HidePlot))
        
    def getPassFailedList(self, FromTupleSize : int = None, ToTupleSize : int = None) -> list:
        if FromTupleSize is None:
            FromTupleSize = self._tmin
        if ToTupleSize is None:
            ToTupleSize = self._tmax
        if ToTupleSize < FromTupleSize:
            Aio.printError("ToTupleSize must be >= FromTupleSize.")
            return []
        Result = []
        for i in range(FromTupleSize, ToTupleSize+1):
            PF = self._pass.get(i, None)
            if PF is None:
                PFS = "-"
            else:
                if PF:
                    PFS = "P"
                else:
                    PFS = "F"
            Result.append(PFS)
        return Result