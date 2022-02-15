
from itertools import chain

from envon.analysis.Valuation import is_valuation, latest_origin_valuation
from envon.helpers            import Log, count, topo_sort_dfs_rev, loop_guard, LoopGuardException, PlaceholderSet
from envon.analysis.optimize  import general_worklist, mark_blocks, mark_by_valuation
from envon.graph              import make_graph_file, make_graph_ons_file

log = Log(__name__)

def print_instructions(output_file, analysis, selections):
    vs = []
    for b in analysis:
        for n in b:
            name = n.en().name()
            if name in selections:
                new_name, ai = selections[name]
                v            = n.valuation
                if not v:
                    log.warning('Skipping picked instruction because it doesn\'t have valuation:', n)
                    continue
                if ai >= 0:
                    v.node.valuation = v.one_arg_form(new_name, ai)
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
            (
                latest_origin_valuation(n.valuation)
                for n in b
                if n.marked and not n.is_memphi() and n.valuation.name != 'FW' # prevent a FW to a later instruction in same block
            )
        ):
            # if is_valuation(v) and v.name in 'PHI' and all(av is None for av in v.avs): continue
            # check if it shouldn't/can't be added here
            if is_valuation(v) and v.node._block != b: continue # TODO this may be assert False (needs testing)
            #
            on = self.ctx.get_on(v)
            if on not in avail_ons:
                avail_ons.add(on)
                ons.append(on)
        #
        if avail_ons != b.marked_avail_ons:
            b.marked_avail_ons = avail_ons
            for b2 in b.out_edges():
                if b2.marked:
                    res.append(MarkedONsUpdate(self.ctx, b2))
        #
        return res


def print_calc_with_jumps(fo, analysis, vs):
    mark_by_valuation(vs)
    mark_blocks(set(v.node._block for v in vs))
    jumps = set()
    for b in analysis:
        if b.marked:
            if b.has_multiple_out_edges():
                jumps.add(b.get_jump())
    jumps.discard(None)
    mark_by_valuation(n.valuation for n in jumps)
    make_graph_file(analysis)
    make_graph_file(analysis, only_marked=True)
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
    bs = [b for b in analysis if b.marked]
    bs.append(None)
    for block_i in range(len(bs)-1):
        b = bs[block_i]
        #
        if b == entry_b: fo.write(repr(b) + ' | ENTRY\n')
        else:            fo.write(repr(b) + ' | ' + ' '.join((repr(b2) for b2 in b.in_edges())) + '\n')
        #
        # Split the ons in ints/phi/non-phi for easier processing
        int_ons  = []
        phi_ons  = []
        rest_ons = []
        for on in b.marked_ons:
            c = ctx.on_calcs[on]
            if   type(c) is int:      int_ons.append((on, c))
            elif      c[0] == 'PHI':  phi_ons.append((on, c))
            else:                    rest_ons.append((on, c))
        #
        # Topologically sort the PHIs
        # The definition must come *after* the use (successor), because PHIs need to get the previous iteration's values.
        #
        phi_ons_map = { on: i for i, (on, _) in enumerate(phi_ons) }
        #
        _sort, _rm = topo_sort_dfs_rev(
            count         = len(phi_ons),
            getSuccessors = lambda i: [ phi_ons_map.get(on2, -1) for on2 in phi_ons[i][1][1] ],
        )
        if _rm:
            # Break the 1 possible loop in the PHI matrix (caused by swaps)
            assert len(_rm) == 1, _rm
            #
            use_i,  def_i = _rm[0]
            use_on, use_c = phi_ons[use_i]
            def_on,    _  = phi_ons[def_i]
            #
            # The cycle causes def to come before the use (backward edge),
            # so we need to copy the def's old value to a temporary (on=0),
            # and modify the use to use the temporary instead.
            fo.write(f'  0 = {def_on}\n')
            new_use_c      = use_c[0], tuple(on if on != def_on else 0 for on in use_c[1])
            phi_ons[use_i] = use_on, new_use_c
            #
            log.debug('Block', b, 'had cycle in phi ons: def_on', def_on, 'use_on', use_on, 'use_c', use_c, 'new_use_c', new_use_c)
        #
        all_ons = int_ons # will modify
        all_ons.extend([phi_ons[i] for i in _sort])
        all_ons.extend(rest_ons)
        #
        c = None
        for on, c in all_ons:
            fo.write(f'{on:3} = ' + (f'#{c:x}' if type(c) is int else c[0] + ''.join(f' {j}' for j in c[1])) + '\n')
        #
        last_was_jump = type(c) is tuple and c[0] == 'JUMP'
        #
        # TODO: refactor
        if         b.fallthrough_edge(): expect_b =       b.fallthrough_edge()
        elif count(b.jump_edges()) == 1: expect_b = tuple(b.jump_edges())[0]
        else:                            expect_b = None
        #
        if not last_was_jump and bs[block_i+1] != expect_b:
            if expect_b and expect_b.marked:
                fo.write(f'  0 = #{expect_b.offset:x}\n')
                fo.write( '  0 = JUMP 0\n')
            else:
                fo.write('STOP\n')
    #
    res = set(
        ctx.on_map.get(v)
        for v in vs
    )
    res.discard(None)
    fo.write(repr(sorted(res)) + '\n')
