import subprocess
import doc_str

def get_reg_dict(i, reg):
    d = {}
    d['num'] = i
    d['name'] = reg.name
    d['offset'] = i*4
    d['desc'] = '-' if reg.desc is None else reg.desc
    return d

def get_field_dict(i, f):
    access_repr = {'rw' : 'R/W', 'ro' : 'RO', 'rwclr' : 'R/WCLR'}
    attr_repr = {'sclr' : 'Self-Clear'}
    d = {}
    d['num'] = i
    d['name'] = f.name
    d['bits'] = str(f.lsb) if f.lsb == f.msb else str(f.msb)+':'+str(f.lsb)
    if f.attr is not None:
        d['type'] = access_repr[f.access] + ', ' + attr_repr[f.attr]
    else:
        d['type'] = access_repr[f.access]
    d['default'] = '0'
    d['desc'] = f.desc
    return d

def generate_word_doc (regs):
    # generate wscript for doc generation
    f = open('word_doc.vbs', 'w')
    f.write(doc_str.vbs_header)
    for i, reg in enumerate(regs):
        f.write(doc_str.vbs_reg.format_map(get_reg_dict(i, reg)))
        for j, field in enumerate(reg.fields):
            f.write(doc_str.vbs_field.format_map(get_field_dict(j, field)))
    f.write(doc_str.vbs_footer)
    f.close()
    # run script
    subprocess.call(['cscript.exe', 'word_doc.wsf'])
