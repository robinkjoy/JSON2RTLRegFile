import extras_str

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
    f.write(extras_str.pkg_header)
    write_reg_addrs(f, regs, extras_str.pkg_reg_addr, max_lens[0])
    f.write('\n')
    write_masks(f, regs, extras_str.pkg_mask, max_lens[1])
    f.write(extras_str.pkg_footer)
    f.close()

# C header file
def generate_c_header(regs, max_lens):
    f = open('pl_regs.h', 'w')
    f.write(extras_str.c_header)
    f.write('\n// Register Offsets\n')
    write_reg_addrs(f, regs, extras_str.c_reg_addr, max_lens[0])
    f.write('\n// Register Masks\n')
    write_masks(f, regs, extras_str.c_mask, max_lens[1])
    f.write(extras_str.c_read_write_fn)
    f.write(extras_str.c_footer)
    f.close()
