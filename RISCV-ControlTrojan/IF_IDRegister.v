module IF_IDRegister (
    input clk,
    input rst,
    input enable,
    input [31:0] instr_in,
    input [31:0] pc_in,
    input [31:0] adder1_in,
    output reg [31:0] instr_out,
    output reg [31:0] pc_out,
    output reg [31:0] adder1_out
);
    always @(posedge clk) begin
        if (~rst) begin
            instr_out <= 0;
            pc_out <= 0;
            adder1_out <= 0;
        end
        else if (enable) begin
            instr_out <= instr_in;
            pc_out <= pc_in;
            adder1_out <= adder1_in;
        end
    end

endmodule