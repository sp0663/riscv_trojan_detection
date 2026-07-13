# Hardware Trojan Detection in a 5-Stage RISC-V Pipeline

Detection of hardware Trojans using formal equivalence checking and power proxy side-channel analysis on a 32-bit RISC-V RV32I pipeline.

---

## Overview

Three classes of hardware Trojans are inserted into a 5-stage RISC-V pipeline (IF/ID/EX/MEM/WB) and detected using two complementary methods:

| Trojan | Location | Trigger | Detected By |
|--------|----------|---------|-------------|
| Combinational | ALU | A=B=0xFFFFFFFF, op=AND | Formal equivalence |
| Sequential | ALU | Every 50th ADD instruction | Power proxy |
| Control-path | Hazard unit | EX/MEM destination = x10, 1-cycle RAW on rs1 | Both |

---

## Requirements

- [Icarus Verilog](http://iverilog.icarus.com/) — simulation
- [Yosys](https://yosyshq.net/yosys/) 0.66+ — formal checking and synthesis
- Python 3.8+ with `numpy`, `matplotlib`
- [NanGate 45nm Open Cell Library](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts) — for synthesis

---

## Usage

### 1. Generate instruction memory
```bash
python scripts/dat_generator.py --seed 0
```

### 2. Compile and simulate all 4 designs
```bash
iverilog -o sim_all testbench.v PipelineCPU.v ALU.v ALU_comb.v ALU_seq.v \
    hazard_detection_unit.v hazard_trojan_ctrl.v \
    PipelineCPU_trojan_comb.v PipelineCPU_trojan_seq.v PipelineCPU_trojan_ctrl.v \
    [all other .v files]
vvp sim_all
```

### 3. Formal equivalence checking
```bash
yosys -s script_comb.ys > comb_result.txt
yosys -s script_ctrl.ys > ctrl_result.txt
```

### 4. Synthesize clean pipeline
```bash
yosys -s synth_clean.ys
```

### 5. Run power proxy analysis
```bash
python power_proxy.py
```
Outputs `deviation.png` and `summary.txt`.

---

## Results Summary

**Formal Equivalence Checking**
- Combinational Trojan: `FAIL` — counterexample: `ALUCtl=AND, A=0xFFFFFFFF, B=0xFFFFFFFF`
- Control-path Trojan: `FAIL` — counterexample: `exmem_rd=x10, exmem_regWrite=1, ex_rs1=x10`
- Sequential Trojan: not applicable (clean is combinational, Trojan is sequential — class mismatch)

**Power Proxy Analysis**
- Combinational Trojan: not detected (−0.0% total, single-shot trigger)
- Sequential Trojan: detected (+4.7% total, +6.4% ID stage)
- Control-path Trojan: detected (+1.2% total, +7.0% MEM, +5.1% WB)

---

## Notes

- The sequential Trojan (`ALU_seq.v`) adds `clk` and `rst` ports to the ALU interface. `PipelineCPU_trojan_seq.v` passes these from the top-level ports.
- Synthesis uses a modified `PipelineCPU_synth.v` with dummy output ports to prevent dead-code elimination.
- Fan-out weights for power proxy are derived from the clean netlist only and applied to all designs.

---

## Collaborators
- Shresh Parti
- SriPrahlad Mukunthan
- Vamshikrishna V Bidari
