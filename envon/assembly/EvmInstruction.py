
from itertools import chain

# https://github.com/ethereum/yellowpaper @80085f7
instruction_list = (
    # Value, Mnemonic,          δ,  α  ->  opcode, name, pops, pushes
    (  0x00, 'STOP',            0,  0),
    (  0x01, 'ADD',             2,  1),
    (  0x02, 'MUL',             2,  1),
    (  0x03, 'SUB',             2,  1),
    (  0x04, 'DIV',             2,  1),
    (  0x05, 'SDIV',            2,  1),
    (  0x06, 'MOD',             2,  1),
    (  0x07, 'SMOD',            2,  1),
    (  0x08, 'ADDMOD',          3,  1),
    (  0x09, 'MULMOD',          3,  1),
    (  0x0a, 'EXP',             2,  1),
    (  0x0b, 'SIGNEXTEND',      2,  1),
    (),
    (),
    (),
    (),
    (  0x10, 'LT',              2,  1),
    (  0x11, 'GT',              2,  1),
    (  0x12, 'SLT',             2,  1),
    (  0x13, 'SGT',             2,  1),
    (  0x14, 'EQ',              2,  1),
    (  0x15, 'ISZERO',          1,  1),
    (  0x16, 'AND',             2,  1),
    (  0x17, 'OR',              2,  1),
    (  0x18, 'XOR',             2,  1),
    (  0x19, 'NOT',             1,  1),
    (  0x1a, 'BYTE',            2,  1),
    (  0x1b, 'SHL',             2,  1),
    (  0x1c, 'SHR',             2,  1),
    (  0x1d, 'SAR',             2,  1),
    (),
    (),
    (  0x20, 'SHA3',            2,  1),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (  0x30, 'ADDRESS',         0,  1),
    (  0x31, 'BALANCE',         1,  1),
    (  0x32, 'ORIGIN',          0,  1),
    (  0x33, 'CALLER',          0,  1),
    (  0x34, 'CALLVALUE',       0,  1),
    (  0x35, 'CALLDATALOAD',    1,  1),
    (  0x36, 'CALLDATASIZE',    0,  1),
    (  0x37, 'CALLDATACOPY',    3,  0),
    (  0x38, 'CODESIZE',        0,  1),
    (  0x39, 'CODECOPY',        3,  0),
    (  0x3a, 'GASPRICE',        0,  1),
    (  0x3b, 'EXTCODESIZE',     1,  1),
    (  0x3c, 'EXTCODECOPY',     4,  0),
    (  0x3d, 'RETURNDATASIZE',  0,  1),
    (  0x3e, 'RETURNDATACOPY',  3,  0),
    (  0x3f, 'EXTCODEHASH',     1,  1),
    (  0x40, 'BLOCKHASH',       1,  1),
    (  0x41, 'COINBASE',        0,  1),
    (  0x42, 'TIMESTAMP',       0,  1),
    (  0x43, 'NUMBER',          0,  1),
    (  0x44, 'DIFFICULTY',      0,  1),
    (  0x45, 'GASLIMIT',        0,  1),
    (  0x46, 'CHAINID',         0,  1),
    (  0x47, 'SELFBALANCE',     0,  1),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (  0x50, 'POP',             1,  0),
    (  0x51, 'MLOAD',           1,  1),
    (  0x52, 'MSTORE',          2,  0),
    (  0x53, 'MSTORE8',         2,  0),
    (  0x54, 'SLOAD',           1,  1),
    (  0x55, 'SSTORE',          2,  0),
    (  0x56, 'JUMP',            1,  0),
    (  0x57, 'JUMPI',           2,  0),
    (  0x58, 'PC',              0,  1),
    (  0x59, 'MSIZE',           0,  1),
    (  0x5a, 'GAS',             0,  1),
    (  0x5b, 'JUMPDEST',        0,  0),
    (),
    (),
    (),
    (),
    (  0x60, 'PUSH1',           0,  1),
    (  0x61, 'PUSH2',           0,  1),
    (  0x62, 'PUSH3',           0,  1),
    (  0x63, 'PUSH4',           0,  1),
    (  0x64, 'PUSH5',           0,  1),
    (  0x65, 'PUSH6',           0,  1),
    (  0x66, 'PUSH7',           0,  1),
    (  0x67, 'PUSH8',           0,  1),
    (  0x68, 'PUSH9',           0,  1),
    (  0x69, 'PUSH10',          0,  1),
    (  0x6a, 'PUSH11',          0,  1),
    (  0x6b, 'PUSH12',          0,  1),
    (  0x6c, 'PUSH13',          0,  1),
    (  0x6d, 'PUSH14',          0,  1),
    (  0x6e, 'PUSH15',          0,  1),
    (  0x6f, 'PUSH16',          0,  1),
    (  0x70, 'PUSH17',          0,  1),
    (  0x71, 'PUSH18',          0,  1),
    (  0x72, 'PUSH19',          0,  1),
    (  0x73, 'PUSH20',          0,  1),
    (  0x74, 'PUSH21',          0,  1),
    (  0x75, 'PUSH22',          0,  1),
    (  0x76, 'PUSH23',          0,  1),
    (  0x77, 'PUSH24',          0,  1),
    (  0x78, 'PUSH25',          0,  1),
    (  0x79, 'PUSH26',          0,  1),
    (  0x7a, 'PUSH27',          0,  1),
    (  0x7b, 'PUSH28',          0,  1),
    (  0x7c, 'PUSH29',          0,  1),
    (  0x7d, 'PUSH30',          0,  1),
    (  0x7e, 'PUSH31',          0,  1),
    (  0x7f, 'PUSH32',          0,  1),
    (  0x80, 'DUP1',            1,  2),
    (  0x81, 'DUP2',            2,  3),
    (  0x82, 'DUP3',            3,  4),
    (  0x83, 'DUP4',            4,  5),
    (  0x84, 'DUP5',            5,  6),
    (  0x85, 'DUP6',            6,  7),
    (  0x86, 'DUP7',            7,  8),
    (  0x87, 'DUP8',            8,  9),
    (  0x88, 'DUP9',            9, 10),
    (  0x89, 'DUP10',          10, 11),
    (  0x8a, 'DUP11',          11, 12),
    (  0x8b, 'DUP12',          12, 13),
    (  0x8c, 'DUP13',          13, 14),
    (  0x8d, 'DUP14',          14, 15),
    (  0x8e, 'DUP15',          15, 16),
    (  0x8f, 'DUP16',          16, 17),
    (  0x90, 'SWAP1',           2,  2),
    (  0x91, 'SWAP2',           3,  3),
    (  0x92, 'SWAP3',           4,  4),
    (  0x93, 'SWAP4',           5,  5),
    (  0x94, 'SWAP5',           6,  6),
    (  0x95, 'SWAP6',           7,  7),
    (  0x96, 'SWAP7',           8,  8),
    (  0x97, 'SWAP8',           9,  9),
    (  0x98, 'SWAP9',          10, 10),
    (  0x99, 'SWAP10',         11, 11),
    (  0x9a, 'SWAP11',         12, 12),
    (  0x9b, 'SWAP12',         13, 13),
    (  0x9c, 'SWAP13',         14, 14),
    (  0x9d, 'SWAP14',         15, 15),
    (  0x9e, 'SWAP15',         16, 16),
    (  0x9f, 'SWAP16',         17, 17),
    (  0xa0, 'LOG0',            2,  0),
    (  0xa1, 'LOG1',            3,  0),
    (  0xa2, 'LOG2',            4,  0),
    (  0xa3, 'LOG3',            5,  0),
    (  0xa4, 'LOG4',            6,  0),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (),
    (  0xf0, 'CREATE',          3,  1),
    (  0xf1, 'CALL',            7,  1),
    (  0xf2, 'CALLCODE',        7,  1),
    (  0xf3, 'RETURN',          2,  0),
    (  0xf4, 'DELEGATECALL',    6,  1),
    (  0xf5, 'CREATE2',         4,  1),
    (),
    (),
    (),
    (),
    (  0xfa, 'STATICCALL',      6,  1),
    (),
    (),
    (  0xfd, 'REVERT',          2,  0),
    (  0xfe, 'INVALID',         0,  0),
    (  0xff, 'SELFDESTRUCT',    1,  0),
    #
    # the following are pseudo-instructions that help with analysis
    #
    ( 0x100, 'DUMMY',           0,  1),
    ( 0x101, 'PHI',             0,  0),
)

