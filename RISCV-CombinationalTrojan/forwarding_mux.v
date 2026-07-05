/*
 * Data Forwarding Multiplexer
 * 
 * Selects which data source to use for ALU operands based on forwarding control signals
 * 
 * Selection:
 * 00 = Register file value (no hazard, normal path)
 * 01 = Forward from EX/MEM stage (1-cycle hazard)
 * 10 = Forward from MEM/WB stage (2-cycle hazard)
 * 11 = Reserved / undefined
 */

module forwarding_mux (
    input [1:0] forward_control,      // Control signal from hazard unit
    input [31:0] reg_file_data,       // Data from register file (no forwarding)
    input [31:0] ex_mem_alu_result,   // Data from EX/MEM stage ALU
    input [31:0] mem_wb_write_data,   // Data from MEM/WB stage (chosen by write-back mux)
    output reg [31:0] alu_operand     // Final operand to feed to ALU
);

    always @(*) begin
        case (forward_control)
            2'b00:   alu_operand = reg_file_data;       // No forwarding
            2'b01:   alu_operand = ex_mem_alu_result;   // Forward from EX/MEM
            2'b10:   alu_operand = mem_wb_write_data;   // Forward from MEM/WB
            2'b11:   alu_operand = 32'h0;               // Undefined (shouldn't happen)
            default: alu_operand = reg_file_data;
        endcase
    end

endmodule
