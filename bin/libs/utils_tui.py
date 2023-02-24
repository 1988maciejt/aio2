
import textual.app as TextualApp
import textual.widgets as TextualWidgets
import textual.reactive as TextualReactive
import textual.containers as TextualContainers
from libs.utils_int import *
from libs.lfsr import *
from libs.aio import *
from libs.pandas_table import *

class _TuiWidgetTextWithLabel(TextualWidgets.Static):
    def __init__(self, Label : str, Value: str = "", Password = False, id: str | None = None) -> None:
        super().__init__(id=id)
        self._Label = str(Label)
        self._Value = str(Value)
        self._Password = bool(Password)
    def compose(self):
        self.styles.height = 3
        self.styles.margin = 1
        Lbl = TextualWidgets.Label(" \n" + self._Label, id="text_with_label_label")
        Txt = TextualWidgets.Input(self._Value, password=bool(self._Password), id="text_with_label_text")
        yield TextualContainers.Horizontal(
            Lbl, 
            Txt
        )
    def getValue(self) -> str:
        Txt = self.query_one(TextualWidgets.Input)
        return Txt.value
    
class _TuiWidgetLfsrSearchParameters(TextualWidgets.Static):
    def __init__(self, Size = 16, Taps = 3, Balancing = 0, MinDistance = 0, N = 0, ResultsAvailable = 0, id: str | None = None) -> None:
        super().__init__(id=id)
        self.Size = Size
        self.Taps = Taps
        self.Balancing = Balancing
        self.MinDistance = MinDistance
        self.N = N
        self.ResultsAvailable = ResultsAvailable
    def compose(self):
        self.dark = False
        yield _TuiWidgetTextWithLabel("Size:", self.Size, id="txt_size")
        yield _TuiWidgetTextWithLabel("Taps:", self.Taps, id="txt_taps")
        yield _TuiWidgetTextWithLabel("Balancing:", self.Balancing, id="txt_balancing")
        yield _TuiWidgetTextWithLabel("Min Distance:", self.MinDistance, id="txt_mindistance")
        yield _TuiWidgetTextWithLabel("Min results count:", self.N, id="txt_n")
        yield TextualWidgets.Button("Search for TIGER LFSRs", id="btn_search_tiger")
        yield TextualWidgets.Button("Search for ANY HYBRID LFSRs", id="btn_search_hybrid")
        if self.ResultsAvailable:
            yield TextualWidgets.Button("Export results to XLSX", id="btn_search_xlsx", variant="primary")
    def updateParams(self):
        self.app.Size = Int.toInt(self.query_one("#txt_size").getValue(), 8)
        self.app.Taps = Int.toInt(self.query_one("#txt_taps").getValue(), 0)
        self.app.Balancing = Int.toInt(self.query_one("#txt_balancing").getValue(), 0)
        self.app.MinDistance = Int.toInt(self.query_one("#txt_mindistance").getValue(), 0)
        self.app.N = Int.toInt(self.query_one("#txt_n").getValue(), 0)
    def on_button_pressed(self, event: TextualWidgets.Button.Pressed) -> None:
        if event.button.id == "btn_search_hybrid":
            self.app.EXE = "h"
        if event.button.id == "btn_search_tiger":
            self.app.EXE = "t"
        if event.button.id == "btn_search_xlsx":
            self.app.EXE = "xlsx"
        self.updateParams()
        self.app.exit()
        
class _TuiWidgetLfsrViewer(TextualWidgets.Static):
    Lbl = None
    def compose(self):
        self.Lbl = TextualWidgets.Label(" \n\n\n\n      < NO LFSRS YET >")
        yield self.Lbl 
    def updateLfsr(self, lfsr : Lfsr):
        self.Lbl.update(lfsr.getDraw())
        
# Polynomial searching
    
