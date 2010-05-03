"""
BNet:
    Bayesian Network data structures, and associated parsers
"""

from exceptions import *
import operator
import pdb

class BNode:
    """Variable in a bayesian network.
    Has an associated list of parents, and a probability table"""

    def __init__( self, id, parents=(), table=None ):
        """
        @id - Node reference id
        @parents - list of parents
        @table - Pr( X | parents )
        """
        self.id = id
        self.parents = parents
        self.table = table

    def __str__( self ):
        return "[Node %d (%s)]\n"%( self.id, self.parents ) + reduce( lambda s, r: s + str(r) + '\n', self.table, '' )

    def __repr__( self ):
        return "[Node %d]"%self.id

class BNet:
    """Graph on Bayesian variables"""

    def __init__( self ):
        self.variables = {}

    def add( self, node ):
        self.variables[ node.id ] = node

    def __str__( self ):
        return "[Net %s]"%( str( self.variables ) )


from pyparsing import *

class BNetParser():
    def parse():
        """ Parse a file. Should be overwritten """
        raise NotImplementedError 

# Note: Using classes just to collect related functions. 
class RaviParser():
    """
    Parse a BNet in "Ravi" format, i.e.:
    // = comments

    network:
        int // number of nodes in network
        nodeblock*  // nodes in network

    nodeblock:
        {
            int*    // parents
            table   // probablility tables
        }

    table:
        (parentValues* float)+   // list of parent values followed by the
                                 // probablity values
    """

    def init( self ):
        self.tokens = []
        self.idx = 0

    def tokenise( self, str ):
        """Tokenise to include empty lines"""
        toks = []
        for line in str.splitlines():
            if line: 
                toks += line.split()
            else:
                toks.append( line )
            toks.append( '\n' )
        self.tokens = toks

    # For now, no pyparsing :-(
    def parse( self, str ):
        self.tokenise( str )
        self.idx = 0
        n = self.network( )
        return n

    def parseFile( self, fname ):
        f = open( fname, 'r' )
        str = f.read()
        f.close()

        return self.parse( str )

    def bools( self ):
        try: 
            n = int( self.tokens[ self.idx ] )
            if n == 0 or n == 1:
                self.idx += 1
                return bool( n )
            else:
                raise ParseException( "Expected bool" ) 
        except ValueError:
            raise ParseException( "Expected integer" ) 

    def integer( self ):
        try: 
            n = int( self.tokens[ self.idx ] )
            self.idx += 1
            return n 
        except ValueError:
            raise ParseException( "Expected integer" ) 

    def comment( self ):
        if self.tokens[ self.idx ].startswith( "//" ):
            # Skip to the new line
            while self.tokens[ self.idx ] != "\n": self.idx += 1

    def real( self ):
        try:
            r = float( self.tokens[ self.idx ] )
            self.idx += 1
            return r
        except ValueError:
            raise ParseException( "Expected float" ) 

    def keyword( self, k ):
        if self.tokens[ self.idx ] == k:
            self.idx += 1
        else:
            raise ParseException( "Expected '%s'"%(k) ) 

    def newline( self ):
        self.keyword( '\n' )

    def listOf( self, expr ):
        val = []
        idx_ = self.idx
        while True:
            try:
                idx_ = self.idx
                val.append( expr( ) )
            except ParseException:
                self.idx = idx_
                break
        return val

    def tableEntry( self ):
        pVals = self.listOf( self.bools )
        pr = self.real( )
        self.comment()
        self.newline()
        return ( tuple( pVals ), pr )

    def table( self ):
        ent = self.listOf( self.tableEntry )
        return ent

    def node( self, id ):
        self.keyword( '{' )
        self.comment()
        self.newline()

        # Handle no parents
        if self.tokens[ self.idx ] == '':
            self.idx += 1
            parents = []
        else:
            parents = self.listOf( self.integer )
        self.comment()
        self.newline()
        ptable = self.table( )
        self.keyword( '}' )
        return BNode( id, parents, ptable )

    def network( self ):
        n = self.integer( )
        self.comment()
        self.newline()

        net = BNet()

        for i in xrange( n ):
            net.add( self.node( i ) )
            self.comment()
            self.newline()

        return net


