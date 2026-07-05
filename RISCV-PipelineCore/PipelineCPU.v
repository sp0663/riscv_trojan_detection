module PipelineCPU (
    input clk,
    input start
    
);

    // When input start is zero, cpu should reset
    // When input start is high, cpu start running

    // Wires for connecting modules
    wire [31:0] pc_o;   
    wire [31:0] pc_i;    
    wire [31:0] adder1_out; 
    wire [31:0] inst;   
    wire  branch;
    wire jump;
    wire jalr;       
    wire  memRead;
    wire  [1:0] ALUOp;
    wire  memWrite;
    wire  ALUSrc;
    wire [31:0] readData1;
    wire [31:0] readData2;
    wire [31:0] imm;
    wire [31:0] imm_shifted;
    wire [31:0] adder2_out;
    wire [31:0] alu_b;
    wire [31:0] ALUOut;
    wire [31:0] readData;
    wire [31:0] writeData;
    wire [3:0] ALUCtl;
    wire zero;
    wire [1:0] write_data_sel;
    wire [1:0] PC_sel;
    wire regWrite;
    wire [2:0] wb_idex_out;
    wire [4:0] mem_idex_out;
    wire [2:0] ex_idex_out;
    wire [2:0] wb_exmem_out;
    wire [4:0] mem_exmem_out;
    wire [2:0] wb_memwb_out;
    wire [31:0] pc_ifid_out;
    wire [31:0] inst_ifid_out;
    wire [31:0] adder1_ifid_out;
    wire [31:0] readData1_idex_out;
    wire [31:0] readData2_idex_out;
    wire [31:0] adder1_idex_out;
    wire [31:0] imm_idex_out;
    wire [3:0] func3_idex_out;
    wire [4:0] rd_idex_out;
    wire [31:0] pc_idex_out;
    wire [31:0] ALUOut_exmem_out;
    wire [31:0] readData2_exmem_out;
    wire [31:0] adder1_exmem_out;
    wire [4:0] rd_exmem_out;
    wire [3:0] func3_exmem_out;
    wire zero_exmem_out;
    wire [31:0] pc_exmem_out;
    wire [31:0] memReadData_memwb_out;
    wire [31:0] adder1_memwb_out;
    wire [31:0] ALUResult_memwb_out;
    wire [4:0] rd_memwb_out;
    wire [4:0] rs1_idex_out;
    wire [4:0] rs2_idex_out;

    // Hazard detection and forwarding signals
    wire [1:0] forward_rs1;              // Forward control for rs1
    wire [1:0] forward_rs2;              // Forward control for rs2
    wire stall_signal;                   // Stall request (for future use)
    wire [31:0] alu_operand1_forwarded;  // Forwarded rs1 to ALU
    wire [31:0] alu_operand2_forwarded;  // Forwarded rs2 to ALU
    wire [31:0] readData1_id_bypass;
    wire [31:0] readData2_id_bypass;

    PC m_PC(
        .clk(clk),
        .rst(start),
        .enable(~stall_signal),
        .pc_i(pc_i),
        .pc_o(pc_o)
    );

    Adder m_Adder_1(
        .a(pc_o),
        .b(32'd4),
        .sum(adder1_out)
    );

    InstructionMemory m_InstMem(
        .readAddr(pc_o),
        .inst(inst)
    );

    Control m_Control(
        .opcode(inst_ifid_out[6:0]),
        .branch(branch),
        .jump(jump),
        .jalr(jalr),
        .memRead(memRead),
        .write_data_sel(write_data_sel),
        .ALUOp(ALUOp),
        .memWrite(memWrite),
        .ALUSrc(ALUSrc),
        .regWrite(regWrite)
    );

    BranchControl m_BranchControl(
        .func3(func3_exmem_out[2:0]),
        .zero(zero_exmem_out),
        .branch(mem_exmem_out[4]),
        .jump(mem_exmem_out[3]),
        .jalr(mem_exmem_out[2]),
        .PC_sel(PC_sel)
    );

    hazard_detection_unit m_hazard_unit (
        // ID stage (for load-use stalling)
        .id_rs1(inst_ifid_out[19:15]),
        .id_rs2(inst_ifid_out[24:20]),

        // EX stage (for forwarding)
        .ex_rs1(rs1_idex_out),
        .ex_rs2(rs2_idex_out),

        // ID/EX stage metadata
        .idex_rd(rd_idex_out),
        .idex_memRead(mem_idex_out[1]),

        // EX/MEM stage metadata
        .exmem_rd(rd_exmem_out),
        .exmem_regWrite(wb_exmem_out[2]),
        .exmem_memRead(mem_exmem_out[1]),

        // MEM/WB stage metadata
        .memwb_rd(rd_memwb_out),
        .memwb_regWrite(wb_memwb_out[2]),
        
        // Outputs
        .forward_rs1(forward_rs1),
        .forward_rs2(forward_rs2),
        .stall(stall_signal)
    );

    Register m_Register(
        .clk(clk),
        .rst(start),
        .regWrite(wb_memwb_out[2]),
        .readReg1(inst_ifid_out[19:15]),
        .readReg2(inst_ifid_out[24:20]),
        .writeReg(rd_memwb_out),
        .writeData(writeData),
        .readData1(readData1),
        .readData2(readData2)
    );

    // Register file writes happen on clock edge; bypass WB data to ID to avoid same-cycle RAW hazards
    assign readData1_id_bypass = (wb_memwb_out[2] && (rd_memwb_out != 5'b0) && (rd_memwb_out == inst_ifid_out[19:15])) ? writeData : readData1;
    assign readData2_id_bypass = (wb_memwb_out[2] && (rd_memwb_out != 5'b0) && (rd_memwb_out == inst_ifid_out[24:20])) ? writeData : readData2;

    ImmGen #(.Width(32)) m_ImmGen(
        .inst(inst_ifid_out),
        .imm(imm)
    );

    ShiftLeftOne m_ShiftLeftOne(
        .i(imm_idex_out),
        .o(imm_shifted)
    );

    Adder m_Adder_2(
        .a(pc_idex_out),
        .b(imm_shifted),
        .sum(adder2_out)
    );

    Mux3to1 #(.size(32)) m_Mux_PC(
        .sel(PC_sel),
        .s0(pc_exmem_out),
        .s1(adder1_out),
        .s2(ALUOut_exmem_out),
        .out(pc_i)
    );

    Mux2to1 #(.size(32)) m_Mux_ALU(
        .sel(ex_idex_out[0]),
        .s0(readData2_idex_out),
        .s1(imm_idex_out),
        .out(alu_b)
    );

    // Forwarding mux for rs1 (ALU operand A)
    forwarding_mux m_forward_rs1 (
        .forward_control(forward_rs1),
        .reg_file_data(readData1_idex_out),
        .ex_mem_alu_result(ALUOut_exmem_out),
        .mem_wb_write_data(writeData),
        .alu_operand(alu_operand1_forwarded)
    );

    // Forwarding mux for rs2 path (also used as store write data path)
    forwarding_mux m_forward_rs2 (
        .forward_control(forward_rs2),
        .reg_file_data(readData2_idex_out),
        .ex_mem_alu_result(ALUOut_exmem_out),
        .mem_wb_write_data(writeData),
        .alu_operand(alu_operand2_forwarded)
    );

    // Final ALU input B: select between forwarded register and immediate
    wire [31:0] alu_b_final = ex_idex_out[0] ? imm_idex_out : alu_operand2_forwarded;

    ALUCtrl m_ALUCtrl(
        .ALUOp(ex_idex_out[2:1]),
        .funct7(func3_idex_out[3]),
        .funct3(func3_idex_out[2:0]),
        .ALUCtl(ALUCtl)
    );

    ALU m_ALU(
        .ALUCtl(ALUCtl),
        .A(alu_operand1_forwarded),
        .B(alu_b_final),
        .ALUOut(ALUOut),
        .zero(zero)
    );

    DataMemory m_DataMemory(
        .rst(start),
        .clk(clk),
        .memWrite(mem_exmem_out[0]),
        .memRead(mem_exmem_out[1]),
        .address(ALUOut_exmem_out),
        .writeData(readData2_exmem_out),
        .readData(readData)
    );

    Mux3to1 #(.size(32)) m_Mux_WriteData(
        .sel(wb_memwb_out[1:0]),
        .s0(ALUResult_memwb_out),
        .s1(memReadData_memwb_out),
        .s2(adder1_memwb_out),
        .out(writeData)
    );

    IF_IDRegister m_IF_IDRegister(
        .clk(clk),
        .rst(start),
        .enable(~stall_signal),
        .pc_in(pc_o),
        .instr_in(inst),
        .adder1_in(adder1_out),
        .pc_out(pc_ifid_out),
        .instr_out(inst_ifid_out),
        .adder1_out(adder1_ifid_out)
    );

    ID_EXRegister m_ID_EXRegister(
        .clk(clk),
        .rst(start),
        .flush(stall_signal),
        .wb_in({regWrite, write_data_sel}),
        .mem_in({branch, jump, jalr, memRead, memWrite}),
        .ex_in({ALUOp, ALUSrc}),
        .readData1_in(readData1_id_bypass),
        .readData2_in(readData2_id_bypass),
        .pc_in(pc_ifid_out),
        .imm_in(imm),
        .func3_in({inst_ifid_out[30], inst_ifid_out[14:12]}),
        .rs1_in(inst_ifid_out[19:15]),
        .rs2_in(inst_ifid_out[24:20]),
        .rd_in(inst_ifid_out[11:7]),
        .adder1_in(adder1_ifid_out),
        .wb_out(wb_idex_out),
        .mem_out(mem_idex_out),
        .ex_out(ex_idex_out),
        .readData1_out(readData1_idex_out),
        .readData2_out(readData2_idex_out),
        .pc_out(pc_idex_out),
        .imm_out(imm_idex_out),
        .func3_out(func3_idex_out),
        .rs1_out(rs1_idex_out),
        .rs2_out(rs2_idex_out),
        .rd_out(rd_idex_out),
        .adder1_out(adder1_idex_out)
    );

    EX_MEMRegister m_EX_MEMRegister(
        .clk(clk),
        .rst(start),
        .wb_in(wb_idex_out),
        .mem_in(mem_idex_out),
        .func3_in(func3_idex_out),
        .ALUResult_in(ALUOut),
        .adder1_in(adder1_idex_out),
        .readData2_in(alu_operand2_forwarded),
        .rd_in(rd_idex_out),
        .zero_in(zero),
        .pc_in(adder2_out),
        .wb_out(wb_exmem_out),
        .mem_out(mem_exmem_out),
        .ALUResult_out(ALUOut_exmem_out),
        .readData2_out(readData2_exmem_out),
        .rd_out(rd_exmem_out),
        .zero_out(zero_exmem_out),
        .func3_out(func3_exmem_out),
        .pc_out(pc_exmem_out),
        .adder1_out(adder1_exmem_out)
    );

    MEM_WBRegister m_MEM_WBRegister(
        .clk(clk),
        .rst(start),
        .wb_in(wb_exmem_out),
        .adder1_in(adder1_exmem_out),
        .memReadData_in(readData),
        .ALUResult_in(ALUOut_exmem_out),
        .rd_in(rd_exmem_out),
        .wb_out(wb_memwb_out),
        .memReadData_out(memReadData_memwb_out),
        .ALUResult_out(ALUResult_memwb_out),
        .rd_out(rd_memwb_out),
        .adder1_out(adder1_memwb_out)
    );

endmodule
