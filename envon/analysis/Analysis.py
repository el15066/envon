
from .BasicBlock   import BasicBlock
from .instructions import Instruction, Constant

from envon.helpers import Log

log = Log(__name__)

class Analysis:

    def __init__(self):
        self._blocks    = []
        self._block_map = {}

    def __iter__(self):
        for b in self._blocks:
            if not b.skip:
                yield b

    def get_entry_block(self):
        return self._blocks[0]

    def get_block_at(self, offset):
        if offset == 0:
            return None # use get_entry_block() for this
        b = self._block_map.get(offset)
        # if b is not None and b.skip:
        #     b = None
        return b

    def get_end(self):
        return self._blocks[-1].end

    def analyze(self, ens, allow_skip):
        assert not self._blocks
        self._prepare_basic_blocks(ens)
        self._fill_blocks(ens, allow_skip)
        self._link_fallthroughs()
        self._link_some_jumps()

    def _prepare_basic_blocks(self, ens):
        breaks = [0]
        for en in ens:
            if   en.is_jumpdest():   breaks.append(en.offset())
            elif en.is_terminator(): breaks.append(en.offset() + en.size())
        breaks.append(ens[-1].offset() + ens[-1].size())
        #
        begins = iter(breaks)
        ends   = iter(breaks)
        next(ends)
        for i0, i1 in zip(begins, ends):
            if i1 > i0:
                b = BasicBlock(self, i0, i1)
                self._blocks.append(b)
                self._block_map[i0] = b

    def _fill_blocks(self, ens, allow_skip):
        l = len(ens)
        j = 0
        for b in self:
            while j < l and ens[j].offset() < b.offset: j += 1
            while j < l:
                en = ens[j]
                if en.offset() >= b.end: break
                j += 1
                #
                if   en.is_jumpdest():                           continue
                elif en.is_pop():      b.stack.pop();            continue
                elif en.is_dup():      b.stack.dup( -en.pops()); continue
                elif en.is_swap():     b.stack.swap(-en.pops()); continue
                elif en.is_push():     n = Constant(   en, b, en.push_value())
                else:                  n = Instruction(en, b)
                #
                if en.needs_memory():
                    n.append_arg(b.get_mem())
                    if en.writes_memory():
                        b.set_mem(n)
                #
                for _ in range(en.pops()):
                    n.append_arg(b.stack.pop())
                #
                if en.pushes() > 0:
                    assert en.pushes() == 1
                    b.stack.push(n)
                #
                b.ns.append(n)
                n = None
                #
                if allow_skip and en.is_rare():
                    b.skip = True

    def _link_fallthroughs(self):
        bs = list(self)
        if bs[-1] is self._blocks[-1]: bs.pop()
        #
        for b in bs:
            if b.ns and b.ns[-1].en().stops_fallthrough(): continue
            b.set_fallthrough()

    def _link_some_jumps(self):
        for b in self:
            if b.ns:
                last = b.ns[-1]
                if last.en().is_jump():
                    for dst in last.get_arg(0).some_possible_values():
                        b.add_jump_to(dst)
