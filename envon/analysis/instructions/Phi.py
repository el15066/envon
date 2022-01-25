
from .Instruction      import Instruction
from .DummyInstruction import DummyInstruction

from envon.assembly        import PhiEvmInstruction
from envon.analysis.events import events

class Phi(Instruction):

    def __init__(self, block):
        en = PhiEvmInstruction(block.offset)
        super().__init__(en, block)
        events.new_event(('New PHI', self))

    def repr_name(self):
        return 'PHI' + repr(self._block)

    def is_phi(self):
        return True

    def refresh(self):
        self.clear_args()
        for edge in self._block.in_edges():
            n = self._get_arg_from(edge)
            self.append_arg(n)

    def _get_arg_from(self, edge):
        raise NotImplementedError


class StackPhi(Phi):

    def __init__(self, block, sp):
        assert sp < 0
        super().__init__(block)
        self._sp = sp

    def repr_name(self):
        return super().repr_name() + f'[{self._sp}]'

    def _get_arg_from(self, edge):
        return edge.stack.get(self._sp)


class StackPhiLoopBreaker(StackPhi):

    def repr_name(self):
        return f'PHI~LB[{self._sp}]'

    def _get_arg_from(self, edge):
        return DummyInstruction(self._block)


class MemPhi(Phi):

    def is_memphi(self):
        return True

    def repr_name(self):
        return super().repr_name() + '-MEM'

    def _get_arg_from(self, edge):
        return edge.get_mem()
