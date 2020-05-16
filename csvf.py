#!/usr/bin/env python
""" Top-level driver script to execute csv subprograms. """

import sys

from csv_tools.csv_cmd import main

        
if __name__ == "__main__":
    sys.exit(main(sys.argv, sys.stdin, sys.stdout, sys.stderr))
