
module hazard_detection_unit (
    // ID stage (used for load-use stall detection)
    input [4:0] id_rs1,
    input [4:0] id_rs2,

    // EX stage (used for forwarding selection)
    input [4:0] ex_rs1,
    input [4:0] ex_rs2,

    // ID/EX stage for load-use hazards
    input [4:0] idex_rd,
    input idex_memRead,

    // EX/MEM stage
    input [4:0] exmem_rd,
    input exmem_regWrite,
    input exmem_memRead,

    // MEM/WB stage
    input [4:0] memwb_rd,
    input memwb_regWrite,

    
    // Forward control:
    // 00 = no forwarding
    // 01 = forward from EX/MEM stage 
    // 10 = forward from MEM/WB stage 
    // 11 = reserved
    output reg [1:0] forward_rs1,
    output reg [1:0] forward_rs2,
    
    output reg stall
    // 1 = stall (insert bubble), 0 = normal operation
);

    // Load result is not available in EX/MEM ALU result path, so don't forward from EX/MEM for loads.
    wire exmem_can_forward = exmem_regWrite && (~exmem_memRead);
    
    always @(*) begin
        forward_rs1 = 2'b00;
        forward_rs2 = 2'b00;
        stall = 1'b0;
        
        // Forward from EX stage (only if MEM doesn't match)
        if (exmem_can_forward && (exmem_rd == ex_rs1) && (exmem_rd != 5'b0)) begin
            forward_rs1 = 2'b01; 
        end
        // Forward from MEM stage 
        else if (memwb_regWrite && (memwb_rd == ex_rs1) && (memwb_rd != 5'b0)) begin
            forward_rs1 = 2'b10;  
        end

        // same for rs2
        if (exmem_can_forward && (exmem_rd == ex_rs2) && (exmem_rd != 5'b0)) begin
            forward_rs2 = 2'b01;
        end
        else if (memwb_regWrite && (memwb_rd == ex_rs2) && (memwb_rd != 5'b0)) begin
            forward_rs2 = 2'b10;
        end
        
        // load-use hazard detection:
        if(idex_memRead &&
            ((id_rs1 == idex_rd && idex_rd != 5'b0) ||
             (id_rs2 == idex_rd && idex_rd != 5'b0))) begin
            stall = 1'b1;       
            forward_rs1 = 2'b00;
            forward_rs2 = 2'b00;
        end
    end

endmodule
