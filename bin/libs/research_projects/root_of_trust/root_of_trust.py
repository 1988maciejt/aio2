from libs.pandas_table import *
from libs.aio import *
from libs.files import *
from libs.lfsr import *
from libs.nlfsr import *
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
from libs.remote_aio import RemoteAioScheduler

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
    
    __slots__ = ("Size", "Cycles", "LfsrIn", "LfsrOut", "Functions", "DirectConnections", "LfsrInPhaseShifter", "MessageLength", "MessageInjectors")
    
    def __init__(self, FileName = None) -> None:
        self.Size = 0
        self.Cycles = 0
        self.MessageLength = 0
        self.LfsrIn = None
        self.LfsrOut = None
        self.MessageInjectors = []
        self.LfsrInPhaseShifter = None
        self.Functions = []
        self.DirectConnections = []
        if FileName is not None:
            self.fromFile(FileName)

    def getBentFunctionsHexString(self) -> str:
        Second = 0
        Result = ""
        for F in self.Functions:
            BF = F[0]
            if Second:
                Result += ", "
            else:
                Second = 1
            Result += BF.toHexString()
        return Result
    
    def getLfsrInHexString(self) -> str:
        return Polynomial(self.LfsrIn._my_poly).toHexString()

    def addDirectConnection(self, SourceInLfsrIn : int, DestinationInLfsrOut : int):
        s, i = Int.splitLettersAndInt(SourceInLfsrIn)
        if 'p' in s.lower():
            i += 100000000
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
        self.Size = 32
        self.Cycles = 32
        Data = readFile(FileName)
        R = re.search(r'INJECTORS\s*:\s*([i 0-9]+[0-9])', Data, re.MULTILINE)
        if R:
            self.MessageInjectors = []
            aux = R.group(1).split(" ")
            for inj in aux:
                s, i = Int.splitLettersAndInt(inj)
                self.MessageInjectors.append(i)
        R = re.search(r'message\s+length\s*:\s*([0-9]+)', Data, re.MULTILINE)
        if R:
            self.MessageLength = int(R.group(1)) 
        R = re.search(r'Poly\s*size:\s*([0-9]+),\s*cycles:\s*([0-9]+)', Data, re.MULTILINE)
        if R:
            self.Size = int(R.group(1))
            self.Cycles = int(R.group(2))
        R = re.search(r'RING\s*IN:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrIn = Lfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))), HYBRID_RING)
        R = re.search(r'RING\s*OUT:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        if R:
            self.LfsrOut = Lfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))), HYBRID_RING)
        else:
            R = re.search(r'RING\s*OUT\s*SIZE:\s*([0-9]+)\s*\n', Data, re.MULTILINE)
            LfsrOutSize = int(R.group(1))
            self.LfsrOut = Lfsr([LfsrOutSize, 0], HYBRID_RING)
        self.Functions = []
        for R in re.finditer(r'Function:\s*([0-9]+)\s+Inputs:\s+([ 0-9]+)\s+Outputs:\s+([ 0-9^]+)', Data, re.MULTILINE):
            Inputs = list(ast.literal_eval(R.group(2).replace(" ", ",")))
            Outputs = list(ast.literal_eval(R.group(3).replace(" ", ",")))
            LUT = bau.int2ba(int(R.group(1)), 1<<len(Inputs), "little")  
            Function = BentFunction(LUT)
            self.Functions.append([Function, Inputs, Outputs])
        for R in re.finditer(r'Inputs:\s*([ iop0-9]+)\s+Output.*:\s*([ io0-9]+)\s+Function:\s*([0-9]+)', Data, re.MULTILINE):
            Inputs_ = R.group(1).split(" ")
            Outputs_ = R.group(2).split(" ")
            Inputs = []
            Outputs = []
            for Input in Inputs_:
                s, i = Int.splitLettersAndInt(Input, DefaultInt=-1)
                if i < 0: 
                    continue
                if s == "o":
                    Inputs.append(i + 100000)
                else:
                    Inputs.append(i)
            for Output in Outputs_:
                s, i = Int.splitLettersAndInt(Output, DefaultInt=-1)
                if i < 0: 
                    continue
                Outputs.append(i)
            LUT = bau.int2ba(int(R.group(3)), 1<<len(Inputs), "little") 
            Function = BentFunction(LUT)
            self.Functions.append([Function, Inputs, Outputs])
        R = re.search(r'Phase\s*shifter:\s+([ \n:OInputsiop0-9]+)', Data, re.MULTILINE)
        if R:
            Gates = []
            Outputs = []
            for R in re.finditer(r'Inputs:\s*([ i[0-9]+)\s+Output:\s*([o0-9]+)', R.group(1), re.MULTILINE):
                Inputs_ = R.group(1).split(" ")
                Output_ = R.group(2).split(" ")
                Inputs = []
                for Input in Inputs_:
                    s, i = Int.splitLettersAndInt(Input, DefaultInt=-1)
                    if i < 0: 
                        continue
                    Inputs.append(i)
                s, i = Int.splitLettersAndInt(Output_)
                Outputs.append(i)
                Gates.append(Inputs)
            self.setLfsrInPhaseShifter(PhaseShifter(self.LfsrIn, Gates))
            for i in range(len(Outputs)):
                self.addDirectConnection(i+100000000, Outputs[i])
        
    def toVerilogObject(self) -> Verilog:
        Ver = Verilog(self.toVerilog())
        return Ver
        
    def toVerilog(self) -> str:
        Content = self.LfsrIn.toVerilog("lfsr_in", [0])
        Content += "\n\n" + self.LfsrOut.toVerilog("lfsr_out", [i for i in range(self.LfsrOut.getSize())])
        if self.LfsrInPhaseShifter is not None:
            Content += "\n\n" + self.LfsrInPhaseShifter.toVerilog("phase_shifter")
        for i in range(len(self.Functions)):
            Bent = self.Functions[i][0]
            Content += "\n\n" + Bent.toVerilog(f"bent_{i}")
        PS = None
        if self.LfsrInPhaseShifter is not None:
            PS = self.LfsrInPhaseShifter._xors
        Content += "\n\n" + preprocessString(readFile(Aio.getPath() + "libs/research_projects/root_of_trust/hash_top.v"),
                                             bent_functions=self.Functions,
                                             lfsr_in_size=self.LfsrIn.getSize(),
                                             lfsr_out_size=self.LfsrOut.getSize(),
                                             phase_shifter=PS,
                                             direct_connections=self.DirectConnections)
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
            InputWord = bitarray(len(Inputs))
            for i in range(len(Inputs)):
                Input = Inputs[i]
                if Input >= 100000:
                    InputWord[i] = self.LfsrOut.getValue()[Input-100000]
                else:
                    InputWord[i] = self.LfsrIn.getValue()[Input]
            FValues.append([Outputs, BF.value(InputWord, [i for i in range(len(Inputs))])])
        Direct = []
        if self.LfsrInPhaseShifter is not None:
            self.LfsrInPhaseShifter.update()
        for DC in self.DirectConnections:
            Src = DC[0]
            if Src >= 100000000:
                Direct.append([self.LfsrInPhaseShifter.getValue()[Src-100000000], DC[1]])
            elif Src >= 100000:
                Direct.append([self.LfsrOut.getValue()[Src-100000], DC[1]])
            else:
                Direct.append([self.LfsrIn.getValue()[Src-100000], DC[1]])
        self.LfsrIn.next()
        self.LfsrOut.next()
        for FVal in FValues:
            Outputs = FVal[0]
            Value = FVal[1]
            OLValue = self.LfsrOut.getValue()
            for O in Outputs:
                OLValue[O] ^= Value
            self.LfsrOut.setValue(OLValue)
        for DC in Direct:
            Val = DC[0]
            Dest = DC[1]
            if Dest >= 100000:
                OLValue = self.LfsrIn.getValue()
                OLValue[Dest-100000] ^= Val
                self.LfsrIn.setValue(OLValue)
            else:
                OLValue = self.LfsrOut.getValue()
                OLValue[Dest] ^= Val
                self.LfsrOut.setValue(OLValue)
                
    def sim(self, Steps : int, LfsrInSeed : bitarray = None, LfsrOutSeed : bitarray = None, Message : bitarray = None, Print = False):
        AddMessage = (Message is not None) and (len(self.MessageInjectors) > 0)
        if Print:
            PT = PandasTable(["LfsrIn", "LfsrOut"], AutoId=1)
        self.simReset()
        if LfsrOutSeed is None:
            Val = self.LfsrIn.getValue()
            Val.setall(0)
            self.LfsrIn.setValue(Val)
        else:
            self.LfsrIn.setValue(LfsrInSeed)
        if LfsrOutSeed is None:
            Val = self.LfsrOut.getValue()
            Val.setall(0)
            self.LfsrOut.setValue(Val)
        else:
            self.LfsrOut.setValue(LfsrOutSeed)
        MBit = 0
        for i in range(Steps):
            self.simStep()
            if AddMessage:
                IVal = self.LfsrIn.getValue()
                for B in self.MessageInjectors:
                    IVal[B] ^= Message[MBit]
                self.LfsrIn.setValue(IVal)
                MBit += 1
                if MBit >= len(Message):
                    AddMessage = False
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
        return self.LfsrOut.getValue()
        
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
                if SD[0] >= 100000000:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrInPhaseShifterValues[SD[0]-100000000]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrInPhaseShifterValues[SD[0]-100000000]
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
            
    def FastANFSimulation(self, MessageLength : int, MsgInjectors : 0, PrintExpressionsEveryCycle = 0, KeyAsSeed = 0, DumpStatsEveryNCycles = 0, DumpFileName = "HASH", PrintDumpedStats = 1, ReturnMonomialCountPerCycle = 0, MonomialsCountPerFlop = None, InitialCycles = 0, TaskScheduler : RemoteAioScheduler = None) -> list:
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
            MonomialCountList = {}
        MsgBit = 0
        if KeyAsSeed:
            AllVariables + LfsrInValues
        for InitialIter in range(InitialCycles):
            print(f"// RoT sim - INITIAL ITERATION {InitialIter+1} / {InitialCycles} --------------------------")
            if MsgBit < MessageLength:
                LfsrInValues = self.LfsrIn.simulateFastANF(ANFSpace, [f'M{MsgBit}'], MsgInjectors, LfsrInValues)
                MsgBit += 1
            else:
                LfsrInValues = self.LfsrIn.simulateFastANF(ANFSpace, [None], MsgInjectors, LfsrInValues)
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
            #BFCombos = []
            for bfun_i in range(len(self.Functions)):
                bfun = self.Functions[bfun_i]
                Inputs = []
                for Iindex in bfun[1]:
                    if Iindex >= 100000:
                        Inputs.append(LfsrOutValues[Iindex - 100000])
                    else:
                        Inputs.append(LfsrInValues[Iindex])
                #BFCombos.append([bfun[0], ANFSpace, Inputs])
                BFValues.append(bfun[0].getFastANFValue(ANFSpace, Inputs, Parallel=1, TaskScheduler=TaskScheduler))
                print(f"// RoT BentFunction {bfun_i+1} / {len(self.Functions)}")
                BFOutputs.append(bfun[2])
            #BVDone = 1
            #for BV in SimpleThread.imap(_bf_evaluate, BFCombos):
            #    BFValues.append(BV)
            #    print(f"// RoT sim - BentFunction {BVDone} / {len(self.Functions)}") 
            #    BVDone += 1
            BFs = []
            for i in range(len(BFValues)):
                BFs.append([BFValues[i], BFOutputs[i]])
            LfsrOutValues = self.LfsrOut.simulateFastANF(ANFSpace, [ANFSpace.createExpression()], 0, LfsrOutValues)
            for bf in BFs:
                Outputs = bf[1]
                for O in Outputs:
                    LfsrOutValues[O] = LfsrOutValues[O] ^ bf[0]
            for SD in self.DirectConnections:
                if SD[0] >= 100000000:
                    if SD[1] >= 100000:
                        LfsrInValues[SD[1]-100000] = LfsrInValues[SD[1]-100000] ^ LfsrInPhaseShifterValues[SD[0]-100000000]
                    else:
                        LfsrOutValues[SD[1]] = LfsrOutValues[SD[1]] ^ LfsrInPhaseShifterValues[SD[0]-100000000]
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
                if MonomialsCountPerFlop is None:
                    for i in range(len(LfsrOutValues)):
                        List = MonomialCountList.get(i, [])
                        List.append(LfsrOutValues[i].getMonomialCount())
                        MonomialCountList[i] = List
                else:
                    Val = LfsrOutValues[MonomialsCountPerFlop]  
                    MH = Val.getMonomialsHistogram()
                    for i in range(len(AllVariables)+1):
                        List = MonomialCountList.get(i, [])
                        List.append(MH[i])
                        MonomialCountList[i] = List
        if ReturnMonomialCountPerCycle:
            return MonomialCountList
        return LfsrOutValues
                    
    def reportMonomials(self, FileName : str, LfsrOutValues : list, AllVariablesLength : int, KeyAsSeed = False, PrintTables = 0, PrintExpressions = 0):
        Result = {'Expression':{}, 'Histogram': {}, 'GlobalMonomialCount': {}, 'MonomialCount': {}}
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
        
        
        

