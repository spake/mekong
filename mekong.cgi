#!/usr/bin/env python2.7

import cgi
import cgitb

# enable fancy verbose errors
cgitb.enable()

import json
import hashlib
import os
import re
import sqlite3
import time

import template

# here are some constants
DATABASE_FILENAME = "mekong.db"

# functions and stuff
def hash(s):
	return hashlib.sha256(s).hexdigest()

def create_session(user):
    # do this similarly to PHP sessions, the code for which is at:
    # https://github.com/php/php-src/blob/master/ext/session/session.c

    # get their username and password hash
    username = user["username"]
    passhash = user["password_hash"]
    # get their IP
    ip = os.environ["REMOTE_ADDR"]
    # stupid time string
    timestr = str(time.time())
    # also a random number because why not
    # even though it's probably seeded by the time so kind of useless
    randomstr = str(random.random())

    s = username + passhash + ip + timestr + randomstr
    sid = hashlib.sha256(s).hexdigest()

    # now insert it into the db
    cur.execute("INSERT INTO sessions VALUES (?, ?)", (sid, username))

    return sid

def session_to_username(sid):
    # get the username from a session id

    result = cur.execute("SELECT username FROM sessions WHERE sid = ?", (sid,)).fetchone()
    if result:
        return result["username"]

def delete_session(sid):
    # remove the session

    cur.execute("DELETE FROM sessions WHERE sid = ?", (sid,))

# create db if it doesn't already exist
db_exists = os.path.exists(DATABASE_FILENAME)
conn = sqlite3.connect(DATABASE_FILENAME)
cur = conn.cursor()

if not db_exists:
    # create tables
    cur.execute("""
        CREATE TABLE books (
            isbn text primary key,
            binding text,
            catalog text,
            ean text,
            edition text,
            numpages integer,
            publication_date text,
            productdescription text,
            publisher text,
            releasedate text,
            salesrank integer,
            price real,
            title text,
            year integer,
            smallimageurl text,
            mediumimageurl text,
            largeimageurl text,
            smallimagewidth integer,
            smallimageheight integer,
            mediumimagewidth integer,
            mediumimageheight integer,
            largeimagewidth integer,
            largeimageheight integer
        )
        """)

    cur.execute("""
        CREATE TABLE authors (
            name text,
            isbn text
        )
    	""")

    cur.execute("""
    	CREATE TABLE users (
    		username text primary key,
    		password_hash text,
    		name text,
    		street text,
    		city text,
    		state text,
    		postcode text,
    		email text
		)
    	""")

    cur.execute("""
        CREATE TABLE sessions (
            id text primary key,
            username text
        """)

    # parse books.json
    f = open("books.json")
    data = json.loads(f.read())
    f.close()

    for values in data.values():
        # convert to defaultdict, because some stupid books don't have all the keys
        values = defaultdict(lambda: None, values) # return None if key doesn't exist

        # add to database
        cur.execute("""
            INSERT INTO books VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (values["isbn"],
            values["binding"],
            values["catalog"],
            values["ean"],
            values["edition"],
            parse_int(values["numpages"]),
            parse_date(values["publication_date"]),
            values["productdescription"],
            values["publisher"],
            parse_date(values["releasedate"]),
            parse_int(values["salesrank"]),
            parse_price(values["price"]),
            values["title"],
            parse_int(values["year"]),
            values["smallimageurl"],
            values["mediumimageurl"],
            values["largeimageurl"],
            values["smallimagewidth"],
            values["smallimageheight"],
            values["mediumimagewidth"],
            values["mediumimageheight"],
            values["largeimagewidth"],
            values["largeimageheight"]))

        for author in values["authors"]:
            cur.execute("INSERT INTO authors VALUES (?, ?)", (author, values["isbn"]))

    # save everything
    conn.commit()

# content time, yay!
form = cgi.FieldStorage()

# some vars
user = None
sid = None

# check query stuff
# is someone trying to sign in?
if "username" in form and "password" in form:
	username = form["username"].value
	password = form["password"].value
	password_hash = hash(password)

	# check database for matching username and password
	result = cur.execute("SELECT COUNT(*) FROM users WHERE username = ? AND password_hash = ?", (username, password_hash)).fetchone()

	if result:
        # it's valid!

        # get all their info
        user = cur.execute("SELECT * FROM users WHERE username = ?", (username,))

        # create a session for them
        sid = create_session(user)
	else:
		# lol they fail
        # TODO: post a fail message
        pass

# print headers
print "Content-Type: text/html"

# cookies
if sid:
    print "Set-Cookie: sid=%s" % sid

# end headers
print ""

# template formatting values
values = {
    "page": form.getfirst("page", "home").lower(),
    "user": user
}

print template.format_file("index.html", values)

cgi.print_environ()
