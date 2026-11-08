import sqlite3

import pytest

import database
import file_inventory
from monitor import monitor_folder


@pytest.fixture
def folder(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "inventory.db")
    folder = tmp_path / "watched"
    folder.mkdir()
    return folder


def test_empty_baseline_and_changes(folder, capsys):
    database.initialize_database()
    assert database.get_folder_inventory(folder) is None
    assert monitor_folder(folder)
    assert "Establishing initial baseline." in capsys.readouterr().out
    assert database.get_folder_inventory(folder) == {}
    assert monitor_folder(folder)
    assert "No changes detected." in capsys.readouterr().out

    file = folder / "document.txt"
    file.write_text("first", encoding="utf-8")
    assert monitor_folder(folder)
    assert "ADDED: document.txt" in capsys.readouterr().out

    file.write_text("other", encoding="utf-8")
    assert monitor_folder(folder)
    assert "MODIFIED: document.txt" in capsys.readouterr().out

    file.unlink()
    assert monitor_folder(folder)
    assert "DELETED: document.txt" in capsys.readouterr().out
    assert database.get_folder_inventory(folder) == {}


@pytest.mark.parametrize("failure", ["directory", "file", "missing", "changing"])
def test_incomplete_scan_preserves_baseline(folder, monkeypatch, capsys, failure):
    nested = folder / "nested"
    nested.mkdir()
    file = nested / "document.txt"
    file.write_text("original", encoding="utf-8")
    removed = folder / "removed.txt"
    removed.touch()
    assert monitor_folder(folder)
    previous = database.get_folder_inventory(folder)
    capsys.readouterr()
    removed.unlink()

    with monkeypatch.context() as patch:
        if failure == "directory":
            scandir = file_inventory.os.scandir

            def deny_nested(path):
                if path == nested:
                    raise PermissionError("directory unreadable")
                return scandir(path)

            patch.setattr(file_inventory.os, "scandir", deny_nested)
        elif failure == "missing":
            folder.rename(folder.with_name("moved"))
        else:
            calculate_hash = file_inventory.calculate_hash

            def hash_file(path):
                if failure == "file":
                    raise PermissionError("file unreadable")
                fingerprint = calculate_hash(path)
                path.write_text("changed while hashing", encoding="utf-8")
                return fingerprint

            patch.setattr(file_inventory, "calculate_hash", hash_file)

        assert not monitor_folder(folder)

    output = capsys.readouterr().out
    assert "Folder scan incomplete." in output
    assert "DELETED:" not in output
    assert database.get_folder_inventory(folder) == previous

    if failure == "missing":
        folder.with_name("moved").rename(folder)
    assert monitor_folder(folder)
    assert "DELETED: removed.txt" in capsys.readouterr().out


def test_legacy_inventory_is_retained(folder):
    file_path = str(folder / "old.txt")
    with sqlite3.connect(database.DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE folder_inventory (
                folder_path TEXT NOT NULL, file_path TEXT NOT NULL,
                file_data TEXT NOT NULL, PRIMARY KEY (folder_path, file_path)
            )
        """)
        connection.execute(
            "INSERT INTO folder_inventory VALUES (?, ?, ?)",
            (str(folder), file_path, '{"name": "old.txt", "hash": "original"}'),
        )
    connection.close()

    database.initialize_database()
    assert database.get_folder_inventory(folder) == {
        file_path: {"name": "old.txt", "hash": "original"}
    }


def test_stale_scan_cannot_replace_new_baseline(folder):
    database.initialize_database()
    database.save_folder_inventory(folder, {})
    newer = {str(folder / "new.txt"): {"hash": "new"}}
    assert database.save_folder_inventory(folder, newer, expected={})
    assert not database.save_folder_inventory(folder, {}, expected={})
    assert database.get_folder_inventory(folder) == newer


def test_monitor_excludes_own_database(folder, capsys):
    assert monitor_folder(folder.parent)
    assert database.get_folder_inventory(folder.parent) == {}
    capsys.readouterr()
    assert monitor_folder(folder.parent)
    assert "No changes detected." in capsys.readouterr().out