########################################################################################
#                          KEYSTREAM GENERATOR
########################################################################################

class ProgrammableNeptunLfsr:
    
    __slots__ = ("_Value", "_Selector", "_Size", "_SelectorDict", "_NextConditionDict", "_FfDict")
    
    def __init__(self, Size : int) -> None:
        self._Size = Size
        self._Value = bau.zeros(Size)
        UpperTaps = []
        LowerTaps = []
        UpperMin = Size >> 1
        LowerMax = UpperMin - 1
        D = Size-3
        for S in range(2, LowerMax+1, 3):
            for _ in range(3):
                if D < LowerMax:
                    break
                UpperTaps.append([S, D])
                D -= 1 
        D = Size-1
        for S in range(Size-2, UpperMin-1, -3):
            for _ in range(3):
                if D >= LowerMax and D < (Size-1):
                    break
                LowerTaps.append([S, D])
                D = (D + 1) % Size 
        SelectorDict = {}
        NextConditionDict = {}
        Index = 0
        for Tap in LowerTaps:
            SelectorDict[Index] = Tap
            if (Index % 3) == 2:
                NextConditionDict[Index] = len(LowerTaps) + len(UpperTaps) + 1 - Index
            else:
                NextConditionDict[Index] = None
            Index += 1
        for Tap in reversed(UpperTaps):
            SelectorDict[Index] = Tap
            NextConditionDict[Index] = None
            Index += 1
        self._SelectorDict = SelectorDict
        self._NextConditionDict = NextConditionDict
        self._Selector = bau.zeros(len(SelectorDict))
        self._FfDict = self._getFFOnDependencyDict()
            
    def getSize(self) -> int:
        return self._Size
    
    def getValue(self) -> bitarray:
        return self._Value.copy()
    
    def getSelector(self) -> bitarray:
        return self._Selector.copy()
    
    def getSelectorSize(self) -> int:
        return len(self._Selector)
    
    def setValue(self, Value : bitarray):
        Value = bitarray(Value)
        if len(Value) != len(self._Value):
            Aio.printError(f"The new value is {len(Value)} bit length while should be {len(self._Value)}.")
            self._Value = Value
    
    def setSelector(self, Value : bitarray):
        Value = bitarray(Value)
        if len(Value) != len(self._Selector):
            Aio.printError(f"The new value is {len(Value)} bit length while should be {len(self._Selector)}.")
            self._Selector = Value
        
    def _getFFOnDependencyDict(self) -> dict:
        Result = {}
        for i in range(self._Size):
            Ff = {}
            for k in self._SelectorDict.keys():
                Tap = self._SelectorDict[k]
                if Tap[1] == i:
                    NextCondition = self._NextConditionDict[k]
                    if NextCondition is not None:
                        Ff[Tap[0]] = [k, NextCondition]
                    else:
                        Ff[Tap[0]] = k
            Result[i] = Ff
        return Result
        
    def next(self, LfsrEnable = True, SelectorEnable = False, InjectorValue = 0) -> bitarray:
        NewValue = self._Value.copy()
        NewSelector = self._Selector.copy()
        if LfsrEnable:
            NewValue = Bitarray.rotl(NewValue)
            for i in range(self._Size):
                Ff = self._FfDict[i]
                for k in Ff.keys():
                    Condition = Ff[k]
                    if Aio.isType(Condition, 0):
                        if self._Selector[Condition]:
                            NewValue[i] ^= self._Value[k]
                    else:
                        if self._Selector[Condition[0]] and (not self._Selector[Condition[1]]):
                            NewValue[i] ^= self._Value[k]
        if SelectorEnable:
            NewSelector = Bitarray.rotl(NewSelector)
            NewSelector[len(NewSelector)-1] ^= self._Value[self._Size-1]
        self._Selector = NewSelector
        self._Value = NewValue

    def prev(self, LfsrEnable = True, SelectorEnable = True) -> bitarray:
        pass
    
    def getLfsr(self, SelectorValue : bitarray) -> Lfsr:
        if Aio.isType(SelectorValue, 0):
            SelectorValue = bau.int2ba(SelectorValue, self.getSelectorSize())
        elif Aio.isType(SelectorValue, ""):
            SelectorValue = bitarray(SelectorValue)
        if len(SelectorValue) != len(self._Selector):
            Aio.printError(f"SelectorValue is {len(SelectorValue)} bit length while it should be {len(self._Selector)} bit wide.")
            return None
        Taps = []
        for i in range(len(self._Selector)):
            if SelectorValue[i]:
                Tap = self._SelectorDict[i]
                NextCondition = self._NextConditionDict[i]
                if NextCondition is not None:
                    if SelectorValue[NextCondition]:
                        continue
                Taps.append(Tap)
        return Lfsr(self._Size, LfsrType.RingWithSpecifiedTaps, Taps)
    
    def generateAllLfsrs(self, ChunkSize = 10000):
        Result = []
        for i in range(1, (1 << self.getSelectorSize())):
            Result.append(self.getLfsr(i))
            if len(Result) >= ChunkSize:
                yield Result
                Result = []
        if len(Result) > 0:
            yield Result
    
    def getMaximumLfsrsAndPolynomialsCount(self) -> tuple:
        FoundLfsrs = 0
        Polys = []
        ChunkSize = 100000
        Iterations = (1 << self.getSelectorSize()) / ChunkSize
        Counter = 0
        for l in self.generateAllLfsrs(ChunkSize):
            PartResult = Lfsr.checkMaximum(l)   
            FoundLfsrs += len(PartResult)
            for lfsr in tqdm(PartResult, desc="Filtering polynomials"):
                poly = Polynomial.decodeUsingBerlekampMassey(lfsr)
                if poly not in Polys:
                    Polys.append(poly)
            Counter += 1
            Percent = round(Counter * 100 / Iterations, 2)
            Percent = 100.0 if Percent > 100.0 else Percent
            print(f"// {Percent}% finished / found {FoundLfsrs} maximum Lfsrs / {len(Polys)} primitive polynomials")
        return FoundLfsrs, len(Polys)
    
    def toVerilog(self, ModuleName : str) -> str:
        Result = f"""module {ModuleName} (
  input wire clk,
  input wire reset,
  input wire lfsr_enable,
  input wire selector_enable,
  input wire injector,
  output reg [{self._Size-1}:0] O
  output reg [{self.getSelectorSize()-1}:0] selector;
);


always @ (posedge clk) begin
  if (reset) begin
    selector    <= {self.getSelectorSize()}`d0;
    O           <= {self._Size}`d0;
  end else begin
    if (lfsr_enable) begin
"""
        for i in range(self._Size):
            Line = f"      O[{i}] <= O[{(i+1) % self._Size}]"
            Ff = self._FfDict[i]
            for k in Ff.keys():
                Condition = Ff[k]
                if Aio.isType(Condition, 0):
                    Line += f" ^ (O[{k}] & selector[{Condition}])"    
                else:
                    Line += f" ^ (O[{k}] & selector[{Condition[0]}] & ~selector[{Condition[1]}])"
            if i == (self._Size-1):
                Line += " ^ injector"
            Line += ";\n"
            Result += Line
        Result += f"""    end
    if (selector_enable) begin
"""
        SelSize = self.getSelectorSize()
        for i in range(SelSize):
            Line = f"      selector[{i}] <= selector[{(i+1) % SelSize}]"
            if i == (SelSize-1):
                Line += f" ^ O[{self._Size-1}]"
            Line += ";\n"
            Result += Line
        Result += f"""    end
  end
end

endmodule"""
        return Result
    
    

