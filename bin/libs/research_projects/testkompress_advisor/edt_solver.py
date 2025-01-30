from libs.aio import *
from libs.lfsr import *
from libs.bin_solver import *
from p_tqdm import *
from libs.utils_list import *
import libs.research_projects.testkompress_advisor.testkompress_advisor as TestKompressAdvisor

class DecompressorSolver:
    
    __slots__ = ('_lfsr', '_phase_shifter', '_scan_length', '_initial_phase_len', '_input_config', '_scan_cell_equations')
    
    def __init__(self, lfsr : Lfsr, phaseshifter : PhaseShifter, ScanLength : int, InitialPhaseLen : int, InputConfig : list):
        """InputConfig must be a list like: [3, [2,5]] which means: two inputs, first to FF3 the second one to FFs 2 and 5"""
        self._lfsr = lfsr
        self._phase_shifter = phaseshifter
        self._scan_length = ScanLength
        self._initial_phase_len = InitialPhaseLen
        self._input_config = InputConfig
        self._scan_cell_equations = None
        
    def __str__(self):
        Result = "DecompressorSolver {\n"
        Result += f"  INPUTS ({len(self._input_config)}):\n"
        for i in range(len(self._input_config)):
            Result += f"    {i}: {self._input_config[i]}\n"
        Result += f"  LFSR:\n"
        Result += f"    {repr(self._lfsr)}\n"
        Result += f"    Initial phase:  {self._initial_phase_len}\n"
        Xors = self._phase_shifter.getXors()
        Result += f"  PHASE SHIFTER ({len(Xors)}):\n"
        for i in range(len(Xors)):
            Result += f"    {i}: {Xors[i]}\n"
        Result += f"  TEST STATS:\n"
        Result += f"    Scan length:              {self._scan_length}\n"
        Result += f"    Scan count:               {len(self._phase_shifter)}\n"
        Result += f"    test data vol / pattern:  {self.getTestDataVolume()}\n"
        Result += f"    clock cycles / pattern:   {self.getTestTime()}\n"
        Result += "}"
        return Result
    
    def getTestDataVolume(self, PatternsCount : int = 1) -> int:
        return len(self._input_config) * self.getTestTime(PatternsCount)
        
    def getTestTime(self, PatternsCount : int = 1) -> int:
        return (self._scan_length + self._initial_phase_len) * PatternsCount
    
    def createEquationBase(self, Verbose : bool = False):
        self._scan_cell_equations = None
        if Verbose:
            print(f"EQUATION BASE Start =========================")
        VarCount = self.getTestDataVolume()
        CycleCount = self.getTestTime()
        LfsrDestDict = self._lfsr.getDestinationsDictionary(self._input_config)
        FFs = [bau.zeros(VarCount) for _ in range(len(self._lfsr))]
        InputCount = len(self._input_config)
        InputAdder = 0
        ScanChainCells = [[bau.zeros(VarCount) for _ in range(self._scan_length)]  for _ in range(len(self._phase_shifter))]
        if Verbose:
            print(f"LfsrDestDict: {LfsrDestDict}")
        ScanChainCycle = 0
        for Cycle in range(CycleCount):
            if Verbose:
                print(f"Cycle: {Cycle} ----------------------")
            FFsNew = [bau.zeros(VarCount) for _ in range(len(self._lfsr))]
            for FFDest in range(len(FFs)):
                if Verbose:
                    print(f"  FFDest: {FFDest}")
                for Val in LfsrDestDict[FFDest]:
                    if Verbose:
                        print(f"    Val: {Val}")
                    if type(Val) is tuple:
                        if Verbose:
                            print(f"    {FFsNew[FFDest]} -> ", end="")
                        FFsNew[FFDest][Val[0] + InputAdder] ^= 1
                        if Verbose:
                            print(f"{FFsNew[FFDest]}")
                    else:
                        if Verbose:
                            print(f"    {FFsNew[FFDest]} ^ {FFs[Val]} ->", end="")
                        FFsNew[FFDest] ^= FFs[Val]
                        if Verbose:
                            print(f"{FFsNew[FFDest]}")
            FFs = FFsNew
            InputAdder += InputCount
            if Verbose:
                print(f"FFs: {FFs}")
            if Cycle>= self._initial_phase_len:
                if Verbose:
                    print(f"  TO_SCAN_CHAINS {ScanChainCycle}")
                Xors = self._phase_shifter.getXors()
                for ScanIndex in range(len(self._phase_shifter)):
                    for XorIn in Xors[ScanIndex]:
                        ScanChainCells[ScanIndex][ScanChainCycle] ^= FFs[XorIn]
                if Verbose:
                    for ScanIndex in range(len(self._phase_shifter)):
                        print(f"  SCAN {ScanIndex}: {ScanChainCells[ScanIndex]}")
                ScanChainCycle += 1
        self._scan_cell_equations = ScanChainCells
        if Verbose:
            print(f"EQUATION BASE End =========================")
            
    def getPatternLength(self) -> int:
        return len(self._phase_shifter) * self._scan_length
    
    def getScanChainCount(self) -> int:
        return len(self._phase_shifter)
    
    def getScanLength(self) -> int:
        return self._scan_length
    
    def getInputCount(self) -> int:
        return len(self._input_config)
    
    def getLfsrLength(self) -> int:
        return len(self._lfsr)
    
    def getMaximumCubeBitsPerDecompressor(self) -> int:
        return int(len(self._phase_shifter) * self._scan_length)
    
    def getMaximumSpecifiedBitPerCycleToBeCompressable(self) -> int:
        return int(1.5 * ((2 + self._initial_phase_len + self._scan_length) * len(self._input_config)))
    
    def getSpecifiedBitPerCycleDict(self, Cube : TestKompressAdvisor.TestCube) -> dict:
        Result = {}
        TCPos = Cube.getSpecifiedBitPositions()
        for Pos in TCPos:
            PosInScan = Pos % self.ScanLength
            Result[PosInScan] = Result.get(PosInScan, 0) + 1
        return Result
    
    def isCompressable(self, Pattern : TestKompressAdvisor.TestCube, Verbose : bool = False, *args, **kwargs) -> bool:
        if self._scan_cell_equations is None:
            self.createEquationBase()
        if len(Pattern) > self.getPatternLength():
            Aio.printError(f"Pattern length is greater than the expected {self.getPatternLength()}")
            return False
        SpecValues = Pattern.getSpecifiedScanCellValues(self.getScanChainCount(), self.getScanLength())
        if Verbose:
            print(f"SpecValues: {SpecValues}")
        Equations = []
        for SpecValue in SpecValues:
            SI = SpecValue[0]
            CI = SpecValue[1]
            V = SpecValue[2]
            Equation = BinSolverEquation(self._scan_cell_equations[SI][CI], V)
            if Verbose:
                print(f"SpecValue: {SpecValue}, Equation: {Equation}")
            Equations.append(Equation)
        Solver = BinSolver(Equations)
        Result = Solver.solve(Verbose=Verbose)
        ResToRet = False if Result is None else True
        if Verbose:
            print(f"Result of sloving: {Result}")
            print(f"Is compressable: {ResToRet} =========================")
        return ResToRet
            
    def getDecompressorForBatteryModelEstimations(self) -> TestKompressAdvisor.TestDataDecompressor:
        Result = TestKompressAdvisor.TestDataDecompressor(self.getInputCount(), self.getScanChainCount(), self.getLfsrLength(), self.getScanLength())
        return Result
    
    def getCompressable(self, Patterns : TestKompressAdvisor.TestCubeSet) -> TestKompressAdvisor.TestCubeSet:
        Result = TestKompressAdvisor.TestCubeSet()
        self.createEquationBase()
        def serial(SubPatterns):
            SubResult = []
            for Pattern in SubPatterns:
                if self.isCompressable(Pattern):
                    SubResult.append(Pattern)
            return SubResult
        for RList in p_uimap(serial, List.splitIntoSublists(Patterns, 100), desc="Checking compressability (x100)"):
            for R in RList:
                Result.addCube(R)
        AioShell.removeLastLine()
        return Result
    
    def getUncompressable(self, Patterns : TestKompressAdvisor.TestCubeSet) -> TestKompressAdvisor.TestCubeSet:
        Result = TestKompressAdvisor.TestCubeSet()
        self.createEquationBase()
        def serial(SubPatterns):
            SubResult = []
            for Pattern in SubPatterns:
                if not self.isCompressable(Pattern):
                    SubResult.append(Pattern)
            return SubResult
        for RList in p_uimap(serial, List.splitIntoSublists(Patterns, 100), desc="Checking compressability (x100)"):
            for R in RList:
                Result.addCube(R)
        AioShell.removeLastLine()
        return Result
    
    def getCompressionRatio(self) -> float:
        return (self._scan_length * len(self._phase_shifter)) / self.getTestDataVolume()

    def makeComparisonWithBatteryModel(self, Patterns : TestKompressAdvisor.TestCubeSet, MinBatteryLevel : float = 0.1) -> tuple:
        """Patterns may be also a list of random pattern params: [Count, Perr, P1]
        Returns 7 counters: (Compressable, Correct, SolverDidBatteryNot, BatteryDidSolverNot, EffectivenessPercent, SolverDidPercent, BatteryDidPercent)"""
        Correct = 0
        SolverDidBatteryNot = 0
        BatteryDidSolverNot = 0
        Compressable = 0
        Iterator = List.splitIntoSublists(Patterns, 100)
        Random = False
        PatternCount = len(Patterns)
        if type(Patterns) in [list, tuple] and 2 >= len(Patterns) <= 3: 
            if type(Patterns[0]) in [int] and type(Patterns[1]) is float:
                Iterator = []
                Cntr = Patterns[0]
                PatternCount = Cntr
                while Cntr > 0:
                    if Cntr >= 100:
                        Iterator.append(100)
                        Cntr -= 100
                    else:
                        Iterator.append(Cntr)
                        Cntr = 0
                Perr = Patterns[1]
                P1 = 0.5
                if len(Patterns) == 3 and type(Patterns[2]) is float:
                    P1 = Patterns[2]
                Plen = self.getScanChainCount() * self.getScanLength()
                Random = True
        if type(MinBatteryLevel) is not float:
            Correct, SolverDidBatteryNot, BatteryDidSolverNot = [0 for _ in range(len(MinBatteryLevel))], [0 for _ in range(len(MinBatteryLevel))], [0 for _ in range(len(MinBatteryLevel))]
        self.createEquationBase()
        BatteryDec = self.getDecompressorForBatteryModelEstimations()
        def single(Pattern : TestKompressAdvisor.TestCube):
            SolvRes = self.isCompressable(Pattern)
            if type(MinBatteryLevel) is float:
                BatRes = BatteryDec.isCompressable(Pattern, MinBatteryLevel)
            else:
                BatRes = []
                for MBL in MinBatteryLevel:
                    BatRes.append(BatteryDec.isCompressable(Pattern, MBL))
            return (SolvRes, BatRes)
        def serial(Patterns : TestKompressAdvisor.TestCubeSet):
            C, SnB, BnS, Comp = 0, 0, 0, 0
            if type(MinBatteryLevel) is not float:
                C, SnB, BnS = [0 for _ in range(len(MinBatteryLevel))], [0 for _ in range(len(MinBatteryLevel))], [0 for _ in range(len(MinBatteryLevel))]
            if Random:
                Count = Patterns
                Patterns = TestKompressAdvisor.TestCubeSet()
                for _ in range(Count):
                    Patterns.addCube(TestKompressAdvisor.TestCube.randomCube(Plen, Perr, P1))
            for Pattern in Patterns:
                S, B = single(Pattern)
                if S:
                    Comp += 1
                if type(MinBatteryLevel) is float:
                    if S == B:
                        C += 1
                    elif S:
                        SnB += 1
                    else:
                        BnS += 1
                else:
                    for Bi in range(len(MinBatteryLevel)):
                        if S == B[Bi]:
                            C[Bi] += 1
                        elif S:
                            SnB[Bi] += 1
                        else:
                            BnS[Bi] += 1
            return (Comp, C, SnB, BnS)
        for Result in p_uimap(serial, Iterator, desc="Making comparison to battery model (x100)"):
            Compressable += Result[0]
            if type(MinBatteryLevel) is float:
                Correct += Result[1]
                SolverDidBatteryNot += Result[2]
                BatteryDidSolverNot += Result[3]
            else:
                for i in range(len(MinBatteryLevel)):
                    Correct[i] += Result[1][i]
                    SolverDidBatteryNot[i] += Result[2][i]
                    BatteryDidSolverNot[i] += Result[3][i]
        AioShell.removeLastLine()
        Uncompressable = PatternCount - Compressable
        if type(MinBatteryLevel) is float:
            if Compressable <= 0:
                if SolverDidBatteryNot > 0:    
                    SolverDidPercent = 100
                else:
                    SolverDidPercent = 0
            else:
                SolverDidPercent = round(SolverDidBatteryNot * 100 / Compressable, 3)
            if Uncompressable <= 0:
                if BatteryDidSolverNot > 0:
                    BatteryDidPercent = 100
                else:
                    BatteryDidPercent = 0
            else:
                BatteryDidPercent = round(BatteryDidSolverNot * 100 / Uncompressable, 3)
            EffectivenessPercent = round(((100-SolverDidPercent) + (100-BatteryDidPercent)) / 2, 3)
        else:
            SolverDidPercent, BatteryDidPercent, EffectivenessPercent = [], [], []
            for i in range(len(MinBatteryLevel)):
                if Compressable <= 0:
                    if SolverDidBatteryNot[i] > 0:    
                        SolverDidPercent.append(100)
                    else:
                        SolverDidPercent.append(0)
                else:
                    SolverDidPercent.append(round(SolverDidBatteryNot[i] * 100 / Compressable, 3))
                if Uncompressable <= 0:
                    if BatteryDidSolverNot[i] > 0:
                        BatteryDidPercent.append(100)
                    else:
                        BatteryDidPercent.append(0)
                else:
                    BatteryDidPercent.append(round(BatteryDidSolverNot[i] * 100 / Uncompressable, 3))
                EffectivenessPercent.append(round(((100-SolverDidPercent[i]) + (100-BatteryDidPercent[i])) / 2, 3))
        return (Compressable, Correct, SolverDidBatteryNot, BatteryDidSolverNot, EffectivenessPercent, SolverDidPercent, BatteryDidPercent)
    
    def calibrateBatteryModelThreshold(self, Patterns : TestKompressAdvisor.TestCubeSet) -> tuple:
        """Returns (BestThreshold, BestEfficiency) or (-1, -1) if calibration impossible due to no uncompressable patterns."""
        ThresholdList = [i/100 for i in range(0, 100, 1)]
        Compressable, _, _, _, ffectivenessList, _, _ = self.makeComparisonWithBatteryModel(Patterns, ThresholdList)
        if Compressable == len(Patterns):
            return -1, -1
        BestThreshold = 0
        BestEffectiveness = 0
        for i in range(len(ffectivenessList)):
            if ffectivenessList[i] > BestEffectiveness:
                BestEffectiveness = ffectivenessList[i]
                BestThreshold = ThresholdList[i]
        return BestThreshold, BestEffectiveness
        
        