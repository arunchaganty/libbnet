"""
Libbnet shell
"""

from bnet.parsers import RaviParser, BNIFParser
from bnet.BNet import *

import sys


def main():
    if len( sys.argv ) != 2:
        print "Usage: %s <file>"%( sys.argv[ 0 ] )
        sys.exit( 1 )

    filename = sys.argv[ 1 ]

    p = BNIFParser()
    n = p.parseFile( filename )

    print str( n )
    for elem in n.variables.values(): print str( elem )


if __name__ == "__main__": main()