class KeystreamGeneratorsMuxBlock:
    
    __slots__ = ("UpperMuxInputs", "UpperMuxSelect", "LowerMuxInputs", "LowerMuxSelect")
    
    def __init__(self, UpperMuxInputs : list, UpperMuxSelect : list, LowerMuxInputs : list, LowerMuxSelect : list):
        self.UpperMuxInputs = UpperMuxInputs
        self.UpperMuxSelect = UpperMuxSelect
        self.LowerMuxInputs = LowerMuxInputs
        self.LowerMuxSelect = LowerMuxSelect
    
    def toVerilogEquation(self, MuxBlockOutputName : str, UpperNlfsrOutputName : str, LowerNlfsrOutputName : str, LeftLfsrOutputName : str) -> str:
        UpperMuxSelectName = f"{MuxBlockOutputName}_upper_mux_sel"
        LowerMuxSelectName = f"{MuxBlockOutputName}_lower_mux_sel"
        UpperMuxSignalName = f"{MuxBlockOutputName}_upper_mux"
        LowerMuxSignalName = f"{MuxBlockOutputName}_lower_mux"
        UpperMuxSelectVector = "{"
        Second = 0
        for S in self.UpperMuxSelect:
            if Second:
                UpperMuxSelectVector += ", "
            else:
                Second = 1
            UpperMuxSelectVector += f"{LeftLfsrOutputName}[{S}]"
        UpperMuxSelectVector += "}"
        LowerMuxSelectVector = "{"
        Second = 0
        for S in self.LowerMuxSelect:
            if Second:
                LowerMuxSelectVector += ", "
            else:
                Second = 1
            LowerMuxSelectVector += f"{LeftLfsrOutputName}[{S}]"
        LowerMuxSelectVector += "}"
        if len(self.UpperMuxSelect) > 1:
            Result  =   f"wire [{len(self.UpperMuxSelect)-1}:0] {UpperMuxSelectName} = {UpperMuxSelectVector};"
        else:
            Result  =   f"wire {UpperMuxSelectName} = {UpperMuxSelectVector};"
        if len(self.LowerMuxSelect) > 1:
            Result += f"\nwire [{len(self.LowerMuxSelect)-1}:0] {LowerMuxSelectName} = {LowerMuxSelectVector};"
        else:
            Result += f"\nwire {LowerMuxSelectName} = {LowerMuxSelectVector};"
        Result += f"\nreg {UpperMuxSignalName}, {LowerMuxSignalName};"
        Result += f"\nalways @ (*) begin"
        for i in range(len(self.UpperMuxInputs)):
            Result += f"\n  if ({UpperMuxSelectName} == {len(self.UpperMuxInputs)}'d{i}) begin"
            Result += f"\n    {UpperMuxSignalName} <= {UpperNlfsrOutputName}[{self.UpperMuxInputs[i]}]"
            Result += f"\n  end"
        Result += f"\nend"
        Result += f"\nalways @ (*) begin"
        for i in range(len(self.LowerMuxInputs)):
            Result += f"\n  if ({LowerMuxSelectName} == {len(self.LowerMuxInputs)}'d{i}) begin"
            Result += f"\n    {LowerMuxSignalName} <= {LowerNlfsrOutputName}[{self.LowerMuxInputs[i]}]"
            Result += f"\n  end"
        Result += f"\nend"
        Result += f"\nwire {MuxBlockOutputName} = {UpperMuxSignalName} ^ {LowerMuxSignalName};"
        return Result


