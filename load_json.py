def get_clock(clocks, clock_name):
    return next((clock for clock in clocks if clock.name == clock_name), None)

class Clock:
    def __init__(self, clock):
        self.name = clock.get("name")
        self.desc = clock.get("desc")
        self.period = clock.get("period")

    def __repr__(self):
        return '    {:10} {:5} ns'.format(self.name, self.period)

class Field:
    def __init__(self, field, access, attr, clock, clocks):
        self.name = field.get("name")
        self.desc = field.get("desc")
        if field.get("access") is not None:
            self.access = field.get("access")
        else:
            self.access = access
        if field.get("attr") is not None:
            self.attr = field.get("attr")
        else:
            self.attr = attr
        if field.get("clock") is not None:
            self.clock = get_clock(clocks, field.get("clock"))
        else:
            self.clock = clock
        self.msb = field.get("msb")
        self.lsb = field.get("lsb")

    def __repr__(self):
        bits = '   [{:2}]'.format(self.lsb) if self.lsb == self.msb else '[{:2}:{:2}]'.format(self.msb, self.lsb)
        attr = '' if self.attr is None else self.attr
        return '    {} {:5} {:4} {:10} {}\n'.format(bits, self.access, attr, self.clock.name, self.name)

class Reg:
    def __init__(self, reg, clocks):
        self.component = "Register"
        self.name = reg.get("name")
        self.desc = reg.get("desc")
        self.placcess = reg.get("placcess")
        self.fields = []
        if reg.get("fields") is not None:
            for f in reg.get("fields"):
                self.fields.append(Field(f, reg.get("access"), reg.get("attr"),
                    get_clock(clocks, reg.get("clock")), clocks))

    def __repr__(self):
        return '{}\n{}'.format(self.name, '\n'.join([repr(f) for f in self.fields]))

def get_clocks(data):
    clocks = []
    for clock in data["clocks"]:
        clocks.append(Clock(clock))
    return clocks

def get_regs(data, clocks):
    regs = []
    for reg in data["regs"]:
        regs.append(Reg(reg, clocks))
    return regs
