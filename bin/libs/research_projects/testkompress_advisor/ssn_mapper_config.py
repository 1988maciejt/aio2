#from libs.aio import *
from libs.pandas_table import AioTable
import libs.research_projects.testkompress_advisor.testkompress_advisor as TestKompressAdvisor

class SSNMapperCore: pass


class SSNMapperCoreConfig:

    __slots__ = ('Lfsr', 'InputCount', 'PatternCount', 'OutputCount', 'MaskingBits')

    def __init__(self, lfsr, InputCount, PatternCount, OutputCount, MaskingBits):
        self.Lfsr = int(lfsr)
        self.InputCount = int(InputCount)
        self.PatternCount = int(PatternCount)
        self.OutputCount = int(OutputCount)
        self.MaskingBits = int(MaskingBits)

    def copy(self):
        return SSNMapperCoreConfig(self.Lfsr, self.InputCount, self.PatternCount, self.OutputCount, self.MaskingBits)

    def __str__(self):
        return f"{self.Lfsr} {self.InputCount} {self.PatternCount} {self.OutputCount} {self.MaskingBits}"

    def __len__(self):
        return self.PatternCount

    def __eq__(self, other):
        if not isinstance(other, SSNMapperCoreConfig):
            return NotImplemented
        return (self.Lfsr == other.Lfsr and
                self.InputCount == other.InputCount and
                self.PatternCount == other.PatternCount and
                self.OutputCount == other.OutputCount and
                self.MaskingBits == other.MaskingBits)

    def __neq__(self, other):
        return not self.__eq__(other)

    def getCompressionRatio(self, MyCore : SSNMapperCore):
        import libs.research_projects.testkompress_advisor.testkompress_advisor as TestKompressAdvisor
        return TestKompressAdvisor.TestKompressCalculator.getCompression(self.InputCount, self.Lfsr, MyCore.ScanLength, MyCore.ScanCount)

    def getReportRow(self, MyCore : SSNMapperCore):
        return [self.Lfsr, self.InputCount, self.OutputCount, round(self.getCompressionRatio(MyCore), 2), self.PatternCount]


class SSNMapperCore:

    __slots__ = ('Id', '_config_list', 'ScanCount', 'ScanLength', 'LowPowerBits', 'Comment')

    def __init__(self, Id, ScanCount, ScanLength, LowPowerBits, config_list=None, Comment : str = None):
        self.Id = Id
        self.ScanCount = int(ScanCount)
        self.ScanLength = int(ScanLength)
        self._config_list = []
        if config_list is not None:
            for config in config_list:
                self.addConfig(config)
        self.LowPowerBits = int(LowPowerBits)
        self.Comment = Comment

    def __str__(self):
        Result = ""
        if self.Comment is not None and len(self.Comment) > 0:
            from libs.utils_str import Str
            Result += Str.makeComment(self.Comment, "# ", "- ", "- ") + "\n"
        Result += f"{self.Id} {self.ScanCount} {self.ScanLength} {self.LowPowerBits} -1\n"
        Result += f"{len(self._config_list)}"
        for config in self._config_list:
            Result += f"\n{config}"
        return Result

    def __len__(self):
        return len(self._config_list)

    def addConfig(self, config):
        if not isinstance(config, SSNMapperCoreConfig):
            raise TypeError("config must be an instance of SSNMapperCoreConfig")
        if config not in self._config_list:
            self._config_list.append(config)

    def __eq__(self, other):
        if not isinstance(other, SSNMapperCore):
            return NotImplemented
        return self.Id == other.Id

    def __neq__(self, other):
        return not self.__eq__(other)

    def getConfigurations(self):
        return self._config_list

    def fromTestKompressMLData(Id : int,TestKompressMLData : TestKompressAdvisor.TestKompressMLData) -> "SSNMapperCore":
        from libs.aio import Aio
        Id = int(Id)
        ScanCount = int(TestKompressMLData.getScanCount())
        ScanLength = int(TestKompressMLData.getScanLength())
        Aio.printError(f"Not finished yet! MLData to grab LowPowerBits...")

    def setOutputCountForAllConfigs(self, OutputCount : int, ExcludeFirstConfig : bool = False):
        First = True
        for config in self._config_list:
            if ExcludeFirstConfig and First:
                First = False
                continue
            config.OutputCount = OutputCount
            First = False

    def getConfigsCompressionList(self):
        Result = []
        for config in self._config_list:
            Result.append(config.getCompressionRatio(self))
        return Result

    def getReportTable(self, BestCompressionOnly : bool = False) -> "AioTable":
        AutoId = True
        if BestCompressionOnly:
            AutoId = False
        Result = AioTable(["LFSR", "Input Count", "Output Count", "Compression Ratio", "Pattern Count"], AutoId=AutoId)
        if BestCompressionOnly:
            Best = None
        for config in self._config_list:
            Row = config.getReportRow(self)
            if BestCompressionOnly:
                if Best is None or abs(Row[3] - 120) < abs(Best[3] - 120):
                    Best = Row
            else:
                Result.addRow(Row)
        if BestCompressionOnly and Best is not None:
            Result.addRow(Best)
        return Result


