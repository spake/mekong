#!/usr/bin/env python2.7

import cgi
import cgitb

# enable fancy verbose errors
cgitb.enable()

from collections import defaultdict
from Cookie import SimpleCookie
import datetime
import json
import hashlib
import os
import random
import re
import sqlite3
import time

import template

# here are some constants
DATABASE_FILENAME = "mekong.db"
MIN_PASSWORD_LENGTH = 6

# functions and stuff
def hash(s):
    return hashlib.sha256(s).hexdigest()

# session functions
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

    conn.commit()

    return sid

def session_to_username(sid):
    # get the username from a session id

    result = cur.execute("SELECT username FROM sessions WHERE sid = ?", (sid,)).fetchone()
    if result:
        return result["username"]

def delete_session(sid):
    # remove the session

    cur.execute("DELETE FROM sessions WHERE sid = ?", (sid,))

    conn.commit()

# user functions
def get_user(username):
    # get all their info
    user = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return user

# email functions
# book parsing functions
def parse_date(date_str):
    if date_str:
        hyphens = date_str.count("-")
        month, day = 1, 1 # default values

        if hyphens == 2:
            year, month, day = map(int, date_str.split("-"))
        elif hyphens == 1:
            year, month = map(int, date_str.split("-"))
        else:
            year = int(date_str)
        return datetime.date(year, month, day)

def parse_int(int_str):
    if int_str and type(int_str) == str:
        return int(int_str)
    return int_str

def parse_price(price_str):
    return float(price_str[1:])

# create db if it doesn't already exist
db_exists = os.path.exists(DATABASE_FILENAME)
conn = sqlite3.connect(DATABASE_FILENAME)
conn.row_factory = sqlite3.Row
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
            sid text primary key,
            username text
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
page = form.getfirst("page", "home").lower()

values = {
    "page": page,
    "signin_fail": False,
    "register_fail": False
}

# some vars
user = None
sid = None

# check cookies
cookies_string = os.environ["HTTP_COOKIE"] if "HTTP_COOKIE" in os.environ else ""
cookies = SimpleCookie(cookies_string)

if "sid" in cookies:
    sid = cookies["sid"].value

# check query stuff
action = form.getvalue("action")

# check basic actions (register/signin)
if action == "signin":
    username = form["username"].value
    password = form["password"].value
    password_hash = hash(password)

    # check database for matching username and password
    result = cur.execute("SELECT username FROM users WHERE username = ? AND password_hash = ?", (username, password_hash)).fetchone()

    if result:
        # it's valid!
        user = get_user(username)

        # create a session for them
        sid = create_session(user)
    else:
        # lol they fail
        page = form["page"].value # homepage
        values["signin_fail"] = True
elif action == "register":
    username = form.getvalue("username")
    password = form.getvalue("password")
    password2 = form.getvalue("password2")

    name = form.getvalue("name")
    street = form.getvalue("street")
    city = form.getvalue("city")
    state = form.getvalue("state")
    postcode = form.getvalue("postcode")
    email = form.getvalue("email")

    error = ""

    # check stuff
    # is the username taken?
    if not username:
        error = "Please enter a username."
    elif not re.match(r"^[A-Za-z0-9_\.]+$", username):
        error = "Make sure that your username only contains alphanumeric characters, _ and ."
    elif get_user(username):
        error = "That username is already taken, try another!"
    elif password != password2:
        error = "Make sure both passwords you entered match."
    elif not password or len(password) < MIN_PASSWORD_LENGTH:
        error = "Please choose a password that's at least %d characters long!" % MIN_PASSWORD_LENGTH
    elif not name or not name.strip():
        error = "Please enter your name."
    elif not street or not street.strip():
        error = "Please enter your street."
    elif not city or not city.strip():
        error = "Please enter your city."
    elif not state or not state.strip():
        error = "Please choose your state."
    elif not postcode or not re.match(r"^[0-9]{4}$", postcode):
        error = "Please enter a valid postcode (4 digits)."
    elif not email or not re.match(r"^[a-z0-9_-]+(\.[a-z0-9_-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*$", email):
        error = "Please enter a valid email address."
    else:
        # oh shit no errors, sweet
        # register the user
        password_hash = hash(password)
        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (username, password_hash, name.strip(), street.strip(),
                 city.strip(), state.strip(), postcode, email))

        # sign them in
        user = get_user(username)
        sid = create_session(user)

    if error:
        # set error stuff
        values["register_fail"] = True
        values["register_error"] = error

        values["register_data"] = {
            "username": username,
            "password": password,
            "password2": password2,
            "name": name,
            "street": street,
            "city": city,
            "state": state,
            "postcode": postcode,
            "email": email
        }
elif action == "signout":
    # remove session
    delete_session(sid)
    sid = None
    user = None

    values["signout_success"] = True

# are they logged in? i.e. is sid set
if sid:
    username = session_to_username(sid)
    if username:
        # yay, it's a valid session + user!
        user = get_user(username)
    else:
        sid = None

# check page selection
if page == "search":
    # get query from post
    query = form.getfirst("query", "")
    values["query"] = query

    # now fetch results from db
    # thanks http://stackoverflow.com/questions/3017417/how-do-i-assign-different-weights-to-columns-in-sql-server-full-text-search
    results = cur.execute("""
    SELECT * FROM (
        SELECT books.*, 3 AS rank FROM books NATURAL JOIN authors WHERE authors.name LIKE "%" || ? || "%"
        UNION
        SELECT *, 2 AS rank FROM books WHERE title LIKE "%" || ? || "%"
        UNION
        SELECT *, 1 AS rank FROM books WHERE productdescription LIKE "%" || ? || "%"
    ) results
    GROUP BY isbn
    ORDER BY rank DESC, -salesrank DESC
    """, (query,)*3).fetchall()
    # remember to also fetch authors
    books = []
    for result in results:
        book = dict(result)
        authors = []
        for author in cur.execute("SELECT name FROM authors WHERE isbn = ?", (book["isbn"],)).fetchall():
            authors.append(author["name"])
        book["authors"] = authors
        books.append(book)

    values["results"] = books

# put sid into cookies
cookies["sid"] = sid if sid else ""

# assign some last minute values
values["user"] = user

# print headers
print "Content-Type: text/html"

# cookies
print cookies.output()

# end headers
print ""

print template.format_file("index.html", values)
