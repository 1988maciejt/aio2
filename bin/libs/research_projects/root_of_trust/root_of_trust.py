from libs.pandas_table import *
from libs.aio import *
from libs.files import *
from libs.lfsr import *
from libs.programmable_lfsr import *
from libs.bent_function import *
from libs.verilog import *
from libs.verilog_creator import *
from libs.phaseshifter import *
from libs.preprocessor import *
from bitarray import *
import sympy.logic.boolalg as SympyBoolalg
from tqdm import tqdm 
from libs.fast_anf_algebra import *
from time import sleep, time
from libs.simple_threading import *

########################################################################################
#                          NEPTUN RG
########################################################################################
def createNeptunLfsr(Size : int, UseDemuxes = False) -> ProgrammableLfsr:
    Step = 3
    Sources = []
    Taps = []
    One = Size & 1
    for S in range(Size-1, (Size>>1)-1+One, -Step):
        Sources.append(S)
    for S in range(Step-1, (Size>>1), Step):
        Sources.append(S)
    for S in Sources:
        D3 = Size - S
        D1 = ((D3 - 2) + Size) % Size 
        D2 = ((D3 - 1) + Size) % Size
        if UseDemuxes:
            TapSet = {f'{S}_Off':None}
            TapSet[f'{S}-{D1}'] = [S,D1]
            if D3 != S:
                TapSet[f'{S}-{D2}'] = [S,D2]
            if D3 != S:
                TapSet[f'{S}-{D3}'] = [S,D3]
            if len(list(TapSet.keys())) > 1:
                Taps.append(TapSet)
        else:
            Taps.append({f'{S}-{D1}_off': None, f'{S}-{D1}_on': [S,D1]})
            if D3 != S:
                Taps.append({f'{S}-{D2}_off': None, f'{S}-{D2}_on': [S,D2]})
            if D3 != S:
                Taps.append({f'{S}-{D3}_off': None, f'{S}-{D3}_on': [S,D3]})
    return ProgrammableLfsr(Size, Taps, 1)


########################################################################################
#                          HASH FUNCTION
########################################################################################

_VarsToExpr = {}
_ExprToVars = {}
_CanWrite = 1
_ExprVarsSize = 0


def _bf_evaluate(BFComb):
    return BFComb[0].getFastANFValue(BFComb[1], BFComb[2], 1)

def _to_anf(Expr):
    try:
        return Expr.to_anf()
    except:
        return False
    
def _expr_expand(Expr):
    global _VarsToExpr
    try:
        Expr = Expr.subs(_VarsToExpr)
    except:
        pass
    return Expr

def _expr_collapse(Expr):
    global _ExprToVars, _VarsToExpr
    try:
        Aux = Expr.subs(_VarsToExpr)
        return Aux.subs(_ExprToVars)
    except:
        return Expr

