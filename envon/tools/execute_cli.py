
import sys
import json
import argparse

from execute import execute_tx

def parse_map(fm):
    m = {}
    for line in fm:
        assert len(line)         == 108
        a =    int(line[   : 40], 16)
        assert     line[ 40: 43] == ' h_'
        h =    int(line[ 43:107], 16)
        assert     line[107]     == '\n'
        m[a] = h
    fm.close()
    return m

def prepare_ctx(line, storage, code_map, code_dir):
    # {
    #     "Block"      : 7500000,
    #     "Index"      : 6,
    #     "Coinbase"   : "829bd824b016326a401d083b33d092293333a830",
    #     "Timestamp"  : 1554358137,
    #     "Difficulty" : 1785444410800885,
    #     "Gaslimit"   : 8023456,
    #     "Chainid"    : 1,
    #     "Address"    : "ff56cc6b1e6ded347aa0b7676c85ab0b3d08b0fa",
    #     "Origin"     : "6672079e4c8a1d5c81c93cac20a267a213a27f58",
    #     "Callvalue"  : "0x0",
    #     "Calldata"   : "a9059cbb0000000000000000000000000250c01d8df44fbacbecf226a1ae047b55e4e89e0000000000000000000000000000000000000000000000000de0b6b3a7640000"
    # }
    t = json.loads(line)
    assert t['Callvalue'][:2] == '0x'
    return {
        'Storage':                  storage,
        'Codemap':                  code_map,
        'Codedir':                  code_dir,
        'Block':                    t['Block'     ],
        'Index':                    t['Index'     ],
        'Coinbase':             int(t['Coinbase'  ],     16),
        'Timestamp':                t['Timestamp' ],
        'Difficulty':               t['Difficulty'],
        'Gaslimit':                 t['Gaslimit'  ],
        'Chainid':                  t['Chainid'   ],
        'Address':              int(t['Address'   ],     16),
        'Codeaddr':             int(t['Address'   ],     16),
        'Origin':               int(t['Origin'    ],     16),
        'Caller':               int(t['Origin'    ],     16),
        'Callvalue':            int(t['Callvalue' ][2:], 16),
        'Calldata':   bytes.fromhex(t['Calldata'  ]),
    }

def main(fi, fm, code_dir):
    storage = {
        0x0000000000085d4780b73119b644ae5ecd22b376: {
            0x0000000000000000000000000000000000000000000000000000000000000003: 0x811c5f8dfbdd70c245e66e4cd181040b2630424a,
            0x6e41e0fbe643dfdb6043698bf865aada82dc46b953f754a3468eaa272a362dc7: 0xc97787c9054c3ede4b96B74AbA3F32a336045d6C,
        },
    }
    code_map = parse_map(fm)
    for i, line in enumerate(fi):
        ctx = prepare_ctx(line, storage, code_map, code_dir)
        execute_tx(ctx)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple EVM-like code execution')
    parser.add_argument('--input',    '-i', type=argparse.FileType('r'),                  help='input file with transcations to excecute')
    parser.add_argument('--addr-map', '-m', type=argparse.FileType('r'),                  help='input file with contract address to code hash pairs')
    parser.add_argument('--code-dir', '-d', type=str,                    default='code/', help='directory with code files for each contract')
    args = parser.parse_args()
    #
    fi = args.input
    fm = args.addr_map
    if fi is None or fm is None:
        parser.print_usage()
        sys.exit(1)
    #
    cd = args.code_dir
    if cd[-1] == '/': cd = cd[:-1]
    #
    main(fi, fm, cd)
