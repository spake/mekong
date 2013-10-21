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

import template

# here are some constants
DATABASE_FILENAME = "mekong.db"

# functions and stuff
def hash(s):
	return hashlib.sha256(s).hexdigest()

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
    		username text,
    		password_hash text,
    		name text,
    		street text,
    		city text,
    		state text,
    		postcode text,
    		email text
		)
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

# template formatting values
values = {
    "page": form.getfirst("page", "home").lower(),
    "user": None
}

# check query stuff
# is someone trying to sign in?
if "username" in form and "password" in form:
	username = form["username"].value
	password = form["password"].value
	password_hash = hash(password)

	# check database for matching username and password
	#raise Exception((username, password_hash))
	result = cur.execute("SELECT COUNT(*) FROM users WHERE username = ? AND password_hash = ?", (username, password_hash)).fetchone()

	if result:
		values["user"] = 1
	else:
		values["user"] = 0

# print headers
print "Content-Type: text/html"
print ""

print template.format_file("index.html", values)
