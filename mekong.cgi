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
import math
import os
import random
import re
import smtplib
import sqlite3
import time
import urllib

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

# cart functions
def get_cart_total(username):
    total = 0
    for result in cur.execute("SELECT price, quantity FROM cart_contents NATURAL JOIN books WHERE username = ?", (username,)):
        total += result["price"]*result["quantity"]
    return total

# email functions
EMAIL_USERNAME = "mekong@caley.com.au"
EMAIL_PASSWORD = "6de2789b4614f57312d8e70f27f2dea65665d2681bc4e87c0f8d9dffd0f0c415"

def send_email(recipient, subject, content):
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nContent-Type: text/html\r\n\r\n%s" % (EMAIL_USERNAME, recipient, subject, content)

    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    smtp.sendmail(EMAIL_USERNAME, recipient, msg)
    smtp.quit()

def send_verification_email(user):
    url = "http://cgi.cse.unsw.edu.au/~gric057/mekong/?verify=%s" % user["verification_token"]

    msg = """Hi there %s! Click the following link to verify your brand new Mekong account:<br>
    <a href="%s">%s</a><br><br>
    If you didn't create an account with Mekong, then you can safely delete this message.
    """ % (user["username"], url, url)

    send_email(user["email"], "Mekong email verification", msg)

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

# string function thing
def in_range(s, minimum, maximum):
    return len(s) >= minimum and len(s) <= maximum

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
            email text,
            verified integer,
            verification_token text
        )
        """)

    cur.execute("""
        CREATE TABLE sessions (
            sid text primary key,
            username text
        )
        """)

    cur.execute("""
        CREATE TABLE cart_contents (
            username text,
            isbn text,
            quantity integer
        )
        """)

    cur.execute("""
        CREATE TABLE orders (
            order_id integer primary key autoincrement,
            username text,
            timestamp integer,
            cc text,
            expiry text,
            total real,
            description text
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
redirect = None

# check cookies
cookies_string = os.environ["HTTP_COOKIE"] if "HTTP_COOKIE" in os.environ else ""
cookies = SimpleCookie(cookies_string)

if "sid" in cookies:
    sid = cookies["sid"].value

# check query stuff
action = form.getvalue("action")
verify = form.getvalue("verify")

# check basic actions (register/signin)
if action == "signin":
    username = form.getfirst("username")
    password = form.getfirst("password")
    password_hash = hash(password)

    # check database for matching username and password
    result = cur.execute("SELECT username, verified FROM users WHERE username = ? AND password_hash = ?", (username, password_hash)).fetchone()

    if result:
        # it's valid!
        # check they're verified
        if result["verified"]:
            user = get_user(username)

            # create a session for them
            sid = create_session(user)
        else:
            page = form.getfirst("page")
            values["signin_fail"] = True
            values["signin_error"] = "We need to verify your email address before you can log in! Check your emails for the link to continue."
    else:
        # lol they fail
        page = form.getfirst("page")
        values["signin_fail"] = True
        values["signin_error"] = "Incorrect username and/or password :("
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
    elif not in_range(username, 3, 16):
        error = "Please choose a username between 3 and 16 characters in length."
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
        token = hash(username + password + name + street + city + state + postcode + email + str(time.time()) + str(random.random())) # verification token

        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (username, password_hash, name.strip(), street.strip(),
                 city.strip(), state.strip(), postcode, email, 0, token))

        conn.commit()

        values["register_success"] = True
        send_verification_email(get_user(username))

        # don't sign them in because we need them to verify email first
        #user = get_user(username)
        #sid = create_session(user)

    if error:
        # set error stuff
        values["register_fail"] = True
        values["register_error"] = error

        values["register_data"] = {
            "username": username or "",
            "password": password or "",
            "password2": password2 or "",
            "name": name or "",
            "street": street or "",
            "city": city or "",
            "state": state or "",
            "postcode": postcode or "",
            "email": email or ""
        }
elif action == "signout":
    # remove session
    delete_session(sid)
    sid = None
    user = None

    values["signout_success"] = True
