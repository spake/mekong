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

class TemplatingError(Exception):
    pass

class Node(object):
    """A generic node for the templating engine."""
    def __init__(self, string):
        """Initialises a node with the given string as its content."""
        self.string = string

    def render(self, values):
        """Renders the node using the given values."""
        raise NotImplementedError

class CollectionNode(Node):
    """Contains a collection of child nodes."""
    def __init__(self):
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def render(self, values):
        output = ""
        for child in self.children:
            output += child.render(values)
        return output

class TextNode(Node):
    """Contains static text."""
    def render(self, values):
        return self.string

class ForNode(Node):
    """Contains a loop to iterate over a set of values."""
    def __init__(self, variable, iterable):
        self.variable = variable
        self.iterable = iterable
        self.contents = None # CollectionNode with the children of the loop

    def set_contents(contents):
        self.contents = contents

    def render(self, values):
        output = ""
        # evaluate and iterate
        for thing in eval(self.iterable, values):
            # create new set of values
            # TODO: figure out how to copy dictionary
            new_values[self.variable] = thing
            # render children using these new values
            output += self.contents.render(new_values)
        return output

class IfNode(Node):
    """Contains a conditional statement."""
    def __init__(self):
        self.conditions = []
        self.contents = []

    def add_condition(condition, condition_type, contents):
        # always evaluate an else
        if condition_type == "else":
            condition = "True"

        self.conditions.append(condition)
        self.contents.append(contents)

    def render(self, values):
        # step through each condition and evaluate one by one until we get one that's true
        for condition, contents in zip(self.conditions, self.contents):
            result = eval(condition, values)
            if result:
                # found one that's true, yay
                return contents.render(values)

        # found nothing true :(
        return ""

class ExpressionNode(Node):
    """Contains an expression to be evaluated."""
    pass

class IncludeNode(Node):
    """Contains another file that gets recursively processed by the templating engine."""
    pass

class Parser(object):
    """Creates a parse tree from a file and processes its templating commands."""
    pass
