#!/usr/bin/env python2.7

import cgi
import cgitb

# enable fancy verbose errors
cgitb.enable()

# print headers
print "Content-Type: text/html"
print ""

# content time, yay!

print """
<!DOCTYPE html>
<html>
    <head>
        <title>hi</title>
    </head>
    <body>
        <b>TODO</b>: assignment
    </body>
</html>
"""
