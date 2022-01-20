
import sys
import logging
import argparse

from envon.helpers import Log

log = Log(__name__)

def parse_args():
    parser = argparse.ArgumentParser(prog='envon', description='Create EVM-like code using selected instructions of a given EVM runtime binary code file.')
    parser.add_argument('--input',     '-i', type=argparse.FileType('r'),                      help='File containing evm runtime bytecode in hex, typ *.runbin.hex')
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
        logging.basicConfig(format='%(levelname)-5s %(name)-40s %(filename)20s:%(lineno)-4d | %(message)s', level=ll, stream=fl)
        #
        fi   = args.input
        fo   = args.output
        skip = args.skip
        assert fi is not None
        assert fo is not None
        #
        pick = {}
        if args.pick:
            log.info('---- Picking instructions ----')
            for name in args.pick.split(','):
                if name.endswith(']'):
                    a = name[:-1].split('[')
                    assert len(a) == 2, name
                    name = a[0]
                    i    = int(a[1])
                    log.info(f' -> arg {i:4} of {name:9}')
                    pick[name] = i
                else:
                    log.info(f' -> all args of {name:9}')
                    pick[name] = -1
            log.info('------------------------------')
        #
        return fi, fo, skip, pick
        #
    except Exception as e: # pylint: disable=broad-except
        log.exception(e)
        print('\n' + parser.format_help(), file=sys.stderr)
        sys.exit(1)
