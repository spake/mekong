# templating engine for mekong
# yes, this is totally necessary.

# basic layout for engine:
# <{ for {var} in {expression} }>
# <{ end }>

# <{ if {expression} }>
# <{ elif {expression} }>
# <{ else }>
# <{ end }>

# <{ include {static_file} }>

# <% {expression} %>

# values are passed into the engine as a hash

# and yes, it'll be written as a parser. hooroo.

import re

COMMAND_OPEN = "<{"
COMMAND_CLOSE = "}>"
EXPRESSION_OPEN = "<%"
EXPRESSION_CLOSE = "%>"

FOR_RE = re.compile(r"^\s+for\s+([^\s]+)\s+in\s+(.*?)\s+$")
IF_RE = re.compile(r"^\s+if\s+(.*?)\s+$")
CONDITION_RE = re.compile(r"^\s+(elif\s+(.*?)|else)\s+$")
INCLUDE_RE = re.compile(r"^\s+include\s+(.*?)\s+$")
END_RE = re.compile(r"^\s+end\s+$")

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

    def set_contents(self, contents):
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

    def add_condition(self, condition, condition_type, contents):
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
        return str(eval(self.expression, values))

class IncludeNode(Node):
    """Contains another file that gets recursively processed by the templating engine."""
    pass

class Parser(object):
    """Creates a parse tree from a file and processes its templating commands."""
    def __init__(self, doc):
        """Initialise a parser with the given HTML document (with templating markup)."""
        # tokenise document
        # split on command/expression symbols
        symbols = tuple(map(re.escape, (COMMAND_OPEN, COMMAND_CLOSE, EXPRESSION_OPEN, EXPRESSION_CLOSE)))
        self.tokens = re.split(r"(%s|%s|%s|%s)" % symbols, doc)
        self.upto = 0

    def parse(self):
        return self.parse_collection(root=True)

    def curr(self):
        if self.upto < len(self.tokens):
            return self.tokens[self.upto]

    def next(self):
        if self.upto+1 < len(self.tokens):
            return self.tokens[self.upto+1]

    def finished(self):
        return self.upto >= len(self.tokens)

    def advance(self):
        self.upto += 1

    def parse_collection(self, root=False, parsing_if=False):
        collection_node = CollectionNode()

        while not self.finished():
            token = self.curr()
            if token == COMMAND_OPEN:
                # check whether it's an end command
                if END_RE.match(self.next()):
                    # if we're parsing the root node, this is not good
                    # otherwise just break
                    if root:
                        raise TemplatingError("Not expecting end command")
                    else:
                        break
                elif CONDITION_RE.match(self.next()):
                    if parsing_if:
                        break
                    else:
                        raise TemplatingError("Not expecting condition")

                self.advance() # consume opening thing
                node = self.parse_command() # parse command

            elif token == EXPRESSION_OPEN:
                self.advance() # consume opening thing
                node = self.parse_expression() # parse expression

            elif token == COMMAND_CLOSE or token == EXPRESSION_CLOSE:
                raise TemplatingError("Not expecting %s" % token)
            else:
                node = self.parse_text() # just a regular old text node

            collection_node.add_child(node)

        return collection_node

    def parse_command(self):
        # we need to discern which type of command we're dealing with
        command = self.curr()
        self.advance()

        # consume end of command token
        if not self.curr() == COMMAND_CLOSE:
            raise TemplatingError("Expecting %s" % COMMAND_CLOSE)
        self.advance()

        for_match = FOR_RE.match(command)
        if_match = IF_RE.match(command)
        include_match = INCLUDE_RE.match(command)

        if for_match:
            variable, expression = for_match.groups()
            node = ForNode(variable, expression)

            # read body of the loop
            contents = self.parse_collection()
            node.set_contents(contents)

        elif if_match:
            node = IfNode()

            # read in the contents of the if
            condition = if_match.group(1)
            condition_type = "if"
            contents = self.parse_collection(parsing_if=True)

            node.add_condition(condition, condition_type, contents)

            # read elifs and elses and such
            while True:
                # consume beginning symbol
                if not self.curr() == COMMAND_OPEN:
                    break # can't be an elif/else! something may be wrong...

                match = CONDITION_RE.match(self.next())
                if not match:
                    break # definitely not an elif/else

                # consume the opening thing and match
                self.advance()
                self.advance()
                # AND consume end symbol
                if not self.curr() == COMMAND_CLOSE:
                    raise TemplatingError("Expecting %s" % COMMAND_CLOSE)
                self.advance()

                condition = match.group(2)
                condition_type = match.group(1)
                contents = self.parse_collection(parsing_if=True)

                node.add_condition(condition, condition_type, contents)

                if condition_type == "else":
                    break

        elif include_match:
            pass # TODO: this

        else:
            raise TemplatingError("Invalid command '%s'" % command)

        # read end command if need be
        if if_match or for_match:
            # consume beginning
            if not self.curr() == COMMAND_OPEN:
                raise TemplatingError("Expecting %s" % COMMAND_OPEN)
            self.advance()
            # consume middle
            if not END_RE.match(self.curr()):
                raise TemplatingError("Expecting end command")
            self.advance()
            # and finally, consume end
            if not self.curr() == COMMAND_CLOSE:
                raise TemplatingError("Expecting %s" % COMMAND_CLOSE)
            self.advance()

        return node

    def parse_expression(self):
        node = ExpressionNode(self.curr())
        self.advance() # consume expression

        # ensure close expression symbol is present
        if not self.curr() == EXPRESSION_CLOSE:
            raise TemplatingError("Expecting %s" % EXPRESSION_CLOSE)
        self.advance()

        return node

    def parse_text(self):
        node = TextNode(self.curr())
        self.advance() # consume text
        return node
