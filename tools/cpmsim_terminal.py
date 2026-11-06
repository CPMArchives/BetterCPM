#!/usr/bin/env python3
"""Check cpmsim's host terminal size, then replace this process with cpmsim."""
import os
import sys

MIN_COLUMNS=80
MIN_ROWS=24


def check_terminal():
    # Query the actual output terminal, never stale COLUMNS/LINES variables.
    # Redirected output has no display geometry (e.g. automated captures).
    if not os.isatty(sys.stdout.fileno()):
        return True
    try:
        columns,rows=os.get_terminal_size(sys.stdout.fileno())
    except OSError:
        columns,rows=0,0
    if columns>=MIN_COLUMNS and rows>=MIN_ROWS:
        return True
    current=f'Terminal is {columns}x{rows}' if columns>0 and rows>0 else 'Cannot determine terminal size'
    print(current+'; BetterCP/M requires at least 80x24.\n'
          'Enlarge the terminal window or reduce its font size, then launch again.\n'
          'cpmsim was not started.',file=sys.stderr)
    return False


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='--':
        args.pop(0)
    if not args:
        print('Usage: cpmsim_terminal.py -- cpmsim [arguments]',file=sys.stderr)
        return 2
    if not check_terminal():
        return 1
    try:
        os.execvp(args[0],args)
    except OSError as error:
        print(f'Cannot start cpmsim: {error}',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
