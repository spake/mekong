#!/usr/bin/env python2.7

import template

values = {
    "test": "poop",
    "things": ['a','b','c','eeeeeep'],
    "matrix": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
}

print template.format_file("template_test.html", values)
