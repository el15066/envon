
from collections import deque #, defaultdict

from .Mempad       import Mempad
from .Valuation    import Valuation, is_valuation, latest_valuation
from .events       import events

from envon.graph   import make_graph_file
from envon.helpers import Log

log = Log(__name__)

def general_worklist(initial_updates):
    wl = deque()
    wl.extend(initial_updates)
    seen = set()
    while wl:
        u = wl.popleft()
        if type(u) is ValuationUpdate: seen.discard(u.node)
        # log.debug('u', u)
        new_updates = []
        for u2 in u.apply():
            if type(u2) is ValuationUpdate:
                if u2.node in seen:
                    continue
                seen.add(u2.node)
            new_updates.append(u2)
        # log.debug('u', u, '->', new_updates)
        wl.extend(new_updates)       # BFS
        # wl.extendleft(new_updates) # DFS
        yield wl

def find_heads(analysis):
    for b in analysis:
        for n in b:
            if not n.args_count():
                yield n

class Optimizer:

    def __init__(self):
        self.graph_requested = True
        self.dead_phis       = set()

    def optimize(self, analysis):
        log.info('Running optimizer')
        #
        iu = []
        self.processEvents(iu)
        #
        for b in analysis:
            iu.append(BlockSkipUpdate(b))
        #
        for h in find_heads(analysis):
            iu.append(ValuationUpdate(self, h))
        #
        max_i = 400000
        graph_count = 0
        for i, wl in enumerate(general_worklist(iu)):
            if  self.graph_requested or i > max_i:
                if i > max_i + 50:
                    import sys
                    log.error('Too many worklist updates')
                    sys.exit(1)
                self.graph_requested = False
                make_graph_file(analysis, set(u.node for u in wl if hasattr(u, 'node')))
                graph_count += 1
                if graph_count > 150: i = max_i
            self.processEvents(wl)
        #
        log.info('Optimizer complete')

    def processEvents(self, wl):
        for ev in events.get_and_clear():
            t    = ev[0]
            args = ev[1:]
            if t == 'New PHI':
                phi, = args
                u = PHIRefreshUpdate(self, phi)
                # log.debug('ev', ev, '->', u)
                wl.append(u)


def mark_blocks(blocks):
    todo = [
        MarkBlockUpdate(b)
        for b in blocks
    ]
    for _ in general_worklist(todo): pass

def mark_instructions(instructions):
    todo = [
        MarkInstructionUpdate(n)
        for n in instructions
    ]
    for _ in general_worklist(todo): pass

def mark_by_valuation(valuations):
    todo = [
        MarkByValuationUpdate(v)
        for v in valuations
    ]
    for _ in general_worklist(todo): pass

def u256(x):
    return x & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

