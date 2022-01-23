
import sys
import json
import argparse

from collections import defaultdict

from execute import execute_tx, debug, warn, sha3

class StorageReader:

    def __init__(self, f):
        self.f    = f
        self.line = ''
        self._readline()

    def _readline(self):
        self.line = self.f.readline()

    def read_for_this_tx(self, tx):
        res = defaultdict(dict)
        while self.line:
            if self.line[0] == 'S':
                ps = self.line.split()
                if len(ps) == 4: ps.append('00')
                [p0, p1, p2, p3, p4] = ps
                assert p0 == 'S'
                _tx = int(p1), int(p2)
                if   _tx >  tx: break
                elif _tx == tx:
                    assert len(p3) == 120
                    assert 2 <= len(p4) <= 64
                    ca = int(p3[  : 40], 16)
                    # ci = int(p3[40: 56], 16)
                    sa = int(p3[56:120], 16)
                    sc = int(p4, 16)
                    res[ca][sa] = sc
            #
            self._readline()
        return res


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

def prepare_ctx(line, code_map, code_dir):
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

def main(fi, fm, fs, code_dir):
    s_reader = StorageReader(fs)
    code_map = parse_map(fm)
    for i, line in enumerate(fi):
        # if i > 10000: break
        #
        ctx = prepare_ctx(line, code_map, code_dir)
        tx  = ctx['Block'], ctx['Index']
        debug(tx)
        ctx['Storage'] = s_reader.read_for_this_tx(tx)
        # if code_map.get(ctx['Address']) != 0x418c9d56c1e2eb1f7466538680767178d3bede656157ff88f3f7ca214c04f37d: continue
        # if code_map.get(ctx['Address']) != 0x53413c38b8692d456854fd748655e4cd72b4130878511d6242f725adea1a80d0: continue
        execute_tx(ctx)
        # return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple EVM-like code execution')
    parser.add_argument('--input',    '-i', type=argparse.FileType('r'),                  help='input file with transcations to excecute')
    parser.add_argument('--addr-map', '-m', type=argparse.FileType('r'),                  help='input file with contract address to code hash pairs')
    parser.add_argument('--storage',  '-s', type=argparse.FileType('r'),                  help='input file with accessed storage data per tx')
    parser.add_argument('--code-dir', '-d', type=str,                    default='code/', help='directory with code files for each contract')
    args = parser.parse_args()
    #
    fi = args.input
    fm = args.addr_map
    fs = args.storage
    if fi is None or fm is None or fs is None:
        parser.print_usage()
        sys.exit(1)
    #
    cd = args.code_dir
    if cd[-1] == '/': cd = cd[:-1]
    #
    main(fi, fm, fs, cd)
