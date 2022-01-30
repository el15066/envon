
import sys
import random
import itertools

from Crypto.Hash import keccak

from envon.helpers import Log, u256, s256

log = Log(__name__)

def u256_to_bytes(x):
    return x.to_bytes(32, 'big')

def bytes_to_u256(x):
    return int.from_bytes(x, 'big')

def sha3(d):
    return bytes_to_u256(keccak.new(digest_bits=256).update(d).digest())

# DEBUG = True
DEBUG = False

ZEROS     = bytes(0x20)
ADDR_MASK = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

random.seed(123)
RANDOMS = bytes([random.getrandbits(8) for i in range(65536)])

UNKNOWN_SHA = sha3(b'UNKNOWN')

class hexint(int):
    def __repr__(self):
        return '#' + hex(self)[2:]

def hexify(x):
    if   type(x) is int:      return hexint(x)
    elif type(x) is tuple:    return tuple(hexify(v) for v in x)
    elif type(x) is list:     return      [hexify(v) for v in x]
    elif isinstance(x, dict): return {hexify(k): hexify(v) for k, v in x.items()}
    else:                     return x

def debug(*args, ctx=None, **kwargs):
    if DEBUG:
        if ctx: args = *args, 'tx', (ctx['Block'], ctx['Index'])
        print(*args, **kwargs, file=sys.stderr)

def warn(*args, ctx=None, **kwargs):
    if ctx: args = *args, 'tx', (ctx['Block'], ctx['Index'])
    print(*args, **kwargs, file=sys.stderr)
    pass

def not_found(*args, ctx=None, **kwargs):
    # if True:
    if DEBUG:
        f = warn if ctx and is_internal(ctx) else debug
        f(*args, ctx=ctx, **kwargs)

def is_internal(ctx):
    return ctx['Caller'] != ctx['Origin']

class UnknownInstructionError(Exception):
    pass

class EmptyPHIError(Exception):
    pass

class WarnError(Exception):
    pass

class Memory:

    def __init__(self, data=65536):
        self._data      = memoryview(bytearray(data))
        self.modified   = False
        self.unknown_i0 = -1
        self.unknown_i1 = -1

    def debug(self):
        if DEBUG and self.modified:
            self.modified = False
            for j in range(0, len(self._data), 0x20):
                w = self._data[j:j+0x20]
                if w != ZEROS:
                    debug(f'  mem {j:4x}  {w.hex()}')

    def _overlaps_unknown(self, i0, i1):
        return i1 > len(self._data) # or i0 < self.unknown_i1 and i1 > self.unknown_i0

    def _remove_unknown(self, i0, i1):
        if i1 > len(self._data): return False
        # self.modified = True
        # if i0 <= self.unknown_i0 <  i1: self.unknown_i0 = min(i1, self.unknown_i1)
        # if i0 <  self.unknown_i1 <= i1: self.unknown_i1 = max(i0, self.unknown_i0)
        return True

    def _add_unknown(self, i0, i1):
        if i1 > len(self._data): return False
        # self.modified = True
        # if i0 < self.unknown_i1 and i1 > self.unknown_i0:
        #     self.unknown_i0 = min(i0, self.unknown_i0)
        #     self.unknown_i1 = max(i1, self.unknown_i1)
        # else:
        #     self.unknown_i0 = i0
        #     self.unknown_i1 = i1
        return True

    def copy(self):
        r = Memory(self._data)
        r.modified   = self.modified
        r.unknown_i0 = self.unknown_i0
        r.unknown_i1 = self.unknown_i1
        return r

    def get_raw(self, i0, i1):
        if i1 > len(self._data): return bytes(min(i1-i0, 65536))
        else:                    return self._data[i0:i1]

    def get(self, i0, i1):
        if self._overlaps_unknown(i0, i1): return UnknownValue()
        else:                              return self._data[i0:i1]

    def get_u256(self, i0):
        i1 = i0 + 32
        if self._overlaps_unknown(i0, i1): return UnknownValue()
        else:                              return bytes_to_u256(self._data[i0:i1])

    def set(self, i0, i1, d):
        if self._remove_unknown(i0, i1):
            self._data[i0:i1] = d

    def set_u256(self, i0, d):
        i1 = i0 + 32
        if self._remove_unknown(i0, i1):
            self._data[i0:i1] = u256_to_bytes(d)

    def set_byte(self, i, d):
        if self._remove_unknown(i, i + 1):
            self._data[i] = d

    def set_unknown(self, i0, i1):
        if self._add_unknown(i0, i1):
            # still clear mem because unknown is approximate
            self._data[i0:i1] = RANDOMS[:i1-i0] # bytes(len(_m)) for 0s