instruction_map = {}

for t in instruction_list:
    if t:
        instruction_map[t[1]] = t[0]

OPCODE_DUMMY    = instruction_map['DUMMY']
OPCODE_PHI      = instruction_map['PHI']

OPCODE_POP      = instruction_map['POP']
OPCODE_PUSH1    = instruction_map['PUSH1']
OPCODE_PUSH32   = instruction_map['PUSH32']
OPCODE_DUP1     = instruction_map['DUP1']
OPCODE_DUP16    = instruction_map['DUP16']
OPCODE_SWAP1    = instruction_map['SWAP1']
OPCODE_SWAP16   = instruction_map['SWAP16']
OPCODE_LOG0     = instruction_map['LOG0']
OPCODE_LOG4     = instruction_map['LOG4']
OPCODE_JUMPDEST = instruction_map['JUMPDEST']

OPCODES_RARE = tuple(instruction_map[t] for t in (
    'CREATE',
    'CREATE2',
    'INVALID',
    'REVERT',
    'SELFDESTRUCT',
))

OPCODES_JUMP = tuple(instruction_map[t] for t in (
    'JUMP',
    'JUMPI',
))

OPCODES_TERMINATOR = tuple(instruction_map[t] for t in (
    'INVALID',
    'JUMP',
    'JUMPI',
    'RETURN',
    'REVERT',
    'SELFDESTRUCT',
    'STOP',
))

