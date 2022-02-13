
IIT = {
    # NAME -> opcode, regc_min, regc_max, has_rd, uses_mem
    'STOP':           (   0,  0,  0, False, False ),
    'CONSTANT__1':    (   1, -1, -1,  True, False ),
    'CONSTANT__2':    (   2, -1, -1,  True, False ),
    'CONSTANT__3':    (   3, -1, -1,  True, False ),
    'CONSTANT__4':    (   4, -1, -1,  True, False ),
    'CONSTANT__5':    (   5, -1, -1,  True, False ),
    'CONSTANT__6':    (   6, -1, -1,  True, False ),
    'CONSTANT__7':    (   7, -1, -1,  True, False ),
    'CONSTANT__8':    (   8, -1, -1,  True, False ),
    'CONSTANT__9':    (   9, -1, -1,  True, False ),
    'CONSTANT_10':    (  10, -1, -1,  True, False ),
    'CONSTANT_11':    (  11, -1, -1,  True, False ),
    'CONSTANT_12':    (  12, -1, -1,  True, False ),
    'CONSTANT_13':    (  13, -1, -1,  True, False ),
    'CONSTANT_14':    (  14, -1, -1,  True, False ),
    'CONSTANT_15':    (  15, -1, -1,  True, False ),
    'CONSTANT_16':    (  16, -1, -1,  True, False ),
    'CONSTANT_17':    (  17, -1, -1,  True, False ),
    'CONSTANT_18':    (  18, -1, -1,  True, False ),
    'CONSTANT_19':    (  19, -1, -1,  True, False ),
    'CONSTANT_20':    (  20, -1, -1,  True, False ),
    'CONSTANT_21':    (  21, -1, -1,  True, False ),
    'CONSTANT_22':    (  22, -1, -1,  True, False ),
    'CONSTANT_23':    (  23, -1, -1,  True, False ),
    'CONSTANT_24':    (  24, -1, -1,  True, False ),
    'CONSTANT_25':    (  25, -1, -1,  True, False ),
    'CONSTANT_26':    (  26, -1, -1,  True, False ),
    'CONSTANT_27':    (  27, -1, -1,  True, False ),
    'CONSTANT_28':    (  28, -1, -1,  True, False ),
    'CONSTANT_29':    (  29, -1, -1,  True, False ),
    'CONSTANT_30':    (  30, -1, -1,  True, False ),
    'CONSTANT_31':    (  31, -1, -1,  True, False ),
    'CONSTANT_32':    (  32, -1, -1,  True, False ),
    'PHI':            (  33,  1, 99,  True, False ),
    'BLOCKID':        (  34,  1,  1, False, False ),
    'JUMP':           (  35,  1,  1, False, False ),
    'JUMPI':          (  36,  2,  2, False, False ),
    'RETURN':         (  37,  2,  2, False,  True ),
    'CODESIZE':       (  40,  1,  1,  True, False ),
    'RETURNDATASIZE': (  41,  1,  1,  True, False ),
    'ADDRESS':        (  48,  1,  1,  True, False ),
    'ORIGIN':         (  49,  1,  1,  True, False ),
    'CALLER':         (  50,  1,  1,  True, False ),
    'CALLVALUE':      (  51,  1,  1,  True, False ),
    'CALLDATASIZE':   (  52,  1,  1,  True, False ),
    'GASPRICE':       (  53,  1,  1,  True, False ),
    'COINBASE':       (  54,  1,  1,  True, False ),
    'TIMESTAMP':      (  55,  1,  1,  True, False ),
    'NUMBER':         (  56,  1,  1,  True, False ),
    'DIFFICULTY':     (  57,  1,  1,  True, False ),
    'GASLIMIT':       (  58,  1,  1,  True, False ),
    'SELFBALANCE':    (  59,  1,  1,  True, False ),
    'GAS':            (  64,  1,  1,  True, False ),
    'MSIZE':          (  65,  1,  1,  True, False ),
    'BALANCE':        (  72,  2,  2,  True, False ),
    'EXTCODESIZE':    (  73,  2,  2,  True, False ),
    'EXTCODEHASH':    (  74,  2,  2,  True, False ),
    'SLOAD':          (  75,  2,  2,  True, False ),
    'CALLDATALOAD':   (  76,  2,  2,  True, False ),
    'BLOCKHASH':      (  77,  2,  2,  True, False ),
    'MLOAD':          (  78,  2,  2,  True,  True ),
    'STOUCH':         (  80,  1,  1, False, False ),
    'NOT':            (  88,  2,  2,  True, False ),
    'ISZERO':         (  89,  2,  2,  True, False ),
    'ADD':            (  96,  3,  3,  True, False ),
    'SUB':            (  97,  3,  3,  True, False ),
    'MUL':            (  98,  3,  3,  True, False ),
    'DIV':            (  99,  3,  3,  True, False ),
    'SDIV':           ( 100,  3,  3,  True, False ),
    'MOD':            ( 101,  3,  3,  True, False ),
    'SMOD':           ( 102,  3,  3,  True, False ),
    'AND':            ( 103,  3,  3,  True, False ),
    'OR':             ( 104,  3,  3,  True, False ),
    'XOR':            ( 105,  3,  3,  True, False ),
    'EQ':             ( 112,  3,  3,  True, False ),
    'LT':             ( 113,  3,  3,  True, False ),
    'GT':             ( 114,  3,  3,  True, False ),
    'SLT':            ( 115,  3,  3,  True, False ),
    'SGT':            ( 116,  3,  3,  True, False ),
    'EXP':            ( 128,  3,  3,  True, False ),
    'SIGNEXTEND':     ( 129,  3,  3,  True, False ),
    'BYTE':           ( 130,  3,  3,  True, False ),
    'SHL':            ( 131,  3,  3,  True, False ),
    'SHR':            ( 132,  3,  3,  True, False ),
    'SAR':            ( 133,  3,  3,  True, False ),
    'SHA3':           ( 136,  3,  3,  True,  True ),
    'MSTORE':         ( 144,  2,  2, False,  True ),
    'MSTORE8':        ( 145,  2,  2, False,  True ),
    'SSTORE':         ( 148,  2,  2, False, False ),
    'ADDMOD':         ( 152,  4,  4,  True, False ),
    'MULMOD':         ( 153,  4,  4,  True, False ),
    'CALLDATACOPY':   ( 160,  3,  3, False,  True ),
    'RETURNDATACOPY': ( 161,  3,  3, False,  True ),
    'CODECOPY':       ( 162,  3,  3, False,  True ),
    'EXTCODECOPY':    ( 168,  4,  4, False,  True ),
    'CALL':           ( 172,  8,  8,  True,  True ),
    'CALLCODE':       ( 173,  8,  8,  True,  True ),
    'DELEGATECALL':   ( 174,  7,  7,  True,  True ),
    'STATICCALL':     ( 175,  7,  7,  True,  True ),
}

def _test():
    t = -1
    for k, v in IIT.items():
        assert t < v[0] < 256, k
        t = v[0]

_test()

def get_opcode(name):
    opcode, _, _, _, _ = IIT[name]
    return opcode

def regc_minmax(name):
    _, regc_min, regc_max, _, _ = IIT[name]
    return regc_min, regc_max

def has_rd(name):
    _, _, _, res, _ = IIT[name]
    return res

def uses_mem(name):
    _, _, _, _, res = IIT[name]
    return res
