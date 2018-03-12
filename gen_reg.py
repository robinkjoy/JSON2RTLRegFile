import sys
import json
import argparse
import load_json
import validate
import rtl_gen
import extras_gen
import doc_gen

parser = argparse.ArgumentParser()
parser.add_argument('--doc', action='store_true',
        dest='doc', help='enable doc file generation')
parser.add_argument('--lang', default='verilog', choices=['vhdl', 'verilog'],
        dest='lang', help='target RTL language (default: %(default)s)')
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

clocks = None
axi_clock = None
regs = load_json.get_regs(data, clocks)
if validate.validate_regs(regs) is False:
    exit('Register validation Failed.')

if args.vprint:
    print('Clocks\n')
    print(*clocks, sep='\n')
    print('\nResgisters\n')
    print(*regs, sep='\n')

rtl_gen.generate_rtl(args.lang, regs)
max_lens = extras_gen.get_max_len_pl_c(regs)
extras_gen.generate_pkg(regs, max_lens)
extras_gen.generate_c_header(regs, max_lens)
if args.doc:
    doc_gen.generate_word_doc(regs)
