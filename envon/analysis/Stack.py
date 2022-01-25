
class Stack:

    def __init__(self, block):
        self._block  = block
        self._raw    = []
        self._buried = {}
        self._pops   = 0

    def __repr__(self):
        return 'Stack' + repr(self._block)

    def __str__(self):
        r  =     f'Stack {self._block} pops={self._pops}\n'
        r +=      ' buried\n'
        for i, n in sorted(self._buried.items()):
            r += f'  {i:2} {repr(n)}\n'
        r +=      ' raw\n'
        for i, n in enumerate(self._raw):
            r += f'  {i:2} {repr(n)}\n'
        return r[:-1]

    def _bury(self, sp, n):
        self._buried[sp] = n

    def _dig(self, sp):
        n = self._buried.get(sp)
        if n is None:
            n = self._block.create_stack_phi(sp)
            self._buried[sp] = n
        return n

    def get(self, diff):
        assert diff < 0
        idx = len(self._raw) + diff
        if idx >= 0:
            return self._raw[idx]
        else:
            sp = idx - self._pops
            return self._dig(sp)

    def push(self, n):
        self._raw.append(n)

    def pop(self):
        if self._raw:
            return self._raw.pop()
        else:
            self._pops += 1
            sp = -self._pops
            return self._dig(sp)

    def dup(self, diff):
        n = self.get(diff)
        self.push(n)

    def swap(self, diff):
        assert diff < 0
        idx = len(self._raw) + diff
        if idx >= 0:
            n1 = self._raw[idx]
            n2 = self.pop()
            self.push(n1)
            self._raw[idx] = n2
        else:
            sp = idx - self._pops
            n1 = self._dig(sp)
            n2 = self.pop()
            self.push(n1)
            self._bury(sp, n2)
