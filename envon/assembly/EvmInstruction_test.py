
from .EvmInstruction import instruction_list

from envon.helpers import Log

log = Log(__name__)

def instruction_list_test():
    assert len(instruction_list) == 256 + 2
    try:
        for i, t in enumerate(instruction_list):
            if t:
                opcode, name, pops, pushes = t
                assert i == opcode
                assert type(name) is str
                assert len(name) > 1
                assert 0 <= pops   <= 17
                assert 0 <= pushes <=  1
    except (ValueError, AssertionError):
        log.error('In instruction_list i =', i, 't =', t)
        raise
