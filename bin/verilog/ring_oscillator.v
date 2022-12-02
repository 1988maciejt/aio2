`inverters_count            = kwargs.get("inverters_count", 3)
`module_name                = kwargs.get("module_name", "NAME")
`output_name                = kwargs.get("output_name", "O")
`all_outputs_vector_name    = kwargs.get("all_outputs_vector_name", "inv")
`enable_name                = kwargs.get("enable_name", "enable")
`enable_input               = kwargs.get("enable_input", 1)

module `(module_name`) (
`if enable_input:
  (*DONT_TOUCH= "true"*) input wire `(enable_name`),
`endif
  (*DONT_TOUCH= "true"*) output wire `(output_name`),
  (*DONT_TOUCH= "true"*) output wire[`(inverters_count-1`):0] `(all_outputs_vector_name`)
);
  
  assign `(output_name`) = `(all_outputs_vector_name`)[0];
  
`for i in range(inverters_count):
 `nexti = (i+1) % inverters_count
 `if i == 0 and enable_input:
  (*DONT_TOUCH= "true"*) nand (`(all_outputs_vector_name`)[`(i`)], `(all_outputs_vector_name`)[`(nexti`)], `(enable_name`));
 `endif
 `else:
  (*DONT_TOUCH= "true"*) not (`(all_outputs_vector_name`)[`(i`)], `(all_outputs_vector_name`)[`(nexti`)]);
 `endif
`endfir
     
endmodule
