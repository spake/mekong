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

COMMAND_OPEN = "<<"
COMMAND_CLOSE = ">>"
EXPRESSION_OPEN = "<%"
EXPRESSION_CLOSE = "%>"

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
            new_values = values.copy()
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
    def __init__(self, expression):
        self.expression = expression

    def render(self, values):
        return eval(self.expression, values)

class IncludeNode(Node):
    """Contains another file that gets recursively processed by the templating engine."""
    pass

class Parser(object):
    """Creates a parse tree from a file and processes its templating commands."""
    def __init__(self, doc):
        """Initialise a parser with the given HTML document (with templating markup)."""
        # tokenise document
        # split on command/expression symbols
        self.tokens = re.split(r"(%s|%s|%s|%s)" % (COMMAND_OPEN, COMMAND_CLOSE, EXPRESSION_OPEN, EXPRESSION_CLOSE), doc)
        self.upto = 0

    def parse(self):
        return self.parse_collection()

    def curr(self):
        if self.upto < len(self.tokens);
            return self.tokens[self.upto]

    def next(self):
        if self.upto+1 < len(self.tokens):
            return self.tokens[self.upto+1]

    def finished(self):
        return self.upto >= len(self.tokens)

    def advance(self):
        self.upto += 1

    def parse_collection(self, root=False):
        collection_node = CollectionNode()

        while not self.finished():
            token = self.curr()
            if token == COMMAND_OPEN:
                self.advance() # consume opening thing
                node = parse_command() # parse command

                # assert closing thing
                if self.curr() != COMMAND_CLOSE:
                    raise TemplatingError("Excepting %s" % COMMAND_CLOSE)

                self.advance() # consume closing thing
            elif token == EXPRESSION_OPEN:
                self.advance() # consume opening thing
                node = parse_expression() # parse expression

                # assert closing thing
                if self.curr() != EXPRESSION_CLOSE:
                    raise TemplatingError("Expecting %s" % EXPRESSION_CLOSE)

                self.advance() # consume closing thing
            elif token == COMMAND_CLOSE:
                # if we are parsing the root node then this is a bad thing
                # otherwise just break out of the loop
                if root:
                    raise TemplatingError("Not expecting %s" % token)
                else:
                    break
            elif token == EXPRESSION_CLOSE:
                raise TemplatingError("Not expecting %s" % token)
            else:
                node = parse_text() # just a regular old text node

            collection_node.add_child(node)

        return collection_node

    def parse_text(self):
        node = TextNode(self.curr())
        self.advance() # consume text

    def parse_command(self):
        # we need to discern which type of command we're dealing with
        command = self.curr().strip()

        FOR_RE = re.compile(r"^for\s+([^\s]+)in\s+(.*)$")
        IF_RE = re.compile(r"^if\s+(.*)$")
        ELIF_RE = re.compile(r"^elif\s+(.*)$")
        ELSE_RE = re.compile(r"^else\s+(.*)$")
        INCLUDE_RE = re.compile(r"^include\s+(.*)$")

        for_match = FOR_RE.match(command)
        if_match = IF_RE.match(command)
        include_match = INCLUDE_RE.match(command)

        if for_match:
            variable, expression = for_match.groups()
            for_node = ForNode(variable, expression)
            # read boyd of the loop

    def parse_expression(self):
        pass
