#!/usr/bin/env python2.7

import template

data = open("template_test.html").read()

values = {
    "test": "poop",
    "things": ['a','b','c'],
    "matrix": [[1,0,0],[0,1,0],[0,0,1]]
}

parser = template.Parser(data)
tree = parser.parse()
output = tree.render(values)

print output
