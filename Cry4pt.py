import sys
import os
import ctypes
import platform
import shutil
import psutil
import locale
import json
from datetime import datetime
import time
import winshell
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QProgressBar, QFileDialog, QGroupBox,
    QListWidget, QListWidgetItem, QMessageBox, QTextEdit, QSystemTrayIcon,
    QMenu, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PySide6.QtGui import QPalette, QColor, QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from win10toast import ToastNotifier

# Constants for File Tracker
SNAPSHOT_FILE = "snapshot_files.json"
SNAPSHOT_BACKUP_DIR = "snapshot_backups"
EXCLUDED_FOLDERS = [
    r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)",
    r"C:\$Recycle.Bin", r"C:\System Volume Information"
]
FILTER_EXTENSIONS = [
    ".exe", ".dll", ".sys", ".ini", ".bat", ".cmd", ".com", ".msi", ".cab",
    ".txt", ".log", ".csv", ".json", ".xml", ".yml", ".yaml",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",
    ".mp4", ".avi", ".mkv", ".mov", ".wmv",
    ".mp3", ".wav", ".flac", ".aac",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".html", ".htm", ".css", ".js", ".ts", ".php", ".asp", ".aspx",
    ".py", ".java", ".cpp", ".c", ".cs", ".rb", ".go", ".rs",
    ".db", ".sqlite", ".bak", ".iso"
]
toaster = ToastNotifier()

# Utility Functions
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()

def apply_dark_mode(app):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Highlight, QColor(70, 70, 150))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(dark_palette)

def get_human_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