elif verify:
    # check verification token
    result = cur.execute("SELECT username FROM users WHERE verified = 0 AND verification_token = ?", (verify,)).fetchone()
    if result:
        # yay
        # set their account to verified, nullify token
        cur.execute("UPDATE users SET verified = 1, verification_token = '' WHERE username = ?", (result["username"],))
        conn.commit()

        # sign them in
        user = get_user(result["username"])
        sid = create_session(user)

        # redirect
        redirect = "?page=home"
    else:
        # do nothing...
        pass

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
    values["quoted_query"] = urllib.quote_plus(query)

    # now fetch results from db
    # thanks http://stackoverflow.com/questions/3017417/how-do-i-assign-different-weights-to-columns-in-sql-server-full-text-search
    # and http://stackoverflow.com/questions/4075026/need-help-with-sql-for-ranking-search-results

    clean_query = re.sub(r"[%_]", "", query)

    sql_count = """
    SELECT COUNT(*)
    FROM books
    NATURAL JOIN authors
    WHERE authors.name LIKE "%" || ? || "%"
    OR title LIKE "%" || ? || "%"
    OR productdescription LIKE "%" || ? || "%"
    GROUP BY isbn
    """

    total = len(cur.execute(sql_count, (clean_query,)*3).fetchall())

    results_per_page = 20
    page = 1
    try:
        page = int(form.getfirst("p", 0))
        if page < 1:
            page = 1
    except:
        pass

    values["num_pages"] = int(math.ceil(float(total) / results_per_page))
    values["p"] = page
    values["start"] = (page-1)*results_per_page + 1
    values["finish"] = min((total, (page-1)*results_per_page + results_per_page))

    sql_real = """
    SELECT *,
    (
        (CASE WHEN authors.name LIKE "%" || ? || "%" THEN 3 ELSE 0 END) +
        (CASE WHEN title LIKE "%" || ? || "%" THEN 2 ELSE 0 END) +
        (CASE WHEN productdescription LIKE "%" || ? || "%" THEN 1 ELSE 0 END)
    ) as rank
    FROM books
    NATURAL JOIN authors
    WHERE authors.name LIKE "%" || ? || "%"
    OR title LIKE "%" || ? || "%"
    OR productdescription LIKE "%" || ? || "%"
    GROUP BY isbn
    ORDER BY rank DESC, -salesrank DESC
    LIMIT ? OFFSET ?
    """

    results = cur.execute(sql_real, (clean_query,)*6 + (results_per_page, (page-1)*results_per_page)).fetchall()
    # remember to also fetch authors
    books = []
    for result in results:
        book = dict(result)
        authors = []
        for author in cur.execute("SELECT name FROM authors WHERE isbn = ?", (book["isbn"],)).fetchall():
            authors.append(author["name"])
        book["authors"] = authors
        books.append(book)

    values["total"] = total
    values["results"] = books
elif page == "details":
    # get id from query
    isbn = form.getfirst("isbn")

    result = cur.execute("SELECT * FROM books WHERE isbn = ?", (isbn,)).fetchone()
    if result:
        result = dict(result)

        authors = []
        for author in cur.execute("SELECT name FROM authors WHERE isbn = ?", (isbn,)).fetchall():
            authors.append(author["name"])

        result["authors"] = authors
        values["book"] = result

        # check if it's in their cart
        if user:
            result = cur.execute("SELECT quantity FROM cart_contents WHERE username = ? AND isbn = ?", (username, isbn)).fetchone()
            if result:
                values["in_cart"] = result["quantity"]
    else:
        # invalid isbn!
        redirect = "?page=home"
