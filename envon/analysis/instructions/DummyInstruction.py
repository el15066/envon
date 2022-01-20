
from .Instruction import Instruction

from envon.assembly import DummyEvmInstruction

class DummyInstruction(Instruction):

    def __init__(self, block):
        en = DummyEvmInstruction(block.offset)
        super().__init__(en, block)
