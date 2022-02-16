import sys
import argparse

# DEBUG = True
DEBUG = False

class Reader:

    def __init__(self, f):
        self.f        = f
        self.tx       = None
        self.contract = None
        self.addrs    = None
        self.line     = None
        self._readline()
        self._read_1_tx()

    def _readline(self):
        self.line = self.f.readline()

    def _process_tx_header(self):
        try:
            if self.line:
                ps = self.line.split()
                assert 3 <= len(ps) <= 4
                if   len(ps) == 4: [p0, p1, p2, p3] =   ps
                else:              [p0, p1, p2, p3] = [*ps, None]
                assert p0 == 'Tx'
                self.tx       = int(p1), int(p2)
                self.contract = p3
                self.addrs    = set()
            else:
                self.tx       = None
                self.contract = None
                self.addrs    = None
        except:
            print('In ' + self.f.name + ': ' + self.line)
            raise

    def _read_1_tx(self):
        self._process_tx_header()
        if self.tx is not None:
            self._readline()
            while self.line and self.line[0] != 'T':
                assert len(self.line) == 65
                assert self.line[64] == '\n'
                self.addrs.add(self.line[:64])
                self._readline()

    def read_1_tx(self):
        res = self.tx, self.contract, self.addrs
        self._read_1_tx()
        return res

    def read_addrs_for_this_tx(self, tx):
        while True:
            if   self.tx is None: return None
            elif self.tx >  tx:   return set() #print('TX', tx, 'not found in', self.f.name); return set() # propably no accesses
            elif self.tx == tx:   return self.addrs
            else:                 self._read_1_tx()


def main(fa, fp):
    ra = Reader(fa)
    rp = Reader(fp)
    results = {}
    while True:
        tx, contract, addrs_p = rp.read_1_tx()
        if tx      is None: break
        addrs_a               = ra.read_addrs_for_this_tx(tx)
        if addrs_a is None: continue
        if DEBUG:
            if addrs_a != addrs_p:
                print(tx)
                for a in addrs_a: print(a)
                print('p:')
                for a in addrs_p: print(a)
                print('-:')
                for a in addrs_a - addrs_p: print(a)
                print('+:')
                for a in addrs_p - addrs_a: print(a)
                print()
        # res is (txs, predicted, actual, common) aka (txs, PP, P, TP)
        res = results.get(contract, [0, 0, 0, 0])
        res[0] += 1
        res[1] += len(addrs_p)
        res[2] += len(addrs_a)
        res[3] += len(addrs_p & addrs_a)
        results[contract] = res
    #
    print()
    totals = [0, 0, 0, 0]
    for k, v in results.items():
        [txs, p, a, c] = v
        totals[0] += txs
        totals[1] += p
        totals[2] += a
        totals[3] += c
        if a > 100000 or a-c > 30000 or p-c > 30000:
            print('--- Contract ' + k)
            print(f'  Coverage: {100*  c  /a if a else -1 :7.1f} %  missed: {a-c:9}')
            print(f'  Overhead: {100*(p-c)/a if a else -1 :7.0f} %  added:  {p-c:9}')
            print(f'  Count:    {               a              :9}  txs:    {txs:9}')
            print()
    #
    [txs, p, a, c] = totals
    print('--- Totals ---')
    print(f'  Coverage: {100*  c  /a if a else -1 :7.1f} %  missed: {a-c:9}')
    print(f'  Overhead: {100*(p-c)/a if a else -1 :7.0f} %  added:  {p-c:9}')
    print(f'  Count:    {               a              :9}  txs:    {txs:9}')
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Confusion matrix for transcation reads')
    parser.add_argument('--actual',  '-a', type=argparse.FileType('r'), help='input file with actual    transcation reads')
    parser.add_argument('--predict', '-p', type=argparse.FileType('r'), help='input file with predicted transcation reads')
    args = parser.parse_args()
    #
    fa, fp = args.actual, args.predict
    if fa is None or fp is None:
        parser.print_usage()
        sys.exit(1)
    #
    main(fa, fp)
