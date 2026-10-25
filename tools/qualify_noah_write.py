#!/usr/bin/env python3
"""Compatibility entry point for production NOAH native qualification.

Revision 6's monolithic LBR-write evidence remains frozen in the repository.
Current NOAH requires its controller/codec companion; qualify those modules and
all LBR operations together with the production campaign. Use --reuse-build to
reuse already parity-checked native groups, rather than the old --reuse-native.
"""
from qualify_noah_codecs import main

if __name__ == '__main__':
    main()
