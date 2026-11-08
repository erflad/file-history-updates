import os
import stat
from pathlib import Path

from database import calculate_file_hash as calculate_hash


def inventory_folder(folder_path, *, exclude=()):
    """Collect information about files and report any incomplete reads."""
    folder = Path(folder_path).expanduser().resolve()
    try:
        is_directory = stat.S_ISDIR(folder.stat().st_mode)
    except FileNotFoundError:
        is_directory = False
    if not is_directory:
        raise NotADirectoryError(f"Folder not found: {folder}")

    inventory = {}
    errors = []
    directories = [folder]
    excluded = set(exclude)
    while directories:
        directory = directories.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if path in excluded:
                        continue
                    try:
                        entry_stats = entry.stat(follow_symlinks=False)
                        reparse_tag = getattr(entry_stats, "st_reparse_tag", None)
                        if reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
                            continue
                        if stat.S_ISDIR(entry_stats.st_mode):
                            directories.append(path)
                            continue
                        stats = path.stat()
                        if stat.S_ISREG(stats.st_mode):
                            inventory[str(path)] = _file_data(path, stats)
                    except OSError as error:
                        errors.append(f"{path}: {error}")
        except OSError as error:
            errors.append(f"{directory}: {error}")
    return inventory, errors


def _file_data(path, stats):
    fingerprint = calculate_hash(path)
    if _file_version(stats) != _file_version(path.stat()):
        raise OSError("File changed during the scan")
    return {
        "path": str(path),
        "name": path.name,
        "size": stats.st_size,
        "modified": stats.st_mtime,
        "hash": fingerprint,
    }


def _file_version(stats):
    return stats.st_dev, stats.st_ino, stats.st_size, stats.st_mtime_ns, stats.st_ctime_ns
