
import os
import textwrap

from collections import deque
from itertools   import chain

from envon.analysis.Valuation import is_valuation
from envon.helpers            import Log, run_command_bg

from . import config

log = Log(__name__)

DOT_COUNT = 0

def dot_graph(analysis, highlights, only_marked):
    #

def _make_graph_file(suffix, content):
    assert not config.DISABLED
    global DOT_COUNT
    try:                    os.mkdir('graphs')
    except FileExistsError: pass
    #
    prefix     = f'graphs/{DOT_COUNT:03}_{suffix}'
    DOT_COUNT += 1
    with open(prefix+'.dot', 'w') as f:
        f.write(content)
    #
    run_command_bg('dot', '-Tsvg', prefix+'.dot', '-o', prefix+'.svg')
    #
    log.info(f'Created graph {prefix}.*')

def make_graph_file(analysis, highlights=None, only_marked=False):
    if config.DISABLED: return
    if  highlights is None:
        highlights = set()
    _make_graph_file('analysis', dot_graph(analysis, highlights, only_marked))
def dot_graph_mem(memory_n):
    #

def make_graph_memory_file(memory_n):
    if config.DISABLED: return
    _make_graph_file('memory', dot_graph_mem(memory_n))

def set_of_ints_summary(s):
    res   = []
    ar    = sorted(s)
    start = ar[0]
    prev  = ar[0] - 1
    for a in chain(ar, [None]):
        if a != prev + 1:
            res.append(f'{start}-{prev}' if start != prev else f'{start}')
            start = a
        prev = a
    return ' '.join(res)

def _word_wrap(line):
    return textwrap.wrap(line, width=50, initial_indent=' . ', subsequent_indent=' . ')

def dot_graph_ons(analysis, ctx):
    #

def make_graph_ons_file(analysis, ctx):
    if config.DISABLED: return
    _make_graph_file('output', dot_graph_ons(analysis, ctx))