class ExecutionState:

    def __init__(self):
        self.gaz      = 10000
        self.phiindex = 0
        self.sloads   = set()
        self.sstores  = set()
        self.mem      = Memory()
        self.saved_regs      = {0: 0}
        self.saved_cur_block = 'ENTRY'
        self.saved_i         = -1

    def copy(self):
        r = ExecutionState()
        r.gaz      = self.gaz
        r.phiindex = self.phiindex
        r.sloads   = self.sloads.copy()
        r.sstores  = self.sstores.copy()
        r.mem      = self.mem.copy()
        r.saved_regs      = self.saved_regs
        r.saved_cur_block = self.saved_cur_block
        r.saved_i         = self.saved_i
        return r


def execute_tx(ctx):
    debug('Storage', hexify(ctx['Storage']), ctx=ctx)
    state = ExecutionState()
    ok    = execute_msg(ctx, state)
    if ok is None or ok == True:
        res = set(
            u256_to_bytes(r).hex()
            for r in itertools.chain(state.sloads, state.sstores)
            if type(r) is int
        )
        print(f"Tx {ctx['Block']:8} {ctx['Index']:3} {ctx['Address']:040x}")
        if res:
            print('\n'.join(res))
            debug('\n'.join(res))

def execute_msg(ctx, state):
    a = None
    h = None
    try:
        a = ctx['Codeaddr']
        h = ctx['Codemap'][hexint(a)]
        d = ctx['Codedir']
        with open(f'{d}/h_{h:064x}.evmlike') as fic:
            code = [l[:-1] for l in fic]
    except KeyError as e:
        not_found('No code mapping for contract', f'{a:040x}', repr(e), ctx=ctx)
        pass
    except FileNotFoundError as e:
        not_found('No code file for contract', f'{a:040x}', repr(e), f'{d}/h_{h:064x}.evmlike', ctx=ctx)
        pass
    else:
        if code:
            lines = code[:-1]
            # for c in code: print(c)
            # gather = json.loads(code[-1])
            # print(ctx)
            debug('---> Executing contract at', f'{a:040x}', 'code hash', f'h_{h:064x}', 'lines', len(lines), ctx=ctx)
            ok = execute_with_jumps(ctx, state, lines)
            debug('---> Execution complete, ok', ok, ctx=ctx)
            return ok
        else:
            not_found('No code in file of', f'h_{h:064x}', ctx=ctx)
            pass
    return None