class KeystreamGenerator:
    
    __slots__ = ("UpperNlfsr", "LowerNlfsr", "LeftLfsr", "MuxBlocks", "LeftPhaseShifter", "UpperExpander", "LowerExpander")
    
    def __init__(self, FileName = None) -> None:
        self.UpperNlfsr = Nlfsr(32, [])
        self.LowerNlfsr = Nlfsr(32, [])
        self.LeftLfsr = ProgrammableLfsr(32, [])
        self.UpperExpander = PhaseShifter(self.UpperNlfsr, [])
        self.LowerExpander = PhaseShifter(self.LowerNlfsr, [])
        self.LeftPhaseShifter = PhaseShifter(Lfsr(32, RING_WITH_SPECIFIED_TAPS, []), [])
        self.MuxBlocks = []
        if FileName is not None:
            self.fromFile(FileName)
            
    def __len__(self) -> int:
        return self.getSize()
            
    def getSize(self) -> int:
        return len(self.MuxBlocks)
            
    def fromFile(FileName):
        pass
    
    def setLeftLfsr(self, ProgrammableLfsrObject : ProgrammableLfsr):
        self.LeftLfsr = ProgrammableLfsrObject
        
    def setUpperNlfsr(self, NlfsrObject : Nlfsr):
        self.UpperNlfsr = NlfsrObject
        
    def setLowerNlfsr(self, NlfsrObject : Nlfsr):
        self.LowerNlfsr = NlfsrObject
        
    def addMuxBlock(self, MuxBlock : KeystreamGeneratorsMuxBlock):
        self.MuxBlocks.append(MuxBlock)
        
    def setLeftPhaseShifter(self, PhaseShifterObject : PhaseShifter):
        self.LeftPhaseShifter = PhaseShifterObject
        
    def setUpperExpander(self, PhaseShifterObject : PhaseShifter):
        self.UpperExpander = PhaseShifterObject
        
    def setLowerExpander(self, PhaseShifterObject : PhaseShifter):
        self.LowerExpander = PhaseShifterObject
        
    def getSizeOfPolynomialSelector(self) -> int:
        return self.LeftLfsr.getConfigVectorLength()
    
    def simulatePolynomialSelectorSettingUp(self, InputSequence : bitarray, LfsrInjectorBitIndex : int, LfsrSelectorOutputBitIndex : int, Verbose = False) -> tuple:
        InputSequence = bitarray(InputSequence)
        SelectorBits = bitarray(self.LeftLfsr.getConfigVectorLength())
        SelectorBits.setall(0)
        lfsr = self.LeftLfsr.getLfsr(SelectorBits)
        lfsr._baValue.setall(0)
        if Verbose:
            PT = PandasTable(["Cycle", "SelectorValue", "LfsrValue", "LfsrObject"])
            PT.add([0, Bitarray.toString(SelectorBits), Bitarray.toString(lfsr._baValue), repr(lfsr)])
        for i in range(len(InputSequence)):
            SelectorInput = lfsr._baValue[LfsrSelectorOutputBitIndex]
            InputValue = InputSequence[i]
            Value = lfsr.next()
            SelectorBits = Bitarray.rotr(SelectorBits)
            SelectorBits[0] ^= SelectorInput
            Value[LfsrInjectorBitIndex] ^= InputValue
            lfsr = self.LeftLfsr.getLfsr(SelectorBits)
            lfsr.setValue(Value)
            if Verbose:
                PT.add([i+1, Bitarray.toString(SelectorBits), Bitarray.toString(lfsr._baValue), repr(lfsr)])
        if Verbose:
            Aio.print("")
            Aio.print("--- simulatePolynomialSelectorSettingUp ----")
            Aio.print("")
            PT.print()
        return (SelectorBits, Value)
    
    def simulateLfsrSeedObtaining(self, InputSequenceLength : int, SelectorBits : bitarray, LfsrValue : bitarray, LfsrInjectorBitIndex : int, LfsrSelectorOutputBitIndex : int, Verbose = False) -> bitarray:
        SelectorBits = bitarray(SelectorBits).copy()
        LfsrValue = bitarray(LfsrValue).copy()
        if len(SelectorBits) != self.LeftLfsr.getConfigVectorLength():
            Aio.printError(f"SelectorBits must contain {self.LeftLfsr.getConfigVectorLength()} bits.")
            return None
        if len(LfsrValue) != self.LeftLfsr.getSize():
            Aio.printError(f"LfsrValue must contain {self.LeftLfsr.getSize()} bits.")
            return None
        InputSequence = bitarray()
        if Verbose:
            PT = PandasTable(["Cycle", "TryForSel", "TryForInj", "SelectorValue", "LfsrValue", "Winner?", "LfsrObject"])
            PT.add([InputSequenceLength, "-", "-", Bitarray.toString(SelectorBits), Bitarray.toString(LfsrValue), "-", repr(self.LeftLfsr.getLfsr(SelectorBits))])
        if InputSequenceLength > 0:
            Zero = bau.zeros(len(LfsrValue))
            SelZero = bau.zeros(len(SelectorBits))
            PrevSelector0 = Bitarray.rotl(SelectorBits)
            PrevLfsr0 = self.LeftLfsr.getLfsr(PrevSelector0)
            PrevLfsr0.setValue(LfsrValue.copy())
            LfsrValue0_0 = PrevLfsr0.prev().copy()
            PrevLfsr0.setValue(LfsrValue.copy())
            PrevLfsr0._baValue[LfsrInjectorBitIndex] ^= 1
            LfsrValue0_1 = PrevLfsr0.prev().copy()
            SelectorBits1 = SelectorBits.copy()
            SelectorBits1[0] ^= 1
            PrevSelector1 = Bitarray.rotl(SelectorBits1)
            PrevLfsr1 = self.LeftLfsr.getLfsr(PrevSelector1)
            PrevLfsr1.setValue(LfsrValue.copy())
            LfsrValue1_0 = PrevLfsr1.prev().copy()
            PrevLfsr1.setValue(LfsrValue.copy())
            PrevLfsr1._baValue[LfsrInjectorBitIndex] ^= 1
            LfsrValue1_1 = PrevLfsr1.prev().copy()
            if InputSequenceLength == 1:
                W0 = (LfsrValue0_0 == Zero) and (PrevSelector0 == SelZero)
                W1 = (LfsrValue0_1 == Zero) and (PrevSelector0 == SelZero)
                if Verbose:
                    PT.add([InputSequenceLength-1, 0, 0, Bitarray.toString(PrevSelector0), Bitarray.toString(LfsrValue0_0), W0, repr(PrevLfsr0)]) 
                    PT.add([InputSequenceLength-1, 0, 1, Bitarray.toString(PrevSelector0), Bitarray.toString(LfsrValue0_1), W1, repr(PrevLfsr0)])
                if W0:
                    InputSequence = bitarray('0')
                elif W1:
                    InputSequence = bitarray('1')
                else:
                    InputSequence = None
            else:
                W0_0 = (LfsrValue0_0[LfsrSelectorOutputBitIndex] == 0)
                W0_1 = (LfsrValue0_1[LfsrSelectorOutputBitIndex] == 0)
                W1_0 = (LfsrValue1_0[LfsrSelectorOutputBitIndex] == 1)
                W1_1 = (LfsrValue1_1[LfsrSelectorOutputBitIndex] == 1)
                if Verbose:
                    PT.add([InputSequenceLength-1, 0, 0, Bitarray.toString(PrevSelector0), Bitarray.toString(LfsrValue0_0), W0_0, repr(PrevLfsr0)]) 
                    PT.add([InputSequenceLength-1, 0, 1, Bitarray.toString(PrevSelector0), Bitarray.toString(LfsrValue0_1), W0_1, repr(PrevLfsr0)])
                    PT.add([InputSequenceLength-1, 1, 0, Bitarray.toString(PrevSelector0), Bitarray.toString(LfsrValue1_0), W1_0, repr(PrevLfsr0)]) 
                    PT.add([InputSequenceLength-1, 1, 1, Bitarray.toString(PrevSelector0), Bitarray.toString(LfsrValue1_1), W1_1, repr(PrevLfsr0)])
                Success = False
                if W0_0:
                    Result = self.simulateLfsrSeedObtaining(InputSequenceLength-1, PrevSelector0, LfsrValue0_0, LfsrInjectorBitIndex, LfsrSelectorOutputBitIndex, Verbose)
                    if Result is not None:
                        InputSequence = Result + bitarray('0')
                        Success = True
                if not Success and W0_1:
                    Result = self.simulateLfsrSeedObtaining(InputSequenceLength-1, PrevSelector0, LfsrValue0_1, LfsrInjectorBitIndex, LfsrSelectorOutputBitIndex, Verbose)
                    if Result is not None:
                        InputSequence = Result + bitarray('1')
                        Success = True
                if not Success and W1_0:
                    Result = self.simulateLfsrSeedObtaining(InputSequenceLength-1, PrevSelector1, LfsrValue1_0, LfsrInjectorBitIndex, LfsrSelectorOutputBitIndex, Verbose)
                    if Result is not None:
                        InputSequence = Result + bitarray('0')
                        Success = True
                if not Success and W1_1:
                    Result = self.simulateLfsrSeedObtaining(InputSequenceLength-1, PrevSelector1, LfsrValue1_1, LfsrInjectorBitIndex, LfsrSelectorOutputBitIndex, Verbose)
                    if Result is not None:
                        InputSequence = Result + bitarray('1')
                        Success = True
                if not Success:
                    InputSequence = None
        else:
            return bitarray('')  
        if Verbose:
            Aio.print("")
            Aio.print(f"--- simulateLfsrSeedObtaining {InputSequenceLength} ----")
            PT.print()
            Aio.print(f"--- Returned InputSequence: {InputSequence} ----")
        return InputSequence