
from collections import defaultdict

class Valuation:

    def __init__(self, node, name, avs, avsh, *, no_value=None, origin=None, _hash=None, possible_values=None):
        self.node            = node
        self.name            = name
        self.avs             = avs
        self.avsh            = avsh
        self.no_value        = node.en().pushes() == 0 if no_value is None else no_value
        self.origin          = node                    if origin   is None else origin
        self._hash           = hash((name, avsh))      if _hash    is None else _hash
        self.possible_values = possible_values
        assert possible_values is None or all(type(v) is int for v in possible_values)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return 'v' + repr(self.node) + '-' + self.name + hex(self._hash&0xfffff)[1:6]

    def __str__(self):
        s = 'V' + repr(self.node) + '-' + self.name + '(' + ', '.join(f'#{v:x}' if type(v) is int else repr(v) for v in self.avs) + ')-' + hex(self._hash&0xfffff)[1:6]
        if self.possible_values:
            s += repr(self.possible_values)
        if self.no_value:
            s += '-NV'
        return s

    def forward(self, n, avs, avsh):
        return Valuation(     n,    'FW',       avs,                   avsh, no_value=False,         origin=self.origin, _hash=self._hash, possible_values=self.possible_values)

    def one_arg_form(self, name, arg_index):
        return Valuation(self.node, name, (self.avs[arg_index],), self.avsh, no_value=self.no_value, origin=self.origin, _hash=self._hash, possible_values=self.possible_values)


def is_valuation(v):
    return isinstance(v, Valuation)

def latest_valuation(v): #, resolve_origin=False):
    # v_orig = v
    i = 0
    # j = 0
    while is_valuation(v):
        _v = v.node.valuation
        if _v is not v:
            v = _v
            i += 1
            continue
        # if resolve_origin and v.origin is not None:
        #     v = v.origin.valuation
        #     j += 1
        #     continue
        break
    latest_valuation.stats[i] += 1
    # latest_valuation.stats[(i,j)] += 1
    # if i + j != 0:
    #     print(hash(v_orig), v_orig, '->', hash(v), v)
    return v

latest_valuation.stats = defaultdict(int)

def latest_origin_valuation(v):
    # v_orig = v
    i = 0
    j = 0
    while is_valuation(v):
        _v = v.node.valuation
        if _v is not v:
            v = _v
            i += 1
            continue
        if _v is not v.origin.valuation:
            v = v.origin.valuation
            j += 1
            continue
        break
    latest_origin_valuation.stats[(i,j)] += 1
    # if i + j != 0:
    #     print(hash(v_orig), v_orig, '->', hash(v), v)
    return v

latest_origin_valuation.stats = defaultdict(int)