def execute_with_jumps(ctx, state, lines):
    #
    block_map  = {}
    for i, line in enumerate(lines):
        if line[0] == '~':
            block, _, _phimap = line.partition(' | ')
            phimap            = _phimap.split()
            block_map[block]  = (i-1, phimap)
    #
    state_q = [state]
    i_max   = len(lines) - 1
    try:
        while state_q:
            state     = state_q.pop()
            regs      = state.saved_regs
            cur_block = state.saved_cur_block
            i         = state.saved_i
            line      = ''
            debug('- Resuming at', i)
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
                        warn('At', i, line, 'phimap', phimap, 'cur_block', cur_block, repr(e), ctx=ctx)
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
                        state.mem.debug()
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
                            # t = v.target
                            # c = v.condition
                            # if type(c) is int:
                            #     if c != 0:
                            #         if t in block_map:
                            #             i, _ = block_map[t]
                            #         else:
                            #             break
                            # else:
                            #     assert type(c) is UnknownValue
                            #     if t in block_map:
                            #         debug('- Saving state at', i)
                            #         s2 = state.copy()
                            #         s2.saved_regs      = regs
                            #         s2.saved_cur_block = cur_block
                            #         s2.saved_i         = i
                            #         state_q.append(s2)
                            #         i, _ = block_map[t]
                        else:
                            raise WarnError('v is ' + repr(v))
                        #
                    except Exception as e:
                        log.exception('At', i, line, 'name', name, 'avs', hexify(avs), 'args', args, 'tx', (ctx['Block'], ctx['Index']))
                        if type(e) is not WarnError:
                            # break
                            return False
                    #
            if state.gaz <= 0:
                warn('Out of gaz' + (' (internal)' if is_internal(ctx) else ''), ctx=ctx)
            else:
                debug('Gaz left:', state.gaz, ctx=ctx)
    except:
        warn('line', i, line, ctx=ctx)
        raise
    #
    # for i, v in enumerate(regs): debug(f' {i:4} = {v:64x}')
    # res = [regs.get(i) for i in gather]
    # debug(hexify(regs))
    # debug(gather)
    # debug(hexify(res))
    return True


class UnknownValue:

    # def __init__(self, v):
    #     self.neg = False
    #     self.v   = v

    def __repr__(self):
        # return f'?({"!" if self.neg else ""}{self.v})'
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
        if type(c) is int:
            go = c != 0
        else:
            # r = random.randrange(10)
            # if   r == 0: go = False
            # elif r == 1: go = True
            # else:        go = t in block_map
            go = t in block_map
        #
        return t if go else ''


