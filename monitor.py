import argparse
from pathlib import Path

import database
from change_detector import detect_changes
from file_inventory import inventory_folder


def monitor_folder(folder_path):
    """Report changes since the last complete scan of this folder."""
    try:
        folder = Path(folder_path).expanduser().resolve()
        database.initialize_database()
        previous = database.get_folder_inventory(folder)
        db_path = Path(database.DATABASE_PATH).resolve()
        excluded = [
            db_path.with_name(db_path.name + suffix)
            for suffix in ("", "-journal", "-wal", "-shm")
        ]
        current, errors = inventory_folder(folder, exclude=excluded)
    except OSError as error:
        errors = [str(error)]

    if errors:
        print("Folder scan incomplete. Saved inventory was kept.")
        for error in errors:
            print(error)
        return False

    changes = detect_changes(previous, current) if previous is not None else []
    if not database.save_folder_inventory(folder, current, expected=previous):
        print("Another scan updated the baseline. Run the scan again.")
        return False

    if previous is None:
        print("Establishing initial baseline.")
    elif not changes:
        print("No changes detected.")
    for change in changes:
        print(f"{change['type'].upper()}: {change['name']}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Compare a folder with its last complete scan."
    )
    parser.add_argument(
        "folder", nargs="?", default=Path(__file__).parent / "sample_documents"
    )
    args = parser.parse_args()
    return 0 if monitor_folder(args.folder) else 1


if __name__ == "__main__":
    raise SystemExit(main())
