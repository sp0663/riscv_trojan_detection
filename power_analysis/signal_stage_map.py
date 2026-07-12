# Maps signal name substrings to pipeline stages and structural regions

STAGE_MAP = [
    # (substring_to_match, stage, region)
    # IF stage 
    ("m_PC",              "IF", "PC"),
    ("m_InstructionMem",  "IF", "InstrMem"),
    ("m_Adder_1",         "IF", "PC_Adder"),
    ("adder1_out",        "IF", "PC_Adder"),
    ("m_IF_IDRegister",   "IF", "IF_ID_Reg"),
    ("inst_ifid",         "IF", "IF_ID_Reg"),
    ("pc_ifid",           "IF", "IF_ID_Reg"),

    # ID stage 
    ("m_Control",         "ID", "Control"),
    ("m_ImmGen",          "ID", "ImmGen"),
    ("m_Register",        "ID", "RegFile"),
    ("readData",          "ID", "RegFile"),
    ("writeData",         "ID", "RegFile"),
    ("m_ID_EXRegister",   "ID", "ID_EX_Reg"),
    ("idex",              "ID", "ID_EX_Reg"),
    ("imm_idex",          "ID", "ID_EX_Reg"),

    # EX stage 
    ("m_ALU",             "EX", "ALU"),
    ("ALUOut",            "EX", "ALU"),
    ("ALUCtl",            "EX", "ALU"),
    ("m_ALUCtrl",         "EX", "ALUCtrl"),
    ("m_Adder_2",         "EX", "Branch_Adder"),
    ("adder2",            "EX", "Branch_Adder"),
    ("m_forwarding",      "EX", "Forwarding"),
    ("forward",           "EX", "Forwarding"),
    ("m_Mux_ALU",         "EX", "ALU_Mux"),
    ("m_Mux_Forward",     "EX", "ALU_Mux"),
    ("alu_operand",       "EX", "ALU_Mux"),
    ("m_ShiftLeftOne",    "EX", "Branch_Adder"),
    ("m_hazard",          "EX", "Hazard"),
    ("stall",             "EX", "Hazard"),
    ("trojan",            "EX", "Trojan"),   # seq trojan signals
    ("m_EX_MEMRegister",  "EX", "EX_MEM_Reg"),
    ("exmem",             "MEM","EX_MEM_Reg"),
    ("pc_exmem",          "MEM","EX_MEM_Reg"),

    # MEM stage 
    ("m_DataMemory",      "MEM","DataMem"),
    ("m_BranchControl",   "MEM","BranchCtrl"),
    ("PC_sel",            "MEM","BranchCtrl"),
    ("m_Mux_PC",          "MEM","BranchCtrl"),
    ("m_MEM_WBRegister",  "MEM","MEM_WB_Reg"),
    ("memwb",             "WB", "MEM_WB_Reg"),

    # WB stage 
    ("m_Mux_WB",          "WB", "WB_Mux"),
    ("write_data_sel",    "WB", "WB_Mux"),
]

STAGE_ORDER  = ["IF", "ID", "EX", "MEM", "WB"]
DESIGN_ORDER = ["clean", "comb", "seq", "ctrl"]
DESIGN_COLORS = {
    "clean": "#2E7D32",
    "comb" : "#C62828",
    "seq"  : "#E65100",
    "ctrl" : "#6A1B9A",
}
def get_stage_region(signal_name: str):
    """
    Return (stage, region) for a signal name.
    Falls back to ("OTHER", "Other") if no match found.
    """
    name_lower = signal_name.lower()
    for substring, stage, region in STAGE_MAP:
        if substring.lower() in name_lower:
            return stage, region
    return "OTHER", "Other"
