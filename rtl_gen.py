from math import log2, ceil
from operator import attrgetter
import rtl_str

def get_max_lengths(regs, axi_clock_name):
    max_all = 0
    max_cdc = 0
    max_ctrl = 0
    for reg in regs:
        for field in reg.fields:
            sig_len = len(reg.name)+len(field.name)+1
            if field.access == 'rwclr':
                sig_len += 4
            max_all = max(sig_len, max_all)
            if field.clock.name != axi_clock_name:
                max_cdc = max(sig_len, max_cdc)
                sig_len += 5
            if reg.placcess == 'r':
                max_ctrl = max(sig_len, max_ctrl)
    return max_all, max_cdc, max_ctrl

def write_cdc_clocks(f, clocks, axi_clock_name, pad):
    f.write('    -- Clocks\n')
    for clock in clocks:
        if clock.name == axi_clock_name:
            continue
        f.write(rtl_str.st.format(clock.name, pad, 'in '))

def write_ports(f, regs, pad):
    f.write('    -- PL Ports\n')
    for reg in regs:
        if reg.placcess == 'nc':
            continue
        direction = 'in ' if reg.placcess == 'w' else 'out'
        for field in reg.fields:
            port_name = reg.name.lower()+'_'+field.name.lower()
            if field.msb == field.lsb:
                f.write(rtl_str.st.format(port_name, pad, direction))
            else:
                f.write(rtl_str.sv.format(port_name, pad, direction, field.msb-field.lsb))
            if field.access == 'rwclr':
                f.write(rtl_str.st.format(port_name+'_vld', pad, direction))

def write_reg_signals(f, regs):
    for i, reg in enumerate(regs):
        f.write(rtl_str.reg_signal.format(i, ' ' if len(regs) > 9 and i <= 9 else ''))

def write_cdc_signals(f, regs, axi_clock_name, pad):
    for reg in regs:
        for field in reg.fields:
            if field.clock.name == axi_clock_name:
                continue
            sig_name = reg.name.lower()+'_'+field.name.lower()
            if field.msb == field.lsb:
                f.write(rtl_str.signal_st.format(sig_name+'_sync', pad+5))
            else:
                f.write(rtl_str.signal_sv.format(sig_name+'_sync', pad+5, field.msb-field.lsb))
            if field.access == 'rwclr':
                f.write(rtl_str.signal_st.format(sig_name+'_vld_sync', pad+5))

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
        for j, field in enumerate(sclr):
            if j != 0:
                s += ' & '
            if prev_lsb != field.msb:
                s += slv+'('+str(prev_lsb)+' downto '+str(field.lsb+1)+') & '
            prev_lsb = field.lsb-1
            s += '"'+'0'*(field.msb-field.lsb+1)+'"'
        if prev_lsb != -1:
            s += ' & '+slv+'('+str(prev_lsb)+' downto 0)'
        s += ';'
    return s

def write_axi_writes(f, regs, mem_addr_bits):
    for i, reg in enumerate(regs):
        if reg.placcess == 'r':
            f.write(rtl_str.axi_write_assign.format(
                format(i, '0'+str(mem_addr_bits)+'b'), i))
            s = write_axi_keep_value(i, reg, 12)
            if s != '':
                f.write(rtl_str.axi_write_assign_else)
                f.write(s)
            f.write(rtl_str.axi_write_assign_end)

def write_axi_keep_values(f, regs, indent):
    s = ''
    for i, reg in enumerate(regs):
        s += write_axi_keep_value(i, reg, 10)
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
        f.write(rtl_str.reg_data_out_when.format(
            format(i, '0'+str(mem_addr_bits)+'b'), i))

def write_ctrl_sig_assgns(f, regs, axi_clock_name, pad):
    for i, reg in enumerate(regs):
        if reg.placcess != 'r':
            continue
        for field in reg.fields:
            sync = '_sync' if field.clock.name != axi_clock_name else ''
            sig_name = reg.name.lower()+'_'+field.name.lower()+sync
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