# Storage Cleaner Widget
class StorageCleaner(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.log_messages = []
        self.init_ui()

    def init_ui(self):
        self.init_drive_info()
        self.init_cleanup_options()
        self.init_preview_area()
        self.init_buttons()
        self.init_progress_area()

    def init_drive_info(self):
        drives = [(part.mountpoint, shutil.disk_usage(part.mountpoint))
                  for part in psutil.disk_partitions() if os.name != 'nt' or 'cdrom' not in part.opts]
        for mount, usage in drives:
            group = QGroupBox(f"Drive {mount} - {get_human_size(usage.used)} used of {get_human_size(usage.total)}")
            layout = QVBoxLayout()
            bar = QProgressBar()
            bar.setValue(int((usage.used / usage.total) * 100))
            layout.addWidget(bar)
            group.setLayout(layout)
            self.layout.addWidget(group)

    def init_cleanup_options(self):
        self.checkboxes = {}
        self.cleanup_options = {
            "Recycle Bin": self.preview_recycle_bin,
            "Microsoft Defender Antivirus": self.preview_defender_files,
            "Downloads Folder": self.preview_downloads_folder,
            "Temp Files": self.preview_temp_files,
            "Internet Cache": self.preview_inet_cache,
            "Thumbnails": self.preview_thumbnails,
            "DirectX Shader Cache": self.preview_dx_shader_cache,
            "Delivery Optimization Files": self.preview_delivery_opt,
            "Windows Upgrade Logs": self.preview_upgrade_logs,
            "Old Installers": self.preview_old_installers
        }
        
        # Detect and add browser caches dynamically
        browser_caches = self.detect_browser_caches()
        for name, paths in browser_caches.items():
            self.cleanup_options[name] = self.create_browser_cache_method(paths)
        
        box = QGroupBox("Cleanup Options")
        layout = QVBoxLayout()
        for name in self.cleanup_options:
            cb = QCheckBox(name)
            cb.stateChanged.connect(self.preview_selection)
            layout.addWidget(cb)
            self.checkboxes[name] = cb
        box.setLayout(layout)
        self.layout.addWidget(box)

    def detect_browser_caches(self):
        detected = {}
        # Chrome
        chrome_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), "Google", "Chrome", "User Data", "Default", "Cache")
        if os.path.exists(chrome_path):
            detected["Chrome Cache"] = [chrome_path]
        
        # Edge
        edge_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), "Microsoft", "Edge", "User Data", "Default", "Cache")
        if os.path.exists(edge_path):
            detected["Edge Cache"] = [edge_path]
        
        # Firefox
        firefox_paths = self.get_firefox_cache_paths()
        if firefox_paths:
            detected["Firefox Cache"] = firefox_paths
        
        # Opera
        opera_path = os.path.join(os.environ.get('APPDATA', ''), "Opera Software", "Opera Stable", "Cache")
        if os.path.exists(opera_path):
            detected["Opera Cache"] = [opera_path]
        
        # Brave
        brave_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache")
        if os.path.exists(brave_path):
            detected["Brave Cache"] = [brave_path]
        
        # Vivaldi
        vivaldi_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), "Vivaldi", "User Data", "Default", "Cache")
        if os.path.exists(vivaldi_path):
            detected["Vivaldi Cache"] = [vivaldi_path]
        
        return detected

    def get_firefox_cache_paths(self):
        firefox_profiles_dir = os.path.join(os.environ.get('APPDATA', ''), "Mozilla", "Firefox", "Profiles")
        cache_paths = []
        if os.path.exists(firefox_profiles_dir):
            for profile in os.listdir(firefox_profiles_dir):
                profile_dir = os.path.join(firefox_profiles_dir, profile)
                cache_dir = os.path.join(profile_dir, "cache2")
                if os.path.isdir(cache_dir):
                    cache_paths.append(cache_dir)
        return cache_paths

    def create_browser_cache_method(self, paths):
        def preview_method():
            files = []
            for path in paths:
                if os.path.exists(path):
                    for dp, _, filenames in os.walk(path):
                        files.extend([os.path.join(dp, f) for f in filenames])
            return files
        return preview_method

    def init_preview_area(self):
        self.preview_list = QListWidget()
        self.layout.addWidget(QLabel("Preview of Files to Delete:"))
        self.layout.addWidget(self.preview_list)

    def init_buttons(self):
        btn_layout = QHBoxLayout()
        self.clean_btn = QPushButton("🧹 Clean Selected")
        self.clean_btn.clicked.connect(self.clean_selected)
        self.export_btn = QPushButton("📝 Export Log")
        self.export_btn.clicked.connect(self.export_log)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clean_btn)
        btn_layout.addWidget(self.export_btn)
        self.layout.addLayout(btn_layout)

    def init_progress_area(self):
        self.progress_bar = QProgressBar()
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.layout.addWidget(QLabel("Status Log:"))
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.status_log)

    def preview_selection(self):
        self.preview_list.clear()
        for name, cb in self.checkboxes.items():
            if cb.isChecked():
                try:
                    files = self.cleanup_options[name]()
                    for f in files:
                        self.preview_list.addItem(QListWidgetItem(f))
                except Exception as e:
                    self.preview_list.addItem(QListWidgetItem(f"[Error] {name}: {e}"))

    def clean_selected(self):
        to_delete = []
        for name, cb in self.checkboxes.items():
            if cb.isChecked():
                try:
                    to_delete.extend(self.cleanup_options[name]())
                except:
                    continue
        total = len(to_delete)
        deleted = 0
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.status_log.clear()
        self.log_messages.clear()
        for idx, f in enumerate(to_delete, 1):
            try:
                if os.path.isfile(f):
                    os.remove(f)
                    msg = f"Deleted: {f}"
                    deleted += 1
                else:
                    msg = f"Skipped (not file): {f}"
            except Exception as e:
                msg = f"Failed to delete: {f} — {e}"
            self.log_messages.append(msg)
            self.status_log.append(msg)
            self.progress_bar.setValue(idx)
        QMessageBox.information(self, "Cleanup Complete", f"Deleted {deleted} out of {total} files.")
        self.preview_selection()

    def export_log(self):
        if not self.log_messages:
            QMessageBox.information(self, "No Log", "Nothing to export.")
            return
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log", f"cleanup_log_{now}.txt", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.log_messages))
            QMessageBox.information(self, "Log Exported", f"Log saved to: {file_path}")

    def preview_recycle_bin(self):
        try:
            return [item.filename() for item in winshell.recycle_bin()]  # Changed .path to .filename()
        except Exception as e:
            print(f"Error accessing Recycle Bin: {e}")
            return []

    def preview_defender_files(self):
        """Preview non-critical temporary files used by Microsoft Defender Antivirus"""
        defender_paths = [
            os.path.join(os.environ.get('ProgramData', ''), "Microsoft", "Windows Defender", "Scans", "History"),
            os.path.join(os.environ.get('ProgramData', ''), "Microsoft", "Windows Defender", "Support"),
            os.path.join(os.environ.get('ProgramData', ''), "Microsoft", "Windows Defender", "Quarantine"),
            os.path.join(os.environ.get('ProgramData', ''), "Microsoft", "Windows Defender", "Reporting")
        ]
        
        defender_files = []
        for path in defender_paths:
            if os.path.exists(path):
                for dp, _, filenames in os.walk(path):
                    # Skip the actual quarantine files as they might be needed
                    if "Quarantine\\Entries" in dp:
                        continue
                    # Add temporary/history/log files
                    for f in filenames:
                        if f.endswith(('.log', '.tmp', '.temp', '.old', '.bak')):
                            defender_files.append(os.path.join(dp, f))
        
        # Add detection history database files (non-critical)
        history_path = os.path.join(os.environ.get('ProgramData', ''), "Microsoft", "Windows Defender", "Scans", "History", "Service")
        if os.path.exists(history_path):
            for dp, _, filenames in os.walk(history_path):
                for f in filenames:
                    if f.endswith(('.dat', '.db', '.sqlite')):
                        file_path = os.path.join(dp, f)
                        # Only include older files (3+ days old) to avoid deleting active ones
                        try:
                            if time.time() - os.path.getmtime(file_path) > 3 * 24 * 60 * 60:  # 3 days
                                defender_files.append(file_path)
                        except:
                            pass
        
        return defender_files

    def preview_downloads_folder(self):
        """Preview files in the user's Downloads folder"""
        # Get the standard Downloads folder path
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Alternative location via shell folders
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
                reg_downloads = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                if os.path.exists(reg_downloads):
                    downloads_path = reg_downloads
        except:
            pass  # Fall back to standard path if registry access fails
        
        download_files = []
        if os.path.exists(downloads_path):
            for item in os.listdir(downloads_path):
                item_path = os.path.join(downloads_path, item)
                if os.path.isfile(item_path):
                    download_files.append(item_path)
        
        return download_files

    def preview_temp_files(self):
        temp = os.environ.get("TEMP", r"C:\Windows\Temp")
        return [os.path.join(temp, f) for f in os.listdir(temp) if os.path.isfile(os.path.join(temp, f))] if os.path.exists(temp) else []

    def preview_thumbnails(self):
        thumb_db = os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Microsoft\Windows\Explorer")
        return [os.path.join(thumb_db, f) for f in os.listdir(thumb_db) if f.startswith("thumbcache")] if os.path.exists(thumb_db) else []

    def preview_inet_cache(self):
        cache = os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Microsoft\Windows\INetCache")
        return [os.path.join(dp, f) for dp, _, filenames in os.walk(cache) for f in filenames] if os.path.exists(cache) else []

    def preview_dx_shader_cache(self):
        shader_cache = os.path.join(os.environ.get('LOCALAPPDATA', ''), "D3DSCache")
        return [os.path.join(shader_cache, f) for f in os.listdir(shader_cache)] if os.path.exists(shader_cache) else []

    def preview_delivery_opt(self):
        """Preview Windows Delivery Optimization files across possible locations"""
        delivery_opt_folders = [
            # Traditional location
            r"C:\Windows\SoftwareDistribution\DeliveryOptimization",
            # Windows 10/11 additional location
            r"C:\Windows\SoftwareDistribution\Delivery Optimization",
            # Alternative location with Download folder
            r"C:\Windows\SoftwareDistribution\Download",
            # Additional location in ProgramData
            os.path.join(os.environ.get('ProgramData', ''), "Microsoft", "Windows", "DeliveryOptimization")
        ]
        
        delivery_files = []
        for folder in delivery_opt_folders:
            if os.path.exists(folder):
                try:
                    for dp, _, filenames in os.walk(folder):
                        for f in filenames:
                            # Focus primarily on cache and temporary files
                            if f.endswith(('.temp', '.tmp', '.etl', '.log', '.dat', '.old')):
                                delivery_files.append(os.path.join(dp, f))
                            # Include content delivery files which can be large
                            elif any(x in f.lower() for x in ['cache', 'download', 'content']):
                                delivery_files.append(os.path.join(dp, f))
                except (PermissionError, OSError):
                    # Some subdirectories might be restricted
                    pass

        return delivery_files

    def preview_upgrade_logs(self):
        logdir = r"C:\Windows\Panther"
        log_files = []
        if os.path.exists(logdir):
            for dp, _, filenames in os.walk(logdir):
                for f in filenames:
                    if f.endswith(".log"):
                        log_files.append(os.path.join(dp, f))
        return log_files

    def preview_old_installers(self):
        installer_dir = os.path.join(os.environ.get('ProgramData', ''), "Package Cache")
        return [os.path.join(dp, f) for dp, _, filenames in os.walk(installer_dir) for f in filenames] if os.path.exists(installer_dir) else []

