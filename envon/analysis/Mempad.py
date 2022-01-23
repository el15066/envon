
from .Valuation import Valuation

from envon.helpers import Log

log = Log(__name__)

class Mempad(Valuation):

    def __init__(self, node, name, avs, avsh, bytemap, *, no_value=None):
        super().__init__(node, name, avs, avsh, no_value=no_value, _hash=0)
        self._bytemap = bytemap

    def __hash__(self):
        h = self._hash
        assert h != 0
        return h

    def finalize(self, extras=None):
        assert self._hash == 0
        if extras is not None:
            self._hash = hash((self.name, extras, tuple(self._bytemap.items())))
        else:
            self._hash = hash((self.name, self.avsh))
        # if  self._bytemap is None:
        #     self._bytemap = {}
        # self._hash = hash((self.name, self.node._id, tuple(self._bytemap.items())))
        # assert self._hash != 0

    def meet(self, others):
        assert self._hash == 0
        a = self._bytemap
        for other in others:
            if other is not None:
                b = other._bytemap # pylint: disable=protected-access
                if a is not None:
                    # strict merge
                    t = [k for k, v in a.items() if b.get(k) != v]
                    for k in t: del a[k]
                    # # lenient merge # has issues with loops
                    # for k, v in b.items():
                    #     v2 = a.get(k)
                    #     if   v2 is None: a[k] = v
                    #     elif v2 != v:    del a[k]
                else:
                    a = b.copy()
                    self._bytemap = a

    def __repr__(self):
        return super().__repr__() + f'-{len(self._bytemap)}B'

    def bytemap_copy(self):
        return self._bytemap.copy()

    def clear(self, addr):
        assert self._hash == 0
        if addr in self._bytemap:
            del    self._bytemap[addr]

    def clear_region(self, addr, size):
        assert self._hash == 0
        if size == 'inf':
            size = max(self._bytemap) - addr + 1
        for i in range(addr, addr + size):
            if i in self._bytemap:
                del self._bytemap[i]

    def clear_all(self):
        assert self._hash == 0
        self._bytemap.clear()

    def store(self, addr, n):
        assert self._hash == 0
        self._bytemap[addr] = (n, 0)

    def store_region(self, addr, size, n):
        assert self._hash == 0
        for i in range(size):
            self._bytemap[addr+i] = (n, i)

    def store32(self, addr, n):
        assert self._hash == 0
        self.store_region(addr, 32, n)

    def load32(self, addr):
        n, _ = self._bytemap.get(addr, (None, -1))
        if n is None:
            return None
        # start from 0 to check index!
        for i in range(32):
            n2, offs = self._bytemap.get(addr+i, (None, -1))
            if n2 != n or offs != i:
                # we can only return aligned words for now
                log.debug('n2 != n or offs != i', n2, n, offs, i)
                return None
        return n

    def load_region(self, addr, size):
        assert size >= 0
        if size == 0:
            return []
        # log.debug(addr, size, self._bytemap)
        n, _ = self._bytemap.get(addr, (None, -1))
        res = [n]
        i_base = addr
        for i in range(addr, addr + size):
            n2, offs = self._bytemap.get(i, (None, -1))
            if n2 is None:
                log.debug('n2 is None')
                return None
            if n2 != n:
                n = n2
                res.append(n)
                i_base = i
            if offs != i - i_base:
                log.debug('offs != i - i_base', offs, i, i_base)
                return None
        return res
