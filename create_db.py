import sqlite3

con = sqlite3.connect("assistant.db")
cursor = con.cursor()

cursor.execute("""
CREATE TABLE people
(id INTEGER PRIMARY KEY AUTOINCREMENT,
chat_id INTEGER UNIQUE,
gru_or_prep TEXT,
login TEXT UNIQUE,
passwd TEXT)""")