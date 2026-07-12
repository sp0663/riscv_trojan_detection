"""
vcd_parser.py — VCD parser for RISC-V Trojan side-channel analysis

Parses all_designs.vcd (produced by iverilog/vvp) and returns a
structured dictionary consumed by every downstream analysis method.

Output structure:
    {
      "clean": {
          "m_ALU.ALUOut": {
              "width"    : 32,
              "toggles"  : 47,
              "waveform" : [(0, 'x'), (20, 15), (40, 255), ...]
          },
          ...
      },
      "comb":  { ... },
      "seq":   { ... },
      "ctrl":  { ... }
    }

Signal names have the dut_X. instance prefix stripped so that
corresponding signals are directly comparable across designs.

Usage:
    from vcd_parser import parse_vcd
    data = parse_vcd("all_designs.vcd")

    # toggle count for a signal
    data["clean"]["m_ALU.ALUOut"]["toggles"]

    # full waveform
    data["comb"]["m_ALU.ALUOut"]["waveform"]
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

DESIGNS = {
    "dut_clean" : "clean",
    "dut_comb"  : "comb",
    "dut_seq"   : "seq",
    "dut_ctrl"  : "ctrl",
}

def _parse_scalar(val_str):
    if val_str in ('x', 'X', 'z', 'Z'):
        return 'x'
    return int(val_str)

def _parse_vector(val_str, width):
    if 'x' in val_str.lower() or 'z' in val_str.lower():
        return 'x'
    return int(val_str, 2)

def _hamming_weight(a, b, width):
    if a == 'x' or b == 'x':
        return 0
    mask = (1 << width) - 1
    return bin((int(a) ^ int(b)) & mask).count('1')


def parse_vcd(vcd_path: str) -> dict:
    """
    Parse a VCD file and return the analysis dictionary.

    Returns
    dict
        Nested dict:  design - signal_name - {width, toggles, waveform}
        Also includes a top-level "meta" key with timescale info.
    """
    vcd_path = Path(vcd_path)
    if not vcd_path.exists():
        sys.exit(f"ERROR: VCD file not found: {vcd_path}")

    symbol_map  = {}
    scope_stack = []
    timescale   = "unknown"

    with open(vcd_path, 'r') as f:
        content = f.read()

    # Tokenise — VCD is whitespace-delimited
    tokens = iter(content.split())

    token_list = content.split()
    idx = 0

    def peek():
        return token_list[idx] if idx < len(token_list) else None

    def consume():
        nonlocal idx
        t = token_list[idx]
        idx += 1
        return t

    while idx < len(token_list):
        tok = consume()

        if tok == '$timescale':
            ts_parts = []
            while True:
                t = consume()
                if t == '$end':
                    break
                ts_parts.append(t)
            timescale = ' '.join(ts_parts)

        elif tok == '$scope':
            scope_type = consume()   # module / begin / fork / task
            scope_name = consume()
            consume()                # $end
            scope_stack.append(scope_name)

        elif tok == '$upscope':
            consume()                # $end
            if scope_stack:
                scope_stack.pop()

        elif tok == '$var':
            var_type  = consume()    # wire / reg / integer …
            width     = int(consume())
            symbol    = consume()    # e.g. '!' or '"' or multi-char
            var_name  = consume()    # signal name (may have [N:0] suffix)
            # consume optional bit-select and $end
            nxt = consume()
            if nxt != '$end':
                consume()            # skip [N:0] range token, next is $end

            # Build full hierarchical name from scope stack + var name
            # Strip any [N:0] from var_name (already have width)
            clean_name = re.sub(r'\[.*\]', '', var_name)
            full_name  = '.'.join(scope_stack + [clean_name]) if scope_stack else clean_name

            symbol_map[symbol] = {
                'name' : full_name,
                'width': width,
            }

        elif tok == '$enddefinitions':
            consume()   # $end
            break       # header done — move to value changes

    raw_waves   = defaultdict(list)
    current_time = 0

    while idx < len(token_list):
        tok = consume()

        if not tok:
            continue

        # Timestamp
        if tok.startswith('#'):
            current_time = int(tok[1:])

        # Multi-bit vector:  bVALUE SYMBOL
        elif tok.startswith('b') or tok.startswith('B'):
            val_str = tok[1:]
            symbol  = consume()
            if symbol in symbol_map:
                width = symbol_map[symbol]['width']
                value = _parse_vector(val_str, width)
                raw_waves[symbol].append((current_time, value))

        # Real value (not used for toggle counting, skip)
        elif tok.startswith('r') or tok.startswith('R'):
            consume()   # skip symbol

        # Single-bit scalar:  VALUE SYMBOL  (no space in older VCDs)
        # Format: e.g.  '0!'  or  '1"'  or  'x#'
        elif len(tok) >= 2 and tok[0] in ('0', '1', 'x', 'X', 'z', 'Z'):
            val_char = tok[0]
            symbol   = tok[1:]
            if symbol in symbol_map:
                value = _parse_scalar(val_char)
                raw_waves[symbol].append((current_time, value))

        # $dumpvars / $dumpall / $end / $comment — skip
        elif tok.startswith('$'):
            if tok not in ('$end', '$dumpvars', '$dumpall',
                           '$dumpon', '$dumpoff', '$dumpports'):
                # consume until $end
                while idx < len(token_list):
                    t = consume()
                    if t == '$end':
                        break

    result = {d: {} for d in DESIGNS.values()}
    result['meta'] = {'timescale': timescale, 'end_time': current_time}

    for symbol, info in symbol_map.items():
        full_name = info['name']
        width     = info['width']
        waveform  = raw_waves.get(symbol, [])

        # Determine which design this signal belongs to
        design_key  = None
        signal_name = full_name
        for prefix, design in DESIGNS.items():
            # full_name starts with  testbench.dut_clean.xxx  or  dut_clean.xxx
            # strip leading 'testbench.' if present
            stripped = re.sub(r'^testbench\.', '', full_name)
            if stripped.startswith(prefix + '.'):
                design_key  = design
                signal_name = stripped[len(prefix) + 1:]  # remove "dut_X."
                break

        if design_key is None:
            # Signal belongs to testbench level (clk, start) — skip
            continue

        # Toggle count = number of value-change events (each entry is one toggle)
        toggles = len(waveform)
        # Strictly: the first entry (time=0) is initialisation, not a toggle.
        # Subtract 1 if waveform is non-empty so we count actual transitions.
        if toggles > 0:
            toggles -= 1

        # Hamming-weighted toggle count (for method-5 power proxy)
        hamming_total = 0
        for i in range(1, len(waveform)):
            hamming_total += _hamming_weight(waveform[i-1][1], waveform[i][1], width)

        result[design_key][signal_name] = {
            'width'         : width,
            'toggles'       : toggles,
            'waveform'      : waveform,
            'hamming_weight': hamming_total,
        }

    return result

if __name__ == '__main__':
    data = parse_vcd("all_designs.vcd")
    print_summary(data)

    designs_found = [d for d in ('clean','comb','seq','ctrl') if data.get(d)]
    designs_missing = [d for d in ('clean','comb','seq','ctrl') if not data.get(d)]

    if designs_missing:
        print(f"WARNING: No signals found for designs: {designs_missing}")
        print("  Check that testbench instance names match DESIGNS dict in parser.")
    else:
        print(f"OK — all 4 designs parsed successfully.")
        print(f"     Signal counts: " +
              ", ".join(f"{d}={len(data[d])}" for d in designs_found))
