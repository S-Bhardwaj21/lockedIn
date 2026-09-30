import os
import sqlite3
from pathlib import Path

state_db = (
    Path(os.environ["APPDATA"])
    / "Code"
    / "User"
    / "globalStorage"
    / "state.vscdb"
)

print("VS Code state database:")
print(state_db)
print("Exists:", state_db.exists())

if not state_db.exists():
    raise SystemExit("VS Code state database not found.")

connection = sqlite3.connect(
    f"file:{state_db}?mode=ro",
    uri=True,
)

cursor = connection.cursor()

print("\n=== TABLES ===")

tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for table in tables:
    print(table[0])

print("\n=== KEYS CONTAINING EDITOR / CURSOR / WORKBENCH ===")

rows = cursor.execute(
    """
    SELECT key, substr(value, 1, 1000)
    FROM ItemTable
    WHERE lower(key) LIKE '%editor%'
       OR lower(key) LIKE '%cursor%'
       OR lower(key) LIKE '%workbench%'
       OR lower(key) LIKE '%history%'
    """
).fetchall()

for key, value in rows:
    print("\nKEY:", key)
    print("VALUE:", value)

connection.close()