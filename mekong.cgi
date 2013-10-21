#!/usr/bin/env python2.7

import cgi
import cgitb

import template

# enable fancy verbose errors
cgitb.enable()

# print headers
print "Content-Type: text/html"
print ""

# content time, yay!

values = {
    "messages": ["hello, world", "templates are not a waste of time", "if you think otherwise you are poop"]
}
print template.format_file("index.html", values)