# File Tracker Widget
class StorageApp(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_ui()

    def init_ui(self):
        self.label = QLabel(r"Click 'Scan Now' to analyze C:\ drive")
        self.filter_selector = QComboBox()
        self.filter_selector.addItem("All Files", None)
        for ext in FILTER_EXTENSIONS:
            self.filter_selector.addItem(f"*{ext}", ext)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File Path", "Size", "Change"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scan_button = QPushButton("Scan Now")
        self.scan_button.clicked.connect(self.start_scan)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.filter_selector)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.scan_button)

    def scan_folder_files(self, root_path, extensions=None):
        file_info = {}
        for current_root, dirs, files in os.walk(root_path, topdown=True):
            if any(current_root.startswith(excluded) for excluded in EXCLUDED_FOLDERS):
                dirs[:] = []
                continue
            for f in files:
                try:
                    if extensions and not any(f.lower().endswith(ext) for ext in extensions):
                        continue
                    path = os.path.join(current_root, f)
                    size = os.path.getsize(path)
                    file_info[path] = size
                except (PermissionError, FileNotFoundError, OSError):
                    continue
        return file_info

    def save_snapshot(self, snapshot):
        os.makedirs(SNAPSHOT_BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(SNAPSHOT_BACKUP_DIR, f"snapshot_{timestamp}.json")
        with open(backup_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(snapshot, f, indent=2)

    def load_snapshot(self):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def compare_file_snapshots(self, old, new):
        new_files = []
        grown_files = []
        deleted_files = []
        for path, size in new.items():
            if path not in old:
                new_files.append((path, size))
            else:
                diff = size - old[path]
                if diff > 10 * 1024 * 1024:  # 10MB threshold
                    grown_files.append((path, diff))
        for path in old:
            if path not in new:
                deleted_files.append(path)
        return new_files, grown_files, deleted_files

    def show_notification(self, title, message):
        toaster.show_toast(title, message, duration=5, threaded=True)

    def start_scan(self):
        if platform.system() != 'Windows':
            self.label.setText("❌ Only works on Windows")
            return
        self.label.setText("Scanning...")
        self.table.setRowCount(0)
        self.scan_button.setEnabled(False)
        selected_ext = self.filter_selector.currentData()
        extensions = None if selected_ext is None else [selected_ext]
        self.thread = QThread()
        self.worker = FolderScanWorker(extensions)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.label.setText)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_scan_finished(self, file_data, new_files, grown_files, deleted_files):
        self.table.setRowCount(0)
        top_files = sorted(file_data.items(), key=lambda x: x[1], reverse=True)[:20]
        change_map = {path: "" for path, _ in top_files}
        for path, _ in new_files:
            change_map[path] = "🆕 New"
        for path, size in grown_files:
            change_map[path] = f"📈 +{get_human_size(size)}"
        for path in deleted_files:
            change_map[path] = "❌ Deleted"
        for path, size in top_files:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(path))
            self.table.setItem(row, 1, QTableWidgetItem(get_human_size(size)))
            self.table.setItem(row, 2, QTableWidgetItem(change_map.get(path, "")))
        for path in deleted_files:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(path))
            self.table.setItem(row, 1, QTableWidgetItem("—"))
            self.table.setItem(row, 2, QTableWidgetItem("❌ Deleted"))
        for path, size in new_files:
            if path not in dict(top_files):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(path))
                self.table.setItem(row, 1, QTableWidgetItem(get_human_size(size)))
                self.table.setItem(row, 2, QTableWidgetItem("🆕 New"))
        self.label.setText("Scan complete.")
        self.show_notification("File Scan Complete", f"{len(new_files)} new, {len(grown_files)} grew, {len(deleted_files)} deleted.")
        self.scan_button.setEnabled(True)

