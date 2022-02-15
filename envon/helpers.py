
import logging
import subprocess

from functools import wraps

FF32  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
ONE31 = 0x8000000000000000000000000000000000000000000000000000000000000000
def u256(x): return x & FF32
def s256(x): return (x ^ ONE31) - ONE31

def count(iterable):
    s = 0
    for _ in iterable: s += 1
    return s

def _merge(args):
    return ' '.join(str(a) for a in args)

class _Log(logging.Logger):
    def debug(    self, *args, **kwargs): super().debug(    _merge(args), **kwargs)
    def info(     self, *args, **kwargs): super().info(     _merge(args), **kwargs)
    def warning(  self, *args, **kwargs): super().warning(  _merge(args), **kwargs)
    def error(    self, *args, **kwargs): super().error(    _merge(args), **kwargs)
    def exception(self, *args, **kwargs): super().exception(_merge(args), **kwargs)
    def findCaller(self, stack_info=False, stacklevel=1):
        return super().findCaller(stack_info, stacklevel+2)

logging.setLoggerClass(_Log)

def Log(name):
    return logging.getLogger(name)

log = Log(__name__)

def run_command(*args, check=True, **kwargs):
    assert all(type(a) is str for a in args), args
    log.info("Running '"            + "' '".join(args) + "'", stacklevel=2)
    subprocess.run(  args, check=check, **kwargs)

def run_command_bg(*args, **kwargs):
    assert all(type(a) is str for a in args), args
    log.info("Running background '" + "' '".join(args) + "'", stacklevel=2)
    subprocess.Popen(args,              **kwargs) # pylint: disable=consider-using-with

class LoopGuardException(Exception):
    pass

def loop_guard(func):
    @wraps(func)
    def w(self, *args, **kwargs):
        #
        if not hasattr(self, '__module__'):
            return func(self, *args, **kwargs)
        #
        # pylint: disable=protected-access
        if hasattr(self, '___guarded') and self.___guarded:
            raise LoopGuardException(self)
        self.___guarded = True
        try:
            return func(self, *args, **kwargs)
        finally:
            self.___guarded = False
    return w

def track_ident(func):
    @wraps(func)
    def w(*args, **kwargs):
        w.ident += '  '
        try:
            return func(*args, ident=w.ident, **kwargs)
        finally:
            w.ident = w.ident[:-2]
    w.ident = ' '
    return w

def print_with_ident(func):
    @wraps(func)
    def w(*args, **kwargs):
        w.ident += '  '
        def _p(*args2, **kwargs2):
            print(w.ident, *args2, **kwargs2)
        try:
            return func(*args, _p=_p, **kwargs)
        finally:
            w.ident = w.ident[:-2]
    w.ident = ' '
    return w

class _PlaceholderSet:
    def __and__(self, other): return other.copy()
    def __or__( self, other): return other.copy()

PlaceholderSet = _PlaceholderSet()


# Topologically sort a directed graph using DFS
# Some edges that are part of a cycle will be ignored and returned,
# so that the rest of the graph is a DAG.
# The guarantee is that:
#  res[j+1] is not a successort of res[j]
#  if the edges (i1, i2) in remove are deleted from the graph
# Notice how `res` is given in reverse
def topo_sort_dfs_rev(count, getSuccessors):
    res    = []
    remove = []
    opened = [False] * count
    closed = [False] * count
    todo   = list(range(count))
    while todo:
        i = todo[-1]
        #
        if opened[i]:
            todo.pop()
            if not closed[i]: res.append(i)
            closed[i] = True
            continue
        #
        opened[i] = True
        #
        for i2 in getSuccessors(i):
            if i2 < 0:     continue
            if closed[i2]: continue
            if opened[i2]: remove.append((i, i2))
            else:            todo.append(i2)
        #
    return res, remove

def topo_sort_dfs(count, getSuccessors):
    res, remove = topo_sort_dfs_rev(count, getSuccessors)
    res.reverse()
    return res, remove
