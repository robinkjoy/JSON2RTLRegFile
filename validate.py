import re

valid_name_re = re.compile("^[a-zA-Z0-9_]+$")
name_tmpl = '({}) \'{}\''

def get_clock(clocks, clock_name):
    return next((clock for clock in clocks if clock.name == clock_name), None)

def validate_clocks(clocks):
    valid = True
    clock_list = []
    for i, clock in enumerate(clocks):
        clock_name = name_tmpl.format(i, clock.name)
        if clock.name is None:
            print('ERROR: Clock {} \'name\' is missing'.format(clock_name))
            valid = False
        elif not valid_name_re.match(clock.name):
            print('ERROR: Clock {} \'name\' is invalid'.format(clock_name))
            valid = False
        elif clock.name in clock_list:
            print('ERROR: Clock {} \'name\' already present'.format(clock_name))
            valid = False
        else:
            clock_list.append(clock.name)
        if clock.desc is None:
            print('WARN: Clock {} \'desc\' is missing'.format(clock_name))
        if clock.period is None:
            print('ERROR: Clock {} \'period\' is missing'.format(clock_name))
            valid = False
        elif type(clock.period) is not int and type(clock.period) is not float:
            print('ERROR: Clock {} \'period\' is not int or float'.format(clock_name))
            valid = False

    return valid

def load_validate_axi_clock(clocks, axi_clock_name):
    if axi_clock_name is None:
        print('\'axi_clock\' not found.')
        return None
    axi_clock = get_clock(clocks, axi_clock_name)
    if axi_clock is None:
        print('\'axi_clock\' not found in \'clocks\'.')
        return None
    valid = True
    for i, clock in enumerate(clocks):
        clock_name = name_tmpl.format(i, clock.name)
        if clock.period > axi_clock.period:
            print('ERROR: Clock {} is slower than AXI Clock'.format(clock_name))
            valid = False
    if valid:
        return axi_clock
    else:
        return None

def validate_regs(regs):
    attributes = ['sclr']
    accesses = ['rw', 'ro', 'rwclr']
    placcesses = ['w', 'r', 'nc']
    valid = True
    reg_list = []
    missing_attr_reg = '{}: Register {} attribute \'{}\' is missing'
    invalid_attr_reg = '{}: Register {} attribute \'{}\' is invalid'
    missing_attr_field = '{}: Register {} Field {} attribute \'{}\' is missing'
    invalid_attr_field = '{}: Register {} Field {} attribute \'{}\' is invalid'
    invalid_combo = 'ERROR: Register {} Field {} {} \'{}\' is valid only for PL {} registers'
    duplicate_reg = 'ERROR: Register name {} already present'
    duplicate_field = 'ERROR: Field name {} already present in Register {}'
    for i, reg in enumerate(regs, start=1):
        reg_name = name_tmpl.format(i, reg.name)
        if reg.name is None:
            print(missing_attr_reg.format('ERROR', reg_name, 'name'))
            valid = False
        elif not valid_name_re.match(reg.name):
            print(invalid_attr_reg.format('ERROR', reg_name, 'name'))
            valid = False
        elif reg.name in reg_list:
            print(duplicate_reg.format(reg_name))
            valid = False
        else:
            reg_list.append(reg.name)
        if reg.desc is None:
            print(missing_attr_reg.format('WARN', reg_name, 'desc'))
        if reg.placcess is None:
            print(missing_attr_reg.format('ERROR', reg_name, 'placcess'))
            valid = False
        elif reg.placcess not in placcesses:
            print(invalid_attr_reg.format('ERROR', reg_name, 'placcess'))
            valid = False
        if not reg.fields:
            print(missing_attr_reg.format('ERROR', reg_name, 'fields'))
            valid = False
        else:
            ranges = set()
            field_list = []
            for j, field in enumerate(reg.fields, start=1):
                field_name = name_tmpl.format(j, field.name)
                if field.name is None:
                    print(missing_attr_field.format('ERROR', reg_name, field_name, 'name'))
                    valid = False
                elif not re.compile("^[a-zA-Z0-9_]+$").match(field.name):
                    print(invalid_attr_field.format('ERROR', reg_name, field_name, 'name'))
                    valid = False
                elif field.name in field_list:
                    print(duplicate_field.format(field_name, reg_name))
                    valid = False
                else:
                    field_list.append(field.name)
                if field.desc is None:
                    print(missing_attr_field.format('WARN', reg_name, field_name, 'desc'))
                if field.access not in accesses:
                    print(invalid_attr_field.format('ERROR', reg_name, field_name, 'access'))
                    valid = False
                if field.access == 'rw' and reg.placcess != 'r':
                    print(invalid_combo.format(reg_name, field_name, 'access', 'rw', 'Read'))
                    valid = False
                if field.access == 'rwclr' and reg.placcess != 'w':
                    print(invalid_combo.format(reg_name, field_name, 'access', 'rwclr', 'Write'))
                    valid = False
                if field.attr is not None and field.attr not in attributes:
                    print(invalid_attr_field.format('ERROR', reg_name, field_name, 'attr'))
                    valid = False
                if field.attr == 'sclr' and reg.placcess != 'r':
                    print(invalid_combo.format(reg_name, field_name, 'attribute', 'sclr', 'Read'))
                    valid = False
                if field.clock is None:
                    print(invalid_attr_reg.format('ERROR', reg_name, 'clock'))
                    valid = False
                if field.lsb is None or field.msb is None:
                    print(missing_attr_field.format('ERROR', reg_name, field_name, 'msb/lsb'))
                    valid = False
                elif type(field.lsb) is not int or type(field.lsb) is not int:
                    print('ERROR: Register {} Field {} msb/lsb is not an integer'.format(
                                                    reg_name, field_name))
                    valid = False
                elif field.lsb < 0 or field.msb > 31 or field.lsb > field.msb:
                    print(invalid_attr_field.format('ERROR', reg_name, field_name, 'msb/lsb'))
                    valid = False
                else:
                    if (ranges & set(range(field.lsb, field.msb+1))):
                        print('ERROR: Register {} Field {} field ranges overlap'.format(
                                                    reg_name, field_name))
                        valid = False
                    ranges = ranges | set(range(field.lsb, field.msb+1))
    return valid


