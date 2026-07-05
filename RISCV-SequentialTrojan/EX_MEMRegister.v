module EX_MEMRegister (
    input clk,
    input rst,
    input [2:0] wb_in,
    input [4:0] mem_in,
    input [3:0] func3_in,
    input [31:0] ALUResult_in,
    input [31:0] readData2_in,
    input [31:0] adder1_in,
    input [4:0] rd_in,
    input zero_in,
    input [31:0] pc_in,
    output reg [2:0] wb_out,
    output reg [4:0] mem_out,
    output reg [31:0] ALUResult_out,
    output reg [31:0] readData2_out,
    output reg [31:0] adder1_out,
    output reg [4:0] rd_out,
    output reg [3:0] func3_out,
    output reg zero_out,
    output reg [31:0] pc_out
);

    always @(posedge clk) begin
        if (~rst) begin
            wb_out <= 0;
            mem_out <= 0;
            ALUResult_out <= 0;
            readData2_out <= 0;
            rd_out <= 0;
            zero_out <= 0;
            pc_out <= 0;
            func3_out <= 0;
            adder1_out <= 0;
        end
        else begin
            wb_out <= wb_in;
            mem_out <= mem_in;
            ALUResult_out <= ALUResult_in;
            readData2_out <= readData2_in;
            rd_out <= rd_in;
            zero_out <= zero_in;
            pc_out <= pc_in;
            func3_out <= func3_in;
            adder1_out <= adder1_in;
        end
    end
    
endmodule