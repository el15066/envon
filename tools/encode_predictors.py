
import os

from IIT import get_opcode, regc_minmax, has_rd, uses_mem

INVALID_REG     = 65000 # leave some room for temporaries (up to a few 100 are expected to ever be needed)
BLOCK_ID_SHIFTS = 0

def encode_bid(x):
    return ( int(x[1:], 16) >> BLOCK_ID_SHIFTS ).to_bytes(2, 'little')

def encode_pos(x):
    return x.to_bytes(3, 'little')

def encode_reg(x):
    return x.to_bytes(2, 'little')

def add_constant(code, on, _v):
    #
    rd = encode_reg(on)
    #
    v  = _v.to_bytes(32, 'big').lstrip(b'\x00') if _v != 0 else b'\x00'
    l  = len(v)
    #
    opcode = get_opcode('CONSTANT_' + str(l).rjust(2, '_')).to_bytes(1, 'little')
    #
    code.extend(opcode + rd + v)

def add_instruction_raw(code, name, regs):
    #
    opcode =  get_opcode(name).to_bytes(1, 'little')
    m, M   = regc_minmax(name)
    assert m <= len(regs) <= M
    #
    code.extend(opcode + b''.join(regs))

def add_blockid(code, bid):
    add_instruction_raw(code, 'BLOCKID', [bid])

def add_stop(code):
    add_instruction_raw(code, 'STOP', [])

def add_instruction(code, name, on, args):
    regs = []
    #
    if has_rd(name):
        rd = encode_reg(on)
        regs.append(rd)
    #
    if uses_mem(name):
        args = args[1:]
    for a in args:
        r  =  encode_reg(a)
        regs.append(r)
    #
    add_instruction_raw(code, name, regs)

def process(f):
    #
    blocks = {}
    code   = bytearray()
    #
    philen = 0
    #
    line = f.readline()
    if not line or line == '[]\n': return b''
    assert line == '~0 | ENTRY\n'
    #
    # print(f.name)
    for line in f:
        line = line[:-1]
        if line[0] == '[': break
        # print(line)
        #
        if line[0] == '~':
            [_bid, _phimap] = line.split(' | ')
            #
            bid = encode_bid(_bid)
            assert bid not in blocks
            #
            _edges = _phimap.split()
            assert all(_bid2[0] == '~' for _bid2 in _edges)
            edges = [
                encode_bid(_bid2)
                for _bid2 in _edges
            ]
            #
            add_blockid(code, bid)
            #
            pos = encode_pos(len(code))
            blocks[bid] = (pos, edges)
            #
            philen = len(edges)
            #
        elif line == 'STOP':
            add_stop(code)
            #
        else:
            [_on, _cmd] = line.split(' = ')
            on   = int(_on)
            cmd  = _cmd.split()
            name = cmd[0]
            args = [int(a) if a != 'None' else INVALID_REG for a in cmd[1:]]
            #
            if name[0] == '#':
                assert not args
                v = int(name[1:], 16)
                add_constant(code, on, v)
            else:
                if name == 'PHI': assert len(args) == philen
                add_instruction(code, name, on, args)
    #
    bt = bytearray()
    for bid, v in blocks.items():
        pos, edges = v
        c = len(edges).to_bytes(1, 'little')
        bt.extend(bid + pos + c + b''.join(edges))
    #
    offs = len(bt).to_bytes(2, 'little')
    #
    return offs + bt + code

def main(ofname, dirname, tag):
    with open(ofname, 'w') as fo:
        fo.write('info ' + dirname + ',' + tag + '\n')
        for path, _, fnames in os.walk(dirname):
            for fname in fnames:
                fullname = path + fname
                try:
                    if len(fname) != 2 + 64 + 8:       continue
                    if     fname[  : 2] != 'h_':       continue
                    if     fname[66:  ] != '.evmlike': continue
                    _h =   fname[ 2:66]
                    h  = bytes.fromhex(_h)
                    #
                    with open(fullname) as f:
                        data = process(f)
                    #
                    if data:
                        fo.write(h.hex() + ' ' + data.hex() + '\n')
                    #
                except Exception as e:
                    print(repr(e), fullname)
                    raise


if __name__ == '__main__':
    import sys
    tag = sys.argv[3] if len(sys.argv) > 3 else 'no_tag'
    main(ofname=sys.argv[1], dirname=sys.argv[2]+'/', tag=tag)

