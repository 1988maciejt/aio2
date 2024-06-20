from bitarray import *
from random import randint
import bitarray.util as bau
import hashlib
import pickle
from libs.utils_list import *
from libs.generators import *
from p_tqdm import *
from functools import partial
from tqdm import *
from libs.stats import *
import numpy
from libs.aio import AioShell
import hyperloglog
import statistics


class Bitarray:
    
    @staticmethod
    def fromFile(FileName : str, Length : int = None) -> bitarray:
        Result = bitarray()
        File = open(FileName, 'rb')
        Result.fromfile(File)
        File.close()
        if Length is not None:
            if len(Result) == 0:
                return None
            if len(Result) > Length:
                Result = Result[:Length]
            elif len(Result) < Length:
                Res2 = Result.copy()
                while len(Res2) < Length:
                    if Length - len(Res2) > len(Result):
                        Res2 += Result
                    else:
                        Res2 += Result[:Length - len(Res2)]
                Result = Res2
        return Result
    
    @staticmethod
    def toFile(FileName : str, Data : bitarray) -> bool:
        try:
            File = open(FileName, 'wb')
            Data.tofile(File)
            File.close()
            return True
        except:
            return False
    
    @staticmethod
    def rotl(BitArrayValue : bitarray) -> bitarray:
        NewValue = BitArrayValue << 1
        NewValue[-1] = BitArrayValue[0]
        return NewValue
    
    @staticmethod
    def rotr(BitArrayValue : bitarray) -> bitarray:
        NewValue = BitArrayValue >> 1
        NewValue[0] = BitArrayValue[-1]
        return NewValue
        
    @staticmethod
    def getShiftBetweenSequences(A : bitarray, B : bitarray) -> int:
        if len(A) == len(B):
            B2 = B + B
            Res = B2.find(A)
            if Res >= 0:
                if Res > (len(A) >> 1):
                    return Res - len(A)
                return Res
        return None
    
    @staticmethod
    def howMuchDelayedIsTheGivenSequence(Sequence : bitarray, Reference : bitarray) -> int:
        if len(Sequence) == len(Reference):
            B2 = Sequence + Sequence
            Res = B2.find(Reference)
            if Res >= 0:
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
            del W
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
                Res = (Res * 2) + b
                if Initial:
                    Initial -= 1
                else:
                    Res &= Mask
                    yield Res
            del W
        else:
            Initial = WindowSize-1
            Res = 0
            Mask = (1 << WindowSize) -1
            for b in Word:
                Res = (Res * 2) + b
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
        if type(BlockSize) is not int:
            Result = []
            for bs in BlockSize:
                Result.append(Bitarray.getRotationInsensitiveSignature(Word, int(bs)))
            return tuple(Result)
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
    
    def getCardinality(Word : bitarray, TupleSize : int, PeriodicSequence = True) -> int:
        Res = bau.zeros(1<<TupleSize)
        Mask = (1 << TupleSize) -1
        ResI = 0
        if PeriodicSequence:
            for i in range(1-TupleSize, 0):
                ResI = (ResI * 2) + Word[i]
            for b in Word:
                ResI = ((ResI * 2) + b) & Mask
                Res[ResI] = 1 
        else:
            for i in range(TupleSize-1):
                ResI = (ResI * 2) + Word[i]
            for i in range(TupleSize-1, len(Word)):
                ResI = ((ResI * 2) + Word[i]) & Mask
                Res[ResI] = 1 
        return Res.count(1)
    
    def getCardinalityList(List : list, TupleSize : int, Parallel = False) -> list:
        if Parallel:
            return p_map(partial(Bitarray.getCardinality, TupleSize=TupleSize), List)
        else:
            Result = []
            for i in tqdm(List):
                Result.append(Bitarray.getCardinality(i, TupleSize))
            return Result
        
    def getCardinalitySafe(Word : bitarray, TupleSize : int) -> int:
        Res = bau.zeros(1<<TupleSize)
        W = Word.copy()
        while len(W) < TupleSize:
            W += Word
        W += W[:TupleSize-1]
        Initial = TupleSize-1
        ResI = 0
        Mask = (1 << TupleSize) -1
        for b in W:
            ResI = (ResI * 2) + b
            if Initial:
                Initial -= 1
            else:
                ResI &= Mask
                Res[ResI] = 1 
        del W
        return Res.count(1)
    
    def getTuplesHistogram(Word : bitarray, TupleSize : int, Cyclic = True) -> list:
        Res = [0 for i in range(1<<TupleSize)]
        for i in range(1<<TupleSize):
            Res[i] = 0
        for t in Bitarray.movingWindowIteratorInt(Word, TupleSize, Cyclic=Cyclic):
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
    
    def getLinearComplexity(Word : bitarray, ProgressBar = False) -> int:
        from libs.lfsr import Polynomial
        return Polynomial.getLinearComplexityUsingBerlekampMassey(Word, ProgressBar=ProgressBar)
        
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
    
    def getTuplesReport(Word : bitarray, FromTupleSize : int = 2, ToTupleSize : int = 8, Significance=0.05):
        return TuplesReport(Word, FromTupleSize, ToTupleSize, Significance)
    
    def areLeftBitsEqual(A : bitarray, B : bitarray) -> bool:
        if len(A) != len(B):
            if len(A) < len(B):
                return A == B[:len(A)]
            return A[:len(B)] == B
        return A == B

    def getFirstAndSecondOnesPosition(Word : bitarray) -> tuple:
        First = Word.find(1, 0)
        Second = Word.find(1, First+1)
        return First, Second
    
    
