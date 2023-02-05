from libs.pandas_table import *
from libs.aio import *
from libs.files import *
from libs.lfsr import *
from libs.programmable_lfsr import *
from libs.bent_function import *
from libs.verilog import *
from libs.verilog_creator import *
from libs.preprocessor import *
from bitarray import *
import sympy.logic.boolalg as SympyBoolalg
from tqdm import tqdm 

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
class HashFunction:
    
    __slots__ = ("Size", "Cycles", "LfsrIn", "LfsrOut", "Functions")
    
    def __init__(self, FileName = None) -> None:
        self.Size = 0
        self.Cycles = 0
        self.LfsrIn = None
        self.LfsrOut = None
        self.Functions = []
        if FileName is not None:
            self.fromFile(FileName)

    def setLfsrIn(self, LfsrObject : Lfsr):
        self.LfsrIn = LfsrObject

    def setLfsrOut(self, LfsrObject : Lfsr):
        self.LfsrOut = LfsrObject
        self.Size = LfsrObject.getSize()
        
    def addBentFunction(self, Function : BentFunction, LfsrInInputs : list, LfsrOutInjectors : list):
        self.Functions.append([Function, LfsrInInputs, LfsrOutInjectors])
        
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
            
    def symbolicSimulation(self, MessageLength : int, MsgInjectors : 0) -> list:
        LfsrInValues = [False for _ in range(self.LfsrIn.getSize())]
        LfsrOutValues = [False for _ in range(self.LfsrOut.getSize())] 
        MsgBit = 0
        for _ in tqdm(range(self.Cycles), desc="Simulation"):
            if MsgBit < MessageLength:
                LfsrInValues = self.LfsrIn.simulateSymbolically([symbols(f'M{MsgBit}')], MsgInjectors, LfsrInValues)
                MsgBit += 1
            else:
                LfsrInValues = self.LfsrIn.simulateSymbolically([False], MsgInjectors, LfsrInValues)
            BFs = []
            for bfun in self.Functions:
                Inputs = []
                for Iindex in bfun[1]:
                    Inputs.append(LfsrInValues[Iindex])
                BFs.append([bfun[0].getSymbolicValue(Inputs), bfun[2]])
            LfsrOutValues = self.LfsrOut.simulateSymbolically([False], 0, LfsrOutValues)
            for bf in BFs:
                Outputs = bf[1]
                for O in Outputs:
                    LfsrOutValues[O] = LfsrOutValues[O] ^ bf[0]
        for i in tqdm(range(len(LfsrOutValues)), desc="Simplification"):
            LfsrOutValues[i] = SympyBoolalg.simplify_logic(LfsrOutValues[i], 'dnf', force=1)
        Result = {'MonomialDegree':{}, 'Expression':{}}
        for i in range(len(LfsrOutValues)):
            V = LfsrOutValues[i]
            Highest = 0
            for A in V.args:
                try:
                    deg = len(A.atoms())
                    if deg > Highest: Highest = deg
                except:
                    pass
            Result['MonomialDegree'][i] = Highest
            Result['Expression'][i] = V
        return Result
            
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