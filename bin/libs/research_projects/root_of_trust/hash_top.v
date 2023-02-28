`bent_functions = kwargs.get("bent_functions", [])
`lfsr_in_size = kwargs.get("lfsr_in_size", 0)
`lfsr_out_size = kwargs.get("lfsr_out_size", 0)
`phase_shifter = kwargs.get("phase_shifter", None)
`direct_connections = kwargs.get("direct_connections", [])
`bent_count = len(bent_functions)

module top (
  input wire clk,
  input wire reset,
  input wire lfsr_in_injector,
  output wire [`(lfsr_out_size-1`):0] O
);
 
wire [`(lfsr_out_size-1`):0] lfsr_out_injectors;
wire [`(lfsr_in_size-1`):0] lfsr_in_output;
`if phase_shifter is not None:
wire [`(len(phase_shifter)-1`):0] phase_shifter_output;
`endif
 
`for i in range(bent_count):
`  InputCount = len(bent_functions[i][1])
wire [`(InputCount-1`):0] bent_`(i`)_in;
`endfor
`for i in range(bent_count):
wire bent_`(i`)_out;
`endfor

`for i in range(bent_count):
 
`  bent_inputs = bent_functions[i][1]
`  for j in range(len(bent_inputs)):
`    Input = bent_inputs[j]
`    if Input > 100000:
`      IString = f"lfsr_out_output[{Input-100000}]"
`    else:
`      IString = f"lfsr_in_output[{Input}]"
`    endif
assign bent_`(i`)_in[`(j`)] = `(IString`);
`  endfor
`endfor
 
`lfsrOutUsedInjectors = []
`for i in range(bent_count):
`  bent_outputs = bent_functions[i][2]
`  for Output in bent_outputs:
`    lfsrOutUsedInjectors.append(Output)
assign lfsr_out_injectors[`(Output`)] = bent_`(i`)_out;
`  endfor
`endfor
 
`for DC in direct_connections:
`  S = DC[0]
`  D = DC[1]
`  if S >= 100000000:
`    SStr = f"phase_shifter_output[{S-100000000}]"
`  else:
`    if  S >= 100000:
`      SStr = f"O[{S-100000}]"
`    else:
`      SStr = f"lfsr_in_output[{S}]"
`    endif
`  endif
`  if D >= 100000:
`    DStr = f"ERROR!!!! UPWARD CONNECTION!"
`  else:
`    DStr = f"lfsr_out_injectors[{D}]"
`    lfsrOutUsedInjectors.append(D)
`  endif
assign `(DStr`) = `(SStr`);
`endfor
 
`for Injector in range(lfsr_out_size):
`  if Injector not in lfsrOutUsedInjectors:
assign lfsr_out_injectors[`(Injector`)] = 1'b0;
`  endif
`endfor
 
lfsr_in lfsr_in(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .injectors (lfsr_in_injector),
    .O (lfsr_in_output)
);

`if phase_shifter is not None:
 
phase_shifter phase_shifter(
    .I (lfsr_in_output),
    .O (phase_shifter_output)
);
`endif
 
lfsr_out lfsr_out(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .injectors (lfsr_out_injectors),
    .O (O)
);

`for i in range(bent_count):
 
bent_`(i`) bent_`(i`) (
    .I(bent_`(i`)_in),
    .O(bent_`(i`)_out)
);
`endfor
 
endmodule