class FolderScanWorker(QObject):
    finished = Signal(object, object, object, object)
    progress = Signal(str)

    def __init__(self, extensions):
        super().__init__()
        self.extensions = extensions

    def run(self):
        self.progress.emit("Scanning C:\\ for file changes...")
        current = self.scan_folder_files(r"C:", self.extensions)
        previous = self.load_snapshot()
        if previous:
            new, grown, deleted = self.compare_file_snapshots(previous, current)
        else:
            new, grown, deleted = [], [], []
        self.save_snapshot(current)
        self.finished.emit(current, new, grown, deleted)

    def scan_folder_files(self, root_path, extensions=None):
        file_info = {}
        for current_root, dirs, files in os.walk(root_path, topdown=True):
            if any(current_root.startswith(excluded) for excluded in EXCLUDED_FOLDERS):
                dirs[:] = []
                continue
            for f in files:
                try:
                    if extensions and not any(f.lower().endswith(ext) for ext in extensions):
                        continue
                    path = os.path.join(current_root, f)
                    size = os.path.getsize(path)
                    file_info[path] = size
                except (PermissionError, FileNotFoundError, OSError):
                    continue
        return file_info

    def save_snapshot(self, snapshot):
        os.makedirs(SNAPSHOT_BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(SNAPSHOT_BACKUP_DIR, f"snapshot_{timestamp}.json")
        with open(backup_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(snapshot, f, indent=2)

    def load_snapshot(self):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def compare_file_snapshots(self, old, new):
        new_files = []
        grown_files = []
        deleted_files = []
        for path, size in new.items():
            if path not in old:
                new_files.append((path, size))
            else:
                diff = size - old[path]
                if diff > 10 * 1024 * 1024:  # 10MB threshold
                    grown_files.append((path, diff))
        for path in old:
            if path not in new:
                deleted_files.append(path)
        return new_files, grown_files, deleted_files

# Main Application
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storage Cleaner & File Tracker")
        self.setMinimumSize(1000, 700)
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.cleaner_tab = StorageCleaner()
        self.tracker_tab = StorageApp()
        self.tab_widget.addTab(self.cleaner_tab, "🧹 Cleaner")
        self.tab_widget.addTab(self.tracker_tab, "📁 Tracker")
        self.init_system_tray()

    def init_system_tray(self):
        # Load icon from file
        icon_path = "icon.ico"  # Make sure this file exists
        if not os.path.exists(icon_path):
            icon_path = None  # Will use default icon
            
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip("Storage Cleaner & File Tracker")
        
        # Rest of the code remains the same
        tray_menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.show)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(restore_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Storage Cleaner & File Tracker",
            "Application minimized to system tray.",
            QSystemTrayIcon.Information,
            2000
        )

if __name__ == "__main__":
    run_as_admin()
    app = QApplication(sys.argv)
    apply_dark_mode(app)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
