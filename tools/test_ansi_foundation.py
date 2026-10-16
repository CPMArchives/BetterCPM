#!/usr/bin/env python3
"""Qualify production ANSI parsing through both actual screen backends."""
from test_ansi_portable import main,ROOT
OUT=ROOT/'build/ansi-development'

if __name__=='__main__':main(production=True)
