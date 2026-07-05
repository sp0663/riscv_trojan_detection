module ID_EXRegister (
    input clk,
    input rst,
    input flush,
    input [2:0] wb_in,
    input [4:0] mem_in,
    input [2:0] ex_in,
    input [31:0] readData1_in,
    input [31:0] readData2_in,
    input [31:0] pc_in,
    input [31:0] adder1_in,
    input [31:0] imm_in,
    input [3:0] func3_in,
    input [4:0] rs1_in,
    input [4:0] rs2_in,
    input [4:0] rd_in,
    output reg [2:0] wb_out,
    output reg [4:0] mem_out,
    output reg [2:0] ex_out,
    output reg [31:0] readData1_out,
    output reg [31:0] readData2_out,
    output reg [31:0] pc_out,
    output reg [31:0] adder1_out,
    output reg [31:0] imm_out,
    output reg [3:0] func3_out,
    output reg [4:0] rs1_out,
    output reg [4:0] rs2_out,
    output reg [4:0] rd_out
);
    always @(posedge clk) begin
        if (~rst) begin
            wb_out <= 0;
            mem_out <= 0;
            ex_out <= 0;
            readData1_out <= 0;
            readData2_out <= 0;
            imm_out <= 0;
            func3_out <= 0;
            rs1_out <= 0;
            rs2_out <= 0;
            rd_out <= 0;
            pc_out <= 0;
            adder1_out <= 0;
        end
        else if (flush) begin
            wb_out <= 0;
            mem_out <= 0;
            ex_out <= 0;
            readData1_out <= 0;
            readData2_out <= 0;
            imm_out <= 0;
            func3_out <= 0;
            rs1_out <= 0;
            rs2_out <= 0;
            rd_out <= 0;
            pc_out <= 0;
            adder1_out <= 0;
        end
        else begin
            wb_out <= wb_in;
            mem_out <= mem_in;
            ex_out <= ex_in;
            readData1_out <= readData1_in;
            readData2_out <= readData2_in;
            imm_out <= imm_in;
            func3_out <= func3_in;
            rs1_out <= rs1_in;
            rs2_out <= rs2_in;
            rd_out <= rd_in;
            pc_out <= pc_in;
            adder1_out <= adder1_in;
        end
    end
    
endmodule