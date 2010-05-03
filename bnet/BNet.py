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


