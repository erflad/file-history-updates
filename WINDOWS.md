# Digital Archaeologist for Windows

Download `DigitalArchaeologist.exe` from this repository's Releases page and place it somewhere you plan to keep it. Double-click it to open the menu. Choose **1** to scan Downloads, Documents, Pictures, Videos, Music, and Desktop. Choose **2** to run automatically at Windows sign-in, or **3** to disable automatic runs. If you move the executable, use option 2 from its new location to update the sign-in entry.

The executable is a standalone Windows x64 build. It runs the folder monitor. The project's document analysis still runs separately through `main.py`.

The first successful scan of each folder establishes its baseline. Later scans report added, modified, and deleted files. A folder with an incomplete scan keeps its previous baseline. The database and scan log are local to your Windows account under `%LOCALAPPDATA%\DigitalArchaeologist`.

For maintainers, push the source files and the workflow to GitHub. To test packaging, run **Build Windows executable** from the repository's Actions tab and download its artifact. To publish, push a version tag such as `v0.1.0` from the commit containing the workflow. A tagged build publishes the executable to Releases after the smoke test succeeds.
