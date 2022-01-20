
import logging
import subprocess

from functools import wraps

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
