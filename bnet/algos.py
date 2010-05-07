"""
Algorithms for Bayesian Networks
"""

import copy
import random

import BNet

def cdf( pdf ):
    """Make a choice from a value set in correspondence with attached probabilities"""
    cdf_ = []
    P = 0
    for v,pr in pdf:
        P += pr
        cdf_.append( (v, P) )

    return cdf_

def binsearch(items, val, key=lambda x: x):
    """
    Returns the item in items whose bucket contains val - assumes items is (item, bottom of bucket)
    """
    low, high = 0, len(items)-1
    while ((high - low) > 0):
        if val < key(items[(low+high)/2]):
            high = (low+high)/2 
        elif val == key(items[(low+high)/2]):
            low = high = (low+high)/2
        else:
            low = (low+high)/2 + 1

    return items[high]

def select( items, key = lambda x: x):
    """Randomly select an item based on the (val, pr) list given"""
    return binsearch(items, random.random(), key) 


def roulette(items, num, key=lambda x: x):
    """
    Runs a roulette selection algorithm on the items in the list given. 
    The algorithm is roughly a binary search on the list to find out which item is to be selected (with random values)
    """

    selection = [ select( items ) for i in xrange(num)]
    return selection

def cross(*args):
    ans = [[]]
    for arg in args:
        ans = [x+[y] for x in ans for y in arg]
    return ans

def selectAttr( attrs, values, attr ):
    return filter( lambda x: x[0] == attr, zip( attrs, values ) )[1]

def selectAttrs( attrs, values, attrList ):
    return map( lambda x: x[1], filter( lambda x: x[0] in attrList, zip( attrs, values ) ) )

def joinTable( net, *tables ):
    """
    Join the n probability tables
    """
    parentIds = ( reduce( lambda state, n : state.union(n.parents), tables, set([]) ) )
    parents = map( net.get, parentIds )
    attrs = ( reduce( lambda state, n : state + n.attrs, tables, () ) )
    values = ( reduce( lambda state, n : state.append( n.values ) or state, tables, [] ) )

    pVals = ( reduce( lambda state, p : state.append( p.values ) or state, parents, [] ) )
    pVals = cross( *pVals )

    table = {}
    for pVal in pVals:
        for value in cross( *values ):
            valueArr = ()
            p = 1
            for node in tables:
                parent_ = selectAttrs( parentIds, pVal, node.parents )
                value_ = selectAttrs( attrs, value, node.attrs )
                p *= selectAttr( node.table[ tuple( parent_ ) ], node.values, value_ )
                valueArr += value_
            print pVal, valueArr

