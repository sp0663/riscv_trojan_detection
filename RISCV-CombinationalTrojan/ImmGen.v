module ImmGen#(parameter Width = 32) (
    input [Width-1:0] inst,
    output reg signed [Width-1:0] imm
);
    // ImmGen generate imm value based on opcode
    wire [2:0] funct3 = inst[14:12];
    wire [6:0] opcode = inst[6:0];
    always @(*) 
    begin
        case(opcode[6:2])
            5'b00100: begin case(funct3)
                            3'b001, 3'b101: imm = {{27{1'b0}}, inst[24:20]};     // Unsigned sign extension for shifting
                            default: imm = {{20{inst[31]}}, inst[31:20]};        // Signed sign extension for other immediate operations
                             endcase
                         end

            5'b00000: imm = {{20{inst[31]}}, inst[31:20]};     //  lw
            5'b01000: imm = {{20{inst[31]}}, inst[31:25], inst[11:7]};      // sw
            5'b11000: imm = {{20{inst[31]}}, inst[31], inst[7], inst[30:25], inst[11:8]};     // beq, bne, blt, bge
            5'b11011: imm = {{11{inst[31]}}, inst[31], inst[19:12], inst[20], inst[30:21]};     // jal
            5'b11001: imm = {{20{inst[31]}}, inst[31:20]};     // jalr
            default: imm = 32'b0;
	    endcase
    end          
endmodule

