from libs.pandas_table import *
from libs.aio import *
from libs.files import *
from libs.lfsr import *
from libs.bent_function import *
from libs.verilog import *
from libs.preprocessor import *
from bitarray import *

########################################################################################
#                          HASH FUNCTION
########################################################################################
class HashFunction:
    
    __slots__ = ("Size", "Cycles", "LfsrIn", "LfsrOut", "Functions", "LfsrOutInjectorList")
    
    def __init__(self, FileName) -> None:
        Data = readFile(FileName)
        R = re.search(r'Poly\s*size:\s*([0-9]+),\s*cycles:\s*([0-9]+)', Data, re.MULTILINE)
        self.Size = int(R.group(1))
        self.Cycles = int(R.group(2))
        R = re.search(r'RING\s*IN:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrIn = Lfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))), HYBRID_RING)
        R = re.search(r'RING\s*OUT:\s*([\-\s0-9]+)\n', Data, re.MULTILINE)
        self.LfsrOut = Lfsr(Polynomial(list(ast.literal_eval(R.group(1).strip().replace(" ", ",")))), HYBRID_RING)
        self.Functions = []
        self.LfsrOutInjectorList = []
        for R in re.finditer(r'Function:\s*([0-9]+)\s+Inputs:\s+([ 0-9]+)\s+Outputs:\s+([ 0-9^]+)', Data, re.MULTILINE):
            Inputs = list(ast.literal_eval(R.group(2).replace(" ", ",")))
            Outputs = list(ast.literal_eval(R.group(3).replace(" ", ",")))
            LUT = bau.int2ba(int(R.group(1)), 1<<len(Inputs), "little")  
            Function = BentFunction(LUT)
            self.LfsrOutInjectorList += Outputs
            self.Functions.append([Function, Inputs, Outputs])
        self.LfsrOutInjectorList.sort()
        
    def toVerilogObject(self) -> Verilog:
        Ver = Verilog(self.toVerilog())
        return Ver
        
    def toVerilog(self) -> Verilog:
        Content = self.LfsrIn.toVerilog("lfsr_in", [0])
        Content += "\n\n" + self.LfsrOut.toVerilog("lfsr_out", self.LfsrOutInjectorList)
        for i in range(len(self.Functions)):
            Bent = self.Functions[i][0]
            Content += "\n\n" + Bent.toVerilog(f"bent_{i}")
        Content += "\n\n" + preprocessString(readFile(Aio.getPath() + "libs/research_projects/root_of_trust/hash_top.v"),
                                             bent_functions=self.Functions,
                                             lfsr_out_injectors_list=self.LfsrOutInjectorList,
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