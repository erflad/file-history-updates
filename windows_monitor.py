import argparse
import ctypes
import os
import sqlite3
import subprocess
import sys
import uuid
import winreg
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path

import database
from monitor import monitor_folder


KNOWN_FOLDERS = {
    "Downloads": "374DE290-123F-4565-9164-39C4925E467B",
    "Documents": "FDD39AD0-238F-46AF-ADB4-6C85480369C7",
    "Pictures": "33E28130-4E1E-4676-835A-98395C3BC3BB",
    "Videos": "18989B1D-99B5-455B-841C-AB7C74E4DDFC",
    "Music": "4BD8D571-6D19-48D3-BE97-422220080E43",
    "Desktop": "B4BFCC3A-DB2C-424C-B029-7FE99A87C641",
}
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "DigitalArchaeologistMonitor"


def known_folder(folder_id):
    guid = (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID(folder_id).bytes_le)
    path = ctypes.c_void_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(
        ctypes.byref(guid), 0x4000, None, ctypes.byref(path)
    )
    try:
        if result:
            raise OSError(f"Windows could not locate this folder (0x{result & 0xFFFFFFFF:08X})")
        return Path(ctypes.wstring_at(path))
    finally:
        ctypes.windll.ole32.CoTaskMemFree(path)


def set_startup(enabled):
    if enabled:
        if not getattr(sys, "frozen", False):
            raise OSError("Use the packaged Windows executable to enable sign-in scans.")
        command = subprocess.list2cmdline([sys.executable, "--scan"])
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, command)
        print("Automatic scans are enabled for this Windows account.")
        print("Keep the executable at its current location.")
        return

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, RUN_NAME)
    except FileNotFoundError:
        pass
    print("Automatic scans are disabled.")


def scan_folders(paths):
    data_dir = Path(os.environ["LOCALAPPDATA"]) / "DigitalArchaeologist"
    data_dir.mkdir(parents=True, exist_ok=True)
    database.DATABASE_PATH = data_dir / "inventory.db"
    log_path = data_dir / "folder-monitor.log"
    targets = [(str(path), path) for path in paths] if paths else KNOWN_FOLDERS.items()
    successful = True
    with log_path.open("a", encoding="utf-8") as log:
        print(f"\nScan started {datetime.now().astimezone():%Y-%m-%d %H:%M:%S %z}", file=log)
        for label, target in targets:
            output = StringIO()
            with redirect_stdout(output):
                try:
                    path = target if paths else known_folder(target)
                    print(f"{label} - {path}")
                    if not monitor_folder(path):
                        successful = False
                except (OSError, sqlite3.Error) as error:
                    print(f"{label}: {error}")
                    successful = False
            report = output.getvalue()
            print(report, end="")
            log.write(report)
            log.flush()
        print(f"Scan finished {datetime.now().astimezone():%Y-%m-%d %H:%M:%S %z}", file=log)
    print(f"Log: {log_path}")
    return 0 if successful else 1


def main():
    parser = argparse.ArgumentParser(description="File History Updates folder monitor")
    parser.add_argument("--scan", action="store_true", help="Scan without opening the menu")
    parser.add_argument("--folder", type=Path, action="append", help="Scan a specific folder")
    args = parser.parse_args()
    if args.scan or args.folder:
        return scan_folders(args.folder)

    print("File History Updates Folder Monitor")
    print("1. Scan Downloads, Documents, Pictures, Videos, Music, and Desktop")
    print("2. Enable scanning at Windows sign-in")
    print("3. Disable scanning at Windows sign-in")
    print("4. Exit")
    try:
        choice = input("Choose an option: ").strip()
        if choice == "1":
            return scan_folders(None)
        if choice in ("2", "3"):
            set_startup(choice == "2")
        elif choice != "4":
            print("Unknown option.")
            return 1
        return 0
    except (OSError, sqlite3.Error) as error:
        print(error)
        return 1
    finally:
        input("Press Enter to close.")


if __name__ == "__main__":
    raise SystemExit(main())
