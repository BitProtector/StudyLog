import sqlite3
import json
import sqlite3, bcrypt, pathlib

AUTH_DB = "users.db"
DB_PATH = "studium.db"  # Datenbankpfad

# -----------------------------------------------------------------------------
# Initialisierung der Datenbank (Tabellen: module, grades)
# -----------------------------------------------------------------------------
def initialize_db(DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module (
                id INTEGER PRIMARY KEY,
                mod_id INTEGER,
                name TEXT,
                description TEXT,
                beschreibung TEXT, 
                assessment INTEGER,
                ects INTEGER, 
                dependencies TEXT, 
                semester INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY,
                module_id INTEGER,
                k1 REAL,
                k2 REAL,
                k1_weight REAL,
                k2_weight REAL,
                msp REAL,
                msp_weight REAL,
                calc_type INTEGER,
                FOREIGN KEY (module_id) REFERENCES module(id)
            )
        ''')
        conn.commit()

def init_auth_db():
    with sqlite3.connect(AUTH_DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
                        username TEXT PRIMARY KEY,
                        pw_hash BLOB NOT NULL,
                        db_path TEXT NOT NULL)""")
        c.commit()

def add_user(username: str, password: str):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    db_path = f"studium_{username}.db"
    with sqlite3.connect(AUTH_DB) as c:
        c.execute("INSERT INTO users VALUES (?,?,?)",
                  (username, pw_hash, db_path))
        c.commit()

def check_user(username: str, password: str):
    with sqlite3.connect(AUTH_DB) as c:
        row = c.execute("SELECT pw_hash, db_path FROM users WHERE username=?",
                        (username,)).fetchone()
    if row and bcrypt.checkpw(password.encode(), row[0]):
        return row[1]          # persoenlicher DB‑Pfad