class SSNMapperData:

    __slots__ = ('_core_list', 'Comment')

    @staticmethod
    def fromFile(FileName : str):
        from libs.files import File
        from libs.aio import Aio
        if File.exists(FileName):
            CoreCount = None
            ConfigCounter = 0
            Result = SSNMapperData()
            for Line in File.readLineByLineGenerator(FileName):
                if Line.startswith("#"):
                    continue
                if CoreCount is None:
                    CoreCount = int(Line.strip())
                else:
                    if ConfigCounter == 0:
                        CoreId, ScanCount, ScanLen, LowPowerBits, _ = map(int, Line.strip().split())
                        CurrentCore = SSNMapperCore(CoreId, ScanCount, ScanLen, LowPowerBits)
                        Result.addCore(CurrentCore)
                        ConfigCounter = -1
                    elif ConfigCounter == -1:
                        ConfigCounter = int(Line.strip())
                    else:
                        LFSR, ChIn, PatternCount, ChOut, MaskingBits = map(int, Line.strip().split())
                        CurrentCore.addConfig(SSNMapperCoreConfig(LFSR, ChIn, PatternCount, ChOut, MaskingBits))
                        ConfigCounter -= 1
            return Result
        else:
            Aio.printError(f"File '{FileName}' does not exist.")
        return None

    def __init__(self, core_list=None, Comment : str = None):
        self._core_list = []
        self.Comment = Comment
        if core_list is not None:
            for core in core_list:
                self.addCore(core)

    def __str__(self):
        self._sort_cores()
        Result = ""
        if self.Comment is not None and len(self.Comment) > 0:
            from libs.utils_str import Str
            Result += Str.makeComment(self.Comment, "# ", "=", "=") + "\n"
        Result += f"{len(self._core_list)}"
        for core in self._core_list:
            Result += f"\n{core}"
        return Result

    def __len__(self):
        return len(self._core_list)

    def _sort_cores(self):
        self._core_list.sort(key=lambda core: core.Id)

    def addCore(self, core):
        if not isinstance(core, SSNMapperCore):
            raise TypeError("core must be an instance of SSNMapperCore")
        if core not in self._core_list:
            self._core_list.append(core)
            self._sort_cores()

    def getCores(self):
        return self._core_list

    def toFile(self, FileName : str):
        from libs.files import File
        File.write(FileName, str(self))

    def getCoreById(self, CoreId : int):
        for core in self._core_list:
            if core.Id == CoreId:
                return core
        return None

    def setOutputCountForAllConfigs(self, OutputCount : int, ExcludeFirstConfig : bool = False):
        for core in self._core_list:
            core.setOutputCountForAllConfigs(OutputCount, ExcludeFirstConfig)

    def getReport(self, BestCompressionOnly : bool = False) -> str:
        Result = ""
        Next = False 
        for core in self._core_list:
            if Next:
                Result += "\n\n"
            else:
                Next = True
            Result += f"Core ID: {core.Id}\n"
            Result += core.getReportTable(BestCompressionOnly).toString()
        return Result

    def printReport(self, BestCompressionOnly : bool = False):
        from libs.aio import Aio
        Aio.print(self.getReport(BestCompressionOnly))