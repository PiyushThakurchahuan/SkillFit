import sqlite3
from pathlib import Path
DB=Path(__file__).resolve().parent.parent/'skillfit.db'
def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    c=conn();
    c.execute('''CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT,education TEXT,experience REAL DEFAULT 0,career_break REAL DEFAULT 0,location TEXT,work_mode TEXT,target_role TEXT,skills TEXT DEFAULT '[]',resume TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY AUTOINCREMENT,profile_id INTEGER,role TEXT,score REAL)'''); c.commit(); c.close()
