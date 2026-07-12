import json
from collections import defaultdict

PIN_DIR = {
    'A1':'input','A2':'input','A3':'input','A4':'input','A':'input',
    'B1':'input','B2':'input','B3':'input','B':'input','C1':'input','C2':'input',
    'CK':'input','D':'input','RN':'input','SN':'input','E':'input',
    'SE':'input','G':'input','GN':'input','CI':'input','SI':'input',
    'EN':'input','I':'input','OE':'input',
    'ZN':'output','Z':'output','GCK':'output','Q':'output','QN':'output',
    'CO':'output','S':'output','IQ':'internal'
}

def process_netlist(filename, module_name):
    data = json.load(open(filename))
    cells = data["modules"][module_name]["cells"]
    netnames = data["modules"][module_name]["netnames"]

    fanout = defaultdict(int)
    for cell in cells.values():
        for pin, nets in cell["connections"].items():
            if PIN_DIR.get(pin) == 'input':
                fanout[nets[0]] += 1

    signal_power_weight = defaultdict(int)
    for name, net in netnames.items():
        if net["hide_name"] == 1:
            continue
        for bit in net["bits"]:
            if isinstance(bit, int):
                signal_power_weight[name] += fanout[bit]

    return dict(signal_power_weight)
