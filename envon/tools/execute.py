
import sys
import itertools

from Crypto.Hash import keccak

ZEROS     = bytes(0x20)
ADDR_MASK = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

class hexint(int):
    def __repr__(self):
        return '#' + hex(self)[2:]

def hexify(x):
    if   type(x) is int:   return hexint(x)
    elif type(x) is tuple: return tuple(hexify(v) for v in x)
    elif type(x) is list:  return      [hexify(v) for v in x]
    elif type(x) is dict:  return {k: hexify(v) for k, v in x.items()}
    else:                  return x

def debug(*args, **kwargs):
    # print(*hexify(args), **kwargs, file=sys.stderr)
    # print(*args, **kwargs, file=sys.stderr)
    pass

def warn(*args, **kwargs):
    # print(*hexify(args), **kwargs, file=sys.stderr)
    print(*args, **kwargs, file=sys.stderr)
    pass

def u256_to_bytes(x):
    return x.to_bytes(32, 'big')

def bytes_to_u256(x):
    return int.from_bytes(x, 'big')

def u256(x):
    return x & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

def s256(x):
    return (((x + 0x8000000000000000000000000000000000000000000000000000000000000000)
                & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
                - 0x8000000000000000000000000000000000000000000000000000000000000000)

def sha3(d):
    return bytes_to_u256(keccak.new(digest_bits=256).update(d).digest())

class UnknownInstructionError(Exception):
    pass

class EmptyPHIError(Exception):
    pass

class WarnError(Exception):
    pass

class ExecutionState:
    def __init__(self):
        self.gaz      = 10000
        self.phiindex = 0
        self.sloads   = set()
        self.sstores  = set()
        self.mem      = memoryview(bytearray(65536))
        self.mem_modified = False

def execute_tx(ctx):
    state = ExecutionState()
    ok    = execute_msg(ctx, state)
    if ok:
        res = set(
            u256_to_bytes(r).hex()
            for r in itertools.chain(state.sloads, state.sstores)
            if type(r) is int
        )
        if res:
            print(f"Tx {ctx['Block']:8} {ctx['Index']:3} {ctx['Address']:040x}")
            print('\n'.join(res))

def execute_msg(ctx, state):
    a = None
    h = None
    try:
        a = ctx['Codeaddr']
        h = ctx['Codemap'][hexint(a)]
        d = ctx['Codedir']
        with open(f'{d}/h_{h:040x}.evmlike') as fic:
            code = [l[:-1] for l in fic]
    except KeyError as e:
        warn('No code mapping for contract', hexify(a), repr(e))
        pass
    except FileNotFoundError as e:
        warn('No code file for contract', hexify(a), 'code hash', hexify(h), repr(e))
        pass
    else:
        if code:
            lines = code[:-1]
            debug('---> Executing contract at', hexify(a), 'code hash', hexify(h), 'lines', len(lines))
            ok = execute_with_jumps(ctx, state, lines)
            debug('---> Execution complete, ok', ok)
            return ok
        else:
            warn('No code in code file of', hexify(h))
            pass
    return False

def execute_with_jumps(ctx, state, lines):
    #
    block_map  = {}
    for i, line in enumerate(lines):
        if line[0] == '~':
            block, _, _phimap = line.partition(' | ')
            phimap            = _phimap.split()
            block_map[block]  = (i-1, phimap)
    #
    regs      = {0: 0}
    cur_block = 'ENTRY'
    try:
        i     = -1
        line  = ''
        i_max = len(lines) - 1
        while i < i_max and state.gaz > 0:
            state.gaz -= 1
            i         += 1
            line       = lines[i]
            #
            if line[0] == '~':
                block, _, _ = line.partition(' | ')
                _, phimap   = block_map[block]
                debug(block, '<-', cur_block)
                try:
                    state.phiindex = phimap.index(cur_block)
                    cur_block      = block
                except ValueError as e:
                    warn('At', i, line, 'phimap', phimap, 'cur_block', cur_block, repr(e))
                    break
                #
            elif line == 'STOP':
                break
            else:
                _on, _, _cmd = line.partition(' = ')
                on   = int(_on)
                cmd  = _cmd.split()
                name = cmd[0]
                args = [int(a) if a != 'None' else None for a in cmd[1:]]
                #
                try:
                    v = None
                    if name[0] == '#':
                        assert not args
                        v = int(name[1:], 16)
                        debug(f'  {on:4}   =', hexify(v))
                    else:
                        avs = tuple(regs.get(a) for a in args)
                        debug(f'  {on:4} ', name, hexify(avs), args)
                        v   = _execute(ctx, state, name, avs)
                        debug(f'  {on:4}   =', hexify(v))
                    #
                    if state.mem_modified:
                        state.mem_modified = False
                        for j in range(0, len(state.mem), 0x20):
                            w = state.mem[j:j+0x20]
                            if w != ZEROS:
                                debug(f'  mem {j:4x}  {w.hex()}')
                    #
                    if   v is None: pass
                    elif type(v) in (int, UnknownValue): regs[on] = v
                    elif type(v) is JumpTarget:
                        t = v.decide(block_map)
                        if t:
                            if t in block_map:
                                i, _ = block_map[t]
                            else:
                                break
                    else:
                        raise WarnError('v is ' + repr(v))
                    #
                except Exception as e:
                    warn('At', i, line, 'name', name, 'avs', hexify(avs), 'args', args, repr(e))
                    if type(e) is not WarnError:
                        # break
                        return False
                #
        if state.gaz <= 0:
            warn('Out of gaz')
        else:
            debug('Gaz left:', state.gaz)
    except:
        warn('line', i, line)
        raise
    #
    return True


class UnknownValue:

    def __repr__(self):
        return '?'

class JumpTarget:

    def __init__(self, target, condition):
        self.target    = target
        self.condition = condition

    def __repr__(self):
        t = self.target
        c = self.condition
        if type(c) is int: return t if c != 0         else ''
        else:              return f'JUMP({t}, {c})'

    def decide(self, block_map):
        t = self.target
        c = self.condition
        if type(c) is int: return t if c != 0         else ''
        else:              return t if t in block_map else ''


def _execute(ctx, state, name, avs):
    if   name == 'PHI':
        return avs[state.phiindex]
        #
    elif name == 'JUMP':
        a0, = avs
        assert type(a0) is int
        return JumpTarget(f'~{a0:x}', 1)
        #
    elif name == 'JUMPI':
        a0, a1 = avs
        return JumpTarget(f'~{a0:x}', a1)
        #
    elif name == 'SSTORE':
        a0, a1 = avs
        state.sstores.add(a0)
        return None
        #
    elif name == 'CALLDATASIZE':
        () = avs
        return len(ctx['Calldata'])
        #
    elif name == 'CALLVALUE':
        () = avs
        return ctx['Callvalue']
        #
    elif name == 'CALLER':
        () = avs
        return ctx['Caller']
        #
    elif name == 'ADDRESS':
        () = avs
        return ctx['Address']
        #
    elif name == 'TIMESTAMP':
        () = avs
        return ctx['Timestamp']
        #
    elif name == 'ORIGIN':
        () = avs
        return ctx['Caller']
        #
    elif name == 'NUMBER':
        () = avs
        return ctx['Block']
        #
    elif name == 'CHAINID':
        () = avs
        return ctx['Chainid']
        #
    elif name == 'DIFFICULTY':
        () = avs
        return ctx['Difficulty']
        #
    elif name == 'GAS':
        () = avs
        return ctx['Gaslimit']
        #
    elif not all(type(av) is int for av in avs):
        return UnknownValue()
        #
    elif name == 'CALLDATALOAD':
        a0, = avs
        return bytes_to_u256(ctx['Calldata'][a0:a0+32].ljust(32))
        #
    elif name == 'CALLDATACOPY':
        _, a1, a2, a3 = avs
        assert a1 + a3 <= len(state.mem)
        state.mem[a1:a1+a3] = ctx['Calldata'][a2:a2+a3].ljust(a3)
        state.mem_modified = True
        return 0
        #
    elif name == 'ADD':
        a0, a1 = avs
        return u256(a0 + a1)
        #
    elif name == 'SUB':
        a0, a1 = avs
        return u256(a0 - a1)
        #
    elif name == 'MUL':
        a0, a1 = avs
        return u256(a0 * a1)
        #
    elif name == 'DIV':
        a0, a1 = avs
        return a0 // a1 if a1 != 0 else 0
        #
    elif name == 'MOD':
        a0, a1 = avs
        return a0 % a1 if a1 != 0 else 0
        #
    elif name == 'ADDMOD':
        a0, a1, a2 = avs
        return (a0 + a1) % a2 if a2 != 0 else 0
        #
    elif name == 'MULMOD':
        a0, a1, a2 = avs
        return (a0 * a1) % a2 if a2 != 0 else 0
        #
    elif name == 'EXP':
        a0, a1 = avs
        return u256(a0 ** a1) if a1 != 0 else 0
        #
    elif name == 'LT':
        a0, a1 = avs
        return 1 if a0 < a1 else 0
        #
    elif name == 'GT':
        a0, a1 = avs
        return 1 if a0 > a1 else 0
        #
    elif name == 'EQ':
        a0, a1 = avs
        return 1 if a0 == a1 else 0
        #
    elif name == 'ISZERO':
        a0, = avs
        return 1 if a0 == 0 else 0
        #
    elif name == 'AND':
        a0, a1 = avs
        return a0 & a1
        #
    elif name == 'OR':
        a0, a1 = avs
        return a0 | a1
        #
    elif name == 'XOR':
        a0, a1 = avs
        return a0 ^ a1
        #
    elif name == 'NOT':
        a0, = avs
        return u256(~a0)
        #
    elif name == 'BYTE':
        a0, a1 = avs
        return (a1 << (8 * a0)) & 0xFF00000000000000000000000000000000000000000000000000000000000000 if a0 < 32 else 0
    elif name == 'SHL':
        a0, a1 = avs
        return u256(a1 << a0) if a0 < 256 else 0
        #
    elif name == 'SHR':
        a0, a1 = avs
        return u256(a1 >> a0) if a0 < 256 else 0
        #
    elif name == 'SAR':
        a0, a1 = avs
        return u256(s256(a1) >> a0) if a0 < 256 else 0
        #
    elif name == 'MSTORE':
        _, a1, a2 = avs
        assert a1 + 32 <= len(state.mem)
        state.mem[a1:a1+32] = u256_to_bytes(a2)
        state.mem_modified = True
        return 0
        #
    elif name == 'MSTORE8':
        _, a1, a2 = avs
        state.mem[a1] = a2 & 0xFF
        state.mem_modified = True
        return 0
        #
    elif name == 'CALL':
        _, a1, a2, a3, a4, a5, a6, a7 = avs
        return _call_common(ctx, state, ctx['Address'], a1,             a2, a2,               a3, a4, a4+a5, a6, a6+a7)
        #
    elif name == 'CALLCODE':
        _, a1, a2, a3, a4, a5, a6, a7 = avs
        return _call_common(ctx, state, ctx['Address'], a1, ctx['Address'], a2,               a3, a4, a4+a5, a6, a6+a7)
        #
    elif name == 'DELEGATECALL':
        _, a1, a2, a3, a4, a5, a6 = avs
        return _call_common(ctx, state, ctx['Caller'],  a1, ctx['Address'], a2, ctx['Callvalue'], a3, a3+a4, a5, a5+a6)
        #
    elif name == 'STATICCALL':
        _, a1, a2, a3, a4, a5, a6 = avs
        return _call_common(ctx, state, ctx['Address'], a1, ctx['Address'], a2,                0, a3, a3+a4, a5, a5+a6)
        #
    elif name == 'MLOAD':
        _, a1 = avs
        assert a1 + 32 <= len(state.mem)
        return bytes_to_u256(state.mem[a1:a1+32])
        #
    elif name == 'SHA3':
        _, a1, a2 = avs
        assert a1 + a2 <= len(state.mem)
        return sha3(state.mem[a1:a1+a2])
        #
    elif name == 'SHA3i':
        return sha3(b''.join(
            u256_to_bytes(a)
            for a in avs
        ))
        #
    elif name == 'SLOAD':
        a0, = avs
        state.sloads.add(a0)
        v = ctx['Storage'].get(ctx['Address'], {}).get(a0)
        return v if v is not None else UnknownValue()
        #
    elif name == 'EXTCODESIZE':
        a0, = avs
        return UnknownValue()
        #
    elif name == 'RETURNDATASIZE':
        () = avs
        return UnknownValue()
        #
    elif name == 'FW':
        debug('!! FW detected !!')
        a0, = avs
        return a0
        #
    else:
        raise UnknownInstructionError(name)

def _call_common(ctx, state, caller, gaslim, addr, code_addr, value, i0, i1, o0, o1):
    assert i1 <= len(state.mem)
    if value > ctx['Callvalue']:
        return 0
    new_ctx              = ctx.copy()
    new_ctx['Gaslimit']  = min(gaslim, ctx['Gaslimit'])
    new_ctx['Address']   =      addr & ADDR_MASK
    new_ctx['Codeaddr']  = code_addr & ADDR_MASK
    new_ctx['Callvalue'] = value
    new_ctx['Calldata']  = bytes(state.mem[i0:i1])
    new_ctx['Caller']    = caller
    new_state            = ExecutionState()
    new_state.sloads     = state.sloads
    new_state.sstores    = state.sstores # for STATICCALL we could leave this empty, but let's be optimistic and keep it simple
    new_state.gaz        = state.gaz
    ok                   = execute_msg(new_ctx, new_state)
    state.gaz            = new_state.gaz
    # clear resulting mem, since we don't currently support return value
    _m    = state.mem[o0:o1]
    _m[:] = bytes(len(_m))
    return 1 if ok else 0
