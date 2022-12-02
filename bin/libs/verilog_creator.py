from libs.verilog import *
from libs.files import *
from libs.preprocessor import *


class VerilogCreator:

    def createRingOscillator(ModuleName : str, InvertersCount : int, **kwargs) -> str:
        """Available kwargs:
            output_name - default 'O'
            all_outputs_vector_name - default: 'inv'
            enable_input - wheather to add pos-active 'enable' input or not (default: True)
            enable_name - name f the enable input (default: 'enable')
        """
        Content = readFile(Aio.getPath() + 'verilog/ring_oscillator.v')
        ModuleContent = preprocessString(Content, module_name=ModuleName, inverters_count=InvertersCount, **kwargs)
        #VerilogObject.addContent(ModuleContent)
        #VerilogObject.Constraints.add("set_property ALLOW_COMBINATORIAL_LOOPS true [get_nets -hierarchical]")
        return ModuleContent