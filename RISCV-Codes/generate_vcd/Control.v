module Control (
    input [6:0] opcode,
    output  memRead,
    output branch,
    output jump,
    output jalr,
    output  [1:0] write_data_sel,
    output  [1:0] ALUOp,
    output  memWrite,
    output  ALUSrc,
    output  regWrite
    );

    wire memtoReg;    

    reg [6:0] control_out;  // memRead, memtoReg, ALUOp, memWrite, ALUSrc, regWrite

    always @(*) begin
        casez (opcode)
            7'b0000011: control_out = 7'b1_1_00_0_1_1;    // lw
            7'b0100011: control_out = 7'b0_0_00_1_1_0;    // sw
            7'b1100011: control_out = 7'b0_0_01_0_0_0;    // beq, bne, blt, bge
            7'b0010011: control_out = 7'b0_0_11_0_1_1;    // I type alu
            7'b0110011: control_out = 7'b0_0_10_0_0_1;    // R type alu
            7'b1101111: control_out = 7'b0_0_11_0_0_1;    // jal
            7'b1100111: control_out = 7'b0_0_11_0_1_1;    // jalr
            default: control_out = 7'b0;
        endcase
    end
    assign {memRead, memtoReg, ALUOp, memWrite, ALUSrc, regWrite} = control_out;
    assign write_data_sel = {jump, memtoReg};
    assign branch = (opcode == 7'b1100011);
    assign jump = (opcode == 7'b1101111) || (opcode == 7'b1100111);
    assign jalr = (opcode == 7'b1100111);
    

endmodule




