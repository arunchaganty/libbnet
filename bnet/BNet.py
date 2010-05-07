"""
BNet:
    Bayesian Network data structures, and associated parsers
"""

from exceptions import *
import operator
import copy

class BNode:
    """Variable in a bayesian network.
    Has an associated list of parents, and a probability table"""

    def __init__( self, id, parents=(), attrs = (), values=(), table=None ):
        """
        @id - Node reference id
        @parents - list of parents
        @table - Pr( X | parents )
        """
        self.id = id
        self.parents = parents
        self.attrs = attrs
        self.values = values
        self.table = table

    def setValues( self, values ):
        self.values = values

    def setTable( self, table ):
        self.table = dict( table )

    def setParents( self, parents ):
        self.parents = tuple( parents )

    def setValue( self, value ):
        prVector = tuple( [ int( value == val ) for val in self.values ] )
        for k in self.table:
            self.table[k] = prVector

    def __str__( self ):
        ret = "[Node %s %s]"%( str( self.id ), self.parents ) + '\n'
        ret += ' '.join( map( str, self.parents ) ) + ' | ' + ' '.join( map( str, self.values ) ) + '\n'
        if self.table: ret += '\n'.join( map( str, self.table.items() ) )
        return ret

    def __repr__( self ):
        return "[Node %s]"%( str( self.id ) )


class BNet:
    """Graph on Bayesian variables"""

    def __init__( self ):
        self.variables = {}
        self.adjList = {}

    def add( self, node ):
        """Add a variable node"""

        self.variables[ node.id ] = node
        self.adjList[ node.id ] = []

        for var in node.parents:
            self.adjList[ var ].append( node.id )

    def getChildren( self, id ):
        """Get children for the node"""
        return self.adjList[ id ]

    def getParents( self, id ):
        """Get parents for the node"""
        return self.get(id).parents

    def get( self, id ):
        """Get a variable node"""
        return self.variables[ id ]

    def getBlanket( self, id ):
        """Get the Markov blanket for a variable"""

        vars = [ id ]
        vars += self.get( id ).parents
        vars += self.getChildren( id )
        
        return vars

    def applyContext( self, ctx ):
        """Set the values defined in the context"""
        for k,v in ctx.getVariables().items():
            self.variables[ k ].setValue( v )

    def toDot( self ):
        """Convert file to a dot"""
        dot = ""
        dot += "digraph {\n"

        for var in self.variables.keys():
            dot += "%s;\n"%( var )

        for var in self.variables.values():
            for parent in var.parents:
                dot += "%s->%s;\n"%( parent, var.id )

        dot += "}\n"
        return dot

    def __str__( self ):
        return "[Net %s]"%( str( self.variables ) )

class Context:
    """Bayesian context"""

    def __init__( self, net, context=None ):
        if context:
            assert net == context.net
            self = copy.copy( context )
        else:
            self.net = net
            self.variables = {}
            for key in net.variables:
                self.variables[key] = None

    def __str__( self ):
        return str( self.variables )

    def __repr__( self ):
        return str( self.variables )

    def getVariables( self ):
        return dict( filter( lambda (k,v): v != None, self.variables.items() ) )

    def get( self, id ):
        return self.variables[ id ]

    def setVariable( self, id, value ):
        if value not in self.net.variables[id].values:
            raise ValueError
        self.variables[id] = value

    def unsetVariable( self, id ):
        self.variables[id] = None

    def prVector( self, id ):
        node = self.net.get( id )
        pr = tuple( map( self.get, node.parents ) )
        values = node.table[pr]
        return dict( zip( node.values, values ) )

