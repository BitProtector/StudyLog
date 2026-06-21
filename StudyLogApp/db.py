import sqlite3
import json
import sqlite3, bcrypt, pathlib

AUTH_DB = "data/users.db"
DB_PATH = "studium.db"  # Datenbankpfad

# -----------------------------------------------------------------------------
# Initialisierung der Datenbank (Tabellen: module, grades)
# -----------------------------------------------------------------------------
def initialize_db(DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module (
                id INTEGER PRIMARY KEY,
                mod_id INTEGER,
                name TEXT,
                description TEXT,
                beschreibung TEXT, 
                assessment INTEGER,
                msp INTEGER,
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (module_id) REFERENCES module(id)
            )
        ''')

        # Die vorherige Version legte einen eindeutigen Index fuer Noten an.
        # Er wird entfernt, damit jede Aenderung als eigene Historienzeile
        # gespeichert werden kann.
        cursor.execute("DROP INDEX IF EXISTS idx_grades_module_id")

        grade_columns = {
            column[1] for column in cursor.execute("PRAGMA table_info(grades)").fetchall()
        }
        if "created_at" not in grade_columns:
            # Bestehende Eintraege behalten ihren unbekannten Zeitstempel
            # (NULL); jede neue Noteneingabe erhaelt einen Zeitstempel.
            cursor.execute("ALTER TABLE grades ADD COLUMN created_at TEXT")

        # Gleichnamige Module werden weiterhin zusammengefuehrt. Ihre
        # vollstaendige Notenhistorie wird dem verbleibenden Modul zugeordnet.
        duplicate_names = cursor.execute('''
            SELECT LOWER(name), MIN(id)
            FROM module
            WHERE name IS NOT NULL
            GROUP BY name COLLATE NOCASE
            HAVING COUNT(*) > 1
        ''').fetchall()
        for normalised_name, canonical_id in duplicate_names:
            duplicate_ids = cursor.execute(
                "SELECT id FROM module WHERE LOWER(name) = ? AND id != ?",
                (normalised_name, canonical_id),
            ).fetchall()
            for (duplicate_id,) in duplicate_ids:
                cursor.execute(
                    "UPDATE grades SET module_id = ? WHERE module_id = ?",
                    (canonical_id, duplicate_id),
                )
                cursor.execute("DELETE FROM module WHERE id = ?", (duplicate_id,))

        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_module_name_nocase
            ON module(name COLLATE NOCASE)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grades_module_history
            ON grades(module_id, id DESC)
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
    db_path = f"data/studium_{username}.db"
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
