# Storage Cleaner & File Tracker

<div align="center">
  
![Storage Cleaner Banner](https://github.com/cry4pt/Storage-Cleaner-File-Tracker/blob/main/Cleaner.png)

**A powerful Windows utility to clean unnecessary files and track storage changes**

[![Windows](https://img.shields.io/badge/Platform-Windows-blue?style=flat-square&logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=flat-square&logo=python)](https://www.python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green?style=flat-square&logo=qt)](https://wiki.qt.io/Qt_for_Python)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

</div>

---

## 🌟 Features

- **🧹 System Cleaner**
  - Clean Recycle Bin, temporary files, browser caches, and more
  - Smart detection of multiple browser caches (Chrome, Edge, Firefox, Opera, Brave, Vivaldi)
  - Safely clean Microsoft Defender temporary files
  - Preview files before deletion
  - Export cleaning logs
  
- **📊 Storage Tracker**
  - Track file system changes over time
  - Identify new, grown, and deleted files
  - Filter by file extension
  - Focus on the largest files consuming your storage
  - Backup file snapshots for historical comparison

- **⚙️ Advanced Capabilities**
  - Dark mode UI
  - System tray integration
  - Administrator mode operation for thorough cleaning
  - Disk usage visualization

## 📋 Requirements

- Windows 10/11
- Python 3.8+
- Required packages:
  - PySide6
  - psutil
  - winshell
  - win10toast

## 🚀 Installation

1. Clone this repository:
   ```
   git clone https://github.com/cry4pt/Storage-Cleaner-File-Tracker.git
   cd Storage-Cleaner-File-Tracker
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python Cry4pt.py
   ```

## 💻 Usage

### Storage Cleaner Tab

1. Select cleanup options from the available checkboxes
2. Preview files that will be deleted
3. Click "Clean Selected" to remove files
4. Optionally export the cleaning log

### File Tracker Tab

1. Click "Scan Now" to analyze your C:\ drive
2. View the largest files on your system
3. See which files are new or have grown significantly
4. Filter results by file extension

## 🛡️ Security Considerations

- The application requires administrator rights to access system folders
- Use caution when cleaning system files
- The application excludes critical Windows directories by default
- No files are deleted without explicit user confirmation

## 🔧 Customization

You can modify the following constants in the code to customize the application:

- `EXCLUDED_FOLDERS`: Add folders to exclude from scanning
- `FILTER_EXTENSIONS`: Manage which file extensions to track
- `SNAPSHOT_FILE` and `SNAPSHOT_BACKUP_DIR`: Change backup file locations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/cry4pt/Storage-Cleaner-File-Tracker/blob/main/LICENCE) file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📬 Contact

Cry4pt - [cry4pt@gmail.com](mailto:cry4pt@gmail.com)

Discord - [cry4pt](https://discord.com/users/1276699402974658571)

Project Link: [https://github.com/cry4pt/Storage-Cleaner-File-Tracker/](https://github.com/cry4pt/Storage-Cleaner-File-Tracker/)

