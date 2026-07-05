module BranchControl (
    input [2:0] func3,
    input zero,
    input branch,
    input jump,
    input jalr,
    output [1:0] PC_sel
);
    reg branch_taken;
    
    always @(*) begin
        case(func3)
            3'b000: branch_taken = zero;       // beq (ALUOut == 0)
            3'b001: branch_taken = ~zero;      // bne (ALUOut != 0)
            3'b100: branch_taken = ~zero;      // blt (SLT result is 1 -> ALUOut=1!=0)
            3'b101: branch_taken = zero;       // bge (SLT result is 0 -> ALUOut=0==0)
            default: branch_taken = 1'b0;
        endcase
    end

    assign PC_sel = {jalr, ~((branch & branch_taken) || jump)};
  

endmodule