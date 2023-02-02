from libs.verilog import *
from libs.files import *
from libs.preprocessor import *
from bitarray import *



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
    
    def createShiftRegister(ModuleName : str, Size : int, ResetValue = 0, **kwargs) -> str:
        """Available kwargs:
            output_name - default 'O'
            enable_name - name of the enable input (default: 'enable')
            reset_name - name of the reset input (default: 'reset')
            clock_name - name of the clock input (default: 'clk')
            input_name - name of the input (default: 'I')
            shift_right - wheather to use right shifting (otherwise uses left shifting) (default: True)
        """
        if Aio.isType(ResetValue, "str"):
            ResetValue = bitarray(ResetValue)
            ResetValue.reverse()
            ResetValue = f"{Size}'b{str(ResetValue)[10:-2]}"
        if Aio.isType(ResetValue, 0):
            ResetValue = f"{Size}'d{ResetValue}"
        if Aio.isType(ResetValue, "bitarray"):
            ResetValue.reverse()
            ResetValue = f"{Size}'b{str(ResetValue)[10:-2]}"
        Content = readFile(Aio.getPath() + 'verilog/shift_register.v')
        ModuleContent = preprocessString(Content, module_name=ModuleName, size=Size, reset_value=ResetValue, **kwargs)
        return ModuleContent