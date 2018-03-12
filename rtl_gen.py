from math import log2, ceil
from operator import attrgetter

def import_strings(lang):
    global rtl_str
    if lang == 'verilog':
        import verilog_str as rtl_str
    else:
        import vhdl_str as rtl_str

def get_max_lengths(regs):
    max_all = 0
    max_ctrl = 0
    for reg in regs:
        for field in reg.fields:
            sig_len = len(reg.name)+len(field.name)+1
            if field.access == 'rwclr':
                sig_len += 4
            max_all = max(sig_len, max_all)
            if reg.placcess == 'r':
                max_ctrl = max(sig_len, max_ctrl)
    return max_all, max_ctrl

def write_ports(f, regs, pad):
    f.write(rtl_str.pl_port_comment)
    for reg in regs:
        if reg.placcess == 'nc':
            continue
        st = rtl_str.st_in if reg.placcess == 'w' else rtl_str.st_out
        sv = rtl_str.sv_in if reg.placcess == 'w' else rtl_str.sv_out
        for field in reg.fields:
            port_name = reg.name.lower()+'_'+field.name.lower()
            if field.msb == field.lsb:
                f.write(st.format(name=port_name, pad=pad))
            else:
                f.write(sv.format(name=port_name, pad=pad, width=field.msb-field.lsb))
            if field.access == 'rwclr':
                f.write(st.format(name=port_name+'_vld', pad=pad))

def write_reg_signals(f, regs):
    for i, reg in enumerate(regs):
        f.write(rtl_str.reg_signal.format(num=i, pad=' ' if len(regs) > 9 and i <= 9 else ''))

def write_reg_resets(f, regs):
    for i, reg in enumerate(regs):
        if reg.placcess == 'r':
            f.write(rtl_str.axi_write_reset_reg.format(i))

def write_axi_keep_value(i, reg, indent):
    slv = 'slv_reg'+str(i)
    sclr = []
    s = ''
    for field in reg.fields:
        if field.attr == 'sclr':
            sclr.append(field)
    if sclr:
        s = '\n'+' '*indent+slv+' <= '
        sclr.sort(key=attrgetter('msb'), reverse=True)
        prev_lsb = 31
        s += rtl_str.axi_sclr_part1
        for j, field in enumerate(sclr):
            if j != 0:
                s += rtl_str.axi_sclr_part2
            if prev_lsb != field.msb:
                s += slv+rtl_str.axi_sclr_part3.format(prev_lsb, field.lsb+1)
                s += rtl_str.axi_sclr_part2
            prev_lsb = field.lsb-1
            zeros = field.msb-field.lsb+1
            s += rtl_str.axi_sclr_part4.format(size=zeros, val='0'*zeros)
        if prev_lsb != -1:
            s += rtl_str.axi_sclr_part2
            s += slv+rtl_str.axi_sclr_part3.format(prev_lsb, 0)
        s += rtl_str.axi_sclr_part5
    return s

def write_axi_writes(f, regs, mem_addr_bits, lang):
    indent = 14 if lang == 'vhdl' else 10
    for i, reg in enumerate(regs):
        if reg.placcess == 'r':
            f.write(rtl_str.axi_write_assign.format(len=mem_addr_bits,
                val=format(i, '0'+str(mem_addr_bits)+'b'), num=i))
            s = write_axi_keep_value(i, reg, indent)
            if s != '':
                f.write(rtl_str.axi_write_assign_else)
                f.write(s)
            f.write(rtl_str.axi_write_assign_end)

def write_axi_keep_values(f, regs, lang):
    s = ''
    indent = 12 if lang == 'vhdl' else 8
    for i, reg in enumerate(regs):
        s += write_axi_keep_value(i, reg, indent)
    if s != '':
        f.write(rtl_str.axi_write_else)
        f.write(s)

def reg_data_out_sensitivity(regs):
    s = ''
    for i in range(len(regs)):
        s += 'slv_reg'+str(i)+', '
    return s

