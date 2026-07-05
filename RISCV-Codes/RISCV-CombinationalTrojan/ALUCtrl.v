module ALUCtrl (
    input [1:0] ALUOp,
    input funct7,         // bit 5 of the R-type funct7
    input [2:0] funct3,
    output reg [3:0] ALUCtl
);

    always @(*) begin
        casez ({ALUOp, funct7, funct3})
            // ALUOp 00: Load/Store
            6'b00_?_???: ALUCtl = 4'b0010; 
            
            // ALUOp 01: Branches
            // For beq/bne (funct3 000/001), we need subtraction to check Zero
            6'b01_?_000: ALUCtl = 4'b0110; 
            6'b01_?_001: ALUCtl = 4'b0110; 
            
            // For blt/bge (funct3 100/101), we need SLT to check magnitude
            6'b01_?_100: ALUCtl = 4'b1000; 
            6'b01_?_101: ALUCtl = 4'b1000; // Using SLT. If A < B, result=1 (Zero=0). If A >= B, result=0 (Zero=1).

            // ALUOp 10: R-type
            6'b10_0_000: ALUCtl = 4'b0010; // add
            6'b10_1_000: ALUCtl = 4'b0110; // sub
            6'b10_0_111: ALUCtl = 4'b0000; // and
            6'b10_0_110: ALUCtl = 4'b0001; // or
            6'b10_0_100: ALUCtl = 4'b0011; // xor
            6'b10_0_010: ALUCtl = 4'b1000; // slt
            6'b10_0_011: ALUCtl = 4'b1001; // sltu
            
            // ALUOp 11: I-type 
            6'b11_?_000: ALUCtl = 4'b0010; // addi / jalr (Combined because pattern is same)
            6'b11_?_111: ALUCtl = 4'b0000; // andi
            6'b11_?_110: ALUCtl = 4'b0001; // ori
            6'b11_?_100: ALUCtl = 4'b0011; // xori
            6'b11_?_010: ALUCtl = 4'b1000; // slti
            6'b11_?_011: ALUCtl = 4'b1001; // sltiu

            // Shifts 
           
            6'b1?_0_001: ALUCtl = 4'b0100; // slli, sll
            6'b1?_0_101: ALUCtl = 4'b0101; // srli, srl
            6'b1?_1_101: ALUCtl = 4'b0111; // srai, sra

            default:     ALUCtl = 4'b0000; 
        endcase
    end

endmodule