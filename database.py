import json
import sqlite3
import hashlib
from contextlib import closing
from pathlib import Path
from datetime import datetime


DATABASE_PATH = Path(__file__).parent / "history.db"
_ANY_INVENTORY = object()


def initialize_database():
    """Create the scan history and file tracking tables."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                scan_time TEXT NOT NULL,
                finding_count INTEGER NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS file_state (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                last_scanned TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                finding_data TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS folder_baselines (
                folder_path TEXT PRIMARY KEY
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS folder_inventory (
                folder_path TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_data TEXT NOT NULL,
                PRIMARY KEY (folder_path, file_path)
            )
        """)
        connection.execute("""
            INSERT OR IGNORE INTO folder_baselines (folder_path)
            SELECT DISTINCT folder_path FROM folder_inventory
        """)


def _folder_key(folder_path):
    return str(Path(folder_path).expanduser().resolve())


def _read_inventory(connection, folder_key):
    rows = connection.execute("""
        SELECT inventory.file_path, inventory.file_data
        FROM folder_baselines AS baseline
        LEFT JOIN folder_inventory AS inventory USING (folder_path)
        WHERE baseline.folder_path = ?
    """, (folder_key,)).fetchall()
    if not rows:
        return None
    return {path: json.loads(data) for path, data in rows if path is not None}


def get_folder_inventory(folder_path):
    """Return the saved snapshot, or None if no baseline exists."""
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        return _read_inventory(connection, _folder_key(folder_path))


def save_folder_inventory(folder_path, inventory, *, expected=_ANY_INVENTORY):
    """Replace a complete snapshot, unless its expected baseline has changed."""
    folder_key = _folder_key(folder_path)
    rows = [(folder_key, path, json.dumps(data)) for path, data in inventory.items()]

    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if (
            expected is not _ANY_INVENTORY
            and _read_inventory(connection, folder_key) != expected
        ):
            return False
        connection.execute(
            "INSERT OR IGNORE INTO folder_baselines (folder_path) VALUES (?)",
            (folder_key,),
        )
        connection.execute(
            "DELETE FROM folder_inventory WHERE folder_path = ?", (folder_key,)
        )
        connection.executemany("""
            INSERT INTO folder_inventory (folder_path, file_path, file_data)
            VALUES (?, ?, ?)
        """, rows)
    return True


def calculate_file_hash(file_path):
    """Calculate a SHA-256 fingerprint of a file's contents."""

    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def has_file_changed(file_path):
    """Check whether a file differs from its most recently scanned version."""

    path = str(Path(file_path).resolve())
    current_hash = calculate_file_hash(file_path)

    with sqlite3.connect(DATABASE_PATH) as connection:
        result = connection.execute("""
            SELECT file_hash
            FROM file_state
            WHERE file_path = ?
        """, (path,)).fetchone()

    if result is None:
        return True

    return current_hash != result[0]


def update_file_state(file_path):
    """Save the latest fingerprint after a successful scan."""

    path = str(Path(file_path).resolve())
    file_hash = calculate_file_hash(file_path)
    scan_time = datetime.now().isoformat(timespec="seconds")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            INSERT INTO file_state (file_path, file_hash, last_scanned)
            VALUES (?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                file_hash = excluded.file_hash,
                last_scanned = excluded.last_scanned
        """, (path, file_hash, scan_time))


def record_scan(file_path, finding_count):
    """Save the result of scanning a document."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            INSERT INTO scan_history (
                file_path,
                scan_time,
                finding_count
            )
            VALUES (?, ?, ?)
        """, (
            str(Path(file_path).resolve()),
            datetime.now().isoformat(timespec="seconds"),
            finding_count
        ))


def get_scan_history():
    """Return all recorded scans, newest first."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute("""
            SELECT file_path, scan_time, finding_count
            FROM scan_history
            ORDER BY scan_time DESC
        """)

        return cursor.fetchall()

def save_findings(file_path, findings):
    """Replace the saved findings for a document."""

    path = str(Path(file_path).resolve())

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "DELETE FROM findings WHERE file_path = ?",
            (path,)
        )

        for finding in findings:
            connection.execute("""
                INSERT INTO findings (file_path, finding_data)
                VALUES (?, ?)
            """, (path, json.dumps(finding)))


def get_all_findings():
    """Retrieve all previously saved findings."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT finding_data FROM findings"
        ).fetchall()

    return [json.loads(row[0]) for row in rows]