def s256(x):
    return (((x + 0x8000000000000000000000000000000000000000000000000000000000000000)
                & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
                - 0x8000000000000000000000000000000000000000000000000000000000000000)


class PHIRefreshUpdate:

    def __init__(self, optimizer, node):
        self.optimizer = optimizer
        self.node      = node

    def __repr__(self):
        return 'PHI(' + repr(self.node) + ')'

    def apply(self):
        phi = self.node
        phi.refresh()
        return [ValuationUpdate(self.optimizer, phi)]


def _forward(v, n, avsh):
    return v.forward(n, avsh) if is_valuation(v) else v

class ValuationUpdate:

    def __init__(self, optimizer, node):
        self.optimizer = optimizer
        self.node      = node

    def __repr__(self):
        return 'V(' + repr(self.node) + ')'

    def apply(self):
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        res   = []
        n     = self.node
        v     = None
        v_old = n.valuation
        name  = n.en().name()
        avs   = tuple(a.valuation for a in n.args())
        if n.en().commutes_first_second():
            a0, a1 = avs[:2]
            if hash(a0) > hash(a1):
                avs = (a1, a0, *avs[2:])
        avsh = hash(avs)
        #
        if is_valuation(v_old) and v_old.avsh == avsh:             return res
        if not n.is_phi() and not all(a is not None for a in avs): return res
        #
        if   n.is_constant():
            v = n.get_value() # int
            #
        elif n.is_phi():
            #
            if n.is_memphi():
                v = Mempad(n, name, avs, avsh, {})
                v.meet(avs)
                v.finalize(n._id)
            else:
                q = set()
                t = set()
                for a in avs:
                    if a is not None:
                        # if a == v_old and is_valuation(a) and a.node == n: # this is not sufficient to conclude `a` came from `n`
                        #                                                    # in case all the inputs are the same as `v_old`, `t` will be empty
                        if is_valuation(a):
                            # if a == v_old and v_old.name == 'PHI': # this is sufficient to conclude `a` came from `v_old` and `v_old` was created here (at `n`)
                            #                                        # but not necessary (i.e. in case there are 2 or more loops through `n`)
                            o = a.origin
                            if o == n:
                                # me = PHI(me, ...rest) <=> me = PHI(...rest)
                                continue
                            if o in self.optimizer.dead_phis:
                                #
                                continue
                            if a.possible_values is not None:
                                for aa in a.possible_values:
                                    t.add(aa)
                        else:
                            assert type(a) is int, a
                            t.add(a)
                        q.add(a)
                # q.discard(v_old)
                assert all(type(a) is int for a in t)
                t = tuple(sorted(t))
                #
                if len(q) == 1:
                    self.optimizer.dead_phis.add(n)
                    v = _forward(q.pop(), n, avsh)
                else:
                    self.optimizer.dead_phis.discard(n)
                    v = Valuation(n, name, avs, avsh, _hash=hash(('PHI', n._id, t)), possible_values=t)
            #
        elif name == 'ADD':
            a0, a1 = avs
            if   a0 == 0:                             v = a1
            elif a1 == 0:                             v = a0
            elif type(a0) is int and type(a1) is int: v = u256(a0 + a1)
            #
        elif name == 'SUB':
            a0, a1 = avs
            if   a1 == 0:                             v = a0
            elif a0 == a1:                            v = 0
            elif type(a0) is int and type(a1) is int: v = u256(a0 - a1)
            #
        elif name == 'MUL':
            a0, a1 = avs
            if   a0 == 0:                             v = 0
            elif a1 == 0:                             v = 0
            elif a0 == 1:                             v = a1
            elif a1 == 1:                             v = a0
            elif type(a0) is int and type(a1) is int: v = u256(a0 * a1)
            #
        elif name == 'DIV':
            a0, a1 = avs
            if   a0 == 0:                             v = 0
            elif a1 == 0:                             v = 0
            elif a1 == 1:                             v = a0
            # elif a0 == a1:                            v = 1 # can't do because 0/0=0
            elif type(a0) is int and type(a1) is int: v = a0 // a1
            #
        elif name == 'MOD':
            a0, a1 = avs
            if   a0 == 0:                             v = 0
            elif a1 in (0, 1, -1):                    v = 0
            elif a0 == a1:                            v = 0
            elif type(a0) is int and type(a1) is int: v = a0 % a1
            #
        elif name == 'ADDMOD':
            a0, a1, a2 = avs
            if   a2 in (0, 1, -1):                    v = 0
            elif all(type(a) is int for a in avs):    v = (a0 + a1) % a2
            #
        elif name == 'MULMOD':
            a0, a1, a2 = avs
            if   a0 == 0:                             v = 0
            elif a1 == 0:                             v = 0
            elif a2 in (0, 1, -1):                    v = 0
            elif all(type(a) is int for a in avs):    v = (a0 * a1) % a2
            #
        elif name == 'EXP':
            a0, a1 = avs
            if   a1 == 0:                             v = 1 # 0**0 = 1 (yellowpaper p.21)
            elif a0 == 0:                             v = 0
            elif a0 == 1:                             v = 1
            elif a1 == 1:                             v = a0
            elif type(a0) is int and type(a1) is int: v = u256(a0 ** a1)
            #
        elif name == 'LT':
            a0, a1 = avs
            if   a1 == 0:                             v = 0
            elif type(a0) is int and type(a1) is int: v = 1 if a0 < a1 else 0
            #
        elif name == 'GT':
            a0, a1 = avs
            if   a0 == 0:                             v = 0
            elif type(a0) is int and type(a1) is int: v = 1 if a0 > a1 else 0
            #
        elif name == 'EQ':
            a0, a1 = avs
            if   a0 == a1:                            v = 1
            elif type(a0) is int and type(a1) is int: v = 1 if a0 == a1 else 0
            #
        elif name == 'ISZERO':
            a0, = avs
            if   type(a0) is int:                     v = 1 if a0 == 0 else 0
            #
        elif name == 'AND':
            a0, a1 = avs
            if   a0 == 0:                             v = 0
            elif a1 == 0:                             v = 0
            elif a0 == a1:                            v = a0
            elif type(a0) is int and type(a1) is int: v = a0 & a1
            #
        elif name == 'OR':
            a0, a1 = avs
            if   a0 == 0:                             v = a1
            elif a1 == 0:                             v = a0
            elif a0 == a1:                            v = a0
            elif type(a0) is int and type(a1) is int: v = a0 | a1
            #
        elif name == 'XOR':
            a0, a1 = avs
            if   a0 == 0:                             v = a1
            elif a1 == 0:                             v = a0
            elif a0 == a1:                            v = 0
            elif type(a0) is int and type(a1) is int: v = a0 ^ a1
            #
        elif name == 'NOT':
            a0, = avs
            if   type(a0) is int:                     v = u256(~a0)
            #
        elif name == 'BYTE':
            a0, a1 = avs
            if type(a0) is int:
                if a0 >= 32:                          v = 0
                elif type(a1) is int:                 v = (a1 << (8 * a0)) & 0xFF00000000000000000000000000000000000000000000000000000000000000
        elif name == 'SHL':
            a0, a1 = avs
            if type(a0) is int:
                if a0 >= 256:                         v = 0
                elif type(a1) is int:                 v = u256(a1 << a0)
            #
        elif name == 'SHR':
            a0, a1 = avs
            if type(a0) is int:
                if a0 >= 256:                         v = 0
                elif type(a1) is int:                 v = u256(a1 >> a0)
            #
        elif name == 'SAR':
            a0, a1 = avs
            if type(a0) is int:
                if a0 >= 256:                         v = 0
                elif type(a1) is int:                 v = u256(s256(a1) >> a0)
            #
        elif name in ('JUMP', 'JUMPI'):
            #
            b        = n._block
            can_jump = True
            #
            if name == 'JUMP':
                a0,    = avs
            else:
                a0, a1 = avs
                if type(a1) is int:
                    if a1 == 0:
                        log.debug('!! CERTAIN EDGE (Not Taken) !!', b)
                        can_jump = False
                        for b2 in list(b.jump_edges()):
                            b.remove_jump_edge(b2)
                            self._edge_update(res, b2)
                    else:
                        log.debug('!! CERTAIN EDGE (Taken) !!', b)
                        b2 = b.remove_fallthrough_edge()
                        self._edge_update(res, b2)
            #
            if can_jump:
                dsts = n.get_arg(0).some_possible_values()
                # add missing edges
                for dst in dsts:
                    b2 = b.add_jump_to(dst)
                    self._edge_update(res, b2)
                # remove unneeded edges
                to_remove = [
                    b2 for b2 in b.jump_edges() if b2.offset not in dsts
                ]
                for b2 in to_remove:
                    b.remove_jump_edge(b2)
                    self._edge_update(res, b2)
            #
            if type(a0) is int:
                res.append(BlockSkipUpdate(b))
            #
        elif name == 'MSTORE':
            m, a1, a2 = avs
            if type(a1) is int:
                v = Mempad(n, name, avs, avsh, m.bytemap_copy())
                v.store32(a1, n.get_arg(2))
            else:
                v = Mempad(n, name, avs, avsh, {})
            v.finalize()
            #
        elif name == 'MSTORE8':
            m, a1, a2 = avs
            if type(a1) is int:
                v = Mempad(n, name, avs, avsh, m.bytemap_copy())
                v.store(  a1, n.get_arg(2))
            else:
                v = Mempad(n, name, avs, avsh, {})
            v.finalize()
            #
        elif name == 'MLOAD':
            m, a1 = avs
            if type(a1) is int:
                t = m.load32(a1)
                if t is not None:
                    v = t.valuation
            # if v is None:
            #     v = Valuation(n, 'MLOAD', (), avsh, _hash=hash(('MLOAD', n._id)))
            #
        elif name == 'SHA3':
            m, a1, a2 = avs
            if type(a1) is int and type(a2) is int:
                ans = m.load_region(a1, a2)
                if ans is not None:
                    v = Valuation(n, 'SHA3i', tuple(an.valuation for an in ans), avsh)
            #
        elif name in ('CALL', 'CALLCODE'):
            m, a1, a2, a3, _, a5, a6, a7 = avs
            if type(a6) is int and type(a7) is int:
                v = Mempad(n, name, avs, avsh, m.bytemap_copy())
                v.clear_region(a6, a7)
            else:
                v = Mempad(n, name, avs, avsh, {})
            v.finalize()
            #
        elif name in ('DELEGATECALL', 'STATICCALL'):
            m, a1, a2, a3, _, a5, a6 = avs
            if type(a5) is int and type(a6) is int:
                v = Mempad(n, name, avs, avsh, m.bytemap_copy())
                v.clear_region(a5, a6)
            else:
                v = Mempad(n, name, avs, avsh, {})
            v.finalize()
            #
        elif name == 'CODECOPY':
            m, a1, a2, a3 = avs
            if type(a1) is int:
                v = Mempad(n, name, avs, avsh, m.bytemap_copy())
                if type(a3) is int:
                    v.clear_region(a1, a3)
                    # v.store_region(a1, a3, n) # can't do that now, n needs to be replaced
                    # TODO if a2 is also int, we can lookup the exact value from the bytecode
                else:
                    v.clear_region(a1, 'inf')
            else:
                v = Mempad(n, name, avs, avsh, {})
            v.finalize()
            #
        elif n.en().writes_memory():
            v = Mempad(n, name, avs, avsh, {})
            v.finalize()
        #
        if v is None:
            v = Valuation(n, name, avs, avsh)
        #
        if v != n.valuation:
            for r in self.node.uses():
                res.append(ValuationUpdate(self.optimizer, r))
        n.valuation = v
        if type(v) is int:
            if not n.is_constant():
                n.comment = f'#{v:x}'
            assert v == u256(v), str(n)
        else:
            n.comment = str(v)
        return res

    def _edge_update(self, res, b2):
        if b2 is not None:
            self.optimizer.graph_requested = True
            for phi in b2.phis():
                res.append(ValuationUpdate(self.optimizer, phi))


def is_final(b):
    return b.ns and b.ns[-1].en().is_final()

def all_out_edges_are_known(b):
    return not (
                 b.ns
        and      b.ns[-1].en().is_jump()
        and type(b.ns[-1].valuation) is not int
    )

class BlockSkipUpdate:

    def __init__(self, block):
        self.block = block

    def __repr__(self):
        return 'SKIP(' + repr(self.block) + ')'

    def apply(self):
        res = []
        b   = self.block
        if (
                not b.skip
            and (not b.fallthrough_edge() or b.fallthrough_edge().skip)
            and all(e.skip for e in b.jump_edges())
            and not is_final(b)
            and all_out_edges_are_known(b)
        ):
            b.skip = True
            for b2 in b.in_edges():
                # b2.remove_edge(b) # don't remove edges
                res.append(BlockSkipUpdate(b2))
        return res

class MarkBlockUpdate:

    def __init__(self, block):
        self.block = block

    def __repr__(self):
        return 'MARK(' + repr(self.block) + ')'

    def apply(self):
        res = []
        b = self.block
        if not b.marked:
            b.marked = True
            for b2 in b.in_edges():
                res.append(MarkBlockUpdate(b2))
        return res

class MarkInstructionUpdate:

    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return 'MARK(' + repr(self.node) + ')'

    def apply(self):
        res = []
        n = self.node
        if not n.marked:
            n.marked = True
            for n2 in n.args():
                res.append(MarkInstructionUpdate(n2))
        return res

class MarkByValuationUpdate:

    def __init__(self, valuation):
        self.valuation = valuation

    def __repr__(self):
        return 'MARK(' + repr(self.valuation) + ')'

    def apply(self):
        res = []
        v   = self.valuation
        n   = v.node
        if not n.marked:
            n.marked = True
            # if v.origin is not None:
            #     res.append(MarkByValuationUpdate(v.origin))
            # else:
            for av in v.avs:
                av = latest_valuation(av)
                if av is None:
                    res = []
                    # TODO: maybe add mark revert update(s) ?
                    break
                elif type(av) is int: n._block.marked_ints.add(av)
                else:                 res.append(MarkByValuationUpdate(av))
        return res

class MarkDepsByValuationUpdate:

    def __init__(self, valuation):
        self.valuation = valuation

    def __repr__(self):
        return 'MARK_DEPS(' + repr(self.valuation) + ')'

    def apply(self):
        res = []
        v   = self.valuation
        n   = v.node
        for av in v.avs:
            av = latest_valuation(av)
            if av is None:
                res = []
                # TODO: maybe add mark revert update(s) ?
                break
            elif type(av) is int:
                n._block.marked_ints.add(av)
            else:
                if not av.marked:
                    av.marked = True
                    res.append(MarkDepsByValuationUpdate(av))
        return res