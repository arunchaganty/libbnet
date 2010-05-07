"""
Libbnet 
"""

from bnet.parsers import RaviParser, BNIFParser
from bnet.BNet import *
from shell import NetShell

import sys

def main():
    if len( sys.argv ) != 2:
        print "Usage: %s <file>"%( sys.argv[ 0 ] )
        sys.exit( 1 )

    filename = sys.argv[ 1 ]

    n = None
    for parser in [ RaviParser, BNIFParser ]:
        try:
            p = parser()
            n = p.parseFile( filename )
        except Exception:
            continue
    if n:
        shell = NetShell( n )
        shell.run()

if __name__ == "__main__": main()

