import sys
import json
import argparse
import load_json
import validate
import rtl_gen
import extras_gen
import doc_gen

parser = argparse.ArgumentParser()
parser.add_argument('--no-doc', action='store_false',
        dest='doc', help='disable doc file generation')
parser.add_argument('--lang', choices=['vhdl', 'verilog'],
        dest='lang', help='target RTL language')
parser.add_argument('--print', action='store_true',
        dest='vprint', help='print JSON contents')
parser.add_argument('input_filename', help='Input JSON filename')
args = parser.parse_args()

with open(args.input_filename) as data_file:
    try:
      data = json.load(data_file)
    except ValueError as e:
        print(e)
        exit('JSON Load Failed.')

clocks = load_json.get_clocks(data)
if validate.validate_clocks(clocks) is False:
    exit('Clock validation Failed.')
axi_clock_name = data.get("axi_clock")
axi_clock = validate.load_validate_axi_clock(clocks, axi_clock_name)
if axi_clock is None:
    exit('axi_clock validation Failed.')
regs = load_json.get_regs(data, clocks)
if validate.validate_regs(regs) is False:
    exit('Register validation Failed.')

if args.vprint:
    print('Clocks\n')
    print(*clocks, sep='\n')
    print('\nResgisters\n')
    print(*regs, sep='\n')

rtl_gen.generate_rtl(args.lang, regs, axi_clock, clocks)
max_lens = extras_gen.get_max_len_pl_c(regs)
extras_gen.generate_pkg(regs, max_lens)
extras_gen.generate_c_header(regs, max_lens)
if args.doc:
    doc_gen.generate_word_doc(regs)