OPCODES_FINAL = tuple(instruction_map[t] for t in (
    'INVALID',
    'RETURN',
    'REVERT',
    'SELFDESTRUCT',
    'STOP',
))

OPCODES_STOP_FALLTHROUGH = tuple(instruction_map[t] for t in (
    'INVALID',
    'JUMP',
    'RETURN',
    'REVERT',
    'SELFDESTRUCT',
    'STOP',
))

OPCODES_READ_MEMORY = tuple(chain(
    (instruction_map[t] for t in (
        'CALL',
        'CALLCODE',
        'CREATE',
        'DELEGATECALL',
        'MLOAD',
        'RETURN',
        'SHA3',
        'STATICCALL',
    )),
    range(OPCODE_LOG0, OPCODE_LOG4),
))

OPCODES_WRITE_MEMORY = tuple(instruction_map[t] for t in (
    'CALL',
    'CALLCODE',
    'CALLDATACOPY',
    'CODECOPY',
    'DELEGATECALL',
    'EXTCODECOPY',
    'MSTORE',
    'MSTORE8',
    'RETURNDATACOPY',
    'STATICCALL',
))

OPCODES_COMMUTE_FIRST_SECOND = tuple(instruction_map[t] for t in (
    'ADD',
    'ADDMOD',
    'AND',
    'EQ',
    'MUL',
    'MULMOD',
    'OR',
    'XOR',
))

class EvmInstruction:

    def __init__(self, offset, opcode, push_value=None):
        self._offset     = offset
        self._opcode     = opcode
        self._push_value = push_value

    def offset(    self): return self._offset
    def opcode(    self): return self._opcode
    def push_value(self): return self._push_value
    def data(      self): return instruction_list[self._opcode]
    def name(      self): return self.data()[1]
    def pops(      self): return self.data()[2]
    def pushes(    self): return self.data()[3]

    def is_pop(               self): return self._opcode == OPCODE_POP
    def is_push(              self): return OPCODE_PUSH1 <= self._opcode <= OPCODE_PUSH32
    def is_dup(               self): return OPCODE_DUP1  <= self._opcode <= OPCODE_DUP16
    def is_swap(              self): return OPCODE_SWAP1 <= self._opcode <= OPCODE_SWAP16
    def is_jumpdest(          self): return self._opcode == OPCODE_JUMPDEST
    def is_rare(              self): return self._opcode in OPCODES_RARE
    def is_jump(              self): return self._opcode in OPCODES_JUMP
    def is_terminator(        self): return self._opcode in OPCODES_TERMINATOR
    def is_final(             self): return self._opcode in OPCODES_FINAL
    def  stops_fallthrough(   self): return self._opcode in OPCODES_STOP_FALLTHROUGH
    def  reads_memory(        self): return self._opcode in OPCODES_READ_MEMORY
    def writes_memory(        self): return self._opcode in OPCODES_WRITE_MEMORY
    def  needs_memory(        self): return self.reads_memory() or self.writes_memory()
    def commutes_first_second(self): return self._opcode in OPCODES_COMMUTE_FIRST_SECOND

    def size(self):
        if self.is_push(): return 2 + self._opcode - OPCODE_PUSH1
        else:              return 1

def DummyEvmInstruction(offset): return EvmInstruction(offset, OPCODE_DUMMY)
def PhiEvmInstruction(  offset): return EvmInstruction(offset, OPCODE_PHI)
