
from envon.analysis.Valuation import is_valuation

ID_COUNTER = 0

def NEW_ID():
    global ID_COUNTER
    i = ID_COUNTER
    ID_COUNTER = i + 1
    return i

class Instruction:

    def __init__(self, en, block):
        self._id       = NEW_ID()
        self._lid      = block.new_instruction_id()
        self._en       = en
        self._block    = block
        self._args     = []
        self._uses     = set()
        self.comment   = None
        self.valuation = None
        self.marked    = False
        self.is_origin = True

    def __str__(self):
        s = f'{repr(self)} = {self.repr_name()}({repr(self._args)[1:-1]})'
        if self.comment: s += f' // {self.comment}'
        return s

    def repr_global(self):
        return f'%{self._id}'               # LLVM-style global numbering

    def repr_global_short(self):
        return f'%{self._id}'

    def repr_local(self):
        return f'{self._block}.{self._lid}' # Block-local numbering prefixed with block id

    def repr_local_short(self):
        return f'.{self._lid}'              # Block-local numbering

    def repr_name(self):
        return self._en.name()

    def repr_val_int_short(self):
        return f'#{self.valuation:x}'[:5] if type(self.valuation) is int else ''

    __repr__   = repr_local
    repr_short = repr_local_short

    def __hash__(self):
        return hash(('Instruction', self._id))

    def en(self):
        return self._en

    def args(self):
        return iter(self._args)

    def args_count(self):
        return len(self._args)

    def is_constant(self):
        # pylint: disable=no-self-use
        return False

    def is_phi(self):
        # pylint: disable=no-self-use
        return False

    def is_memphi(self):
        # pylint: disable=no-self-use
        return False

    def uses(self):
        return iter(self._uses)

    def add_use(self, a):
        self._uses.add(a)

    def remove_use(self, a):
        self._uses.discard(a)

    def get_arg(self, i):
        return self._args[i]

    def append_arg(self, a):
        self._args.append(a)
        a.add_use(self)

    def clear_args(self):
        for a in self._args:
            a.remove_use(self)
        self._args.clear()

    def _some_possible_values(self, depth):
        res = set()
        if   type(self.valuation) is int: res.add(self.valuation)
        elif self.is_constant():          res.add(self.get_value())
        elif self.is_phi() and depth:
            for a in self._args:
                res |= a._some_possible_values(depth - 1) # pylint: disable=protected-access
        return res

    def some_possible_values(self):
        v = self.valuation
        if is_valuation(v) and v.possible_values is not None:
            return self._some_possible_values(5) | set(v.possible_values)
        else:
            return self._some_possible_values(7)
