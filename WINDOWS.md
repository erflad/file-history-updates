# File History Updates for Windows

Download `FileHistoryUpdates.exe` from the repository's **Releases** tab. Save it where you plan to keep it, then double-click it. The Windows x64 executable includes the folder monitor and runs without a separate Python installation.

1. **Scan now** checks Downloads, Documents, Pictures, Videos, Music, and Desktop.
2. **Enable scanning at Windows sign-in** starts a scan each time you sign in. If you move or rename the executable, run this option again from its new location.
3. **Disable scanning at Windows sign-in** removes the automatic run.

The first successful scan sets a baseline for each folder. Later scans report added, modified, and deleted files. An incomplete scan keeps that folder's last complete baseline.

The app continues to use `%LOCALAPPDATA%\DigitalArchaeologist` so upgrades can pick up the existing database and log. Open `folder-monitor.log` in that folder to review unattended scans. Document analysis is available through the source project.

## Build and publish

Run **Build Windows executable** from the repository's **Actions** tab. Download the `FileHistoryUpdates-windows-x64` artifact, extract it, and test the executable. To publish, push a new version tag from the commit containing the workflow. The tagged build runs a smoke test before attaching the executable to a GitHub release.
