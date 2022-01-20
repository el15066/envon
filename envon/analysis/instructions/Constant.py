
from .Instruction import Instruction

class Constant(Instruction):

    def __init__(self, en, block, value):
        super().__init__(en, block)
        self._value = value

    def __str__(self):
        s = f'{repr(self)} = {self.repr_name()}'
        if self.comment: s += f' // {self.comment}'
        return s

    def repr_name(self):
        return f'#{self._value:x}'

    def is_constant(self):
        return True

    def get_value(self):
        return self._value
