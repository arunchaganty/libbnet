"""
BNet:
    Bayesian Network data structures, and associated parsers
"""

from exceptions import *

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

class BNet:
    """Graph on Bayesian variables"""

    def __init__( self ):
        self.variables = {}


import pyparsing as pp

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
        (parentValues* float)*   // list of parent values followed by the
                                 // probablity values
    """

    def parse():
        pass






