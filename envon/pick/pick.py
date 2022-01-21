
from itertools import chain

from envon.analysis.Valuation import is_valuation, latest_origin_valuation
from envon.helpers            import Log, count, loop_guard, LoopGuardException, PlaceholderSet
from envon.analysis.optimize  import general_worklist, mark_blocks, mark_by_valuation
from envon.graph              import make_graph_file, make_graph_ons_file

log = Log(__name__)

def print_instructions(output_file, analysis, selections):
    vs = []
    for b in analysis:
        for n in b:
            name = n.en().name()
            if name in selections:
                ai = selections[name]
                v  = n.valuation
                if ai >= 0:
                    v = v.one_arg_form(ai)
                vs.append(v)
    #
    print_calc_with_jumps(output_file, analysis, vs)

class MarkedONsUpdateContext:

    def __init__(self):
        self.on_calcs = [('ON_0_RESERVED', ())]
        self.on_map   = {}

    def calc(self, v):
        if is_valuation(v):
            return v.name, tuple(
                0 if is_valuation(av) and av.no_value else self.on_map.get(latest_origin_valuation(av))
                for av in v.avs
            )
        else:
            return v

    def resolve_calcs(self):
        for v, on in self.on_map.items():
            self.on_calcs[on] = self.calc(v)

    def get_on(self, v):
        if v in self.on_map:
            on = self.on_map[v]
        else:
            on = len(self.on_calcs)
            self.on_map[v] = on
            self.on_calcs.append(None) # keep a placeholder, we'll resolve later
        return on


class MarkedONsUpdate:

    def __init__(self, ctx, block):
        self.ctx   = ctx
        self.block = block

    def __repr__(self):
        return 'MARK_ONS(' + repr(self.block) + ')'

    def apply(self):
        res = []
        b   = self.block
        #
        avail_ons = PlaceholderSet
        for b2 in b.in_edges():
            if b2.marked_avail_ons is not None:
                avail_ons &= b2.marked_avail_ons
        avail_ons |= set()
        #
        ons = []
        b.marked_ons = ons
        for v in chain(
            b.marked_ints,
            (latest_origin_valuation(n.valuation) for n in b if n.marked and not n.is_memphi())
        ):
            if is_valuation(v) and v.name in 'PHI' and all(av is None for av in v.avs): continue
            on = self.ctx.get_on(v)
            if on not in avail_ons:
                avail_ons.add(on)
                ons.append(on)
        #
        if avail_ons != b.marked_avail_ons:
            b.marked_avail_ons = avail_ons
            for b2 in chain(
                [b.fallthrough_edge()],
                b.jump_edges()
            ):
                if b2 and b2.marked:
                    res.append(MarkedONsUpdate(self.ctx, b2))
        #
        return res


def print_calc_with_jumps(fo, analysis, vs):
    bs = set(v.node._block for v in vs)
    mark_blocks(bs)
    mark_by_valuation(vs)
    jumps = set()
    for b in analysis:
        if b.marked:
            if b.has_multiple_out_edges():
                jumps.add(b.get_jump())
    jumps.discard(None)
    mark_by_valuation(n.valuation for n in jumps)
    make_graph_file(analysis)
    log.debug(latest_origin_valuation.stats)
    #
    entry_b = analysis.get_entry_block()
    ctx     = MarkedONsUpdateContext()
    _t      = MarkedONsUpdate(ctx, entry_b)
    for _ in general_worklist([_t]):
        # ctx.resolve_calcs() # only for debug!
        # make_graph_ons_file(analysis, ctx)
        pass
    # Unmark blocks not reached from entry_b
    for b in analysis:
        if b.marked_ons is None: b.marked = False
    #
    ctx.resolve_calcs()
    make_graph_ons_file(analysis, ctx)
    log.debug(latest_origin_valuation.stats)
    #
    expect_b      = entry_b
    last_was_jump = False
    for b in analysis:
        if b.marked:
            if b != expect_b and not last_was_jump:
                if  expect_b and expect_b.marked:
                    fo.write(f'  0 = #{expect_b.offset:x}\n')
                    fo.write( '  0 = JUMP 0\n')
                else:
                    fo.write('STOP\n')
            #
            if b == entry_b: fo.write(repr(b) + ' | ENTRY\n')
            else:            fo.write(repr(b) + ' | ' + ' '.join((repr(b2) for b2 in b.in_edges())) + '\n')
            #
            c = None
            for on in b.marked_ons:
                c = ctx.on_calcs[on]
                fo.write(f'{on:3} = ' + (f'#{c:x}' if type(c) is int else c[0] + ''.join(f' {j}' for j in c[1])) + '\n')
            #
            last_was_jump = type(c) is tuple and c[0] == 'JUMP'
            #
            # TODO: refactor
            if         b.fallthrough_edge(): expect_b =       b.fallthrough_edge()
            elif count(b.jump_edges()) == 1: expect_b = tuple(b.jump_edges())[0]
            else:                            expect_b = None
    #
    res = set(
        ctx.on_map.get(v)
        for v in vs
    )
    res.discard(None)
    fo.write(repr(sorted(res)) + '\n')