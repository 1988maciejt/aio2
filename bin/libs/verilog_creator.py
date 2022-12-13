from libs.verilog import *
from libs.files import *
from libs.preprocessor import *



class VerilogCreator:

    def createRingOscillator(ModuleName : str, InvertersCount : int, **kwargs) -> str:
        """Available kwargs:
            output_name - default 'O'
            all_outputs_vector_name - default: 'inv'
            enable_input - wheather to add pos-active 'enable' input or not (default: True)
            enable_name - name of the enable input (default: 'enable')
        """
        Content = readFile(Aio.getPath() + 'verilog/ring_oscillator.v')
        ModuleContent = preprocessString(Content, module_name=ModuleName, inverters_count=InvertersCount, **kwargs)
        return ModuleContent
    
    def createProgrammableLfsr(ModuleName : str, Size : int, TapsList : list, **kwargs) -> str:
        """Available kwargs:
            output_name - default 'O'
            enable_input - wheather to add pos-active 'enable' input or not (default: True)
            enable_name - name of the enable input (default: 'enable')
            injectors_input - wheather to add pos-active 'injectors' input or not (default: True)
            injectors_name - name of the injectors input (default: 'enable')
            reset_name - name of the reset input (default: 'reset')
            clock_name - name of the clock input (default: 'clk')
            reset_value - reset value (Verilog format)
        """
        FeedbackDict = {}
        for Tap in TapsList:
            TapDict = ""
        Content = readFile(Aio.getPath() + 'verilog/programmable_lfsr.v')
        ModuleContent = preprocessString(Content, module_name=ModuleName, size=Size, **kwargs)
        return ModuleContent