def gibbsSample( net, ctx, burnIn=100, samples=1000 ):
    """
    Apply gibbs sampling to infer a new Network
    """
    def gibbsChoice( net, ctx, node ):
        # Get the nodes for the Markov Blanket
        children = map( net.get, net.getChildren( node.id ) )
        parents = map( net.get , net.getParents( node.id ) )

        Pr = []
        # Get P( V | p)
        prVector = ctx.prVector( node.id )
        for val, prP in prVector.items():
            # Pr of any value Pr( V | p, c ) = P( c | V ) * P( V | p ) 
            ctx.setVariable( node.id, val )
            pr = prP
            for child in net.getChildren( node.id ):
                prVector_ = ctx.prVector( child )
                pr *= prVector_[ ctx.get( child ) ]
            Pr.append( (val, pr ) )
        total = sum( [ pr for v, pr in Pr ] )
        Pr = [ (v,pr/total) for v,pr in Pr ] 

        val = select( cdf( Pr ), key = lambda vPr: vPr[1] )
        return val[0]
    def removeParent( node, ctx_variables ):
        parents_ = filter( lambda k: k not in ctx_variables.keys(), node.parents )
        # Join with parents list to get key
        table_ = {}
        for key,value in node.table.items() :
            key_ = zip( node.parents, node.table[key] )
            key_ = tuple( [ kV[1] for kV in key_ if kV[0] in parents_ ] )
            table_[key_] = value

        node.parents = parents_
        node.table = table_

    # Create a deep copy of the net to modify
    net = copy.deepcopy( net )
    ctx = copy.deepcopy( ctx )

    # Set the variables present in the context to be equal to the value in the
    # context
    net.applyContext( ctx )

    # List of variables whose value is to be modified
    variables = net.variables.keys()
    ctx_variables = ctx.getVariables()
    for k,v in ctx_variables.items():
        variables.remove( k )

    # Choose a random initial value for all variables 
    for var in variables:
        ctx.setVariable( var, random.choice( net.get( var ).values ) )

    # Just follow the MC
    for i in xrange( burnIn ):
        # Choose one variable, a randomly 
        var = random.choice( variables )
        node = net.get( var )
        val = gibbsChoice( net, ctx, node )
        ctx.setVariable( node.id, val )

    # Initialise the stats table
    stats = {}
    for var in net.variables.values():
        stat = {}
        for parentValues in var.table.keys():
            stat_ = {}
            for value in var.values:
                stat_[value] = 0
            stat[parentValues] = stat_
        stats[var.id] = stat

    # Now for samples duration, compute statistics
    for i in xrange( samples ):
        var = random.choice( variables )
        node = net.get( var )
        val = gibbsChoice( net, ctx, node )
        ctx.setVariable( node.id, val )

        # set statistics using the variable and it's parents
        stats[node.id][ tuple( map( ctx.get, node.parents ) ) ][ val ] += 1

    # Compute distribution
    # Update the original network, and remove any dependence on our key variable
    for node, stat in stats.items():
        node = net.get( node )
        
        if node.id in ctx_variables.keys():
            node.parents = []
            node.table = { (): tuple([ int( value == ctx_variables[ node.id ]) for value in node.values]) }
            continue

        for parentValue, stat_ in stat.items():
            total = sum( stat_.values() )
            if total > 0:
                for key in stat_.keys():
                    stat_[key] = float(stat_[key])/total
        node.table = dict( zip( map( tuple, stat.keys() ),  [ tuple([ stat_[val] for val in node.values ]) for stat_ in stat.values() ]  ) )
        node = removeParent( node, ctx_variables )

    return net

def exactQuery( net, ctx, query ):
    """
    Query the probability distribution of a variable given evidence
    """
    
    # Create a deep copy of the net to modify
    net = copy.deepcopy( net )
    ctx = copy.deepcopy( ctx )

    variables = net.variables
    ctx_variables = ctx.getVariables()

    # Create a variable ordering
    ordering = net.variables.keys()
    ordering.remove( query )

    max_id = max( ordering )

    # Process functions bucket by bucket
    for bVar in ordering:
        # Get all variables which involve var
        bucket = [ var_ for var_ in variables.values() if bVar in var_.parents ]

        # Create a new node whose value is sum_{ var } ( pi( bucket ) )

        # Get consolidated list of parents
        parents = set([])
        attrs = []
        for var in bucket: 
            parents = parents.union( set( var.parents ) )
        parents = map( net.get, list( parents ) )
        if not parents:
            continue
        parents.remove( net.get( bVar ) )
        print parents
        print bucket
        print attrs


        # Iterate over all possible values
        table = {}
        index  = [ bVar ]
        index += [ p.id for p in parents]

        for var in cross( *( [ p.values for p in parents ] ) ):
            P = [ 0 for i in attrs ]
            for val in net.get( bVar ).values:
                value = [ val ]
                value += var

                p = (1,1)
                attr_ = []
                for node in bucket:
                    value_ = tuple( map( lambda x: x[1], filter( lambda x: x[0] in node.parents, zip(index, value) ) ) )
                    p = ( p[0] * node.table[ value_ ][0], p[1] * node.table[ value_ ][1] )
                P = (P[0]+p[0], P[1]+p[1])
            table[ tuple( var ) ] = P
            print var, (P)
        max_id += 1
        variables[ max_id ] = BNet.BNode( max_id, [ p.id for p in parents ], (True,False), table )

    return variables