class BitarrayStats:
    
    @staticmethod
    def probabilityOf1(BitStream : bitarray, SampleSize : int = 1000000) -> tuple:
        SamplesCount = len(BitStream) // SampleSize
        Counters = [0 for _ in range(SampleSize)]
        for i in range(SamplesCount):
            FromBit = i * SampleSize
            ToBit = FromBit + SampleSize
            SubArray = BitStream[FromBit : ToBit]
            j = 0
            for b in SubArray:
                if b:
                    Counters[j] += 1
                j += 1
        for i in range(len(Counters)):
            Counters[i] /= SamplesCount
        Pmean = statistics.mean(Counters)
        Pstdev = statistics.stdev(Counters)
        Z = sqrt(SamplesCount) * (Pmean - 0.5) / Pstdev
        return (Pmean, Pstdev, Z) 
    
    @staticmethod
    def correlation(BitStream : bitarray, SampleSize : int = 128) -> tuple:
        SamplesCount = len(BitStream) // SampleSize
        def corr(Word : bitarray) -> list:
            Result = []
            for i in range(len(Word)):
                b1 = Word[i]
                for j in range(i+1, len(Word)):
                    if b1 == Word[j]:
                        Result.append(1)
                    else:
                        Result.append(-1)
            return Result
        Samples = [BitStream[i * SampleSize : i * SampleSize + SampleSize] for i in range(SamplesCount)]
        iter = p_uimap(corr, Samples)
        Second = 0
        for C in iter:
            if Second:
                for i in range(len(C)):
                    Sum[i] += C[i]
            else:
                Sum = C
        AioShell.removeLastLine()
        for i in range(len(Sum)):
            Sum[i] /= SamplesCount
        Cmean = statistics.mean(Sum)
        Cstdev = statistics.stdev(Sum)
        Z = sqrt(len(Sum)) * Cmean / Cstdev
        return (Cmean, Cstdev, Z) 
        
        
    
    
