#!/usr/bin/env python3
"""
dat_generator.py — Random RISC-V .dat file generator for Trojan detection
═══════════════════════════════════════════════════════════════════════════
Reads the fixed structured prefix (already in TEST_INSTRUCTIONS.dat),
appends N random instructions to fill 512 bytes (128 instructions total),
then writes the result back to TEST_INSTRUCTIONS.dat.

Usage:
    python dat_generator.py                  # seed=0, default output
    python dat_generator.py --seed 42        # specific seed
    python dat_generator.py --seed 42 --out run_042.dat
    python dat_generator.py --batch 100      # generate 100 files: run_000.dat ... run_099.dat

Instruction memory layout (512 bytes):
    [0   .. 87 ]  22 structured instructions (fixed prefix, always included)
    [88  .. 511]  106 random instructions    (vary per seed)
"""

import argparse
import os
import random
import sys

# ── Constants ─────────────────────────────────────────────────────────────
MEM_BYTES        = 512          # expanded InstructionMemory size
INSTR_BYTES      = 4
MAX_INSTRUCTIONS = MEM_BYTES // INSTR_BYTES   # 128
PREFIX_FILE      = "TEST_INSTRUCTIONS.dat"    # existing structured prefix

# Registers to use in random section (avoid x0, keep x1/x2 = 0xFFFFFFFF)
RAND_REGS  = list(range(1, 16))   # x1 .. x15 (x1,x2 already set to 0xFFFFFFFF)
SAFE_REGS  = list(range(3, 16))   # x3 .. x15 (don't overwrite Trojan operands)

# ── RISC-V encoders ───────────────────────────────────────────────────────
def r_type(rd, rs1, rs2, funct3, funct7=0):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | 0x33