elif page == "cart":
    if user:
        # yay we get to display the cart woo
        # if only i knew how to style things properly

        # checkout stuff
        # are we checking out?
        if action == "checkout":
            # yep
            # get cc, expiry
            creditcard = form.getfirst("creditcard")
            expirymonth = form.getfirst("expirymonth")
            expiryyear = form.getfirst("expiryyear")

            error = ""

            if not creditcard or not re.match(r"^\d{16}$", creditcard):
                error = "Please enter a <a target='_blank' href='http://www.getcreditcardnumbers.com/'>valid credit card number</a>."
            elif not expirymonth or not re.match(r"^\d{1,2}$", expirymonth) or not (int(expirymonth) >= 1 and int(expirymonth) <= 12):
                error = "Please enter a valid expiry month (between 01 and 12)."
            elif not expiryyear or not re.match(r"^\d{2}$", expiryyear) or not (int(expiryyear) >= 13 and int(expiryyear) <= 50):
                error = "Please enter a valid expiry year (two digits, between 13 and 50)."
            else:
                # correctamundo
                expirystr = str(int(expirymonth)).zfill(2) + "/" + expiryyear

                total = get_cart_total(username)

                lines = []
                # get cart contents
                results = cur.execute("SELECT * FROM cart_contents NATURAL JOIN books WHERE username = ?", (username,)).fetchall()

                for result in results:
                    lines.append("%s (ISBN: %s) &times; %d ($%.2f each)" % (result["title"], result["isbn"], result["quantity"], result["price"]))
                description = "<br>".join(lines)

                result = cur.execute("INSERT INTO orders (username, timestamp, cc, expiry, total, description) VALUES (?, ?, ?, ?, ?, ?)",
                        (username, int(time.time()), creditcard, expirystr, total, description))
                conn.commit()

                result_id = cur.lastrowid

                redirect = "?page=checkout_success&id=%d" % result_id

            if error:
                values["checkout_fail"] = True
                values["checkout_error"] = error

                values["checkout_data"] = {
                    "creditcard": creditcard or "",
                    "expirymonth": expirymonth or "",
                    "expiryyear": expiryyear or ""
                }

        # firstly, do we need to add something to the cart?
        isbn = form.getfirst("isbn")
        if isbn:
            # make sure it's a valid isbn...
            result = cur.execute("SELECT isbn FROM books WHERE isbn = ?", (isbn,)).fetchone()
            if result:
                # hold up, is this a quantity thing or an add to cart thing

                quantity = form.getfirst("quantity")
                if quantity:
                    try:
                        quantity = int(quantity)
                    except ValueError:
                        pass
                    else:

                        if quantity >= 1 and quantity <= 100:
                            # anything outside that range would be a little ridiculous...
                            cur.execute("UPDATE cart_contents SET quantity = ? WHERE username = ? AND isbn = ?", (quantity, username, isbn))
                            conn.commit()
                else:
                    # ensure it isn't already in the cart
                    result = cur.execute("SELECT quantity FROM cart_contents WHERE username = ? AND isbn = ?", (username, isbn)).fetchone()
                    if not result:
                        # not in the cart; add new
                        cur.execute("INSERT INTO cart_contents VALUES (?, ?, ?)", (username, isbn, 1))
                    else:
                        # in the cart; increment
                        cur.execute("UPDATE cart_contents SET quantity = ? WHERE username = ? AND isbn = ?", (result["quantity"]+1, username, isbn))
                    conn.commit()

            # redirect
            redirect = "?page=cart"
        else:
            # do we need to remove something from the cart?
            isbn = form.getfirst("remove")
            if isbn:
                cur.execute("DELETE FROM cart_contents WHERE username = ? AND isbn = ?", (username, isbn))
                conn.commit()

                # redirect
                redirect = "?page=cart"
            else:

                # get cart contents
                results = cur.execute("SELECT * FROM cart_contents NATURAL JOIN books WHERE username = ?", (username,)).fetchall()

                books = []
                for result in results:
                    book = dict(result)
                    authors = []
                    for author in cur.execute("SELECT name FROM authors WHERE isbn = ?", (book["isbn"],)).fetchall():
                        authors.append(author["name"])
                    book["authors"] = authors
                    books.append(book)
                values["books"] = books
elif page == "checkout_success":
    # if it's a valid id, add description
    id = form.getfirst("id")
    if id:
        result = cur.execute("SELECT description FROM orders WHERE order_id = ?", (id,)).fetchone()
        if result:
            values["description"] = result["description"]

# cart total
if user:
    values["cart_total"] = get_cart_total(username)

# put sid into cookies
cookies["sid"] = sid if sid else ""

# assign some last minute values
values["user"] = user

# print headers
if redirect:
    print "Location: %s" % redirect
else:
    print "Content-Type: text/html"

# cookies
print cookies.output()

# end headers
print ""

if not redirect:
    print template.format_file("index.html", values)
