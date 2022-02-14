
import sys
import json
import logging
import argparse

# from bisect import bisect_right

from envon.helpers import Log
from envon         import graph

log = Log(__name__)

def parse_args():
    parser = argparse.ArgumentParser(prog='envon', description='Create EVM-like code using selected instructions of a given EVM runtime binary code file.')
    parser.add_argument('--input',     '-i', type=argparse.FileType('r'),                      help='File containing evm runtime bytecode in hex, typ *.runbin.hex')
    parser.add_argument('--jumps',     '-j', type=argparse.FileType('r'),                      help='JSON file containing known jump edges')
    parser.add_argument('--skip',      '-s',                              action='store_true', help='Skip blocks with rare instrunctions')
    parser.add_argument('--pick',      '-p', type=str,                    default='',          help='Comma-separated list of instrunction names needed in the output code')
    parser.add_argument('--output',    '-o', type=argparse.FileType('w'), default=sys.stdout,  help='File to write code to, typ *.evmlike, [stdout]')
    parser.add_argument('--log',       '-l', type=argparse.FileType('w'), default=sys.stderr,  help='File to write log to, [stderr]')
    parser.add_argument('--log-level', '-L', type=str,                    default='info',      help='Minimum log level, see https://docs.python.org/3/library/logging.html#levels, [Info]')
    try:
        args = parser.parse_args()
        #
        fl = args.log
        ll = args.log_level.upper()
        try:
            ll = int(ll)
        except ValueError:
            pass
        if 'DEBUG' in ll:
            graph.config.DISABLED = False
        logging.basicConfig(format='%(levelname)-7s %(name)-40s %(filename)20s:%(lineno)-4d | %(message)s', level=ll, stream=fl)
        #
        fi   = args.input
        fo   = args.output
        skip = args.skip
        assert fi is not None
        assert fo is not None
        #
        log.info('Analyzing', fi.name)
        log.info('Output is', fo.name)
        log.info('Skip is', 'enabled' if skip else 'disabled')
        #
        kje = None
        fj  = args.jumps
        if fj:
            log.info('Using known jump edge file', fj.name)
            code_hash = fi.name.rpartition('/')[2].partition('.')[0]
            #
            kje = None
            #
            # The file is sorted so we can binary search it first and keep only the relevant line,
            # but this needs to be done without reading all lines.
            # "h_001dd42ca6f50d3cb606eca69dc5127ee42608656b4db9b5ac7fc0485bccd282":[[1382,4228],[97,98],[108,109],[1311,1316],[141,142]],\n
            # lines = fj.readlines()
            # i     = bisect_right(lines[1:-1], '"' + code_hash) + 1 # won't exist exactly, so left/right doesn't matter
            # if lines[i][1:67] == code_hash:
            #     kje = json.loads(lines[i][69:-2])
            #
            # A simple linear scan is ok
            for line in fj:
                t = line[1:67]
                if   t >  code_hash: break
                elif t == code_hash:
                    kje = json.loads(line[69:-2])
                    break
            #
            if kje is None:
                log.warning('Code hash', code_hash, 'not found in jump edges file')
            elif not kje:
                log.warning('Known jump list for code hash', code_hash, 'is empty')
        #
        pick = {}
        if args.pick:
            log.info('Will pick', args.pick)
            log.debug('---- Will pick instructions ----')
            for name in args.pick.split(','):
                abc, _, d = name.partition('=')
                ab,  _, c =  abc.partition(']')
                a,   _, b =   ab.partition('[')
                assert not c, name
                name     = a
                _ai      = b
                new_name = d
                if _ai:
                    assert new_name, name
                    ai = int(_ai)
                    log.debug(f' -> arg {ai:4} of {name:15}' + ('as '+new_name if new_name else ' '))
                    pick[name] = new_name, ai
                else:
                    log.debug(f' -> all args of {  name:15}')
                    pick[name] =     None, -1
            log.debug('--------------------------------')
        #
        return fi, fo, skip, kje, pick
        #
    except Exception as e: # pylint: disable=broad-except
        log.exception(e)
        print('\n' + parser.format_help(), file=sys.stderr)
        sys.exit(1)
