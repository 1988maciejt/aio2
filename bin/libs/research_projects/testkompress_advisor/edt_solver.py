from libs.aio import *
from libs.lfsr import *

class DecompressorSolver:
    
    __slots__ = ('_lfsr', '_phase_shifter', '_scan_length', '_initial_phase_len', '_input_config')
    
    def __init__(self, lfsr : Lfsr, phaseshifter : PhaseShifter, ScanLength : int, InitialPhaseLen : int, InputConfig : list):
        """InputConfig must be a list like: [3, [2,5]] which means: two inputs, first to FF3 the second one to FFs 2 and 5"""
        self._lfsr = lfsr
        self._phase_shifter = phaseshifter
        self._scan_length = ScanLength
        self._initial_phase_len = InitialPhaseLen
        self._input_config = InputConfig
        
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
    
    def getTestDataVolume(self) -> int:
        return len(self._input_config) * self.getTestTime()
        
    def getTestTime(self) -> int:
        return self._scan_length + self._initial_phase_len