class TuplesReport:
    
    __slots__ = ("_histo_dict", "_tmin", "_tmax", "_stats", "_pass")
    
    def __init__(self, Word : bitarray, FromTupleSize : int = 2, ToTupleSize : int = 8, Significance=0.05, NonCyclicSampleSize = None, SpeedUpByDecreasingAccuacy : int = 1):
        self._histo_dict = {}
        self._tmin = FromTupleSize
        self._tmax = ToTupleSize
        self._stats = {}
        self._pass = {}
        from scipy.stats import chisquare
        from scipy.stats import chi2
        if NonCyclicSampleSize is None:
            for TSize in tqdm(range(FromTupleSize, ToTupleSize+1), desc="Counting tuples"):
                H = Bitarray.getTuplesHistogram(Word, TSize)
                self._histo_dict[TSize] = H
                self._stats[TSize] = chisquare(H)
                Critical = chi2.isf(Significance, (1<<TSize)-1)
                self._pass[TSize] = True if self._stats[TSize].statistic <= Critical else False
        else:
            SamplesCount = len(Word) // NonCyclicSampleSize // SpeedUpByDecreasingAccuacy
            for TSize in tqdm(range(FromTupleSize, ToTupleSize+1), desc="Counting tuples"):
                H = [0 for i in range(1<<TSize)]
                Samples = [Word[i * NonCyclicSampleSize : i * NonCyclicSampleSize + NonCyclicSampleSize] for i in range(SamplesCount)]
                iter = p_uimap(partial(Bitarray.getTuplesHistogram, TupleSize=TSize, Cyclic=False), Samples)
                for SubH in iter:
                    for j in range(len(H)):
                        H[j] += SubH[j]
                if SpeedUpByDecreasingAccuacy > 1:
                    for j in range(len(H)):
                        H[j] *= SpeedUpByDecreasingAccuacy
                AioShell.removeLastLine()
                self._histo_dict[TSize] = H
                self._stats[TSize] = chisquare(H)
                Critical = chi2.isf(Significance, (1<<TSize)-1)
                self._pass[TSize] = True if self._stats[TSize].statistic <= Critical else False
        AioShell.removeLastLine()
            
    def getReport(self, FromTupleSize : int = None, ToTupleSize : int = None, Colored = False, HidePlot = False, HideNumbers = False) -> str:
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
            if not HideNumbers:
                Result += "HistogramValues = " + str(H)
            Result += "\n\n"
        return Result
            
    def getTableRow(self, FromTupleSize : int = None, ToTupleSize : int = None) -> list:
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
        # Min, Max, Chi2, Pass, PVal
        Result = []
        for TSize in range(FromTupleSize, ToTupleSize+1):
            H = self._histo_dict[TSize]
            HValues = H
            Min = min(HValues)
            Max = max(HValues)
            PDiv = self._stats[TSize]
            Pass = self._pass[TSize]
            Result += [Min, Max, PDiv.statistic, 'Y' if Pass else 'N', PDiv.pvalue]
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
    
    def printReport(self, FromTupleSize : int = None, ToTupleSize : int = None, Colored = True, HidePlot = False, HideNumbers = False) -> None:
        Aio.print(self.getReport(FromTupleSize, ToTupleSize, Colored, HidePlot, HideNumbers))
        
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


