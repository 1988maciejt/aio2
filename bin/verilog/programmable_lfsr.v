`module_name                = kwargs.get("module_name", "NAME")
`size                       = kwargs.get("size", 8)
`output_name                = kwargs.get("output_name", "O")
`reset_value                = kwargs.get("reset_value", f"{size}'d0" )
`reset_name                 = kwargs.get("reset_name", "reset")
`clock_name                 = kwargs.get("reset_name", "clk")
`config_input_name          = kwargs.get("enable_name", "config_input")
`enable_name                = kwargs.get("enable_name", "enable")
`enable_input               = kwargs.get("enable_input", 1)
`injectors_name             = kwargs.get("injectors_name", "injectors")
`injectors_input            = kwargs.get("injectors_input", 1)
`feedback_dict              = kwargs.get("feedback_dict", {})

module `(module_name`) (
  input wire `(clock_name`),
  input wire `(reset_name`),
`if enable_input:
  input wire `(enable_name`),
`endif
`if len(feedback_dict) > 0:
  input wire [`(len(feedback_dict)-1`):0] `(config_input_name`),
`endif
`if injectors_input:
  output reg [`(size-1`):0] `(injectors_name`),
`endif
  output reg [`(size-1`):0] `(output_name`)
);

`indent = ""
`if enable_input:
`  indent = "  "
`endif
  
always @ (posedge `(clock_name`)) begin
  if (`(reset_name`)) begin
    `(output_name`) <= `(reset_value`);
  end else begin
`if enable_input:
    if (`(enable_name`)) begin
`endif
`for i in range(size):
    `(indent`)`(output_name`)[`(i`)] <= `(output_name`)[`((i+1)%size`)];
`endfor
`if enable_input:
    end
`endif
  end
end

endmodule