def write_sts_sig_assgns(f, regs, mem_addr_bits, axi_clock_name):
    for i, reg in enumerate(regs):
        if reg.placcess != 'w':
            continue
        for field in reg.fields:
            sync = '_sync' if field.clock.name != axi_clock_name else ''
            sig_name = reg.name.lower()+'_'+field.name.lower()
            if field.access == 'rwclr':
                tmpl = rtl_str.sts_sig_assgns_with_clr_1bit if field.msb == field.lsb else rtl_str.sts_sig_assgns_with_clr
                f.write(tmpl.format(
                    signal_valid=sig_name+'_vld'+sync,
                    reg_no=i, msb=field.msb, lsb=field.lsb,
                    signal=sig_name+sync,
                    addr_bin=format(i, '0'+str(mem_addr_bits)+'b'),
                    strb_msb=field.msb//8, strb_lsb=field.lsb//8,
                    strb_1s='1'*(field.msb//8-field.lsb//8+1)
                    ))
            else:
                tmpl = rtl_str.sts_sig_assgns_no_clr_1bit if field.msb == field.lsb else rtl_str.sts_sig_assgns_no_clr
                f.write(tmpl.format(reg_no=i, msb=field.msb, lsb=field.lsb, signal=sig_name+sync))

def write_cdc(f, regs, axi_clock):
    for reg in regs:
        for field in reg.fields:
            if field.clock.name == axi_clock.name:
                continue
            if reg.placcess == 'r':
                if field.attr == 'sclr':
                    inst = rtl_str.cdc_inst_pl_read_pulse
                else:
                    inst = rtl_str.cdc_inst_pl_read
            elif field.access == 'rwclr':
                inst = rtl_str.cdc_inst_pl_write_vld
            else:
                inst = rtl_str.cdc_inst_pl_write
            sig_name = reg.name.lower()+'_'+field.name.lower()
            onebit = '(0)' if field.msb == field.lsb else ''
            spaces = '   ' if field.msb == field.lsb else ''
            dst_per = float(field.clock.period) if reg.placcess == 'r' else float(axi_clock.period)
            src_per = float(axi_clock.period) if reg.placcess == 'r' else float(field.clock.period)
            f.write(inst.format(signal=sig_name, clock=field.clock.name,
                                width=field.msb-field.lsb+1, onebit=onebit, spaces=spaces,
                                src_per=src_per, dst_per=dst_per))

# main function
def generate_rtl(regs, axi_clock, clocks):
    max_all, max_cdc, max_ctrl = get_max_lengths(regs, axi_clock.name)
    f = open('axilite_reg_if.vhd', 'w')
    f.write(rtl_str.libraries)
    f.write(rtl_str.entity_header.format(32, 8))
    pad = max(max_all, 13)
    write_cdc_clocks(f, clocks, axi_clock.name, pad)
    write_ports(f, regs, pad)
    f.write(rtl_str.axi_ports_end(spaces=' '*(pad-13)))
    mem_addr_bits = ceil(log2(len(regs)))
    f.write(rtl_str.components)
    f.write(rtl_str.constants.format(mem_addr_bits-1))
    f.write(rtl_str.internal_signals)
    write_reg_signals(f, regs)
    f.write('\n')
    write_cdc_signals(f, regs, axi_clock.name, max_cdc)
    f.write(rtl_str.begin_io_assgns_axi_logic)
    f.write(rtl_str.axi_write_header)
    write_reg_resets(f, regs)
    f.write(rtl_str.axi_write_else_header)
    write_axi_writes(f, regs, mem_addr_bits)
    write_axi_keep_values(f, regs, 10)
    f.write(rtl_str.axi_write_footer)
    f.write(rtl_str.axi_logic2)
    f.write(rtl_str.reg_data_out_header.format(reg_data_out_sensitivity(regs)))
    write_reg_data_out_when(f, regs, mem_addr_bits)
    f.write(rtl_str.reg_data_out_footer_axi_logic)
    f.write(rtl_str.ctrl_sig_assgns_header)
    write_ctrl_sig_assgns(f, regs, axi_clock.name, max_ctrl)
    f.write(rtl_str.sts_sig_assgns_header)
    write_sts_sig_resets(f, regs)
    f.write(rtl_str.sts_sig_assgns_reset_else)
    write_sts_sig_assgns(f, regs, mem_addr_bits, axi_clock.name)
    f.write(rtl_str.sts_sig_assgns_footer)
    write_cdc(f, regs, axi_clock)
    f.write(rtl_str.arc_footer)
    f.close()

# PL reg package

def get_max_len_pl_c (regs):
    max_reg_name_len = 0
    max_reg_mask_len = 0
    for reg in regs:
        if len(reg.fields) == 1:
            max_reg_name_len = max(len(reg.name)+len(reg.fields[0].name)+5, max_reg_name_len)
        else:
            max_reg_name_len = max(len(reg.name)+4, max_reg_name_len)
        for field in reg.fields:
            if field.msb != 31 or field.lsb != 0:
                max_reg_mask_len = max(len(reg.name+'_'+field.name)+5, max_reg_mask_len)
    return (max_reg_name_len, max_reg_mask_len)

def write_reg_addrs(f, regs, str_templ, max_len):
    for i, reg in enumerate(regs):
        if len(reg.fields) == 1:
            f.write(str_templ.format((reg.name+'_'+reg.fields[0].name).upper()+'_REG',
                max_len, i*4))
        else:
            f.write(str_templ.format(reg.name.upper(), max_len, i*4))

def get_mask(msb, lsb):
    temp = 0
    for i in range(lsb, msb+1):
        temp = temp + 2**i
    return format(temp, '08x')

def write_masks(f, regs, str_templ, max_len):
    for i, reg in enumerate(regs):
        for field in reg.fields:
            if field.msb != 31 or field.lsb != 0:
                f.write(str_templ.format((reg.name+'_'+field.name).upper()+'_MASK',
                    max_len, get_mask(field.msb, field.lsb)))

# pkg main function
def generate_pkg(regs, max_lens):
    f = open('pl_reg_pkg.vhd', 'w')
    f.write(rtl_str.pkg_header)
    write_reg_addrs(f, regs, rtl_str.pkg_reg_addr, max_lens[0])
    f.write('\n')
    write_masks(f, regs, rtl_str.pkg_mask, max_lens[1])
    f.write(rtl_str.pkg_footer)
    f.close()

# C header file
def generate_c_header(regs, max_lens):
    f = open('pl_regs.h', 'w')
    f.write(rtl_str.c_header)
    f.write('\n// Register Offsets\n')
    write_reg_addrs(f, regs, rtl_str.c_reg_addr, max_lens[0])
    f.write('\n// Register Masks\n')
    write_masks(f, regs, rtl_str.c_mask, max_lens[1])
    f.write(rtl_str.c_read_write_fn)
    f.write(rtl_str.c_footer)
    f.close()
