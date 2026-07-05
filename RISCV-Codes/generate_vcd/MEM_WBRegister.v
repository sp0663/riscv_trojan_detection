module MEM_WBRegister (
    input clk,
    input rst,
    input [2:0] wb_in,
    input [31:0] memReadData_in,
    input [31:0] ALUResult_in,
    input [31:0] adder1_in,
    input [4:0] rd_in,
    output reg [2:0] wb_out,
    output reg [31:0] memReadData_out,
    output reg [31:0] ALUResult_out,
    output reg [31:0] adder1_out,
    output reg [4:0] rd_out
);

    always @(posedge clk) begin
        if (~rst) begin
            wb_out <= 0;
            memReadData_out <= 0;
            ALUResult_out <= 0;
            rd_out <= 0;
            adder1_out <= 0;
        end
        else begin
            wb_out <= wb_in;
            memReadData_out <= memReadData_in;
            ALUResult_out <= ALUResult_in;
            rd_out <= rd_in;
            adder1_out <= adder1_in;
        end
    end
    
endmodule