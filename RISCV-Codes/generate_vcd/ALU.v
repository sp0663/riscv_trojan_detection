module ALU (
    input [3:0] ALUCtl,
    input [31:0] A,B,
    output reg [31:0] ALUOut,
    output zero
);
    // ALU has two operand, it execute different operator based on ALUctl wire 
    // output zero is for determining taking branch or not 
    
    // Output assignment based on ALUCtl
    always @(*) begin
        case (ALUCtl)
            4'b0000: ALUOut = A & B; // AND
            4'b0001: ALUOut = A | B;  // OR
            4'b0010: ALUOut = A + B;   // ADD
            4'b0110: ALUOut = A - B;   // SUB
            4'b0011: ALUOut = A ^ B;   // XOR
            4'b0100: ALUOut = A << B[4:0];   // SLL
            4'b0101: ALUOut = A >> B[4:0];   // SRL
            4'b0111: ALUOut = $signed(A) >>> B[4:0];   // SRA
            4'b1000: ALUOut = ($signed(A) < $signed(B)) ? 32'b1 : 32'b0;   // SLT, SLTI
            4'b1001: ALUOut = (A < B) ? 32'b1 : 32'b0;   // SLTU, SLTUI
            default: ALUOut = 32'b0;   // Default case
        endcase
    end

    assign zero = (ALUOut == 32'b0) ? 1'b1 : 1'b0;
    
endmodule
