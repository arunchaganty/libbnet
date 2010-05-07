"""
bnet.parsers:
    Parses various Bayesian Network formats to construct a BNet
"""

import operator
from exceptions import *
from BNet import *
from pyparsing import *

class BNetParser():
    """
    Generic BNetParser
    """
    def parse( self, str ):
        """ Parse a file. Should be overwritten """
        raise NotImplementedError 

    def parseFile( self, fname ):
        f = open( fname, 'r' )
        str = f.read()
        f.close()

        return self.parse( str )

class RaviParser( BNetParser ):
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

    def __init__( self ):
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
        return ( tuple( pVals ), (pr, 1-pr) )

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
        ptable = dict( self.table( ) )
        self.keyword( '}' )

        values = [True, False]

        return BNode( id, parents, (id,), values, ptable )

    def network( self ):
        n = self.integer( )
        self.comment()
        self.newline()

        net = BNet()

        for i in xrange( 1, n+1 ):
            net.add( self.node( i ) )
            self.comment()
            self.newline()

        return net

class BNIFParser( BNetParser ):
    """
    Parse a BNet in BNIF format, i.e.:
    // = comments
    /* */ = comments
    
    PROPERTYSTRING: PROPERTY (~[";"])* ";"

    CompilationUnit() :
      NetworkDeclaration() 
      ( VariableDeclaration()   |    ProbabilityDeclaration()  )*
      EOF

    NetworkDeclaration() :
      NETWORK WORD NetworkContent()

    NetworkContent() :
      "{" ( Property()  )* "}"

    VariableDeclaration() :
      VARIABLE ProbabilityVariableName() VariableContent()

    VariableContent(String name) :
      "{"  ( Property() | VariableDiscrete() )*   "}"

    VariableDiscrete() :
      VARIABLETYPE DISCRETE 
        "[" DECIMAL_LITERAL "]" "{"    VariableValuesList()    "}" ";"

    void VariableValuesList() :
        ProbabilityVariableValue() 
        ( ProbabilityVariableValue() )*

    ProbabilityVariableValue() : WORD

    ProbabilityDeclaration() :
      PROBABILITY ProbabilityVariablesList() ProbabilityContent()

    ProbabilityVariablesList() :
       "("  ProbabilityVariableName() ( ProbabilityVariableName()   )* ")"

    ProbabilityVariableName() : 

    ProbabilityContent()
      "{" ( Property() | ProbabilityDefaultEntry()   | ProbabilityEntry()   |
          ProbabilityTable()  )* "}"

    ProbabilityEntry() :
       ProbabilityValuesList() FloatingPointList() ";"

    ProbabilityValuesList() :
       "(" ProbabilityVariableValue() ( ProbabilityVariableValue()   )* ")"

    ProbabilityDefaultEntry() :
       FloatingPointList() ";"

    ProbabilityTable() :
       FloatingPointList() ";"

    FloatingPointList() :
      FloatingPointToken()  ( FloatingPointToken()  )*

    FloatingPointToken() :  

    Property() :  
    """

    def __init__( self ):
        self.debug = False
        pass

    def parse( self, inp ):
        net = BNet()

        NETWORK = Keyword( "network" ).suppress()
        VARIABLE = Keyword( "variable" ).suppress()
        PROBABILITY = Keyword( "probability" ).suppress()
        PROPERTY = Keyword( "property" ).suppress()
        VARIABLETYPE = Keyword( "type" ).suppress()
        DISCRETE = Keyword( "discrete" ).suppress()
        DEFAULTVALUE = Keyword( "default" ).suppress()
        TABLEVALUES = Keyword( "table" ).suppress()

        LBRAC = Literal( '(' ).suppress()
        RBRAC = Literal( ')' ).suppress()
        LCURL = Literal( '{' ).suppress()
        RCURL = Literal( '}' ).suppress()
        LSQUA = Literal( '[' ).suppress()
        RSQUA = Literal( ']' ).suppress()
        SEMI = Literal( ';' ).suppress()
        ORSEP = Literal( '|' ).suppress()

        identifier = Word( alphas, alphanums )
        identifier.setName( 'identifier' )

        property = PROPERTY + OneOrMore( ~( SEMI ) ) + SEMI
        property.setName( 'property' )

        number = Word( nums )
        number.setName( 'number' )
        number.setParseAction( lambda s,l,t: [ int( t[ 0 ] ) ] )

        real = Combine( number + '.' + number )
        real.setName( 'real' )
        real.setParseAction( lambda s,l,t: [ float( t[ 0 ] ) ] )

        value = identifier
        variable_values = Group( delimitedList( value ) )
        
        prEntry = LBRAC + variable_values + RBRAC + Group( delimitedList( real ) ) + SEMI
        prEntry.setName( 'prEntry' )
        prEntry.setParseAction( lambda s,l,t: [ ( tuple( t[0] ), tuple( t[1] ) ) ] )

        defaultPrEntry = Group( delimitedList( real ) ) + SEMI
        defaultPrEntry.setName( 'defaultPrEntry' )
        defaultPrEntry.setParseAction( lambda s,l,t: [ tuple( t[0] ) ] )

        prTable = TABLEVALUES + Group( delimitedList( real ) ) + SEMI
        prTable.setName( 'prTable' )
        prTable.setParseAction( lambda s,l,t: [ ((), tuple( t[0] )) ] )

        condVars = LBRAC + Group( identifier + Optional( ORSEP + delimitedList( identifier ) ) ) + RBRAC
        condVars.setName( 'condVars' )

        probability = PROBABILITY + condVars + LCURL + Group( ZeroOrMore( property ) ) + Group( ZeroOrMore( defaultPrEntry | prEntry | prTable ) ) + RCURL
        probability.setName( 'probability' )
        probability.addParseAction( lambda s,l,t: net.get( t[0][0] ).setTable( t[2] ) )
        probability.addParseAction( lambda s,l,t: ( net.get( t[ 0 ][0] ).setParents( t[0][1:] ) ) if len( t[0] ) > 1 else False )

        variable_discrete = VARIABLETYPE + DISCRETE + LSQUA + number + RSQUA + LCURL + variable_values + RCURL + SEMI
        variable_discrete.setName( 'variable_discrete' )
        variable_discrete.setParseAction( lambda s,l,t : [ t[ 1 ] ] )

        variable = VARIABLE + identifier + LCURL + ZeroOrMore( property | variable_discrete ) + RCURL
        variable.setName( 'variable' )
        variable.addParseAction( lambda s,l,t : net.add( BNode( t[ 0 ], values = map( str, t[1] ) )) ) 
        variable.addParseAction( lambda s,l,t : [] ) 

        network = NETWORK + identifier + LCURL + Group( ZeroOrMore( property ) ) + RCURL
        network.setName( 'name' )
        toplevel = network + ZeroOrMore( variable | probability )
        toplevel.setName( 'toplevel' )

        if self.debug:
            for elem in [ value, variable_values, prEntry, defaultPrEntry, prTable, condVars,
                    probability, variable_discrete, variable, network, toplevel ]:
                elem.setDebug()

        toplevel.parseString( inp )
        
        return net