def _execute(ctx, state, name, avs):
    if   name == 'PHI':
        # for a in avs:
        #     if type(a) is int:
        #         return a
        # raise EmptyPHIError()
        return avs[state.phiindex]
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
        return ctx['Origin']
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
    elif name == 'GASLIMIT':
        () = avs
        return ctx['Gaslimit']
        #
    elif name == 'COINBASE':
        () = avs
        return ctx['Coinbase']
        #
    elif name == 'MSIZE':
        () = avs
        return 2048 # or UnknownValue()
        #
    elif name == 'RETURNDATASIZE':
        () = avs
        return UnknownValue()
        #
    elif name == 'CODESIZE':
        () = avs
        return UnknownValue()
        #
    elif name == 'GASPRICE':
        () = avs
        return UnknownValue()
        #
    elif name == 'JUMP':
        a0, = avs
        return JumpTarget(f'~{a0:x}' if type(a0) is int else '~', 1)
        #
    elif name == 'JUMPI':
        a0, a1 = avs
        return JumpTarget(f'~{a0:x}' if type(a0) is int else '~', a1)
        #
    elif name == 'SSTORE':
        a0, a1 = avs
        if type(a0) is int:
            state.sstores.add(a0)
            ctx['Storage'][ctx['Address']][a0] = a1
        return None
        #
    elif name == 'MSTORE':
        _, a1, a2 = avs
        if type(a1) is int:
            if type(a2) is int: state.mem.set_u256(   a1, a2)
            else:               state.mem.set_unknown(a1, a1+32)
        return None
        #
    elif name == 'MSTORE8':
        _, a1, a2 = avs
        if type(a1) is int:
            if type(a2) is int: state.mem.set_byte(   a1, a2 & 0xFF)
            else:               state.mem.set_unknown(a1, a1+1)
        return None
        #
    elif not all(type(av) is int for av in avs):
        return UnknownValue()
        #
    elif name == 'CALLDATALOAD':
        a0, = avs
        if a0 < 65536: return bytes_to_u256(ctx['Calldata'][a0:a0+32].ljust(32))
        else:          return UnknownValue()
        #
    elif name == 'CALLDATACOPY':
        _, a1, a2, a3 = avs
        if a2+a3 < 65536:
            state.mem.set(a1, a1+a3, ctx['Calldata'][a2:a2+a3].ljust(a3))
        return None
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
    elif name == 'SDIV':
        a0, a1 = avs
        return u256(s256(a0) // s256(a1)) if a1 != 0 else 0
        #
    elif name == 'MOD':
        a0, a1 = avs
        return a0 % a1 if a1 != 0 else 0
        #
    elif name == 'SMOD':
        a0, a1 = avs
        return u256(s256(a0) % s256(a1)) if a1 != 0 else 0
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
        if a1 == 0: return 1
        if a0 == 0: return 0
        if a0 == 1: return 1
        if a0 == 2: return u256(1 << min(a1, 256))
        if a1 > 256:
            warn('Too large EXP', a0, a1, ctx=ctx)
            return UnknownValue()
        return exp_u256(a0, a1)
        #
    elif name == 'SIGNEXTEND':
        a0, a1 = avs
        if a0 < 31:
            m = 1 << (8 * (a0 + 1))
            r = a1 & (m - 1)
            s = a1 &  m
            return u256(r - s)
        else:
            return a1
        #
    elif name == 'LT':
        a0, a1 = avs
        return 1 if a0 < a1 else 0
        #
    elif name == 'GT':
        a0, a1 = avs
        return 1 if a0 > a1 else 0
        #
    elif name == 'SLT':
        a0, a1 = avs
        return 1 if s256(a0) < s256(a1) else 0
        #
    elif name == 'SGT':
        a0, a1 = avs
        return 1 if s256(a0) > s256(a1) else 0
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
        return (a1 >> (8 * (31 - a0))) & 0xFF if a0 < 32 else 0
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
    elif name == 'CODECOPY':
        _, a1, a2, a3 = avs
        # clear mem, since we don't have runbin here
        state.mem.set_unknown(a1, a1+a3)
        return None
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
        return state.mem.get_u256(a1)
        #
    elif name == 'SHA3':
        _, a1, a2 = avs
        d = state.mem.get(a1, a1+a2)
        if type(d) is UnknownValue: return UNKNOWN_SHA
        else:                       return sha3(d)
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
        v = ctx['Storage'][ctx['Address']].get(a0)
        return v if v is not None else UnknownValue()
        #
    elif name == 'BLOCKHASH':
        a0, = avs
        return sha3(b'BLOCKHASH_' + u256_to_bytes(a0))
        #
    elif name == 'EXTCODESIZE':
        a0, = avs
        return UnknownValue()
        #
    elif name == 'BALANCE':
        a0, = avs
        return UnknownValue()
        #
    elif name == 'FW':
        warn('!! FW detected !!', ctx=ctx)
        a0, = avs
        return a0
        #
    else:
        raise UnknownInstructionError(name)

def _call_common(ctx, state, caller, gaslim, addr, code_addr, value, i0, i1, o0, o1):
    if value > ctx['Callvalue']:
        return 0
    new_ctx              = ctx.copy()
    new_ctx['Gaslimit']  = min(gaslim, ctx['Gaslimit'])
    new_ctx['Address']   =      addr & ADDR_MASK
    new_ctx['Codeaddr']  = code_addr & ADDR_MASK
    new_ctx['Callvalue'] = value
    new_ctx['Calldata']  = bytes(state.mem.get_raw(i0, i1))
    new_ctx['Caller']    = caller
    new_state            = ExecutionState()
    new_state.sloads     = state.sloads
    new_state.sstores    = state.sstores # for STATICCALL we could leave this empty, but let's be optimistic and keep it simple
    reserved_gaz         = state.gaz // 4
    new_state.gaz        = state.gaz - reserved_gaz
    ok                   = execute_msg(new_ctx, new_state)
    state.gaz            = new_state.gaz + reserved_gaz
    # clear resulting mem, since we don't currently support return value
    state.mem.set_unknown(o0, o1)
    if ok is None: return UnknownValue()
    else:          return 1 if ok else 0

def exp_u256(b, e):
    r = 1
    for _ in range(256):
        if e & 1: r = u256(r * b)
        b = u256(b * b)
        e >>= 1
    return r
