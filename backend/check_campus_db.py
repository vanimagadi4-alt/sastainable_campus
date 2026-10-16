import sqlite3
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
db_path = project_root / "backend" / "campus.db"

conn = sqlite3.connect(str(db_path))

tables = conn.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' ORDER BY name"
).fetchall()

print("Tables in backend/campus.db:")
for table in tables:
    print(table[0])

conn.close()