class SequenceUnion:
    
    __slots__ = ("_sequences", "_orig_len", "_long_seq", "_bitwise", "_function")
    
    def __len__(self) -> int:
        if self._long_seq is not None:
            return len(self._long_seq)
        if self._sequences is not None:
            return len(self._sequences[0])
        return 0
    
    def __init__(self, Sequences = [], MergingFunction = None, MergingFunctionIsBitwise : bool = False) -> None:
        self._long_seq = None
        self._sequences = None
        self._orig_len = None
        if len(Sequences) > 0:
            self.setSequences(Sequences)
        self.setFunction(MergingFunction, MergingFunctionIsBitwise)
    
    def setFunction(self, Function, isBitwise : bool = False):
        self._function = Function
        self._bitwise = isBitwise
        self._long_seq = None
    
    def setSequences(self, Sequences : list):
        Lengths = numpy.asarray([len(s) for s in Sequences], dtype="int64")
        SLen = int(numpy.lcm.reduce(Lengths))
        self._sequences = [Sequences[i] * (SLen // int(Lengths[i])) for i in range(len(Sequences))]
        self._long_seq = None
        self._orig_len = list(Lengths)
        
    def getInputSequence(self, Index : int, InputLength : bool = True) -> bitarray:
        if self._sequences is not None and len(self._sequences) > Index:
            if InputLength:
                return self._sequences[Index][:self._orig_len[Index]]
            return self._sequences[Index].copy()
        return None
    
    def getLengthOfInputSequence(self, Index : int) -> int:
        if self._sequences is not None and len(self._sequences) > Index:
            return self._orig_len[Index]
        return 0
        
    def getLongSequence(self) -> bitarray:
        if self._long_seq is not None:
            return self._long_seq.copy()
        if self._sequences is not None and self._function is not None:
            if self._bitwise:
                N = len(self._sequences)
                SLen = len(self._sequences[0])
                self._long_seq = bitarray(SLen)
                for i in range(SLen):
                    self._long_seq[i] = self._function([self._sequences[n][i] for n in range(N)])
            else:
                self._long_seq = self._function(self._sequences.copy())
            return self._long_seq.copy()
        return None
    
    
class RotationInsensitiveSignature:
    
    __slots__ = ('_hash', "_nhash", '_inv_ins', '_len', '_hb')
    
    def __init__(self, Sequence : bitarray, HBlockSize : int = 0, InversionInsensitive : bool = False) -> None:
        from math import log2, ceil
        self._inv_ins = InversionInsensitive
        if HBlockSize <= 0:
            HBlockSize = int(ceil(log2(len(Sequence))))
        if HBlockSize < 3:
            HBlockSize = 3
        self._hash = Bitarray.getRotationInsensitiveSignature(Sequence, HBlockSize)
        if InversionInsensitive:
            self._nhash = Bitarray.getRotationInsensitiveSignature(~Sequence, HBlockSize)
        self._len = len(Sequence)
        self._hb = HBlockSize
            
    def __eq__(self, __value: object) -> bool:
        if self._inv_ins:
            if __value._inv_ins:
                return (self._hash == __value._hash) or (self._nhash == __value._hash) or (self._hash == __value._nhash) or (self._nhash == __value._nhash)
            else:
                return (self._hash == __value._hash) or (self._nhash == __value._hash)
        else:
            if __value._inv_ins:
                return (self._hash == __value._hash) or (self._hash == __value._nhash)
            else:
                return (self._hash == __value._hash)
            
    def __ne__(self, __value: object) -> bool:
        return not (self == __value)
    
    def __hash__(self) -> int:
        if self._inv_ins:
            return self._hash * self._nhash
        return self._hash
    
    def __len__(self) -> int:
        return self._len
    
    def __repr__(self) -> str:
        return f"RotationInsensitiveSignature(BITARRAY({self._len}, {self._hb}, {self._inv_ins}))"
    
    def __str__(self) -> str:
        if self._inv_ins:
            return f"SIGN({self._hash}, {self._nhash})"
        else:
            return f"SIGN({self._hash})"
        
        
        
class BitarrayExtendedMatrix:
    pass
class BitarrayExtendedMatrix:
    
    __slots__ = ('_rows', '_cols', "_echelon_form", "_recursion_level", "_unambiguous")
    
    def __init__(self, Rows : list = None) -> None:
        self._rows = []
        self._cols = 0
        self._echelon_form = 0
        self._recursion_level = 0
        self._unambiguous = {}
        if Rows is not None:
            for r in Rows:
                self.addRow(r)
        
    def __len__(self) -> int:
        return len(self._rows)
    
    def __getitem__(self, Index : int) -> bitarray:
        return self._rows[Index]
    
    def __repr__(self) -> str:
        return f"BitarrayExtendedMatrix(ROWS={self._rows}, COLS={self._cols})"
                
    def __str__(self) -> str:
        Result = ""
        Second, i = 0, 0
        for Row in self._rows:
            if Second:
                Result += "\n"
            else:
                Second = 1
            Result += f"{i} \t: {str(Row)[10:-2]}"
            if self.isUnambiguous(i):
                Result += " U"
            i += 1
        return Result
        
    def addRow(self, Row : bitarray) -> None:
        if type(Row) in (list, tuple):
            for R in Row:
                self.addRow(R)
            return
        if type(Row) is not bitarray:
            try:
                Row = bitarray(Row)
            except:
                Aio.printError('Row must be a bitarray or at least be conversibl;e to bitarray.')
                return
        if self._cols == 0:
            self._cols = len(Row)
        if len(Row) == self._cols:
            self._rows.append(Row)
            self._echelon_form = 0
        else:
            Aio.printError(f"Row length ({len(Row)}) must be equal to the previous row length ({self._cols}).")
            
    def sortRows(self) -> None:
        self._unambiguous = {}
        import itertools, operator
        def sort_uniq(sequence):
            return map(
                operator.itemgetter(0),
                itertools.groupby(sorted(sequence, reverse=True)))
        self._rows = list(sort_uniq(self._rows))
        #self._rows.sort(reverse=True)
        
    def toEchelonForm(self, Debug = 0) -> None:
        self.sortRows()
        if Debug:
            print("toEchelonForm ---")
            print(f"Sorted:\n{self}")
        BaseRow = bau.zeros(self._cols)
        RowToSearchFirst = bau.ones(self._cols)
        BaseRow[0] = 1
        for ColI in range(self._cols-1):
            FirstRow = 0
            MaxRowI = -1
            for RowI in range(len(self._rows)):
                if self._rows[RowI] > RowToSearchFirst:
                    FirstRow = RowI + 1
            if Debug:
                print(f"FirstRow: {FirstRow}")
            for RowI in range(FirstRow, len(self._rows)):
                if self._rows[RowI] >= BaseRow:
                    if MaxRowI < 0:
                        MaxRowI = RowI
                        if Debug:
                            print("MaxRowI:", MaxRowI)
                    else:
                        if Debug:
                            print("To eliminate:",RowI)
                        self._rows[RowI] ^= self._rows[MaxRowI]
            self.sortRows()
            BaseRow >>= 1
            RowToSearchFirst >>= 1
            if Debug:
                print(f"After {ColI} iter:\n{self}")
        self._echelon_form = 1
    
    def hasNoSolution(self) -> bool:
        if not self._echelon_form:
            self.toEchelonForm()
        for i in range(len(self._rows)-1):
            if self._rows[i][:-1] == self._rows[i+1][:-1]:
                return True
            if self._rows[i+1][:-1].count(1) == 0:
                return True
        return False
    
    def solve(self, MaxFailCount : int = 10, Debug=0):
        if not self._echelon_form:
            self.toEchelonForm(Debug=0)
        if Debug:
            print(f"{' '*self._recursion_level}solve -----------")
        for RowI in range(len(self)-1):
            for RfixerI in range(RowI+1, len(self)):
                Aux = self._rows[RowI] ^ self._rows[RfixerI]
                if (Aux < self._rows[RowI]):
                    self._rows[RowI] = Aux
                    try:
                        del self._unambiguous[RowI]
                    except:
                        pass
        if Debug:
            print(f"{' '*self._recursion_level}Resultant:")
            print(self)
        if self.hasNoSolution():
            if Debug:
                print(f"{' '*self._recursion_level}HAS NO SOLUTION:")
            return None
        TheBestAmbiguous = None
        for i in range(len(self._rows)):
            if not self.isUnambiguous(i):
                if TheBestAmbiguous is None:
                    TheBestAmbiguous = self._rows[i]
                else:
                    if not TheBestAmbiguous[-1]:
                        if self._rows[i][-1]:
                            TheBestAmbiguous = self._rows[i]
                        elif TheBestAmbiguous[:-1].count(1) > self._rows[i][:-1].count(1):
                            TheBestAmbiguous = self._rows[i]
                    elif self._rows[i][-1]:  
                        if TheBestAmbiguous[:-1].count(1) > self._rows[i][:-1].count(1):
                            TheBestAmbiguous = self._rows[i]
        if TheBestAmbiguous is None:
            Result = bau.zeros(self._cols)
            oc = 0
            for i in range(len(self._rows)):
                if self._rows[i][-1]:
                    Result[i] = 1
                    oc += 1
                    if oc > MaxFailCount:
                        return None
            if Debug:
                print("FOUND!! ",Result)
            return [Result]
        else:
            if self.isUnambiguousOnesCountGreaterThan(MaxFailCount):
                return None
            if Debug:
                print(f"{' '*self._recursion_level}TheBestAmbiguous: {TheBestAmbiguous}")
            VarCandidates = TheBestAmbiguous[:-1].search(1)
            if Debug:
                print(f"{' '*self._recursion_level}VarCandidates: {VarCandidates}")
            Combinations = []
            if TheBestAmbiguous[-1]:
                Val = 1
                for i in range(1, len(VarCandidates)+1, 2):
                    Combinations += List.getCombinations(VarCandidates, i)
            else:
                Val = 0
                for i in range(2, len(VarCandidates)+1, 2):
                    Combinations += List.getCombinations(VarCandidates, i)
            if Debug:
                print(f"{' '*self._recursion_level}- Eq value is {Val}  New trees: {Combinations}")
            Result = []
            for Comb in Combinations:
                R = self._deepSearch(Comb, 1, MaxFailCount, Debug=Debug)
                if R is not None:
                    for RI in R:
                        if RI not in Result:
                            Result.append(RI)
                if not Val:
                    R = self._deepSearch(Comb, 0, MaxFailCount, Debug=Debug)
                    if R is not None:
                        for RI in R:
                            if RI not in Result:
                                Result.append(RI)
            return Result
                    
                    
    def _deepSearch(self, EqVars : list, EqVal : int, MaxFailCount : int = 10, Debug = 0):
        if self._recursion_level > 10:
            Aio.printError(f"{' '*self._recursion_level}Deep search is too deep.")
            return None
        if Debug:
            print(f"{' '*self._recursion_level}_recursion_level={self._recursion_level}")
        M = self.copy()
        M._recursion_level = self._recursion_level + 1
        for c in EqVars:
            Eq = bau.zeros(self._cols)
            Eq[c] = 1
            if EqVal:
                Eq[-1] = 1
            M.addRow(Eq)
            if Debug:
                print(f"{' '*self._recursion_level}Deep search Eq: {Eq} --------")
        return M.solve(MaxFailCount, Debug=Debug)
            
    def isUnambiguous(self, RowIndex : int = None) -> bool:
        if RowIndex is None:
            Result = True
            for i in range(len(self._rows)):
                if not self.isUnambiguous(i):
                    Result = False
                    break
            return Result
        else:
            Cached = self._unambiguous.get(RowIndex, None)
            if Cached is not None:
                return Cached
            if RowIndex >= len(self._rows):
                return False
            Result = self._rows[RowIndex][:-1].count(1) == 1
            self._unambiguous[RowIndex] = Result
            return Result
        
    def isUnambiguousOnesCountGreaterThan(self, HowMuch : int) -> bool:
        C = 0
        for i in range(len(self._rows)):
            if self.isUnambiguous(i):
                if self._rows[i][-1]:
                    C += 1
                    if C > HowMuch:
                        return True
        return False
        
    def copy(self) -> BitarrayExtendedMatrix:
        Result = BitarrayExtendedMatrix()
        Result._rows = self._rows.copy()
        Result._cols = self._cols
        Result._echelon_form = self._echelon_form
        Result._unambiguous = self._unambiguous.copy()
        return Result