class _TuiHybridLfsrSearching(TextualApp.App):   
    BINDINGS = [("q", "quit", "Quit")]     
    CSS_PATH = "tui/utils_tui.css"
    def __init__(self, Size = 16, Taps = 3, Balancing = 0, MinDistance = 0, N = 0, Lfsrs = [], Polys = [], CPolys = [], driver_class = None, css_path = None, watch_css = False):
        super().__init__(driver_class, css_path, watch_css)
        self.Size = Size
        self.Taps = Taps
        self.Balancing = Balancing
        self.MinDistance = MinDistance
        self.N = N
        self.Lfsrs = Lfsrs
        self.Polys = Polys
        self.CPolys = CPolys
        self.EXE = ""
    def compose(self):
        self.dark = False
        yield TextualWidgets.Header()
        yield TextualContainers.Horizontal(
            _TuiWidgetLfsrSearchParameters(self.Size, self.Taps, self.Balancing, self.MinDistance, self.N, len(self.Lfsrs)>0, id="lfsr_search_params"),
            TextualWidgets.Static(id="lfsr_search_separator"),
            TextualContainers.Vertical(
                _TuiWidgetLfsrViewer(id="lfsr_search_viewer"),
                TextualWidgets.DataTable(zebra_stripes=1, id="lfsr_search_table"),
                id="lfsr_search_vcontainer"
            )
        )
        yield TextualWidgets.Footer()
    def on_mount(self):
        DT = self.query_one(TextualWidgets.DataTable)
        DT.add_columns("Architecture defining polynomial", "Decoded characteristic polynomial", ".")
        for i in range(len(self.Polys)):
            DT.add_row(str(self.Polys[i]), str(self.CPolys[i]), "[EXPLORE]")
        if len(self.Lfsrs) > 0:
            Viewer = self.query_one(_TuiWidgetLfsrViewer)
            Viewer.updateLfsr(self.Lfsrs[0])
    def on_data_table_cell_selected(self, event: TextualWidgets.DataTable.CellSelected) -> None:
        Index = event.coordinate.row
        Command = event.coordinate.column
        if Command == 2:
            self.EXE = f"e{Index}"    
            self.exit()
        else:
            Viewer = self.query_one(_TuiWidgetLfsrViewer)
            Viewer.updateLfsr(self.Lfsrs[Index])
        
        

class Tui:
    
    @staticmethod
    def searchForHybridLfsrs(ReturnResults = True) -> list:
        Result = []
        Lfsrs = []
        CPolys = []
        Size, Taps, Balancing, MinDistance, N = 32, 5, 4, 2, 10
        while 1:
            tui = _TuiHybridLfsrSearching(Size, Taps, Balancing, MinDistance, N, Lfsrs, Result, CPolys)
            tui.run()
            Exe = tui.EXE
            Size = tui.Size
            Taps = tui.Taps
            Balancing = tui.Balancing
            MinDistance = tui.MinDistance
            N = tui.N
            if Exe == "t":
                Result = Polynomial.listTigerPrimitives(
                    tui.Size,
                    tui.Taps+2,
                    tui.Balancing,
                    MinDistance=tui.MinDistance,
                    n=tui.N
                )
                Lfsrs = [Lfsr(P, LfsrType.TigerRing) for P in Result]
            elif Exe == "h":
                Result = Polynomial.listHybridPrimitives(
                    tui.Size,
                    tui.Taps+2,
                    tui.Balancing,
                    MinDistance=tui.MinDistance,
                    n=tui.N
                )
                Lfsrs = [Lfsr(P, LfsrType.HybridRing) for P in Result]
            elif Exe == "xlsx":
                if len(Lfsrs) < 1:
                    Aio.msgBox("Saving results to XLSX", "No results!!")
                else:
                    time.sleep(0.2)
                    Dir = pickDirectory("./", "Select directory in which to save the results:")
                    if Dir is None:
                        continue
                    File = Aio.inputBox("Saving results to XLSX", "Enter a file name:", "results.xlsx")
                    FileName = f"{Dir}/{File}"
                    PT = PandasTable(["Architecture defining polynomial", "Decoded characteristic polynomial"])
                    for i in range(len(Lfsrs)):
                        Poly = str(Result[i]).replace("[", "").replace("]", "")
                        CPoly = str(CPolys[i]).replace("[", "").replace("]", "")
                        PT.add([Poly, CPoly])
                    PT.print()
                    PT.toXls(FileName)
            elif Exe == "":
                break
            else:
                cmd, index = Int.splitLettersAndInt(Exe, "", -1)
                if cmd == "e" and index >= 0:
                    Lfsrs[index].tui()
            CPolys = [Polynomial.decodeUsingBerlekampMassey(L) for L in Lfsrs]
        if ReturnResults:
            return Result
        return None
    
    
    
    
    
    
    
    
    
    

