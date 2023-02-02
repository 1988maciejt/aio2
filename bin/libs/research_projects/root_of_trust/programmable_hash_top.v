`bent_functions = kwargs.get("bent_functions", 0)
`lfsr_out_injectors_list = kwargs.get("lfsr_out_injectors_list", 0)
`lfsr_in_size = kwargs.get("lfsr_in_size", 0)
`lfsr_in_config_size = kwargs.get("lfsr_in_config_size", 0)
`lfsr_out_size = kwargs.get("lfsr_out_size", 0)
`lfsr_out_config_size = kwargs.get("lfsr_out_config_size", 0)
`bent_count = len(bent_functions)

module top(
    input wire clk,
    input wire reset,
    input wire lfsr_in_injector,
    output wire [`(lfsr_out_size-1`):0] O
);
 
wire [`(len(lfsr_out_injectors_list)-1`):0] lfsr_out_injectors;
wire [`(lfsr_in_size-1`):0] lfsr_in_output;
wire [`(lfsr_in_config_size-1`):0] lfsr_in_config;
wire [`(lfsr_out_config_size-1`):0] lfsr_out_config;
wire [1:0] johnsons_counter_outputs;
 
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
assign bent_`(i`)_in[`(j`)] = lfsr_in_output[`(Input`)];
`  endfor
`endfor

`for i in range(bent_count):
 
`  bent_outputs = bent_functions[i][2]
`  for Output in bent_outputs:
`    Mapped = lfsr_out_injectors_list.index(Output)
assign lfsr_out_injectors[`(Mapped`)] = bent_`(i`)_out;
`  endfor
`endfor
 
lfsr_in lfsr_in(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .config_vector (lfsr_in_config),
    .injectors (lfsr_in_injector),
    .O (lfsr_in_output)
);
 
lfsr_out lfsr_out(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .config_vector (lfsr_out_config),
    .injectors (lfsr_out_injectors),
    .O (O)
);
 
lfsr_in_config_reg lfsr_in_config_reg_inst(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .I (johnsons_counter_outputs[0]),
    .O (lfsr_in_config)
);
 
lfsr_out_config_reg lfsr_out_config_reg_inst(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .I (johnsons_counter_outputs[0]),
    .O (lfsr_out_config)
);
 
johnsons_counter johnsons_counter_inst(
    .clk (clk),
    .enable (1'b1),
    .reset (reset),
    .I (~johnsons_counter_outputs[0]),
    .O (johnsons_counter_outputs)
);

`for i in range(bent_count):
 
bent_`(i`) bent_`(i`) (
    .I(bent_`(i`)_in),
    .O(bent_`(i`)_out)
);
`endfor
 
endmodule
