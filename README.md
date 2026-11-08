# File History Updates

Track added, modified, and deleted files on your Windows PC. File History Updates compares each scan with the last complete inventory and keeps the results on your device.

## Windows download

Download `FileHistoryUpdates.exe` from the repository's **Releases** tab and double-click it. The menu lets you scan Downloads, Documents, Pictures, Videos, Music, and Desktop, or enable scans at Windows sign-in. See [the Windows guide](WINDOWS.md) for setup and release instructions.

The first successful scan of each folder sets its baseline. An incomplete scan keeps that folder's previous baseline so unreadable files don't show up as deletions.

## Run from source

From the project folder in PowerShell, create a virtual environment and install the document-analysis and test dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pypdf python-dateutil pytest
```

Scan the six Windows folders, or compare a single folder by supplying its path.

```powershell
.\.venv\Scripts\python.exe windows_monitor.py --scan
.\.venv\Scripts\python.exe monitor.py "$env:USERPROFILE\Downloads"
```

## Document analysis

Place TXT, Markdown, or text-based PDF files in `sample_documents` and run:

```powershell
.\.venv\Scripts\python.exe main.py
```

The analyzer extracts possible deadlines, reminders, follow-ups, and registrations, ranks them, and writes `reports/latest_report.html`. It reuses findings from unchanged files. Image-only PDFs require OCR, and relative dates such as “next Friday” are currently unsupported.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