def i_type(rd, rs1, imm, funct3, opcode=0x13):
    imm12 = imm & 0xFFF
    return (imm12 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def s_type(rs1, rs2, imm, funct3):
    imm  = imm & 0xFFF
    imm_11_5 = (imm >> 5) & 0x7F
    imm_4_0  = imm & 0x1F
    return (imm_11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm_4_0 << 7) | 0x23

def nop():
    return i_type(0, 0, 0, 0)   # addi x0, x0, 0

# ── Instruction factories ─────────────────────────────────────────────────
def instr_add(rd, rs1, rs2):  return r_type(rd, rs1, rs2, 0b000, 0b0000000)
def instr_sub(rd, rs1, rs2):  return r_type(rd, rs1, rs2, 0b000, 0b0100000)
def instr_and(rd, rs1, rs2):  return r_type(rd, rs1, rs2, 0b111, 0b0000000)
def instr_or (rd, rs1, rs2):  return r_type(rd, rs1, rs2, 0b110, 0b0000000)
def instr_xor(rd, rs1, rs2):  return r_type(rd, rs1, rs2, 0b100, 0b0000000)
def instr_slt(rd, rs1, rs2):  return r_type(rd, rs1, rs2, 0b010, 0b0000000)

def instr_addi(rd, rs1, imm): return i_type(rd, rs1, imm, 0b000)
def instr_andi(rd, rs1, imm): return i_type(rd, rs1, imm, 0b111)
def instr_ori (rd, rs1, imm): return i_type(rd, rs1, imm, 0b110)
def instr_xori(rd, rs1, imm): return i_type(rd, rs1, imm, 0b100)

def instr_lw(rd, rs1, imm):   return i_type(rd, rs1, imm, 0b010, 0x03)
def instr_sw(rs1, rs2, imm):  return s_type(rs1, rs2, imm, 0b010)

# ── Conversion helpers ────────────────────────────────────────────────────
def instr_to_bytes_be(instr):
    """Convert 32-bit instruction to 4 big-endian bytes."""
    return [
        (instr >> 24) & 0xFF,
        (instr >> 16) & 0xFF,
        (instr >>  8) & 0xFF,
        (instr >>  0) & 0xFF,
    ]

def byte_to_binstr(b):
    return format(b, '08b')

# ── Structured prefix loader ──────────────────────────────────────────────
def load_prefix(path):
    """Read existing .dat file, return list of binary strings (one per byte)."""
    if not os.path.exists(path):
        sys.exit(f"ERROR: prefix file '{path}' not found.\n"
                 f"Run from the directory containing TEST_INSTRUCTIONS.dat")
    with open(path) as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    # Validate: must be binary strings
    for i, ln in enumerate(lines):
        if not all(c in '01' for c in ln) or len(ln) != 8:
            sys.exit(f"ERROR: line {i+1} in prefix is not an 8-bit binary string: '{ln}'")
    return lines

# ── Random instruction generator ─────────────────────────────────────────
def generate_random_instructions(rng, n_slots):
    """
    Generate n_slots random instructions.
    Mix of:
      70%  — general R-type / I-type ops    (vary the toggle pattern)
      10%  — combinational Trojan trigger   (AND x_,x1,x2 → A=B=0xFFFFFFFF)
      10%  — control Trojan trigger         (produce x10, then use x10 in RAW)
      10%  — load/store to safe address 0

    No branches generated (safe: no risk of jumping to uninitialized memory).
    """
    instructions = []

    # R-type pool
    r_ops = [instr_add, instr_sub, instr_and, instr_or, instr_xor, instr_slt]
    # I-type pool
    i_ops = [instr_addi, instr_andi, instr_ori, instr_xori]

    i = 0
    while i < n_slots:
        roll = rng.random()

        # ── Combinational Trojan trigger (needs 1 instruction, uses 1 slot)
        if roll < 0.10 and i < n_slots:
            # AND x_dest, x1, x2  →  A=x1=0xFFFF, B=x2=0xFFFF → trigger!
            rd = rng.choice(SAFE_REGS)
            instructions.append(instr_and(rd, 1, 2))
            i += 1

        # ── Control Trojan trigger (needs 2 consecutive instructions)
        elif roll < 0.20 and i + 1 < n_slots:
            # Instruction 1: produce x10
            rs_a = rng.choice(RAND_REGS)
            rs_b = rng.choice(RAND_REGS)
            instructions.append(instr_add(10, rs_a, rs_b))   # x10 = rs_a + rs_b
            i += 1
            # Instruction 2: immediately consume x10 (1-cycle RAW → Trojan fires)
            rd2  = rng.choice(SAFE_REGS)
            rs_c = rng.choice(RAND_REGS)
            instructions.append(instr_add(rd2, 10, rs_c))    # rd2 = x10 + rs_c
            i += 1

        # ── Load / store to address 0 (safe, also counts as ADD-type for seq Trojan)
        elif roll < 0.30 and i < n_slots:
            if rng.random() < 0.5:
                rd = rng.choice(SAFE_REGS)
                instructions.append(instr_lw(rd, 0, 0))      # lw rd, 0(x0)
            else:
                rs2 = rng.choice(RAND_REGS)
                instructions.append(instr_sw(0, rs2, 0))     # sw rs2, 0(x0)
            i += 1

        # ── General R-type
        elif roll < 0.65 and i < n_slots:
            op   = rng.choice(r_ops)
            rd   = rng.choice(SAFE_REGS)
            rs1  = rng.choice(RAND_REGS)
            rs2  = rng.choice(RAND_REGS)
            instructions.append(op(rd, rs1, rs2))
            i += 1

        # ── General I-type
        else:
            op   = rng.choice(i_ops)
            rd   = rng.choice(SAFE_REGS)
            rs1  = rng.choice(RAND_REGS)
            imm  = rng.randint(-512, 511)
            instructions.append(op(rd, rs1, imm))
            i += 1

    return instructions

# ── File writer ───────────────────────────────────────────────────────────
def write_dat(path, prefix_lines, random_instrs):
    """Combine prefix + random instructions, pad to MEM_BYTES, write .dat."""
    # Convert random instructions to binary strings
    rand_lines = []
    for instr in random_instrs:
        for b in instr_to_bytes_be(instr):
            rand_lines.append(byte_to_binstr(b))

    # Pad remainder with NOPs if needed
    total_lines = len(prefix_lines) + len(rand_lines)
    pad_bytes   = MEM_BYTES - total_lines
    if pad_bytes < 0:
        sys.exit(f"ERROR: prefix ({len(prefix_lines)} bytes) + random "
                 f"({len(rand_lines)} bytes) exceeds {MEM_BYTES} bytes")
    nop_lines = [byte_to_binstr(b) for b in instr_to_bytes_be(nop())] * (pad_bytes // 4)

    all_lines = prefix_lines + rand_lines + nop_lines

    with open(path, 'w') as f:
        f.write('\n'.join(all_lines) + '\n')

    n_rand_instrs = len(rand_lines) // 4
    n_total       = len(all_lines)  // 4
    print(f"  wrote {path}  "
          f"[{len(prefix_lines)//4} structured + {n_rand_instrs} random + "
          f"{len(nop_lines)//4} NOPs = {n_total} instructions]")

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="RISC-V .dat generator for Trojan detection")
    parser.add_argument('--seed',    type=int, default=0,
                        help='Random seed (default: 0)')
    parser.add_argument('--out',     type=str, default=None,
                        help='Output filename (default: TEST_INSTRUCTIONS.dat)')
    parser.add_argument('--batch',   type=int, default=None,
                        help='Generate N files: run_000.dat .. run_N-1.dat')
    parser.add_argument('--prefix',  type=str, default=PREFIX_FILE,
                        help=f'Structured prefix file (default: {PREFIX_FILE})')
    args = parser.parse_args()

    prefix = load_prefix(args.prefix)
    prefix_bytes = len(prefix)
    if prefix_bytes % 4 != 0:
        sys.exit(f"ERROR: prefix has {prefix_bytes} bytes — not a multiple of 4")

    prefix_instrs = prefix_bytes // 4
    rand_slots    = MAX_INSTRUCTIONS - prefix_instrs
    print(f"Prefix: {prefix_instrs} instructions ({prefix_bytes} bytes)")
    print(f"Random: {rand_slots} instruction slots available")
    print()

    if args.batch:
        # ── Batch mode: generate N separate files ──────────────────────
        os.makedirs("dat_runs", exist_ok=True)
        for i in range(args.batch):
            seed = args.seed + i
            rng  = random.Random(seed)
            instrs = generate_random_instructions(rng, rand_slots)
            out_path = os.path.join("dat_runs", f"run_{i:03d}.dat")
            write_dat(out_path, prefix, instrs)
        print(f"\nBatch complete: {args.batch} files in ./dat_runs/")
    else:
        # ── Single file mode ───────────────────────────────────────────
        rng      = random.Random(args.seed)
        instrs   = generate_random_instructions(rng, rand_slots)
        out_path = args.out if args.out else PREFIX_FILE
        write_dat(out_path, prefix, instrs)

if __name__ == "__main__":
    main()
