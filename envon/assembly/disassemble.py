
from .EvmInstruction import EvmInstruction

from envon.helpers import Log

log = Log(__name__)

def disassemble_file(f):
    c = f.read()
    c = bytes.fromhex(c.strip())
    # c = strip_metadata(c)
    return disassemble(c)

def strip_metadata(runbin):
    r = runbin
    if len(r) < 2:
        return r
    meta_len = 2 + int.from_bytes(r[-2:], 'big')
    if len(r) < meta_len:
        return r
    log.info('Removed', meta_len, 'bytes of metadata')
    return r[:-meta_len]

def disassemble(runbin):
    res = []
    i   = 0
    l   = len(runbin)
    try:
        while i < l:
            en = EvmInstruction(i, runbin[i])
            if en.is_push():
                s  = en.size()
                assert i + s < l, (i, s, l)
                pv = int.from_bytes(runbin[i+1:i+s], 'big')
                en = EvmInstruction(i, runbin[i], pv)
                i += s
            else:
                i += 1
            res.append(en)
    except (AssertionError, IndexError, KeyError, ValueError) as e:
        log.info('At byte', i, e)
    return res
