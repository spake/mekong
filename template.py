# templating engine for mekong
# yes, this is totally necessary.

# basic layout for engine:
# << for {var} in {expression} >>
# << end for >>

# << if {expression} >>
# << elif {expression} >>
# << else >>
# << end if >>

# << include {static_file} >>

# <% {expression} %>

# values are passed into the engine as a hash

# and yes, it'll be written as a parser. hooroo.

class Node(object):
    """A generic node for the templating engine."""
    pass

class CollectionNode(Node):
    """Contains a collection of child nodes."""
    pass

class TextNode(Node):
    """Contains static text."""
    pass

class ForNode(Node):
    """Contains a loop to iterate over a set of values."""
    pass

class IfNode(Node):
    """Contains a conditional statement."""
    pass

class ExpressionNode(Node):
    """Contains an expression to be evaluated."""
    pass

class IncludeNode(Node):
    """Contains another file that gets recursively processed by the templating engine."""
    pass

class Parser(object):
    """Creates a parse tree from a file and processes its templating commands."""
    pass
