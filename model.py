#!/usr/bin/env python2.7

# all the database shit
# also creates tables for users, baskets, orders, etc.

from collections import defaultdict
import datetime
import json
import os
import sqlite3

DATABASE_FILENAME = "mekong.db"

conn = None
cur = None

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
    if int_str:
        return int(int_str)

def parse_price(price_str):
    if price_str:
        return float(price_str[1:])

class Book(object):
    def __init__(self, values):
        self.isbn = values["isbn"]
        self.binding = values["binding"]
        self.catalog = values["catalog"]
        self.ean = values["ean"]
        self.edition = values["edition"]
        self.numpages = parse_int(values["numpages"])
        self.publication_date = parse_date(values["publication_date"])
        self.productdescription = values["productdescription"]
        self.publisher = values["publisher"]
        self.releasedate = parse_date(values["releasedate"])
        self.salesrank = parse_int(values["salesrank"])
        self.price = parse_price(values["price"])
        self.title = values["title"]
        self.year = parse_int(values["year"])
        self.smallimageurl = values["smallimageurl"]
        self.mediumimageurl = values["mediumimageurl"]
        self.largeimageurl = values["largeimageurl"]
        self.smallimagewidth = parse_int(values["smallimagewidth"])
        self.smallimageheight = parse_int(values["smallimageheight"])
        self.mediumimagewidth = parse_int(values["mediumimagewidth"])
        self.mediumimageheight = parse_int(values["mediumimageheight"])
        self.largeimagewidth = parse_int(values["largeimagewidth"])
        self.largeimageheight = parse_int(values["largeimageheight"])
        self.authors = values["authors"]

    def put(self):
        """Puts book into database."""
        cur.execute("""
            INSERT INTO books VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (self.isbn, self.binding, self.catalog, self.ean, self.edition, self.numpages,
            self.publication_date, self.productdescription, self.publisher,
            self.releasedate, self.salesrank, self.price, self.title, self.year,
            self.smallimageurl, self.mediumimageurl, self.largeimageurl,
            self.smallimagewidth, self.smallimageheight,
            self.mediumimagewidth, self.mediumimageheight,
            self.largeimagewidth, self.largeimageheight))

        for author in self.authors:
            cur.execute("INSERT INTO authors VALUES (?, ?)", (author, self.isbn))

def open_database(check_exists=True):
    """Opens connection to database."""
    global conn
    global cur

    if check_exists and not os.path.exists(DATABASE_FILENAME):
        create_database()

    conn = sqlite3.connect(DATABASE_FILENAME)
    cur = conn.cursor()

def save_database():
    conn.commit()

def close_database():
    """Closes connection to database."""
    conn.close()

def create_database():
    """Creates a new database from scratch."""

    # open database connection
    open_database(check_exists=False)

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
        )""")

    # parse books.json
    f = open("books.json")
    data = json.loads(f.read())
    f.close()

    for values in data.values():
        # convert to defaultdict, because some stupid books don't have all the keys
        values = defaultdict(lambda: None, values) # return None if key doesn't exist
        book = Book(values)
        book.put()

    save_database()