def write_reg_data_out_when(f, regs, mem_addr_bits):
    for i in range(len(regs)):
        f.write(rtl_str.reg_data_out_when.format(size=mem_addr_bits,
            num_bin=format(i, '0'+str(mem_addr_bits)+'b'), num=i))

def write_ctrl_sig_assgns(f, regs, pad):
    for i, reg in enumerate(regs):
        if reg.placcess != 'r':
            continue
        for field in reg.fields:
            sig_name = reg.name.lower()+'_'+field.name.lower()
            if field.msb == field.lsb:
                f.write(rtl_str.ctrl_sig_assgns_1bit.format(
                    sig_name, pad, i, field.msb))
            else:
                f.write(rtl_str.ctrl_sig_assgns.format(
                    sig_name, pad, i, field.msb, field.lsb))

def write_sts_sig_resets(f, regs):
    for i, reg in enumerate(regs):
        if reg.placcess == 'w':
            f.write(rtl_str.sts_sig_assgns_reset.format(i))

def write_sts_sig_assgns(f, regs, mem_addr_bits):
    for i, reg in enumerate(regs):
        if reg.placcess != 'w':
            continue
        for field in reg.fields:
            sig_name = reg.name.lower()+'_'+field.name.lower()
            if field.access == 'rwclr':
                tmpl = rtl_str.sts_sig_assgns_with_clr_1bit if field.msb == field.lsb else rtl_str.sts_sig_assgns_with_clr
                f.write(tmpl.format(
                    signal_valid=sig_name+'_vld',
                    reg_no=i, msb=field.msb, lsb=field.lsb,
                    signal=sig_name,
                    addr_bin=format(i, '0'+str(mem_addr_bits)+'b'),
                    size=mem_addr_bits,
                    strb_msb=field.msb//8, strb_lsb=field.lsb//8,
                    strb_1s='1'*(field.msb//8-field.lsb//8+1),
                    strb_size=field.msb//8-field.lsb//8+1
                    ))
            else:
                tmpl = rtl_str.sts_sig_assgns_no_clr_1bit if field.msb == field.lsb else rtl_str.sts_sig_assgns_no_clr
                f.write(tmpl.format(reg_no=i, msb=field.msb, lsb=field.lsb, signal=sig_name))

# main function
def generate_rtl(lang, regs):
    import_strings(lang)
    max_all, max_ctrl = get_max_lengths(regs)
    file_ext = 'v' if lang == 'verilog' else 'vhd'
    f = open('outputs/axilite_reg_if.'+file_ext, 'w')
    f.write(rtl_str.libraries)
    f.write(rtl_str.entity_header.format(32, 8))
    pad = max(max_all, 13)
    write_ports(f, regs, pad)
    f.write(rtl_str.axi_ports_end(spaces=' '*(pad-13)))
    mem_addr_bits = ceil(log2(len(regs)))
    f.write(rtl_str.constants.format(mem_addr_bits-1))
    f.write(rtl_str.internal_signals)
    write_reg_signals(f, regs)
    f.write('\n')
    f.write(rtl_str.begin_io_assgns_axi_logic)
    f.write(rtl_str.axi_write_header)
    write_reg_resets(f, regs)
    f.write(rtl_str.axi_write_else_header)
    write_axi_writes(f, regs, mem_addr_bits, lang)
    write_axi_keep_values(f, regs, lang)
    f.write(rtl_str.axi_write_footer)
    f.write(rtl_str.axi_logic2)
    f.write(rtl_str.reg_data_out_header.format(sens=reg_data_out_sensitivity(regs)))
    write_reg_data_out_when(f, regs, mem_addr_bits)
    f.write(rtl_str.reg_data_out_footer_axi_logic)
    f.write(rtl_str.ctrl_sig_assgns_header)
    write_ctrl_sig_assgns(f, regs, max_ctrl)
    f.write(rtl_str.sts_sig_assgns_header)
    write_sts_sig_resets(f, regs)
    f.write(rtl_str.sts_sig_assgns_reset_else)
    write_sts_sig_assgns(f, regs, mem_addr_bits)
    f.write(rtl_str.sts_sig_assgns_footer)
    f.write(rtl_str.arc_footer)
    f.close()
