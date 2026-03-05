import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.abspath(__file__))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import sqlite3
from datetime import datetime

DB_FOLDER = os.path.join(PROJECT, "data", "DB")
os.makedirs(DB_FOLDER, exist_ok=True)
DB = os.path.join(DB_FOLDER, "database.db")


def connect():
    return sqlite3.connect(DB)


def create_tables():
    with connect() as c:
        cur = c.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT, password TEXT, role TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, file_path TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, lesson_id INTEGER,
            accuracy REAL, timestamp TEXT)""")
        cur.execute("SELECT COUNT(*) FROM lessons")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO lessons (title,file_path) VALUES (?,?)",
                        ("Lesson 1 \u2013 Alphabets", "lessons/lesson1.txt"))
            cur.execute("INSERT INTO lessons (title,file_path) VALUES (?,?)",
                        ("Lesson 2 \u2013 Words", "lessons/lesson2.txt"))


def get_lessons():
    with connect() as c:
        return c.execute("SELECT id,title,file_path FROM lessons").fetchall()


def save_performance(uid, lesson_id, acc):
    with connect() as c:
        c.execute("INSERT INTO performance VALUES (NULL,?,?,?,?)",
                  (uid, lesson_id, acc,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def get_performance(uid):
    with connect() as c:
        return c.execute(
            "SELECT lesson_id,accuracy FROM performance WHERE user_id=?",
            (uid,)).fetchall()


create_tables()