
from collections   import deque

from .Stack        import Stack
from .instructions import StackPhi, StackPhiLoopBreaker, MemPhi, DummyInstruction

from envon.helpers import Log

log = Log(__name__)

class BasicBlock:

    def __init__(self, analysis, offset, end):
        self._id_counter       = 0
        self.ns                = deque()
        self._phis             = []
        self._memphi           = None
        self._mem              = None
        self.stack             = Stack(self)
        self._analysis         = analysis
        self.offset            = offset
        self.end               = end
        self.skip              = False
        self._in_edges         = []
        self._fallthrough_edge = None
        self._jump_edges       = set()
        self.marked            = False
        self.marked_ints       = set()
        self.marked_ons        = None
        self.marked_avail_ons  = None

    def __repr__(self):
        return f'~{self.offset:x}'

    def __iter__(self):
        return iter(self.ns)

    def new_instruction_id(self):
        i = self._id_counter
        self._id_counter = i + 1
        return i

    def phis(self):
        return iter(self._phis)

    def _add_phi(self, phi):
        self._phis.append(phi)
        self.ns.appendleft(phi)

    def create_stack_phi(self, sp):
        if self.offset == 0: return DummyInstruction(self)
        else:
            if sp >= -90: phi = StackPhi(           self, sp)
            else:         phi = StackPhiLoopBreaker(self, sp) # arbitrarily stop stack dig loops
            self._add_phi(phi)
            return phi

    def in_edges(self):
        return iter(self._in_edges)

    def fallthrough_edge(self):
        return self._fallthrough_edge

    def jump_edges(self):
        return iter(self._jump_edges) # TODO: maybe frozenset?

    def out_edges(self):
        res = []
        b2  = self._fallthrough_edge
        if  b2 is not None:         res.append(b2)
        for b2 in self._jump_edges: res.append(b2)
        return res

    def accept_edge(self, src):
        assert not src.skip
        assert src not in self._in_edges
        self._in_edges.append(src)
        log.debug('!! NEW IN EDGE !!', src, self)
        for phi in self._phis:
            phi.refresh()

    def forget_edge(self, src):
        self._in_edges.remove(src)
        log.debug('!! REMOVED IN EDGE !!', src, self)
        for phi in self._phis:
            phi.refresh()

    def add_jump_to(self, offset):
        b = self._analysis.get_block_at(offset)
        if b is None or b in self._jump_edges: return None
        self._jump_edges.add(b)
        b.accept_edge(self)
        return b

    def remove_jump_edge(self, b):
        self._jump_edges.remove(b)
        b.forget_edge(self)

    def set_fallthrough_to(self, offset):
        assert self._fallthrough_edge is None
        b = self._analysis.get_block_at(offset)
        if b is not None:
            self._fallthrough_edge = b
            b.accept_edge(self)
        else:
            log.warning(f'Can\'t find fallthrough to {offset:x}')

    def remove_fallthrough_edge(self):
        b = self._fallthrough_edge
        if b is not None:
            self._fallthrough_edge = None
            b.forget_edge(self)
        return b

    def remove_edge(self, b):
        if b == self._fallthrough_edge:
            self.remove_fallthrough_edge()
        else:
            self.remove_jump_edge(b)

    def get_mem(self):
        n = self._mem
        if n is None:
            n = MemPhi(self)
            self._add_phi(n)
            self._memphi = n
            self._mem    = n
        return n

    def get_memphi(self):
        return self._memphi

    def set_mem(self, n):
        self._mem = n

    def get_jump(self):
        ns = self.ns
        if ns:
            n = ns[-1]
            if n.en().is_jump(): return n
        return None

    def has_multiple_out_edges(self):
        return (
            len(self._jump_edges) >  1 or
            len(self._jump_edges) == 1 and self._fallthrough_edge is not None
        )
