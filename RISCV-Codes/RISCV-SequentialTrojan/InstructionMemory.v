module InstructionMemory (
    input [31:0] readAddr,
    output [31:0] inst
);
    
    // Do not modify this file!

    reg [7:0] insts [511:0];
    
    assign inst = (readAddr >= 512) ? 32'b0 : {insts[readAddr], insts[readAddr + 1], insts[readAddr + 2], insts[readAddr + 3]};

    initial begin
        integer i;
        for (i = 0; i < 512; i = i + 1)
            insts[i] = 8'h00;
        $readmemb("TEST_INSTRUCTIONS.dat", insts);
    end

endmodule