class HashFunction:
    
    __slots__ = ("Size", "Cycles", "LfsrIn", "LfsrOut", "Functions", "DirectConnections", "LfsrInPhaseShifter")
    
    def __init__(self, FileName = None) -> None:
        self.Size = 0
        self.Cycles = 0
        self.LfsrIn = None
        self.LfsrOut = None
        self.LfsrInPhaseShifter = None
        self.Functions = []
        self.DirectConnections = []
        if FileName is not None:
            self.fromFile(FileName)

    def addDirectConnection(self, SourceInLfsrIn : int, DestinationInLfsrOut : int):
        s, i = Int.splitLettersAndInt(SourceInLfsrIn)
        if 'p' in s.lower():
            i += 1000000
        elif 'o' in s.lower():
            i += 100000
        SourceInLfsrIn = i
        s, i = Int.splitLettersAndInt(DestinationInLfsrOut)
        if 'i' in s.lower():
            i += 100000
        DestinationInLfsrOut = i
        self.DirectConnections.append([SourceInLfsrIn, DestinationInLfsrOut])

    def setLfsrIn(self, LfsrObject : Lfsr):
        self.LfsrIn = LfsrObject
        
    def setLfsrInPhaseShifter(self, LfsrInPhaseShifter : PhaseShifter):
        self.LfsrInPhaseShifter = LfsrInPhaseShifter

    def setLfsrOut(self, LfsrObject : Lfsr):
        self.LfsrOut = LfsrObject
        self.Size = LfsrObject.getSize()
        
    def addBentFunction(self, Function : BentFunction, LfsrInInputs : list, LfsrOutInjectors : list):
        Inputs = []
        for Input in LfsrInInputs:        
            s, i = Int.splitLettersAndInt(Input)
            if 'o' in s.lower():
                i += 100000
            Inputs.append(i)
        Outputs = []
        for Output in LfsrOutInjectors:        
            s, i = Int.splitLettersAndInt(Output)
            Outputs.append(i)
        self.Functions.append([Function, Inputs, Outputs])
        
    def setCycles(self, Cycles : int):
        self.Cycles = Cycles
        
    def clearBentFunctions(self):
        self.Functions.clear()
        
    def fromFile(self, FileName : str):
        Data = readFile(FileName)
        R = re.search(r'Poly\s*size:\s*([0-9]+),\s*cycles:\s*([0-9]+)', Data, re.MULTILINE)
        self.Size = int(R.group(1))
        self.Cycles = int(R.group(2))
        R = re.search(r'RING\s*IN:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrIn = Lfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))), HYBRID_RING)
        R = re.search(r'RING\s*OUT:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrOut = Lfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))), HYBRID_RING)
        self.Functions = []
        for R in re.finditer(r'Function:\s*([0-9]+)\s+Inputs:\s+([ 0-9]+)\s+Outputs:\s+([ 0-9^]+)', Data, re.MULTILINE):
            Inputs = list(ast.literal_eval(R.group(2).replace(" ", ",")))
            Outputs = list(ast.literal_eval(R.group(3).replace(" ", ",")))
            LUT = bau.int2ba(int(R.group(1)), 1<<len(Inputs), "little")  
            Function = BentFunction(LUT)
            self.Functions.append([Function, Inputs, Outputs])
        
    def toVerilogObject(self) -> Verilog:
        Ver = Verilog(self.toVerilog())
        return Ver
        
    def toVerilog(self) -> str:
        LfsrOutInjectorList = []
        for bf in self.Functions:
            LfsrOutInjectorList += bf[2]
        Content = self.LfsrIn.toVerilog("lfsr_in", [0])
        Content += "\n\n" + self.LfsrOut.toVerilog("lfsr_out", LfsrOutInjectorList)
        for i in range(len(self.Functions)):
            Bent = self.Functions[i][0]
            Content += "\n\n" + Bent.toVerilog(f"bent_{i}")
        Content += "\n\n" + preprocessString(readFile(Aio.getPath() + "libs/research_projects/root_of_trust/hash_top.v"),
                                             bent_functions=self.Functions,
                                             lfsr_out_injectors_list=LfsrOutInjectorList,
                                             lfsr_in_size=self.LfsrIn.getSize(),
                                             lfsr_out_size=self.LfsrOut.getSize(),)
        return Content
    
    def simReset(self):
        self.LfsrIn.reset()
        self.LfsrOut.reset()
        
    def simStep(self):
        FValues = []
        for F in self.Functions:
            BF = F[0]
            Inputs = F[1]
            Outputs = F[2]
            FValues.append([Outputs, BF.value(self.LfsrIn.getValue(), Inputs)])
        self.LfsrIn.next()
        self.LfsrOut.next()
        for FVal in FValues:
            Outputs = FVal[0]
            Value = FVal[1]
            OLValue = self.LfsrOut.getValue()
            for O in Outputs:
                OLValue[O] ^= Value
            self.LfsrOut.setValue(OLValue)
            
    def sim(self, Steps : int, LfsrInSeed : bitarray, LfsrOutSeed : bitarray, Print = False):
        if Print:
            PT = PandasTable(["LfsrIn", "LfsrOut"], AutoId=1)
        self.simReset()
        self.LfsrIn.setValue(LfsrInSeed)
        self.LfsrOut.setValue(LfsrOutSeed)
        for i in range(Steps):
            self.simStep()
            if Print:
                IString = ""
                for S in reversed(str(self.LfsrIn)):
                    IString += S
                OString = ""
                for S in reversed(str(self.LfsrOut)):
                    OString += S
                PT.add([IString, OString])
        if Print:
            PT.print()       
        
    def symbolicSimulation(self, MessageLength : int, MsgInjectors : 0, PrintExpressionsEveryCycle = 0, KeyAsSeed = 0) -> list:
        global _VarsToExpr, _ExprToVars, _ExprVarsSize
        if KeyAsSeed:
            LfsrInValues = [symbols(f"K{i}") for i in range(self.LfsrIn.getSize())]
        else:
            LfsrInValues = [False for _ in range(self.LfsrIn.getSize())]
        LfsrOutValues = [False for _ in range(self.LfsrOut.getSize())] 
        MsgBit = 0
        _VarsToExpr = {}
        _ExprToVars = {}
        _ExprVarsSize = 0
        MsgVariables = [symbols(f'M{i}') for i in range(MessageLength)]
        AllVariables = MsgVariables
        if KeyAsSeed:
            AllVariables + LfsrInValues
        VIndex = 0
        Avg = len(AllVariables)>>1
        kValues = [i  for i in range(Avg-0, Avg+0 + 1, 1) if i > 0]
        for k in kValues:
            for C in List.getCombinations(AllVariables, k):
                Expr = True
                for Cx in C:
                    Expr &= Cx
                GVar = symbols(f"G{VIndex}")
                VIndex += 1
                _VarsToExpr[GVar] = Expr
                _ExprToVars[Expr] = GVar
        for Iter in tqdm(range(self.Cycles), desc="SIMULATION"):
            if MsgBit < MessageLength:
                LfsrInValues = self.LfsrIn.simulateSymbolically([symbols(f'M{MsgBit}')], MsgInjectors, LfsrInValues)
                MsgBit += 1
            else:
                LfsrInValues = self.LfsrIn.simulateSymbolically([False], MsgInjectors, LfsrInValues)
            if self.LfsrInPhaseShifter is not None:
                LfsrInPhaseShifterValues = self.LfsrInPhaseShifter.symbolicValues(LfsrInValues)
            BFValues = []
            BFOutputs = []
            for bfun in self.Functions:
                Inputs = []
                for Iindex in bfun[1]:
                    if Iindex >= 100000:
                        Inputs.append(LfsrOutValues[Iindex - 100000])
                    else:
                        Inputs.append(LfsrInValues[Iindex])
                BFValues.append(bfun[0].getSymbolicValue(Inputs))
                BFOutputs.append(bfun[2])
            BFs = []
            for i in range(len(BFValues)):
                BFs.append([BFValues[i], BFOutputs[i]])
            LfsrOutValues = self.LfsrOut.simulateSymbolically([False], 0, LfsrOutValues)
            AllOutputs = []
            for bf in BFs:
                Outputs = bf[1]
                AllOutputs += Outputs
                for O in Outputs:
                    LfsrOutValues[O] = LfsrOutValues[O] ^ bf[0]
            for SD in self.DirectConnections:
                if SD[0] >= 1000000:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrInPhaseShifterValues[SD[0]-1000000]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrInPhaseShifterValues[SD[0]-1000000]
                elif SD[0] >= 100000:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrOutValues[SD[0]-100000]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrOutValues[SD[0]-100000]
                else:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrInValues[SD[0]]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrInValues[SD[0]]
            LfsrOutValues = p_map(_to_anf, LfsrOutValues, desc="To ANF")
            #AllOutputs = [i for i in range(len(LfsrInValues))]
            ColList = []
            for i in AllOutputs:
                ColList.append(LfsrOutValues[i])
            i = -1
            for Collapsed in p_imap(_expr_collapse, ColList, desc="Collapsing expr"):
                i += 1
                LfsrOutValues[AllOutputs[i]] = Collapsed
            if PrintExpressionsEveryCycle:
                Aio.print(f"CYCLE {Iter}:")
                for i in range(len(LfsrOutValues)):
                    Val = LfsrOutValues[i]
                    Aio.print(f"FF{i} \t= {Val}")
                Aio.print()
        #ResultValues = p_map(SympyBoolalg.to_anf, LfsrOutValues, desc="To ANF")
        Result = {'MonomialDegree':{}, 'Expression':{}, 'Histogram': {}}
        i = -1
        for Vaux in p_imap(_expr_expand, LfsrOutValues, desc="Postprocessing"):
            i += 1
            try:
                Vaux = Vaux.subs(_VarsToExpr)
            except:
                pass
            try:
                Vaux = Vaux.to_anf()
            except:
                pass
            #print(f"{i}  =  {Vaux}\n")
            Histogram = {}
            Highest = 0
            V = False
            try:
                if Vaux.func == Not:
                    V = Vaux.args[0]
                    Histogram[0] = 1
                    Highest = 1
                else:
                    V = Vaux
            except:
                pass
            try:
                for A in V.args:
                    try:
                        deg = len(A.atoms())
                        if deg > Highest: Highest = deg
                        HV = Histogram.get(deg, 0)
                        Histogram[deg] = HV + 1
                    except:
                        HV = Histogram.get(0, 0)
                        Histogram[0] = HV + 1
            except:
                pass
            Result['MonomialDegree'][i] = Highest
            Result['Histogram'][i] = Histogram
            Result['Expression'][i] = V
        _VarsToExpr = {}
        _ExprToVars = {}
        return Result
            
    def FastANFSimulation(self, MessageLength : int, MsgInjectors : 0, PrintExpressionsEveryCycle = 0, KeyAsSeed = 0, DumpStatsEveryNCycles = 0, DumpFileName = "HASH", PrintDumpedStats = 1, ReturnMonomialCountPerCycle = 0) -> list:
        AllVariables = [f'M{i}' for i in range(MessageLength)]
        if KeyAsSeed:
            AllVariables += [f"K{i}" for i in range(self.LfsrIn.getSize())]
        ANFSpace = FastANFSpace(AllVariables)
        if KeyAsSeed:
            LfsrInValues = [ANFSpace.createExpression(InitValue=f"K{i}") for i in range(self.LfsrIn.getSize())]
        else:
            LfsrInValues = [ANFSpace.createExpression() for _ in range(self.LfsrIn.getSize())]
        LfsrOutValues = [ANFSpace.createExpression() for _ in range(self.LfsrOut.getSize())] 
        if ReturnMonomialCountPerCycle:
            MonomialCountList = []
        MsgBit = 0
        if KeyAsSeed:
            AllVariables + LfsrInValues
        for Iter in range(self.Cycles):
            print(f"// RoT sim - ITERATION {Iter+1} / {self.Cycles} --------------------------")
            if MsgBit < MessageLength:
                LfsrInValues = self.LfsrIn.simulateFastANF(ANFSpace, [f'M{MsgBit}'], MsgInjectors, LfsrInValues)
                MsgBit += 1
            else:
                LfsrInValues = self.LfsrIn.simulateFastANF(ANFSpace, [None], MsgInjectors, LfsrInValues)
            if self.LfsrInPhaseShifter is not None:
                LfsrInPhaseShifterValues = self.LfsrInPhaseShifter.fastANFValues(ANFSpace, LfsrInValues)
            BFValues = []
            BFOutputs = []
            BFCombos = []
            for bfun_i in range(len(self.Functions)):
                bfun = self.Functions[bfun_i]
                Inputs = []
                for Iindex in bfun[1]:
                    if Iindex >= 100000:
                        Inputs.append(LfsrOutValues[Iindex - 100000])
                    else:
                        Inputs.append(LfsrInValues[Iindex])
                #print(f"// RoT BentFunction {bfun_i+1} / {len(self.Functions)}")
                BFCombos.append([bfun[0], ANFSpace, Inputs])
                #BFValues.append(bfun[0].getFastANFValue(ANFSpace, Inputs, Parallel=1))
                BFOutputs.append(bfun[2])
            BVDone = 1
            for BV in SimpleThread.imap(_bf_evaluate, BFCombos):
                BFValues.append(BV)
                print(f"// RoT sim - BentFunction {BVDone} / {len(self.Functions)}") 
                BVDone += 1
            BFs = []
            for i in range(len(BFValues)):
                BFs.append([BFValues[i], BFOutputs[i]])
            LfsrOutValues = self.LfsrOut.simulateFastANF(ANFSpace, [ANFSpace.createExpression()], 0, LfsrOutValues)
            for bf in BFs:
                Outputs = bf[1]
                for O in Outputs:
                    LfsrOutValues[O] = LfsrOutValues[O] ^ bf[0]
            for SD in self.DirectConnections:
                if SD[0] >= 1000000:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrInPhaseShifterValues[SD[0]-1000000]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrInPhaseShifterValues[SD[0]-1000000]
                elif SD[0] >= 100000:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrOutValues[SD[0]-100000]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrOutValues[SD[0]-100000]
                else:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrInValues[SD[0]]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrInValues[SD[0]]
            if PrintExpressionsEveryCycle:
                Aio.print(f"CYCLE {Iter}:")
                for i in range(len(LfsrOutValues)):
                    Val = LfsrOutValues[i]
                    Aio.print(f"FF{i} \t= {Val}")
                Aio.print()
            if DumpStatsEveryNCycles > 0:
                self.reportMonomials(f'{DumpFileName}_Cycle{Iter+1}', LfsrOutValues, len(AllVariables), KeyAsSeed, PrintDumpedStats, PrintDumpedStats)
                if PrintDumpedStats:
                    Aio.transcriptToHTML()
            if ReturnMonomialCountPerCycle:
                Sum = 0
                for V in LfsrOutValues:
                    Sum += V.getMonomialCount()
                MonomialCountList.append(Sum)
        if ReturnMonomialCountPerCycle:
            return MonomialCountList
        return LfsrOutValues
                    
    def reportMonomials(self, FileName : str, LfsrOutValues : list, AllVariablesLength : int, KeyAsSeed = False, PrintTables = 0, PrintExpressions = 0):
        Result = {'Expression':{}, 'Histogram': {}, 'GlobalMonomialCount': {}, 'MonomialCount': 0}
        if KeyAsSeed:
            Result['KeyHistogram'] = {}
        Sum = 0
        for i in tqdm(range(len(LfsrOutValues)), desc="Postprocessing"):
            Vaux = LfsrOutValues[i]
            #print(f"{i}  =  {Vaux}\n")
            HistogramList = Vaux.getMonomialsHistogram()
            Sumi = Vaux.getMonomialCount()
            Sum += Sumi
            if KeyAsSeed:
                KeyHistogramList = Vaux.getMonomialsHistogram((1 << self.LfsrIn.getSize()))
            Histogram = {}
            for j in range(len(HistogramList)):
                HV = HistogramList[j]
                Histogram[j] = HV
            if KeyAsSeed:
                KeyHistogram = {}
                for j in range(len(HistogramList)):
                    HV = KeyHistogramList[j]
                    KeyHistogram[j] = HV
            Result['Histogram'][i] = Histogram
            if KeyAsSeed:
                Result['KeyHistogram'][i] = KeyHistogram
            Result['Expression'][i] = str(Vaux)
            Result['MonomialCount'][i] = Sumi
        Result['GlobalMonomialCount'][i] = Sum
        if PrintTables or PrintExpressions:
            Aio.printSection(FileName)
        PT = PandasTable(["#FF"] + [f"Deg{i}" for i in range(AllVariablesLength+1)])
        Histograms = Result['Histogram']
        for key in Histograms:
            Histogram = Histograms[key]
            Values = [key]
            for i in range(AllVariablesLength+1):
                Values.append(Histogram.get(i, 0))
            PT.add(Values)
        if PrintTables:
            Aio.printSubsection(f'full monomials degrees')
            PT.print()
        PT.toXls(f"{FileName}__full_monomials.xlsx")
        if KeyAsSeed:
            PT = PandasTable(["#FF"] + [f"Deg{i}" for i in range(AllVariablesLength+1)])
            Histograms = Result['KeyHistogram']
            for key in Histograms:
                Histogram = Histograms[key]
                Values = [key]
                for i in range(AllVariablesLength+1):
                    Values.append(Histogram.get(i, 0))
                PT.add(Values)
            if PrintTables:
                Aio.printSubsection(f'monomials with key degrees')
                PT.print()
            PT.toXls(f"{FileName}__monomials_with_key_degrees.xlsx")
        Expressions = Result['Expression']
        ExprStr = ""
        Second = 0
        for i in range(len(Expressions)):
            if Second:
                ExprStr += "\n\n"
            else:
                Second = 1
            E = Expressions[i]
            ExprStr += f"FF{i} = {str(E)}"
        if PrintExpressions:
            Aio.printSubsection(f'Expressions')
            Aio.print(ExprStr)
        writeFile(f"{FileName}__expressions.txt", ExprStr)
        writeObjectToFile(f"{FileName}__LfsrOutValues_raw.bin", LfsrOutValues)
        
    
    
            
            
class ProgrammableHashFunction(HashFunction):
    
    __slots__ = ("Size", "Cycles", "LfsrIn", "LfsrOut", "Functions")
    
    def __init__(self, FileName = None) -> None:
        self.Size = 0
        self.Cycles = 0
        self.LfsrIn = None
        self.LfsrOut = None
        self.Functions = []
        if FileName is not None:
            self.fromFile(FileName)
        
    def fromFile(self, FileName : str):
        Data = readFile(FileName)
        R = re.search(r'Poly\s*size:\s*([0-9]+),\s*cycles:\s*([0-9]+)', Data, re.MULTILINE)
        self.Size = int(R.group(1))
        self.Cycles = int(R.group(2))
        R = re.search(r'RING\s*IN:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrIn = createNeptunLfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))).getDegree())  
        R = re.search(r'RING\s*OUT:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrOut = createNeptunLfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))).getDegree())  
        self.Functions = []
        for R in re.finditer(r'Function:\s*([0-9]+)\s+Inputs:\s+([ 0-9]+)\s+Outputs:\s+([ 0-9^]+)', Data, re.MULTILINE):
            Inputs = list(ast.literal_eval(R.group(2).replace(" ", ",")))
            Outputs = list(ast.literal_eval(R.group(3).replace(" ", ",")))
            LUT = bau.int2ba(int(R.group(1)), 1<<len(Inputs), "little")  
            Function = BentFunction(LUT)
            self.Functions.append([Function, Inputs, Outputs])
        
    def setLfsrIn(self, Size : int, UseDemuxes = False):
        self.LfsrIn = createNeptunLfsr(Size, UseDemuxes)

    def setLfsrOut(self, Size : int, UseDemuxes = False):
        self.LfsrOut = createNeptunLfsr(Size, UseDemuxes)
        self.Size = Size
    
    def addBentFunction(self, Function : BentFunction, LfsrInInputs : list, LfsrOutInjectors : list):
        self.Functions.append([Function, LfsrInInputs, LfsrOutInjectors])
        
    def toVerilog(self) -> str:
        LfsrOutInjectorList = []
        for bf in self.Functions:
            LfsrOutInjectorList += bf[2]
        Content = self.LfsrIn.toVerilog("lfsr_in", [0])
        Content += "\n\n" + self.LfsrOut.toVerilog("lfsr_out", LfsrOutInjectorList)
        for i in range(len(self.Functions)):
            Bent = self.Functions[i][0]
            Content += "\n\n" + Bent.toVerilog(f"bent_{i}")
        Content += "\n\n" + VerilogCreator.createShiftRegister("lfsr_in_config_reg", self.LfsrIn.getConfigVectorLength())
        Content += "\n\n" + VerilogCreator.createShiftRegister("lfsr_out_config_reg", self.LfsrOut.getConfigVectorLength())
        Content += "\n\n" + VerilogCreator.createShiftRegister("johnsons_counter", 2)
        Content += "\n\n" + preprocessString(readFile(Aio.getPath() + "libs/research_projects/root_of_trust/programmable_hash_top.v"),
                                             bent_functions=self.Functions,
                                             lfsr_out_injectors_list=LfsrOutInjectorList,
                                             lfsr_in_size=self.LfsrIn.getSize(),
                                             lfsr_out_size=self.LfsrOut.getSize(),
                                             lfsr_in_config_size=self.LfsrIn.getConfigVectorLength(),
                                             lfsr_out_config_size=self.LfsrOut.getConfigVectorLength(),)
        return Content