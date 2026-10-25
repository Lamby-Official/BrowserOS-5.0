# ============================================================
# Browser OS
# A single-file Python desktop/browser OS prototype.
#
# Requires:
#   py -m pip install PyQt6 PyQt6-WebEngine
#
# Start:
#   py BrowserOS.py
#
# Main features:
# - Virtual desktop windows
# - Real Chromium-based browser via Qt WebEngine
# - Tabs, navigation, search, downloads
# - Custom start page
# - Individually configurable desktop app tiles
# - Pinned apps and recent websites
# - Browser sessions (.bos_session.json)
# - Window positions/sizes in sessions
# - Scroll-position saving/restoring where the web page permits it
# - Workspaces
# - Themes and wallpaper/video background
# - Settings
# - File Explorer, Notes, Calculator, Task Manager
# - Browser history and bookmarks
# - Start menu with website apps and PC apps
# - Per-app tile backgrounds and independent start-menu themes
# - App Store-style app launcher
# - Autosave and last-session restore
# - Import von Browser-Lesezeichen und Verlauf
# - Webseiten-Übersetzer
# - Privacy branding: Kein Tracking / Keine Spyware / Open-Source Browser
#
# This is a prototype "Browser OS" running as a normal Windows app.
# ============================================================

import sys
import os

import json
import time
import shutil
import subprocess
import ctypes
import time
import uuid
import shlex
import sqlite3
import tempfile
import threading
import imaplib
import smtplib
import ssl
import email as email_lib
from email.header import decode_header
from email.message import EmailMessage
from email.utils import parseaddr
import html as html_lib
import re
from urllib.parse import quote

try:
    import winreg
except ImportError:
    winreg = None
import platform
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import (
    Qt,
    QObject,
    QUrl,
    QPoint,
    QSize,
    QRect,
    QTimer,
    QThread,
    pyqtSignal,
    QLocale,
)
from PyQt6.QtGui import (
    QAction,
    QFont,
    QIcon,
    QPixmap,
    QColor,
    QCursor,
    QFileSystemModel,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QToolButton,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QTreeView,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QColorDialog,
    QFileDialog,
    QMessageBox,
    QTabWidget,
    QTabBar,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QScrollArea,
    QSplitter,
    QGroupBox,
    QAbstractItemView,
    QCalendarWidget,
    QMenu,
    QSystemTrayIcon,
    QStyle,
)


from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
)

try:
    from PyQt6.QtWebEngineCore import QWebEngineExtensionManager
    WEBENGINE_EXTENSIONS_AVAILABLE = True
except ImportError:
    QWebEngineExtensionManager = None
    WEBENGINE_EXTENSIONS_AVAILABLE = False
from PyQt6.QtWebEngineWidgets import QWebEngineView

APP_NAME = "Browser OS"
VERSION = "1.5"

# ------------------------------------------------------------
# Paths / data
# ------------------------------------------------------------

APP_DIR = Path.home() / "Browser OS"
DATA_DIR = APP_DIR / "Data"
SESSIONS_DIR = APP_DIR / "Browser-Sessions"
LAYOUTS_DIR = APP_DIR / "Startseiten"
DOWNLOADS_DIR = APP_DIR / "Downloads"
WEB_PROFILE_DIR = APP_DIR / "WebProfile"
CACHE_DIR = APP_DIR / "Cache"

for folder in (
    APP_DIR,
    DATA_DIR,
    SESSIONS_DIR,
    LAYOUTS_DIR,
    DOWNLOADS_DIR,
    WEB_PROFILE_DIR,
    CACHE_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "history.json"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
NOTES_FILE = DATA_DIR / "notes.txt"
WINDOW_STATE_FILE = DATA_DIR / "last_session.json"


# ------------------------------------------------------------
# Small data helpers
# ------------------------------------------------------------

def deep_copy(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def load_json(path, fallback):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return deep_copy(fallback)


def save_json(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"Could not save {path}: {exc}")


# ------------------------------------------------------------
# Languages
# ------------------------------------------------------------

LANGUAGE_OPTIONS = [
    ("auto", "Automatisch (PC)"),
    ("en", "English"),
    ("de", "Deutsch"),
    ("fr", "Français"),
    ("es", "Español"),
    ("it", "Italiano"),
    ("pt", "Português"),
    ("nl", "Nederlands"),
    ("sv", "Svenska"),
    ("no", "Norsk"),
    ("da", "Dansk"),
    ("fi", "Suomi"),
    ("is", "Íslenska"),
    ("ga", "Gaeilge"),
    ("cy", "Cymraeg"),
    ("pl", "Polski"),
    ("cs", "Čeština"),
    ("sk", "Slovenčina"),
    ("sl", "Slovenščina"),
    ("hr", "Hrvatski"),
    ("bs", "Bosanski"),
    ("sr", "Српски"),
    ("bg", "Български"),
    ("ro", "Română"),
    ("hu", "Magyar"),
    ("el", "Ελληνικά"),
    ("tr", "Türkçe"),
    ("sq", "Shqip"),
    ("et", "Eesti"),
    ("lv", "Latviešu"),
    ("lt", "Lietuvių"),
    ("uk", "Українська"),
    ("ru", "Русский"),
    ("be", "Беларуская"),
    ("mk", "Македонски"),
    ("ka", "ქართული"),
    ("hy", "Հայերեն"),
    ("az", "Azərbaycan dili"),
    ("kk", "Қазақша"),
    ("uz", "Oʻzbekcha"),
    ("tk", "Türkmençe"),
    ("mn", "Монгол"),
    ("fa", "فارسی"),
    ("ar", "العربية"),
    ("he", "עברית"),
    ("ur", "اردو"),
    ("hi", "हिन्दी"),
    ("bn", "বাংলা"),
    ("pa", "ਪੰਜਾਬੀ"),
    ("gu", "ગુજરાતી"),
    ("mr", "मराठी"),
    ("ne", "नेपाली"),
    ("si", "සිංහල"),
    ("ta", "தமிழ்"),
    ("te", "తెలుగు"),
    ("kn", "ಕನ್ನಡ"),
    ("ml", "മലയാളം"),
    ("th", "ไทย"),
    ("vi", "Tiếng Việt"),
    ("id", "Bahasa Indonesia"),
    ("ms", "Bahasa Melayu"),
    ("tl", "Filipino"),
    ("zh-CN", "简体中文"),
    ("zh-TW", "繁體中文"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("sw", "Kiswahili"),
    ("af", "Afrikaans"),
    ("am", "አማርኛ"),
    ("zu", "isiZulu"),
    ("xh", "isiXhosa"),
    ("yo", "Yorùbá"),
    ("ig", "Igbo"),
    ("ha", "Hausa"),
    ("so", "Soomaali"),
    ("la", "Latina"),
    ("eo", "Esperanto"),
]


def detect_system_language_code():
    try:
        name = QLocale.system().name().lower().replace("-", "_")
    except Exception:
        return "en"

    if name.startswith("zh_cn"):
        return "zh-CN"
    if name.startswith("zh_tw"):
        return "zh-TW"

    code = name.split("_", 1)[0]
    valid = {
        item[0]
        for item in LANGUAGE_OPTIONS
        if item[0] != "auto"
    }
    return code if code in valid else "en"


def get_language_code():
    value = settings.get("language", "auto")

    if value == "auto":
        return detect_system_language_code()

    valid = {item[0] for item in LANGUAGE_OPTIONS}
    return value if value in valid else "en"


def get_current_language_name():
    code = get_language_code()
    for option_code, label in LANGUAGE_OPTIONS:
        if option_code == code:
            return label
    return "English"




def remove_browseros_autostart():
    """
    Remove common Browser OS startup entries created by older prototypes.

    Browser OS must NOT start on Windows login just because it is a
    default browser candidate.
    """
    if platform.system() != "Windows" or winreg is None:
        return

    try:
        run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            run_path,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            for name in ("Browser OS", "BrowserOS", "BrowserOS.py"):
                try:
                    winreg.DeleteValue(key, name)
                except OSError:
                    pass
    except Exception:
        pass


def get_previous_default_browser():
    """
    Try to read the current Windows default HTTP/HTTPS browser before
    Browser OS changes anything. This is only for display; Browser OS
    does not silently change Windows file associations.
    """
    if platform.system() != "Windows" or winreg is None:
        return "Windows Standardbrowser"

    try:
        subkeys = [
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
            ),
        ]

        progids = []
        for root, key_path in subkeys:
            try:
                with winreg.OpenKey(root, key_path) as key:
                    progid, _ = winreg.QueryValueEx(key, "ProgId")
                    if progid and progid not in progids:
                        progids.append(str(progid))
            except OSError:
                continue

        if not progids:
            return "Windows Standardbrowser"

        progid = progids[0].lower()

        names = {
            "microsoft.microsoftedge_8wekyb3d8bbwe!microsoftedge": "Microsoft Edge",
            "microsoft-edge": "Microsoft Edge",
            "chromehtml": "Google Chrome",
            "firefoxurl": "Mozilla Firefox",
            "bravehtml": "Brave",
            "opera.stable": "Opera",
            "vivaldi": "Vivaldi",
            "yandex": "Yandex Browser",
        }

        return names.get(progid, progids[0])

    except Exception:
        return "Windows Standardbrowser"




def refresh_windows_associations():
    """
    Tell Explorer/Windows that new file/protocol associations were registered.

    Microsoft documents SHChangeNotify(SHCNE_ASSOCCHANGED) for this exact
    purpose after registering a new browser/default-app candidate.
    """
    if platform.system() != "Windows":
        return

    try:
        shell32 = ctypes.windll.shell32
        shell32.SHChangeNotify(
            0x08000000,  # SHCNE_ASSOCCHANGED
            0x0003,      # SHCNF_DWORD
            None,
            None,
        )
        time.sleep(1.0)
    except Exception:
        pass


def get_browser_command(argument="%1"):
    """
    Build the command Windows uses for Browser OS URL/file associations.

    When running as a normal Python script, use pythonw.exe so opening an
    HTML/PDF/URL does not create a visible console window.
    When packaged as an EXE, use the EXE directly.
    """
    try:
        if getattr(sys, "frozen", False):
            executable = Path(sys.executable)
            return f'"{executable}" "{argument}"'

        executable = Path(sys.executable)
        pythonw = executable.with_name("pythonw.exe")
        if not pythonw.exists():
            pythonw = executable

        script = Path(__file__).resolve()

        return f'"{pythonw}" "{script}" "{argument}"'
    except Exception:
        return f'"{sys.executable}" "{Path(__file__).resolve()}" "{argument}"'


def register_browser_windows():
    """
    Register Browser OS as a per-user Windows default-app candidate.

    IMPORTANT:
    Windows 11 intentionally keeps the final choice under the user's control.
    This function registers Browser OS correctly and opens the official
    Windows page where the user can press "Set default".
    """
    if platform.system() != "Windows" or winreg is None:
        return False, "Windows-Registrierung ist nur unter Windows verfügbar."

    try:
        app_name = "Browser OS"
        capabilities = r"Software\BrowserOS\Capabilities"

        # Separate ProgIDs for HTTP and HTTPS.
        http_progid = "BrowserOSHTTP"
        https_progid = "BrowserOSHTTPS"
        html_progid = "BrowserOSHTML"
        pdf_progid = "BrowserOSPDF"

        if getattr(sys, "frozen", False):
            executable = Path(sys.executable)
            command = f'"{executable}" "%1"'
            icon = f'"{executable}",0'
        else:
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            if not pythonw.exists():
                pythonw = Path(sys.executable)

            script = Path(__file__).resolve()
            command = f'"{pythonw}" "{script}" "%1"'
            icon = f'"{pythonw}",0'

        # --------------------------------------------------------
        # Root application registration.
        # --------------------------------------------------------
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\BrowserOS"
        ) as key:
            winreg.SetValueEx(key, "Installed", 0, winreg.REG_DWORD, 1)

        # --------------------------------------------------------
        # Capabilities.
        # --------------------------------------------------------
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            capabilities
        ) as key:
            winreg.SetValueEx(
                key,
                "ApplicationName",
                0,
                winreg.REG_SZ,
                app_name,
            )
            winreg.SetValueEx(
                key,
                "ApplicationDescription",
                0,
                winreg.REG_SZ,
                "Browser OS – Webbrowser für Windows",
            )
            winreg.SetValueEx(
                key,
                "ApplicationIcon",
                0,
                winreg.REG_SZ,
                icon,
            )

        # --------------------------------------------------------
        # ProgIDs for HTTP / HTTPS.
        # --------------------------------------------------------
        def create_progid(progid, title, add_url_protocol=False):
            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                rf"Software\Classes\{progid}"
            ) as key:
                winreg.SetValueEx(
                    key,
                    "",
                    0,
                    winreg.REG_SZ,
                    title,
                )
                if add_url_protocol:
                    winreg.SetValueEx(
                        key,
                        "URL Protocol",
                        0,
                        winreg.REG_SZ,
                        "",
                    )

            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                rf"Software\Classes\{progid}\DefaultIcon"
            ) as key:
                winreg.SetValueEx(
                    key,
                    "",
                    0,
                    winreg.REG_SZ,
                    icon,
                )

            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                rf"Software\Classes\{progid}\shell\open\command"
            ) as key:
                winreg.SetValueEx(
                    key,
                    "",
                    0,
                    winreg.REG_SZ,
                    command,
                )

        create_progid(
            http_progid,
            "Browser OS HTTP Link",
            True,
        )
        create_progid(
            https_progid,
            "Browser OS HTTPS Link",
            True,
        )

        # --------------------------------------------------------
        # HTML ProgID.
        # --------------------------------------------------------
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\{html_progid}"
        ) as key:
            winreg.SetValueEx(
                key,
                "",
                0,
                winreg.REG_SZ,
                "Browser OS HTML Document",
            )

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\{html_progid}\DefaultIcon"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon)

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\{html_progid}\shell\open\command"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

        # --------------------------------------------------------
        # PDF ProgID.
        # --------------------------------------------------------
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\{pdf_progid}"
        ) as key:
            winreg.SetValueEx(
                key,
                "",
                0,
                winreg.REG_SZ,
                "Browser OS PDF Document",
            )

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\{pdf_progid}\DefaultIcon"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon)

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\{pdf_progid}\shell\open\command"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

        # --------------------------------------------------------
        # Capability associations.
        # --------------------------------------------------------
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            capabilities + r"\URLAssociations"
        ) as key:
            winreg.SetValueEx(
                key,
                "http",
                0,
                winreg.REG_SZ,
                http_progid,
            )
            winreg.SetValueEx(
                key,
                "https",
                0,
                winreg.REG_SZ,
                https_progid,
            )

        # Explorer's Open With list as an additional per-user registration.
        content_types = {
            ".html": "text/html",
            ".htm": "text/html",
            ".xhtml": "application/xhtml+xml",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".mht": "message/rfc822",
            ".mhtml": "message/rfc822",
        }

        open_with = {
            ".htm": html_progid,
            ".html": html_progid,
            ".xhtml": html_progid,
            ".mht": html_progid,
            ".mhtml": html_progid,
            ".svg": html_progid,
            ".pdf": pdf_progid,
        }

        for extension, mime in content_types.items():
            try:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    rf"Software\Classes\{extension}"
                ) as key:
                    winreg.SetValueEx(
                        key,
                        "Content Type",
                        0,
                        winreg.REG_SZ,
                        mime,
                    )
            except Exception:
                pass

        for extension, progid in open_with.items():
            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                rf"Software\Classes\{extension}\OpenWithProgids"
            ) as key:
                winreg.SetValueEx(
                    key,
                    progid,
                    0,
                    winreg.REG_NONE,
                    b"",
                )

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            capabilities + r"\FileAssociations"
        ) as key:
            for extension in (
                ".htm",
                ".html",
                ".xhtml",
                ".mht",
                ".mhtml",
                ".svg",
            ):
                winreg.SetValueEx(
                    key,
                    extension,
                    0,
                    winreg.REG_SZ,
                    html_progid,
                )

            winreg.SetValueEx(
                key,
                ".pdf",
                0,
                winreg.REG_SZ,
                pdf_progid,
            )

        # --------------------------------------------------------
        # RegisteredApplications is what Windows uses to find the app.
        # --------------------------------------------------------
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\RegisteredApplications"
        ) as key:
            winreg.SetValueEx(
                key,
                app_name,
                0,
                winreg.REG_SZ,
                capabilities,
            )

        refresh_windows_associations()

        return True, (
            "Browser OS ist jetzt bei Windows als Standard-App registriert.\n\n"
            "Öffne jetzt die Browser-OS-Seite in Windows → Standard-Apps "
            "und drücke dort den Windows-Button zum Festlegen als Standard."
        )

    except Exception as exc:
        return False, f"Registrierung fehlgeschlagen:\n{exc}"


def is_browseros_registered_as_default():
    """Check whether Windows currently uses Browser OS for HTTP/HTTPS."""
    if platform.system() != "Windows" or winreg is None:
        return False

    try:
        expected = {
            "http": "BrowserOSHTTP",
            "https": "BrowserOSHTTPS",
        }

        for protocol in ("http", "https"):
            key_path = (
                r"Software\Microsoft\Windows\Shell\Associations"
                rf"\UrlAssociations\{protocol}\UserChoice"
            )

            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    key_path,
                ) as key:
                    progid, _ = winreg.QueryValueEx(key, "ProgId")
                    if str(progid) != expected[protocol]:
                        return False
            except OSError:
                return False

        return True

    except Exception:
        return False

def register_browser_only(parent=None):
    """
    Register Browser OS as a Windows default-app candidate.

    Does not start the browser and does not open Windows Settings.
    """
    success, message = register_browser_windows()

    if success:
        QMessageBox.information(
            parent,
            APP_NAME,
            message
            + "\n\n"
            "Browser OS wurde registriert, aber NICHT automatisch gestartet.\n"
            "Öffne die Windows-Standard-Apps nur über den dafür vorgesehenen Button.",
        )
    else:
        QMessageBox.warning(parent, APP_NAME, message)

    return success



def remove_browser_windows_registration(parent=None):
    """
    Remove the Browser OS registration created by register_browser_windows().
    It does not change another browser's defaults.
    """
    if platform.system() != "Windows" or winreg is None:
        return

    try:
        def delete_tree(root, path_value):
            try:
                with winreg.OpenKey(root, path_value, 0, winreg.KEY_READ) as key:
                    while True:
                        try:
                            child = winreg.EnumKey(key, 0)
                            delete_tree(root, path_value + "\\" + child)
                        except OSError:
                            break
                winreg.DeleteKey(root, path_value)
            except OSError:
                pass

        delete_tree(
            winreg.HKEY_CURRENT_USER,
            r"Software\BrowserOS",
        )

        delete_tree(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\BrowserOSURL",
        )
        delete_tree(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\BrowserOSHTML",
        )
        delete_tree(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\BrowserOSPDF",
        )

        # Remove RegisteredApplications value.
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\RegisteredApplications",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            try:
                winreg.DeleteValue(key, "Browser OS")
            except OSError:
                pass

        if parent is not None:
            QMessageBox.information(
                parent,
                APP_NAME,
                "Browser OS wurde aus den registrierten Windows-Apps entfernt.",
            )

    except Exception as exc:
        if parent is not None:
            QMessageBox.warning(
                parent,
                APP_NAME,
                f"Registrierung konnte nicht entfernt werden:\n{exc}",
            )


def open_windows_default_apps():
    """Open Windows' general Default Apps settings."""
    if platform.system() != "Windows":
        QMessageBox.information(
            None,
            APP_NAME,
            "Die Windows-Standardsbrowser-Einstellungen sind nur unter Windows verfügbar.",
        )
        return

    try:
        subprocess.Popen(
            ["explorer.exe", "ms-settings:defaultapps"],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as exc:
        QMessageBox.warning(
            None,
            APP_NAME,
            f"Die Windows-Standardeinstellungen konnten nicht geöffnet werden:\n{exc}",
        )


def open_browseros_default_app_page():
    """
    Open the specific Windows 11 Default Apps page for Browser OS.

    Windows 11 supports the registeredAppUser query parameter for apps
    registered under HKCU\\Software\\RegisteredApplications.
    """
    if platform.system() != "Windows":
        QMessageBox.information(
            None,
            APP_NAME,
            "Diese Funktion ist nur unter Windows verfügbar.",
        )
        return

    try:
        registered_name = quote("Browser OS", safe="")
        uri = (
            "ms-settings:defaultapps?"
            f"registeredAppUser={registered_name}"
        )

        subprocess.Popen(
            ["explorer.exe", uri],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as exc:
        QMessageBox.warning(
            None,
            APP_NAME,
            f"Die Browser-OS-Standardseite konnte nicht geöffnet werden:\n{exc}",
        )


# ------------------------------------------------------------
# Default settings
# ------------------------------------------------------------

DEFAULT_SETTINGS = {
    "language": "auto",
    "setup_completed": False,
    "search_engine_mode": "standard",
    "theme": "Purple Dark",
    "accent": "#a855f7",
    "desktop_color": "#11131a",
    "wallpaper_mode": "color",
    "wallpaper_path": "",

    "search_engine": "Google",
    "custom_search_url": "https://www.google.com/search?q={query}",

    "show_recent": True,
    "show_pinned": True,
    "show_clock": True,
    "show_system": True,
    "show_widgets": True,

    "pinned_apps": [
        "browser",
        "files",
        "notes",
        "calculator",
        "settings",
    ],

    "auto_restore": True,
    "auto_save": True,
    "startup_mode": "desktop",
    "developer_mode": False,
    "privacy_notice": "Kein Tracking • Keine Spyware • Open-Source Browser",

    "start_menu_theme": "Glass",
    "start_menu_background_mode": "color",
    "start_menu_background_color": "#151827",
    "start_menu_background_path": "",
    "custom_apps": [],

    "desktop_tiles": [
        {
            "id": "browser",
            "name": "Browser",
            "icon": "🌍",
            "x": 35,
            "y": 100,
            "w": 150,
            "h": 92,
        },
        {
            "id": "files",
            "name": "Dateien",
            "icon": "📁",
            "x": 210,
            "y": 100,
            "w": 150,
            "h": 92,
        },
        {
            "id": "notes",
            "name": "Notizen",
            "icon": "📝",
            "x": 385,
            "y": 100,
            "w": 150,
            "h": 92,
        },
        {
            "id": "calculator",
            "name": "Rechner",
            "icon": "🧮",
            "x": 35,
            "y": 210,
            "w": 150,
            "h": 92,
        },
        {
            "id": "settings",
            "name": "Einstellungen",
            "icon": "⚙️",
            "x": 210,
            "y": 210,
            "w": 150,
            "h": 92,
        },
        {
            "id": "sessions",
            "name": "Sitzungen",
            "icon": "💾",
            "x": 385,
            "y": 210,
            "w": 150,
            "h": 92,
        },
        {
            "id": "mail",
            "name": "Mails",
            "icon": "📧",
            "x": 35,
            "y": 320,
            "w": 150,
            "h": 92,
        },
        {
            "id": "downloads",
            "name": "Downloads",
            "icon": "📥",
            "x": 210,
            "y": 320,
            "w": 150,
            "h": 92,
        },
        {
            "id": "music",
            "name": "Musik",
            "icon": "🎵",
            "x": 385,
            "y": 320,
            "w": 150,
            "h": 92,
        },
        {
            "id": "videos",
            "name": "Videos",
            "icon": "🎬",
            "x": 35,
            "y": 430,
            "w": 150,
            "h": 92,
        },
        {
            "id": "pictures",
            "name": "Bilder",
            "icon": "🖼️",
            "x": 210,
            "y": 430,
            "w": 150,
            "h": 92,
        },
        {
            "id": "calendar",
            "name": "Kalender",
            "icon": "📅",
            "x": 385,
            "y": 430,
            "w": 150,
            "h": 92,
        },
        {
            "id": "terminal",
            "name": "Terminal",
            "icon": "💻",
            "x": 35,
            "y": 540,
            "w": 150,
            "h": 92,
        },
        {
            "id": "systeminfo",
            "name": "Systeminfo",
            "icon": "🖥️",
            "x": 210,
            "y": 540,
            "w": 150,
            "h": 92,
        },
        {
            "id": "trash",
            "name": "Papierkorb",
            "icon": "🗑️",
            "x": 385,
            "y": 540,
            "w": 150,
            "h": 92,
        },
    ],

    "workspaces": [
        "Normal",
        "Coding",
        "Gaming",
        "Schule",
    ],
    "current_workspace": "Normal",
}


settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)


def ensure_desktop_plus_apps():
    """Add newly introduced desktop apps without overwriting the user's layout."""
    existing = {str(item.get("id")) for item in settings.get("desktop_tiles", [])}
    additions = [
        ("mail", "Mails", "📧", 35, 320),
        ("downloads", "Downloads", "📥", 210, 320),
        ("music", "Musik", "🎵", 385, 320),
        ("videos", "Videos", "🎬", 35, 430),
        ("pictures", "Bilder", "🖼️", 210, 430),
        ("calendar", "Kalender", "📅", 385, 430),
        ("terminal", "Terminal", "💻", 35, 540),
        ("systeminfo", "Systeminfo", "🖥️", 210, 540),
        ("trash", "Papierkorb", "🗑️", 385, 540),
    ]
    for app_id, name, icon, x, y in additions:
        if app_id in existing:
            continue
        settings.setdefault("desktop_tiles", []).append({
            "id": app_id,
            "name": name,
            "icon": icon,
            "x": x,
            "y": y,
            "w": 150,
            "h": 92,
        })
    save_json(SETTINGS_FILE, settings)


ensure_desktop_plus_apps()
history = load_json(HISTORY_FILE, [])
bookmarks = load_json(BOOKMARKS_FILE, [])


def ensure_settings():
    changed = False

    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = deep_copy(value)
            changed = True

    if settings.get("browser_default_choice") not in ("browseros", "previous"):
        settings["browser_default_choice"] = "previous"
        changed = True

    if not settings.get("previous_browser_name"):
        settings["previous_browser_name"] = get_previous_default_browser()
        changed = True

    valid_language_codes = {
        code for code, _ in LANGUAGE_OPTIONS
    }
    if settings.get("language") not in valid_language_codes:
        settings["language"] = "auto"
        changed = True

    valid_engines = {
        "Google",
        "Bing",
        "Yahoo",
        "DuckDuckGo",
        "Brave Search",
        "Startpage",
        "Ecosia",
        "Eigene",
    }

    if settings.get("search_engine") not in valid_engines:
        settings["search_engine"] = "Google"
        changed = True

    if settings.get("search_engine_mode") not in ("standard", "test"):
        settings["search_engine_mode"] = "standard"
        changed = True

    if changed:
        save_json(SETTINGS_FILE, settings)


ensure_settings()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def now_string():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def safe_file_name(text):
    invalid = '<>:"/\\|?*'
    result = "".join("_" if c in invalid else c for c in text)
    return result.strip() or "Sitzung"


def normalize_url(text):
    text = text.strip().strip('"')

    if not text:
        return "https://www.google.com"

    lowered = text.lower()

    # Real web URLs.
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return text

    # Local HTML/PDF/MHT/HTM/XHTML/SVG files passed by Windows
    # or entered as a normal file path.
    try:
        local_path = Path(text).expanduser()
        if local_path.exists() and local_path.is_file():
            if local_path.suffix.lower() in {
                ".pdf",
                ".html",
                ".htm",
                ".xhtml",
                ".mht",
                ".mhtml",
                ".svg",
            }:
                return QUrl.fromLocalFile(
                    str(local_path.resolve())
                ).toString()
    except Exception:
        pass

    # Already a file:// URL.
    if lowered.startswith("file://"):
        return text

    # browseros://home is only an internal Python sentinel.
    if text.startswith("browseros://"):
        return "https://www.google.com"

    if "://" in text:
        return text
    if lowered.startswith(("localhost:", "127.0.0.1:", "192.168.")):
        return "http://" + text

    if "." in text or lowered.startswith("localhost"):
        return "https://" + text

    return build_search_url(text)


def build_search_url(query):
    engine = settings.get("search_engine", "Google")

    templates = {
        "Google": "https://www.google.com/search?q={query}",
        "Bing": "https://www.bing.com/search?q={query}",
        "Yahoo": "https://search.yahoo.com/search?p={query}",
        "DuckDuckGo": "https://duckduckgo.com/?q={query}",
        "Brave Search": "https://search.brave.com/search?q={query}",
        "Startpage": "https://www.startpage.com/sp/search?query={query}",
        "Ecosia": "https://www.ecosia.org/search?q={query}",
    }

    if engine == "Eigene":
        template = settings.get(
            "custom_search_url",
            templates["Google"],
        )
    else:
        template = templates.get(
            engine,
            templates["Google"],
        )

    return template.replace(
        "{query}",
        QUrl.toPercentEncoding(query).data().decode("utf-8"),
    )


def open_external(path_or_url):
    try:
        if platform.system() == "Windows":
            os.startfile(str(path_or_url))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(path_or_url)])
        else:
            subprocess.Popen(["xdg-open", str(path_or_url)])
    except Exception as exc:
        QMessageBox.warning(None, APP_NAME, f"Konnte nicht öffnen:\n{exc}")


def add_history(url, title=""):
    if not url or url.startswith("browseros://"):
        return
    item = {
        "url": url,
        "title": title or url,
        "time": now_string(),
    }
    global history
    history.insert(0, item)
    history = history[:1000]
    save_json(HISTORY_FILE, history)


def add_bookmark(url, title=""):
    global bookmarks
    if not url:
        return
    if not any(x.get("url") == url for x in bookmarks):
        bookmarks.insert(0, {"url": url, "title": title or url})
        save_json(BOOKMARKS_FILE, bookmarks)


def is_dark_theme():
    return settings.get("theme", "Purple Dark") != "Light"


# ------------------------------------------------------------
# Theme
# ------------------------------------------------------------

def build_stylesheet():
    theme = settings.get("theme", "Purple Dark")
    accent = settings.get("accent", "#a855f7")
    if theme == "Light":
        bg = "#f3f4f8"
        panel = "#ffffff"
        panel2 = "#e9eaf0"
        text = "#1b1d24"
        sub = "#5f6472"
        border = "#d5d8e1"
    elif theme == "Midnight":
        bg = "#05060a"
        panel = "#0b0d14"
        panel2 = "#111522"
        text = "#f5f7ff"
        sub = "#9ba3b8"
        border = "#252b3b"
    elif theme == "Ocean":
        bg = "#08141d"
        panel = "#0d202d"
        panel2 = "#113045"
        text = "#effbff"
        sub = "#9fc1ce"
        border = "#234659"
    else:
        bg = "#101019"
        panel = "#171722"
        panel2 = "#222234"
        text = "#f7f7fb"
        sub = "#a8a8ba"
        border = "#303044"

    return f"""
    * {{
        font-family: "Segoe UI";
        color: {text};
    }}
    QMainWindow, QWidget#Root {{
        background: {bg};
    }}
    QToolTip {{
        background: {panel};
        color: {text};
        border: 1px solid {border};
        padding: 6px;
    }}
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 9px;
        padding: 8px;
        color: {text};
        selection-background-color: {accent};
    }}
    QPushButton, QToolButton {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 9px;
        padding: 8px 12px;
    }}
    QPushButton:hover, QToolButton:hover {{
        background: {panel2};
        border-color: {accent};
    }}
    QPushButton:pressed, QToolButton:pressed {{
        background: {accent};
        color: white;
    }}
    QListWidget, QTreeView, QTableWidget {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 10px;
        alternate-background-color: {panel2};
    }}
    QTabWidget::pane {{
        border: 1px solid {border};
        background: {panel};
        border-radius: 10px;
    }}
    QTabBar::tab {{
        background: {panel2};
        padding: 8px 13px;
        margin: 2px;
        border-radius: 8px;
    }}
    QTabBar::tab:selected {{
        background: {accent};
        color: white;
    }}
    QProgressBar {{
        border: 1px solid {border};
        border-radius: 8px;
        text-align: center;
        background: {panel};
    }}
    QProgressBar::chunk {{
        background: {accent};
        border-radius: 7px;
    }}
    QScrollArea {{
        border: none;
    }}
    QGroupBox {{
        border: 1px solid {border};
        border-radius: 10px;
        margin-top: 10px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    """


# ------------------------------------------------------------
# Desktop tiles
# ------------------------------------------------------------

APP_INFO = {
    "browser": ("🌍", "Browser"),
    "files": ("📁", "Dateien"),
    "notes": ("📝", "Notizen"),
    "calculator": ("🧮", "Rechner"),
    "settings": ("⚙️", "Einstellungen"),
    "sessions": ("💾", "Sitzungen"),
    "history": ("🕘", "Verlauf"),
    "bookmarks": ("⭐", "Lesezeichen"),
    "taskmanager": ("📊", "Task Manager"),
    "store": ("🛒", "App Store"),
    "mail": ("📧", "Mails"),
    "downloads": ("📥", "Downloads"),
    "music": ("🎵", "Musik"),
    "videos": ("🎬", "Videos"),
    "pictures": ("🖼️", "Bilder"),
    "calendar": ("📅", "Kalender"),
    "terminal": ("💻", "Terminal"),
    "systeminfo": ("🖥️", "Systeminfo"),
    "trash": ("🗑️", "Papierkorb"),
    "games": ("🎮", "Spiele"),
    "about": ("ℹ️", "Über Browser OS"),
}


class TileEditDialog(QDialog):
    def __init__(self, tile_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("App anpassen")
        self.resize(420, 420)

        self.name_edit = QLineEdit(tile_data.get("name", "App"))
        self.icon_edit = QLineEdit(tile_data.get("icon", "📦"))

        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 5000)
        self.x_spin.setValue(int(tile_data.get("x", 30)))

        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 5000)
        self.y_spin.setValue(int(tile_data.get("y", 80)))

        self.w_spin = QSpinBox()
        self.w_spin.setRange(80, 1000)
        self.w_spin.setValue(int(tile_data.get("w", 150)))

        self.h_spin = QSpinBox()
        self.h_spin.setRange(60, 1000)
        self.h_spin.setValue(int(tile_data.get("h", 92)))

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Icon:", self.icon_edit)
        form.addRow("X:", self.x_spin)
        form.addRow("Y:", self.y_spin)
        form.addRow("Breite:", self.w_spin)
        form.addRow("Höhe:", self.h_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def data(self):
        return {
            "name": self.name_edit.text().strip() or "App",
            "icon": self.icon_edit.text().strip() or "📦",
            "x": self.x_spin.value(),
            "y": self.y_spin.value(),
            "w": self.w_spin.value(),
            "h": self.h_spin.value(),
        }


class DesktopTile(QFrame):
    moved = pyqtSignal()
    launch = pyqtSignal(str)
    customize = pyqtSignal(object)

    def __init__(self, data, app_id, parent=None):
        super().__init__(parent)
        self.data = data
        self.app_id = app_id
        self.drag_offset = None

        self.setObjectName("DesktopTile")
        self.setStyleSheet("""
            QFrame#DesktopTile {
                background: rgba(25, 28, 40, 220);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 18px;
            }
            QFrame#DesktopTile:hover {
                background: rgba(46, 49, 66, 235);
                border: 1px solid rgba(168,85,247,150);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.icon_label = QLabel(data.get("icon", "📦"))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 30))
        layout.addWidget(self.icon_label)

        self.name_label = QLabel(data.get("name", "App"))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        self.setGeometry(
            int(data.get("x", 30)),
            int(data.get("y", 100)),
            int(data.get("w", 150)),
            int(data.get("h", 92)),
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.position().toPoint()
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            menu = self.createStandardContextMenu()
            menu.addSeparator()
            action = menu.addAction("✏️ App anpassen")
            action.triggered.connect(lambda: self.customize.emit(self))
            menu.exec(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self.drag_offset is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            parent = self.parentWidget()
            if parent:
                new_pos = self.pos() + event.position().toPoint() - self.drag_offset
                new_pos.setX(max(0, new_pos.x()))
                new_pos.setY(max(0, new_pos.y()))
                max_x = max(0, parent.width() - self.width())
                max_y = max(0, parent.height() - self.height())
                new_pos.setX(min(max_x, new_pos.x()))
                new_pos.setY(min(max_y, new_pos.y()))
                self.move(new_pos)
                self.data["x"] = self.x()
                self.data["y"] = self.y()
                self.moved.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drag_offset is not None:
            self.drag_offset = None
            self.launch.emit(self.app_id)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def refresh(self):
        self.icon_label.setText(self.data.get("icon", "📦"))
        self.name_label.setText(self.data.get("name", "App"))
        self.setGeometry(
            int(self.data.get("x", self.x())),
            int(self.data.get("y", self.y())),
            int(self.data.get("w", self.width())),
            int(self.data.get("h", self.height())),
        )


# ------------------------------------------------------------
# Virtual windows
# ------------------------------------------------------------

class VirtualWindow(QFrame):
    closed = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, manager, title, icon="🪟", width=900, height=620, workspace=None):
        super().__init__(manager.desktop)
        self.manager = manager
        self.workspace = workspace or manager.current_workspace
        self.drag_offset = None
        self.resizing = False
        self.resize_start = None
        self.start_geom = None
        self.minimized = False

        self.setObjectName("VirtualWindow")
        self.setStyleSheet("""
            QFrame#VirtualWindow {
                background: #141621;
                border: 1px solid rgba(255,255,255,55);
                border-radius: 14px;
            }
        """)

        self.titlebar = QFrame(self)
        self.titlebar.setObjectName("TitleBar")
        self.titlebar.setStyleSheet("""
            QFrame#TitleBar {
                background: rgba(25,27,38,245);
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
        """)

        title_layout = QHBoxLayout(self.titlebar)
        title_layout.setContentsMargins(10, 5, 7, 5)
        title_layout.setSpacing(6)

        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 17))

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))

        self.pin_button = QToolButton()
        self.pin_button.setText("📌")
        self.pin_button.setToolTip("Immer im Vordergrund")
        self.pin_button.clicked.connect(self.toggle_pin)

        self.min_button = QToolButton()
        self.min_button.setText("—")
        self.min_button.clicked.connect(self.minimize)

        self.max_button = QToolButton()
        self.max_button.setText("□")
        self.max_button.clicked.connect(self.toggle_maximize)

        self.close_button = QToolButton()
        self.close_button.setText("×")
        self.close_button.clicked.connect(self.close_window)

        title_layout.addWidget(self.icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.pin_button)
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.max_button)
        title_layout.addWidget(self.close_button)

        self.content = QFrame(self)
        self.content.setStyleSheet("QFrame { background: transparent; }")

        self.resize_handle = QLabel("◢", self)
        self.resize_handle.setFixedSize(18, 18)
        self.resize_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resize_handle.setStyleSheet("color: rgba(255,255,255,120); background: transparent;")

        self.pinned = False
        self.normal_geometry = QRect(0, 0, width, height)

        self.setGeometry(60, 80, width, height)
        self.raise_()

    def set_content(self, widget):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.titlebar.setGeometry(0, 0, self.width(), 44)
        self.content.setGeometry(0, 44, self.width(), self.height() - 44)
        self.resize_handle.move(self.width() - 18, self.height() - 18)
        self.changed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.y() <= 44:
                self.drag_offset = pos
                self.raise_()
                event.accept()
                return
            handle_rect = QRect(self.width() - 30, self.height() - 30, 30, 30)
            if handle_rect.contains(pos):
                self.resizing = True
                self.resize_start = event.globalPosition().toPoint()
                self.start_geom = self.geometry()
                self.raise_()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            new_pos = self.pos() + event.position().toPoint() - self.drag_offset
            new_pos.setX(max(0, new_pos.x()))
            new_pos.setY(max(45, new_pos.y()))
            self.move(new_pos)
            self.changed.emit()
            event.accept()
            return

        if self.resizing and self.start_geom:
            delta = event.globalPosition().toPoint() - self.resize_start
            new_width = max(320, self.start_geom.width() + delta.x())
            new_height = max(220, self.start_geom.height() + delta.y())
            self.resize(new_width, new_height)
            self.changed.emit()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = None
            self.resizing = False
        super().mouseReleaseEvent(event)

    def minimize(self):
        self.minimized = True
        self.hide()
        self.manager.refresh_taskbar()
        self.changed.emit()

    def restore(self):
        self.minimized = False
        self.show()
        self.raise_()
        self.manager.refresh_taskbar()

    def toggle_maximize(self):
        desktop = self.manager.desktop

        is_already_maximized = (
            self.x() <= 12
            and self.y() <= 60
            and self.width() >= desktop.width() - 24
            and self.height() >= desktop.height() - 115
        )

        if not is_already_maximized:
            # Save exact current geometry so it can be restored later.
            self.normal_geometry = self.geometry()

            is_browser = (
                self.title_label.text().strip().lower().startswith("browser")
            )

            if is_browser:
                # Hide the Browser OS topbar and bottom taskbar so the browser
                # gets the entire desktop area for web content.
                self.manager.set_browsing_chrome_state(True)
                top_margin = 8
                bottom_margin = 8
            else:
                top_margin = 52
                bottom_margin = 64

            self.setGeometry(
                8,
                top_margin,
                max(320, desktop.width() - 16),
                max(220, desktop.height() - top_margin - bottom_margin),
            )

            self.max_button.setText("❐")
        else:
            is_browser = (
                self.title_label.text().strip().lower().startswith("browser")
            )

            if is_browser:
                self.manager.set_browsing_chrome_state(False)

            if self.normal_geometry.isValid():
                self.setGeometry(self.normal_geometry)

            self.max_button.setText("□")

        self.raise_()
        self.changed.emit()

    def toggle_pin(self):
        self.pinned = not self.pinned
        self.pin_button.setText("📍" if self.pinned else "📌")
        self.changed.emit()
        self.raise_()

    def close_window(self):
        if self.title_label.text().strip().lower().startswith("browser"):
            self.manager.set_browsing_chrome_state(False)

        self.closed.emit(self)
        self.deleteLater()


# ------------------------------------------------------------
# Browser
# ------------------------------------------------------------

class BrowserView(QWebEngineView):
    """Embedded Chromium view with F12 developer tools support."""

    def __init__(self, browser_app, parent=None):
        super().__init__(parent)
        self.browser_app = browser_app

        page = QWebEnginePage(browser_app.main.get_web_profile(), self)
        self.setPage(page)

        try:
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.PdfViewerEnabled,
                True,
            )
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled,
                True,
            )
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalStorageEnabled,
                True,
            )
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.FullScreenSupportEnabled,
                True,
            )
        except Exception:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F12:
            if settings.get("developer_mode", False):
                self.browser_app.toggle_devtools()
                event.accept()
                return
        super().keyPressEvent(event)

    def createWindow(self, window_type):
        # Open target=_blank/window.open() as a new Browser OS tab.
        tab = self.browser_app.add_tab("about:blank")
        return tab.view


class BrowserTab(QWidget):
    def __init__(self, browser_app, url="about:blank"):
        super().__init__()
        self.browser_app = browser_app
        self.scroll_target = 0

        self.view = BrowserView(browser_app, self)

        self.view.urlChanged.connect(
            lambda url: self.browser_app.update_tab_ui(self)
        )
        self.view.titleChanged.connect(
            lambda title: self.browser_app.update_tab_ui(self)
        )
        self.view.iconChanged.connect(
            lambda icon: self.browser_app.update_tab_ui(self)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.load(url)

    def load(self, url):
        if not url or url == "about:blank":
            self.load_home()
            return

        self.view.setUrl(QUrl(normalize_url(url)))

    def load_home(self):
        self.view.setHtml(
            self.browser_app.build_home_html(),
            QUrl("about:blank"),
        )

    def current_url(self):
        url = self.view.url().toString()
        if not url or url == "about:blank":
            return "browseros://home"
        return url

    def current_title(self):
        title = self.view.title().strip()
        return title or "Neue Seite"

    def get_scroll_position(self, callback):
        self.view.page().runJavaScript(
            "Math.round(window.scrollY || document.documentElement.scrollTop || 0);",
            callback,
        )


class DevToolsWindow(QMainWindow):
    """A dockable Chromium DevTools window for the current Browser OS tab."""

    def __init__(self, browser_app, target_page):
        super().__init__(browser_app)
        self.browser_app = browser_app
        self.setWindowTitle("Browser OS – Entwicklerwerkzeuge")
        self.resize(1100, 720)

        self.view = QWebEngineView(self)
        self.dev_page = QWebEnginePage(browser_app.main.get_web_profile(), self.view)
        self.dev_page.setInspectedPage(target_page)
        self.view.setPage(self.dev_page)
        self.setCentralWidget(self.view)

    def closeEvent(self, event):
        self.browser_app.devtools_window = None
        super().closeEvent(event)


class ExtensionsDialog(QDialog):
    """Manage Manifest V3 extensions supported by Qt WebEngine 6.10+."""

    def __init__(self, browser_app, parent=None):
        super().__init__(parent)
        self.browser_app = browser_app
        self.setWindowTitle("Browser OS – Erweiterungen")
        self.resize(650, 520)

        layout = QVBoxLayout(self)
        info = QLabel(
            "Chrome-kompatible Manifest-V3-Erweiterungen können als ZIP-Datei "
            "oder entpackter Erweiterungsordner installiert werden.\n\n"
            "Der Google Chrome Web Store kann hier geöffnet werden. Die "
            "eigentliche Installation im Store wird von Qt WebEngine nicht "
            "direkt über die Chrome-Store-Schaltfläche übernommen; installiere "
            "die Erweiterung dafür als ZIP/Ordner."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        buttons = QHBoxLayout()
        store = QPushButton("🛍️ Google Chrome Web Store")
        store.clicked.connect(
            lambda: self.browser_app.add_tab(
                "https://chromewebstore.google.com/"
            )
        )
        install = QPushButton("➕ Erweiterung installieren")
        install.clicked.connect(self.install_extension)
        refresh = QPushButton("🔄 Aktualisieren")
        refresh.clicked.connect(self.refresh_extensions)
        close = QPushButton("Schließen")
        close.clicked.connect(self.accept)
        buttons.addWidget(store)
        buttons.addWidget(install)
        buttons.addWidget(refresh)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        self.refresh_extensions()

    def refresh_extensions(self):
        self.list.clear()
        if not WEBENGINE_EXTENSIONS_AVAILABLE:
            self.list.addItem(
                "⚠️ Erweiterungen benötigen PyQt6 / Qt WebEngine 6.10 oder neuer."
            )
            return

        try:
            manager = self.browser_app.main.get_web_profile().extensionManager()
            extensions = manager.extensions()
            if not extensions:
                self.list.addItem("Keine Erweiterungen installiert.")
                return
            for ext in extensions:
                try:
                    name = ext.name()
                except Exception:
                    name = "Unbekannte Erweiterung"
                try:
                    version = ext.version()
                except Exception:
                    version = ""
                try:
                    enabled = ext.isEnabled()
                except Exception:
                    enabled = False
                state = "aktiv" if enabled else "deaktiviert"
                self.list.addItem(f"🧩 {name}  {version}  — {state}")
        except Exception as exc:
            self.list.addItem(f"⚠️ Erweiterungen konnten nicht geladen werden: {exc}")

    def install_extension(self):
        if not WEBENGINE_EXTENSIONS_AVAILABLE:
            QMessageBox.warning(
                self,
                "Erweiterungen",
                "Deine Qt-WebEngine-Version unterstützt den Erweiterungsmanager noch nicht. "
                "Benötigt wird Qt WebEngine 6.10 oder neuer.",
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chrome-Erweiterung auswählen",
            "",
            "Erweiterungen (*.zip);;Alle Dateien (*.*)",
        )
        if not path:
            folder = QFileDialog.getExistingDirectory(
                self, "Entpackten Erweiterungsordner auswählen"
            )
            path = folder
        if not path:
            return

        try:
            manager = self.browser_app.main.get_web_profile().extensionManager()
            manager.installExtension(path)
            QMessageBox.information(
                self,
                "Erweiterung",
                "Die Installation wurde gestartet. Unterstützt werden Manifest-V3-Erweiterungen.",
            )
            QTimer.singleShot(700, self.refresh_extensions)
        except Exception as exc:
            QMessageBox.critical(self, "Erweiterung", f"Installation fehlgeschlagen:\n{exc}")



# ------------------------------------------------------------
# Start menu / custom apps
# ------------------------------------------------------------

def get_custom_apps():
    apps = settings.get("custom_apps", [])
    return apps if isinstance(apps, list) else []


def find_custom_app(app_id):
    for app in get_custom_apps():
        if app.get("id") == app_id:
            return app
    return None


def custom_app_display(app):
    return f"{app.get('icon', '📦')} {app.get('name', 'App')}"


def app_tile_styles(app):
    color = app.get("background_color", "#24283a")
    image = app.get("background_path", "") if app.get("background_mode") == "image" else ""
    if image and Path(image).exists():
        path = QUrl.fromLocalFile(image).toString().replace('"', '\\"')
        return (
            "QPushButton {"
            "border:1px solid rgba(255,255,255,35);"
            "border-radius:18px;"
            f"background-image:url({path});"
            "background-position:center;"
            "color:white;"
            "padding:14px;"
            "font-weight:600;"
            "}"
            "QPushButton:hover {border:2px solid rgba(168,85,247,190); }"
        )
    return (
        "QPushButton {"
        "border:1px solid rgba(255,255,255,35);"
        "border-radius:18px;"
        f"background:{color};"
        "color:white;"
        "padding:14px;"
        "font-weight:600;"
        "}"
        "QPushButton:hover {border:2px solid rgba(168,85,247,190); background:#30364d;}"
    )


class AppDesignFields(QWidget):
    def __init__(self, app_data=None, parent=None):
        super().__init__(parent)
        app_data = app_data or {}
        self.bg_mode = QComboBox()
        self.bg_mode.addItems(["color", "image"])
        self.bg_mode.setCurrentText(app_data.get("background_mode", "color"))

        self.bg_color = QPushButton(app_data.get("background_color", "#24283a"))
        self.bg_color.clicked.connect(self.pick_color)

        self.bg_path = QLineEdit(app_data.get("background_path", ""))
        browse = QPushButton("Auswählen…")
        browse.clicked.connect(self.pick_image)
        row = QHBoxLayout()
        row.addWidget(self.bg_path, 1)
        row.addWidget(browse)

        form = QFormLayout(self)
        form.addRow("Kachel-Hintergrund:", self.bg_mode)
        form.addRow("Hintergrundfarbe:", self.bg_color)
        form.addRow("Hintergrundbild:", row)

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.bg_color.text()), self)
        if color.isValid():
            self.bg_color.setText(color.name())

    def pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "App-Hintergrund auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self.bg_path.setText(path)
            self.bg_mode.setCurrentText("image")

    def values(self):
        return {
            "background_mode": self.bg_mode.currentText(),
            "background_color": self.bg_color.text().strip() or "#24283a",
            "background_path": self.bg_path.text().strip(),
        }


class WebAppDialog(QDialog):
    def __init__(self, main, app_data=None, initial_url="", initial_name="", parent=None):
        super().__init__(parent or main)
        self.main = main
        self.app_data = app_data or {}
        self.is_edit = bool(app_data)
        self.setWindowTitle("Website als App" if not self.is_edit else "Website-App bearbeiten")
        self.resize(650, 520)

        form = QFormLayout()
        self.name_edit = QLineEdit(self.app_data.get("name", initial_name))
        self.url_edit = QLineEdit(self.app_data.get("url", initial_url))
        self.icon_edit = QLineEdit(self.app_data.get("icon", "🌐"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(500, 2200)
        self.width_spin.setValue(int(self.app_data.get("width", 1100)))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(350, 1400)
        self.height_spin.setValue(int(self.app_data.get("height", 720)))

        form.addRow("Name:", self.name_edit)
        form.addRow("Webseite:", self.url_edit)
        form.addRow("Icon:", self.icon_edit)
        form.addRow("App-Breite:", self.width_spin)
        form.addRow("App-Höhe:", self.height_spin)

        design = AppDesignFields(self.app_data)

        hint = QLabel(
            "Die Website wird im Startmenü wie eine eigene App geöffnet – ohne die normale Browser-Adressleiste."
        )
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addWidget(design)
        layout.addWidget(buttons)
        self.design = design

    def data(self):
        url = normalize_url(self.url_edit.text().strip())
        name = self.name_edit.text().strip() or "Website"
        if not url or not url.startswith(("http://", "https://")):
            return None
        result = dict(self.app_data)
        result.update({
            "id": result.get("id") or f"webapp_{uuid.uuid4().hex}",
            "type": "web",
            "name": name,
            "url": url,
            "icon": self.icon_edit.text().strip() or "🌐",
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "pinned": True,
        })
        result.update(self.design.values())
        return result


class PCAppDialog(QDialog):
    def __init__(self, main, app_data=None, parent=None):
        super().__init__(parent or main)
        self.main = main
        self.app_data = app_data or {}
        self.is_edit = bool(app_data)
        self.setWindowTitle("PC-App erstellen" if not self.is_edit else "PC-App bearbeiten")
        self.resize(650, 500)

        self.name_edit = QLineEdit(self.app_data.get("name", ""))
        self.path_edit = QLineEdit(self.app_data.get("path", ""))
        choose = QPushButton("Datei auswählen…")
        choose.clicked.connect(self.choose_file)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(choose)
        self.icon_edit = QLineEdit(self.app_data.get("icon", "🖥️"))

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Programm:", path_row)
        form.addRow("Icon:", self.icon_edit)
        design = AppDesignFields(self.app_data)

        hint = QLabel(
            "PC-Apps werden als echte Windows-Programme gestartet. Unterstützt werden EXE, BAT, CMD, PY und LNK."
        )
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addWidget(design)
        layout.addWidget(buttons)
        self.design = design

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "PC-App auswählen",
            "",
            "Programme (*.exe *.bat *.cmd *.py *.lnk);;Alle Dateien (*.*)",
        )
        if path:
            self.path_edit.setText(path)
            if not self.name_edit.text().strip():
                self.name_edit.setText(Path(path).stem)

    def data(self):
        path = self.path_edit.text().strip()
        if not path or not Path(path).exists():
            return None
        result = dict(self.app_data)
        result.update({
            "id": result.get("id") or f"pcapp_{uuid.uuid4().hex}",
            "type": "pc",
            "name": self.name_edit.text().strip() or Path(path).stem,
            "path": path,
            "icon": self.icon_edit.text().strip() or "🖥️",
            "pinned": True,
        })
        result.update(self.design.values())
        return result


class WebAppView(QWebEngineView):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.page_obj = QWebEnginePage(main.get_web_profile(), self)
        self.setPage(self.page_obj)
        try:
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        except Exception:
            pass


class StartMenuDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent or main)
        self.main = main
        self.setObjectName("StartMenu")
        self.setWindowTitle("Browser OS Startmenü")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.resize(760, 560)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("🌍 Browser OS")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("Startmenü-Einstellungen")
        settings_btn.clicked.connect(lambda: (self.accept(), self.main.open_app("settings")))
        header.addWidget(settings_btn)
        outer.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Apps suchen…")
        self.search.textChanged.connect(self.refresh_apps)
        outer.addWidget(self.search)

        buttons = QHBoxLayout()
        web_btn = QPushButton("🌐 Website-App erstellen")
        web_btn.clicked.connect(self.create_web_app)
        pc_btn = QPushButton("🖥️ PC-App erstellen")
        pc_btn.clicked.connect(self.create_pc_app)
        buttons.addWidget(web_btn)
        buttons.addWidget(pc_btn)
        outer.addLayout(buttons)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.inner = QWidget()
        self.grid = QGridLayout(self.inner)
        self.grid.setSpacing(10)
        self.scroll.setWidget(self.inner)
        outer.addWidget(self.scroll, 1)

        self.set_style_from_settings()
        self.refresh_apps()

    def set_style_from_settings(self):
        theme = settings.get("start_menu_theme", "Glass")
        color = settings.get("start_menu_background_color", "#151827")
        path = settings.get("start_menu_background_path", "")
        mode = settings.get("start_menu_background_mode", "color")

        if theme == "Light":
            base = "#f5f6fb"
            text = "#171924"
            panel = "rgba(255,255,255,225)"
        elif theme == "Neon":
            base = "#0c0714"
            text = "#ffffff"
            panel = "rgba(28,14,45,225)"
        elif theme == "Dark":
            base = "#090b11"
            text = "#ffffff"
            panel = "rgba(17,20,29,235)"
        else:
            base = color
            text = "#ffffff"
            panel = "rgba(20,24,38,225)"

        if mode == "image" and path and Path(path).exists():
            bg = f'background-image:url("{QUrl.fromLocalFile(path).toString()}"); background-position:center; background-repeat:no-repeat; background-size:cover;'
        else:
            bg = f"background:{base};"

        self.setStyleSheet(f"""
            QDialog#StartMenu {{ {bg} color:{text}; border:1px solid rgba(255,255,255,45); border-radius:24px; }}
            QLineEdit, QPushButton {{ background:{panel}; color:{text}; border:1px solid rgba(255,255,255,35); border-radius:12px; padding:9px 12px; }}
            QLineEdit {{ background:rgba(8,10,16,125); }}
            QPushButton:hover {{ border-color:#a855f7; }}
        """)

    def filtered_apps(self):
        query = self.search.text().strip().lower()
        apps = []
        for app_id in settings.get("pinned_apps", []):
            icon, name = APP_INFO.get(app_id, ("📦", app_id))
            apps.append({
                "id": app_id, "type": "builtin", "name": name, "icon": icon,
                "background_color": "#20263a", "background_mode": "color"
            })
        for app in get_custom_apps():
            if app.get("pinned", True):
                apps.append(app)

        if query:
            apps = [a for a in apps if query in a.get("name", "").lower() or query in a.get("url", "").lower()]
        return apps

    def refresh_apps(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        apps = self.filtered_apps()
        if not apps:
            empty = QLabel("Keine angehefteten Apps gefunden.")
            self.grid.addWidget(empty, 0, 0)
            return

        for i, app in enumerate(apps):
            card = QPushButton()
            card.setMinimumSize(180, 110)
            card.setMaximumHeight(130)
            card.setText(f"{app.get('icon','📦')}\n{app.get('name','App')}")
            card.clicked.connect(lambda checked=False, a=app: self.launch_app(a))
            card.setStyleSheet(app_tile_styles(app))
            self.grid.addWidget(card, i // 3, i % 3)

    def launch_app(self, app):
        self.accept()
        if app.get("type") == "builtin":
            self.main.open_app(app.get("id"))
        else:
            self.main.open_custom_app(app)

    def create_web_app(self):
        dialog = WebAppDialog(self.main, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        app = dialog.data()
        if not app:
            QMessageBox.warning(self, "Website-App", "Bitte eine gültige HTTP- oder HTTPS-Webseite eingeben.")
            return
        settings.setdefault("custom_apps", []).append(app)
        save_json(SETTINGS_FILE, settings)
        self.refresh_apps()
        QMessageBox.information(self, "Website-App", f"„{app['name']}“ wurde ins Startmenü angeheftet.")

    def create_pc_app(self):
        dialog = PCAppDialog(self.main, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        app = dialog.data()
        if not app:
            QMessageBox.warning(self, "PC-App", "Bitte eine gültige Programmdatei auswählen.")
            return
        settings.setdefault("custom_apps", []).append(app)
        save_json(SETTINGS_FILE, settings)
        self.refresh_apps()
        QMessageBox.information(self, "PC-App", f"„{app['name']}“ wurde ins Startmenü angeheftet.")


class BrowserApp(QWidget):
    def __init__(self, main, virtual_window):
        super().__init__()
        self.main = main
        self.virtual_window = virtual_window
        self.profile = main.get_web_profile()
        self.devtools_window = None

        root = QVBoxLayout(self)
        root.setContentsMargins(7, 7, 7, 7)
        root.setSpacing(6)

        nav = QHBoxLayout()

        self.back_btn = QToolButton()
        self.back_btn.setText("←")
        self.back_btn.setToolTip("Zurück")

        self.forward_btn = QToolButton()
        self.forward_btn.setText("→")
        self.forward_btn.setToolTip("Vorwärts")

        self.reload_btn = QToolButton()
        self.reload_btn.setText("⟳")
        self.reload_btn.setToolTip("Neu laden")

        self.home_btn = QToolButton()
        self.home_btn.setText("🏠")
        self.home_btn.setToolTip("Startseite")

        self.address = QLineEdit()
        self.address.setPlaceholderText("Adresse oder Suche…")
        self.address.returnPressed.connect(self.go_address)

        self.bookmark_btn = QToolButton()
        self.bookmark_btn.setText("⭐")
        self.bookmark_btn.setToolTip("Lesezeichen")

        self.downloads_btn = QToolButton()
        self.downloads_btn.setText("📥")
        self.downloads_btn.setToolTip("Downloads öffnen")

        self.save_session_btn = QToolButton()
        self.save_session_btn.setText("💾")
        self.save_session_btn.setToolTip("Sitzung speichern")

        self.pin_app_btn = QToolButton()
        self.pin_app_btn.setText("📌")
        self.pin_app_btn.setToolTip("Aktuelle Webseite als Start-App anheften")

        self.translate_btn = QToolButton()
        self.translate_btn.setText("A文")
        self.translate_btn.setToolTip("Webseite übersetzen")

        self.more_btn = QToolButton()
        self.more_btn.setText("⋮")

        for widget in (
            self.back_btn,
            self.forward_btn,
            self.reload_btn,
            self.home_btn,
        ):
            nav.addWidget(widget)

        nav.addWidget(self.address, 1)
        nav.addWidget(self.bookmark_btn)
        nav.addWidget(self.downloads_btn)
        nav.addWidget(self.pin_app_btn)
        nav.addWidget(self.translate_btn)
        nav.addWidget(self.save_session_btn)
        nav.addWidget(self.more_btn)

        # Die Tabs sind bewusst vom Webseiten-Stack getrennt.
        # Dadurch ist die Reihenfolge wirklich:
        # 1. Tabs
        # 2. Navigation / Adressleiste
        # 3. Webseite
        self.tabs = QTabBar()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setExpanding(False)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)

        self.tab_pages = QStackedWidget()

        plus = QToolButton()
        plus.setText("+")
        plus.setToolTip("Neuer Tab")
        plus.clicked.connect(lambda: self.add_tab())

        tabs_row = QHBoxLayout()
        tabs_row.setContentsMargins(0, 0, 0, 0)
        tabs_row.setSpacing(6)
        tabs_row.addWidget(self.tabs, 1)
        tabs_row.addWidget(plus)

        # Exakt die gewünschte Anordnung:
        # TAB-LEISTE -> NAVIGATION/ADRESSLEISTE -> WEBSEITE
        root.addLayout(tabs_row)
        root.addLayout(nav)
        root.addWidget(self.tab_pages, 1)

        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.reload_btn.clicked.connect(self.reload)
        self.home_btn.clicked.connect(self.home)
        self.bookmark_btn.clicked.connect(self.bookmark_current)
        self.downloads_btn.clicked.connect(
            lambda: open_external(DOWNLOADS_DIR)
        )
        self.save_session_btn.clicked.connect(self.save_session)
        self.pin_app_btn.clicked.connect(self.pin_current_as_app)
        self.translate_btn.clicked.connect(self.translate_current_page)
        self.more_btn.clicked.connect(self.show_more)

        self.add_tab()

    def add_tab(self, url="about:blank"):
        tab = BrowserTab(self, url)
        index = self.tabs.addTab("Startseite")
        self.tab_pages.addWidget(tab)
        self.tabs.setCurrentIndex(index)
        self.tab_pages.setCurrentIndex(index)
        return tab

    def current_tab(self):
        widget = self.tab_pages.currentWidget()
        return widget if isinstance(widget, BrowserTab) else None

    def close_tab(self, index):
        if self.tabs.count() <= 1:
            return
        widget = self.tab_pages.widget(index)
        self.tabs.removeTab(index)
        if widget:
            self.tab_pages.removeWidget(widget)
            widget.deleteLater()

    def tab_changed(self, index):
        if index < 0:
            return
        self.tab_pages.setCurrentIndex(index)
        tab = self.tab_pages.widget(index)
        self.update_tab_ui(tab)

    def update_tab_ui(self, tab):
        if not isinstance(tab, BrowserTab):
            return

        index = self.tab_pages.indexOf(tab)
        if index < 0:
            return

        url = tab.current_url()
        title = tab.current_title()

        if url == "browseros://home":
            self.tabs.setTabText(index, "Startseite")
            if tab == self.current_tab():
                self.address.setText("")
        else:
            short_title = title if len(title) <= 22 else title[:20] + "…"
            self.tabs.setTabText(index, short_title)
            if tab == self.current_tab():
                self.address.setText(url)

            if url.startswith(("http://", "https://")):
                add_history(url, title)

    def go_address(self):
        tab = self.current_tab()
        if not tab:
            return

        value = self.address.text().strip()
        if not value:
            return

        tab.load(value)

    def go_back(self):
        tab = self.current_tab()
        if tab:
            tab.view.back()

    def go_forward(self):
        tab = self.current_tab()
        if tab:
            tab.view.forward()

    def reload(self):
        tab = self.current_tab()
        if tab:
            tab.view.reload()

    def home(self):
        tab = self.current_tab()
        if tab:
            tab.scroll_target = 0
            tab.load_home()

    def bookmark_current(self):
        tab = self.current_tab()
        if not tab:
            return

        url = tab.current_url()
        if url.startswith(("http://", "https://")):
            add_bookmark(url, tab.current_title())
            QMessageBox.information(self, APP_NAME, "Lesezeichen gespeichert.")

    def pin_current_as_app(self):
        tab = self.current_tab()
        if not tab:
            return
        url = tab.current_url()
        if not url.startswith(("http://", "https://")):
            QMessageBox.information(self, APP_NAME, "Öffne zuerst eine normale HTTP/HTTPS-Webseite.")
            return
        existing = next((a for a in get_custom_apps() if a.get("type") == "web" and a.get("url") == url), None)
        dialog = WebAppDialog(
            self.main,
            app_data=existing,
            initial_url=url,
            initial_name=tab.current_title(),
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        app = dialog.data()
        if not app:
            QMessageBox.warning(self, APP_NAME, "Bitte eine gültige HTTP/HTTPS-Webseite eingeben.")
            return
        apps = settings.setdefault("custom_apps", [])
        if existing:
            existing.update(app)
        else:
            apps.append(app)
        save_json(SETTINGS_FILE, settings)
        QMessageBox.information(self, APP_NAME, f"„{app['name']}“ wurde als App im Startmenü angeheftet.")

    def translate_current_page(self):
        tab = self.current_tab()
        if not tab:
            return

        url = tab.current_url()
        if not url.startswith(("http://", "https://")):
            QMessageBox.information(
                self,
                "Webseite übersetzen",
                "Öffne zuerst eine normale HTTP/HTTPS-Webseite.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("🌐 Webseite übersetzen")
        dialog.resize(360, 180)
        layout = QVBoxLayout(dialog)

        label = QLabel("Zielsprache auswählen:")
        layout.addWidget(label)

        combo = QComboBox()
        for code, name in TRANSLATION_LANGUAGES:
            combo.addItem(name, code)
        current = get_language_code()
        idx = combo.findData(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        layout.addWidget(combo)

        privacy = QLabel(
            "Hinweis: Die Übersetzung wird über Google Translate geöffnet. "
            "Browser OS selbst speichert dabei keine Übersetzungsprofile."
        )
        privacy.setWordWrap(True)
        layout.addWidget(privacy)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        target = combo.currentData() or "de"
        translated_url = translate_url_with_google(url, target)
        self.add_tab(translated_url)

    def show_more(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Browser")
        dialog.resize(380, 470)

        layout = QVBoxLayout(dialog)

        actions = [
            ("➕ Neuer Tab", lambda: self.add_tab()),
            ("🔎 Zoom +", lambda: self.zoom(0.1)),
            ("🔍 Zoom -", lambda: self.zoom(-0.1)),
            ("🔎 Seite durchsuchen", self.find_text),
            ("⭐ Lesezeichen", self.bookmark_current),
            ("📥 Downloads öffnen", lambda: open_external(DOWNLOADS_DIR)),
            ("📌 Aktuelle Webseite als App anheften", self.pin_current_as_app),
            ("🌐 Webseite übersetzen", self.translate_current_page),
            ("📥 Browser-Daten importieren", self.main.open_browser_import),
            ("🖥️ Browser maximieren", self.virtual_window.toggle_maximize),
            ("💾 Sitzung speichern", self.save_session),
            ("🧩 Erweiterungen", self.show_extensions),
            ("🛠️ Entwicklerwerkzeuge (F12)", self.toggle_devtools),
            ("🕘 Verlauf", lambda: self.main.open_app("history")),
            ("⭐ Lesezeichen öffnen", lambda: self.main.open_app("bookmarks")),
            ("💾 Sitzungen", lambda: self.main.open_app("sessions")),
        ]

        for label, callback in actions:
            button = QPushButton(label)
            button.clicked.connect(callback)
            layout.addWidget(button)

        close = QPushButton("Schließen")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)

        dialog.exec()

    def zoom(self, delta):
        tab = self.current_tab()
        if tab:
            tab.view.setZoomFactor(
                max(0.25, min(5.0, tab.view.zoomFactor() + delta))
            )

    def find_text(self):
        tab = self.current_tab()
        if not tab:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Seite durchsuchen")
        layout = QVBoxLayout(dialog)

        edit = QLineEdit()
        edit.setPlaceholderText("Suchtext…")
        layout.addWidget(edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted and edit.text().strip():
            tab.view.findText(edit.text().strip())

    def toggle_devtools(self):
        if not settings.get("developer_mode", False):
            QMessageBox.information(
                self,
                "Entwicklermodus",
                "Aktiviere zuerst den Entwicklermodus in den Browser OS Einstellungen.",
            )
            return

        tab = self.current_tab()
        if not tab:
            return

        if self.devtools_window is not None:
            try:
                self.devtools_window.close()
            except Exception:
                pass
            self.devtools_window = None
            return

        self.devtools_window = DevToolsWindow(self, tab.view.page())
        self.devtools_window.show()
        self.devtools_window.raise_()
        self.devtools_window.activateWindow()

    def show_extensions(self):
        dialog = ExtensionsDialog(self, self)
        dialog.exec()

    def save_session(self):
        name, ok = self.main.simple_input("Browser-Sitzung speichern", "Name:")
        if not ok or not name.strip():
            return

        session = {
            "name": name.strip(),
            "created": now_string(),
            "workspace": self.virtual_window.workspace,
            "window": {
                "x": self.virtual_window.x(),
                "y": self.virtual_window.y(),
                "w": self.virtual_window.width(),
                "h": self.virtual_window.height(),
            },
            "tabs": [],
        }

        remaining = self.tabs.count()
        collected = [None] * remaining

        if remaining == 0:
            self.write_session(session)
            return

        def done():
            session["tabs"] = [x for x in collected if x is not None]
            self.write_session(session)

        for i in range(remaining):
            tab = self.tab_pages.widget(i)

            if not isinstance(tab, BrowserTab):
                remaining -= 1
                continue

            def got_scroll(value, tab=tab, index=i):
                nonlocal remaining

                collected[index] = {
                    "url": tab.current_url(),
                    "title": tab.current_title(),
                    "scroll_y": int(value or 0),
                    "zoom": float(tab.view.zoomFactor()),
                    "active": self.tab_pages.currentWidget() is tab,
                }

                remaining -= 1
                if remaining <= 0:
                    done()

            tab.get_scroll_position(got_scroll)

    def write_session(self, session):
        file_name = safe_file_name(session["name"]) + ".bos_session.json"
        path = SESSIONS_DIR / file_name
        save_json(path, session)
        QMessageBox.information(
            self,
            APP_NAME,
            f"Sitzung gespeichert:\n{path}",
        )

    def build_home_html(self):
        accent = settings.get("accent", "#a855f7")
        color = settings.get("desktop_color", "#11131a")
        theme = settings.get("theme", "Purple Dark")
        mode = settings.get("wallpaper_mode", "color")
        wallpaper = settings.get("wallpaper_path", "")

        if theme == "Light":
            text_color = "#181a22"
            panel = "rgba(255,255,255,.82)"
        else:
            text_color = "#ffffff"
            panel = "rgba(17,20,32,.72)"

        background = f"background:{color};"
        video_html = ""

        if mode == "image" and wallpaper and Path(wallpaper).exists():
            image_url = QUrl.fromLocalFile(wallpaper).toString()
            background = (
                f"background-image:url('{image_url}');"
                "background-size:cover;"
                "background-position:center;"
                "background-attachment:fixed;"
            )

        if mode == "video" and wallpaper and Path(wallpaper).exists():
            video_url = QUrl.fromLocalFile(wallpaper).toString()
            video_html = (
                f'<video class="bg-video" autoplay muted loop playsinline>'
                f'<source src="{video_url}"></video>'
            )

        pinned = []
        for app_id in settings.get("pinned_apps", []):
            icon, name = APP_INFO.get(app_id, ("📦", app_id))
            pinned.append(
                f'<div class="app-card">'
                f'<div class="app-icon">{icon}</div>'
                f'<div>{name}</div>'
                f'</div>'
            )

        recent = []
        for item in history[:8]:
            title = item.get("title", item.get("url", "Webseite"))
            url = item.get("url", "")
            recent.append(
                f'<div class="recent-card" data-url="{url.replace(chr(34), "&quot;")}">'
                f'<b>{title[:55]}</b>'
                f'<small>{url[:100]}</small>'
                f'</div>'
            )

        pinned_html = ""
        if settings.get("show_pinned", True):
            pinned_html = (
                '<section><h2>📌 Angeheftete Apps</h2>'
                '<div class="apps">'
                + "".join(pinned)
                + "</div></section>"
            )

        recent_html = ""
        if settings.get("show_recent", True):
            recent_html = (
                '<section><h2>🕘 Letzte Webseiten</h2>'
                '<div class="recent-grid">'
                + (
                    "".join(recent)
                    if recent
                    else '<div class="muted">Noch keine Webseiten besucht.</div>'
                )
                + "</div></section>"
            )

        clock_html = (
            '<div class="clock" id="clock"></div>'
            if settings.get("show_clock", True)
            else ""
        )

        search_template = settings.get(
            "custom_search_url",
            "https://www.google.com/search?q={query}",
        )

        return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Browser OS Startseite</title>
<style>
* {{ box-sizing:border-box; }}
html,body {{ margin:0; min-height:100%; }}
body {{
    {background}
    color:{text_color};
    font-family:"Segoe UI",Arial,sans-serif;
    min-height:100vh;
}}
.bg-video {{
    position:fixed;
    inset:0;
    width:100%;
    height:100%;
    object-fit:cover;
    z-index:-2;
}}
body::after {{
    content:"";
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.28);
    z-index:-1;
}}
.wrap {{
    max-width:1100px;
    margin:0 auto;
    padding:40px;
}}
.hero {{
    text-align:center;
    padding-top:25px;
}}
.logo {{ font-size:70px; }}
h1 {{
    font-size:42px;
    margin:2px 0;
}}
.subtitle {{
    opacity:.7;
    margin-bottom:15px;
}}
.clock {{
    opacity:.78;
    margin-bottom:20px;
}}
.search {{
    max-width:780px;
    margin:0 auto 25px;
    display:flex;
    border-radius:22px;
    overflow:hidden;
    background:rgba(15,17,27,.86);
    border:1px solid rgba(255,255,255,.14);
}}
.search input {{
    flex:1;
    border:0;
    outline:0;
    color:white;
    background:transparent;
    padding:17px 20px;
    font-size:18px;
}}
.search button {{
    border:0;
    background:{accent};
    color:white;
    width:75px;
    font-size:22px;
}}
section {{
    background:{panel};
    border:1px solid rgba(255,255,255,.1);
    border-radius:21px;
    padding:20px;
    margin-top:15px;
    backdrop-filter:blur(18px);
}}
h2 {{
    font-size:18px;
    margin:0 0 15px;
}}
.apps {{
    display:flex;
    flex-wrap:wrap;
    gap:12px;
}}
.app-card {{
    min-width:135px;
    text-align:center;
    padding:16px;
    border-radius:16px;
    background:rgba(255,255,255,.06);
}}
.app-icon {{
    font-size:35px;
    margin-bottom:5px;
}}
.recent-grid {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:10px;
}}
.recent-card {{
    padding:14px;
    border-radius:14px;
    background:rgba(255,255,255,.06);
    cursor:pointer;
    overflow:hidden;
}}
.recent-card:hover,
.app-card:hover {{
    background:rgba(255,255,255,.11);
}}
.recent-card small {{
    display:block;
    margin-top:5px;
    opacity:.55;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}}
.muted {{
    opacity:.55;
}}
.footer {{
    text-align:center;
    opacity:.42;
    margin:25px 0;
}}
</style>
</head>
<body>
{video_html}
<div class="wrap">
    <div class="hero">
        <div class="logo">🌍</div>
        <h1>Browser OS</h1>
        <div class="subtitle">Dein Browser. Dein Desktop. Deine Regeln.</div>
        <div class="privacy">🌍 Kein Tracking • Keine Spyware • Open-Source Browser</div>
        {clock_html}

        <form class="search" onsubmit="doSearch(event)">
            <input id="search" autofocus placeholder="Adresse oder Suche…">
            <button>🔎</button>
        </form>
    </div>

    {pinned_html}
    {recent_html}

    <div class="footer">
        Browser OS {VERSION} • Custom Startseite
    </div>
</div>

<script>
const SEARCH_TEMPLATE = {json.dumps(search_template)};

function doSearch(event) {{
    event.preventDefault();

    const value = document.getElementById("search").value.trim();
    if (!value) return;

    let target;

    if (
        value.includes("://") ||
        value.includes(".") ||
        value.startsWith("localhost")
    ) {{
        target = value.includes("://") ? value : "https://" + value;
    }} else {{
        target = SEARCH_TEMPLATE.replace(
            "{{query}}",
            encodeURIComponent(value)
        );
    }}

    window.location.href = target;
}}

document.querySelectorAll(".recent-card").forEach(card => {{
    card.addEventListener("click", () => {{
        const url = card.getAttribute("data-url");
        if (url) window.location.href = url;
    }});
}});

function updateClock() {{
    const clock = document.getElementById("clock");
    if (!clock) return;
    const d = new Date();
    clock.textContent =
        d.toLocaleDateString() + " • " + d.toLocaleTimeString();
}}

updateClock();
setInterval(updateClock, 1000);
</script>
</body>
</html>
"""



# ------------------------------------------------------------
# Browser data import
# ------------------------------------------------------------

BROWSER_IMPORTS = {
    "Google Chrome": Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data",
    "Microsoft Edge": Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "User Data",
    "Brave": Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "User Data",
    "Vivaldi": Path(os.environ.get("LOCALAPPDATA", "")) / "Vivaldi" / "User Data",
    "Opera": Path(os.environ.get("APPDATA", "")) / "Opera Software" / "Opera Stable",
    "Firefox": Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles",
}


def _dedupe_add(items, value, key):
    if not value:
        return
    value = str(value).strip()
    if not value:
        return
    if not any(str(item.get(key, "")).strip() == value for item in items):
        items.append(value)


def _copy_locked_db(source):
    try:
        if not source.exists():
            return None
        fd, temp_name = tempfile.mkstemp(prefix="browseros_import_", suffix=".sqlite")
        os.close(fd)
        target = Path(temp_name)
        shutil.copy2(source, target)
        return target
    except Exception:
        return None


def _chromium_profile_dirs(root):
    if not root.exists():
        return []
    dirs = []
    for name in ["Default"]:
        path = root / name
        if path.is_dir():
            dirs.append(path)
    try:
        for path in sorted(root.glob("Profile *")):
            if path.is_dir() and path not in dirs:
                dirs.append(path)
    except Exception:
        pass
    if root.name in {"Opera Stable", "Opera GX Stable"}:
        dirs = [root]
    return dirs


def _read_chromium_bookmarks(profile):
    path = profile / "Bookmarks"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    result = []

    def walk(node, folder_path=""):
        if isinstance(node, dict):
            if node.get("type") == "url":
                url = str(node.get("url", "")).strip()
                title = str(node.get("name", "")).strip() or url
                if url.startswith(("http://", "https://")):
                    result.append({
                        "title": title,
                        "url": url,
                        "folder": folder_path,
                        "source": "Chromium",
                    })
            for child in node.get("children", []) or []:
                child_name = str(node.get("name", "")).strip()
                next_folder = folder_path
                if node.get("type") == "folder" and child_name:
                    next_folder = f"{folder_path}/{child_name}".strip("/")
                walk(child, next_folder)
        elif isinstance(node, list):
            for child in node:
                walk(child, folder_path)

    roots = data.get("roots", {})
    for root_name, root_value in roots.items():
        if isinstance(root_value, dict):
            walk(root_value, root_name)
    return result


def _chromium_time_to_text(value):
    try:
        # Chromium stores microseconds since 1601-01-01 UTC.
        unix_seconds = (int(value) / 1_000_000) - 11644473600
        return datetime.fromtimestamp(unix_seconds).strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return now_string()


def _read_chromium_history(profile):
    source = profile / "History"
    copied = _copy_locked_db(source)
    if not copied:
        return []
    result = []
    conn = None
    try:
        conn = sqlite3.connect(str(copied))
        rows = conn.execute(
            "SELECT url, title, last_visit_time FROM urls "
            "WHERE url LIKE 'http://%' OR url LIKE 'https://%' "
            "ORDER BY last_visit_time DESC LIMIT 1000"
        ).fetchall()
        for url, title, last_visit_time in rows:
            result.append({
                "url": str(url),
                "title": str(title or url),
                "visited": _chromium_time_to_text(last_visit_time),
                "source": "Chromium",
            })
    except Exception:
        pass
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
        try:
            copied.unlink(missing_ok=True)
        except Exception:
            pass
    return result


def _read_firefox_profile(profile):
    bookmarks = []
    history_items = []
    source = profile / "places.sqlite"
    copied = _copy_locked_db(source)
    if not copied:
        return bookmarks, history_items
    conn = None
    try:
        conn = sqlite3.connect(str(copied))
        rows = conn.execute(
            "SELECT p.url, p.title, p.last_visit_date FROM moz_places p "
            "WHERE p.url LIKE 'http://%' OR p.url LIKE 'https://%' "
            "ORDER BY p.last_visit_date DESC LIMIT 1000"
        ).fetchall()
        for url, title, last_visit_date in rows:
            visited = now_string()
            try:
                if last_visit_date:
                    visited = datetime.fromtimestamp(int(last_visit_date) / 1_000_000).strftime("%d.%m.%Y %H:%M:%S")
            except Exception:
                pass
            history_items.append({
                "url": str(url),
                "title": str(title or url),
                "visited": visited,
                "source": "Firefox",
            })

        bookmark_query = (
            "SELECT p.url, COALESCE(b.title, p.title, p.url) "
            "FROM moz_bookmarks b JOIN moz_places p ON p.id = b.fk "
            "WHERE p.url LIKE 'http://%' OR p.url LIKE 'https://%' "
            "ORDER BY b.dateAdded DESC LIMIT 2000"
        )
        for url, title in conn.execute(bookmark_query).fetchall():
            bookmarks.append({
                "title": str(title or url),
                "url": str(url),
                "folder": "Firefox",
                "source": "Firefox",
            })
    except Exception:
        pass
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
        try:
            copied.unlink(missing_ok=True)
        except Exception:
            pass
    return bookmarks, history_items


def import_browser_data(browser_name, import_bookmarks=True, import_history=True):
    """Import bookmarks/history without touching passwords or cookies."""
    root = BROWSER_IMPORTS.get(browser_name)
    if not root or not root.exists():
        return {"bookmarks": 0, "history": 0, "profiles": 0, "found": False}

    imported_bookmarks = []
    imported_history = []
    profiles = 0

    if browser_name == "Firefox":
        profile_dirs = [p for p in sorted(root.iterdir()) if p.is_dir() and (p / "places.sqlite").exists()]
        for profile in profile_dirs:
            profiles += 1
            bmarks, hist = _read_firefox_profile(profile)
            imported_bookmarks.extend(bmarks)
            imported_history.extend(hist)
    else:
        profile_dirs = _chromium_profile_dirs(root)
        for profile in profile_dirs:
            profiles += 1
            if import_bookmarks:
                imported_bookmarks.extend(_read_chromium_bookmarks(profile))
            if import_history:
                imported_history.extend(_read_chromium_history(profile))

    if browser_name == "Firefox" and import_bookmarks:
        pass
    elif not import_bookmarks:
        imported_bookmarks = []

    if not import_history:
        imported_history = []

    if import_bookmarks:
        existing = {str(item.get("url", "")).strip() for item in bookmarks}
        for item in imported_bookmarks:
            url = str(item.get("url", "")).strip()
            if url and url not in existing:
                bookmarks.append({
                    "url": url,
                    "title": item.get("title", url),
                    "added": now_string(),
                    "source": item.get("source", browser_name),
                })
                existing.add(url)
        save_json(BOOKMARKS_FILE, bookmarks)

    if import_history:
        existing = {(str(item.get("url", "")), str(item.get("title", ""))) for item in history}
        # Newest imported items first, while keeping the local history intact.
        to_add = []
        for item in imported_history:
            key = (str(item.get("url", "")), str(item.get("title", "")))
            if key not in existing:
                to_add.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", item.get("url", "")),
                    "visited": item.get("visited", now_string()),
                    "source": item.get("source", browser_name),
                })
                existing.add(key)
        history[:0] = to_add
        del history[5000:]
        save_json(HISTORY_FILE, history)

    return {
        "bookmarks": len(imported_bookmarks) if import_bookmarks else 0,
        "history": len(imported_history) if import_history else 0,
        "profiles": profiles,
        "found": True,
    }


class BrowserImportDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent or main)
        self.main = main
        self.setWindowTitle("Browser OS – Browser-Daten importieren")
        self.resize(620, 420)

        layout = QVBoxLayout(self)
        title = QLabel("📥 Daten aus einem anderen Browser importieren")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        info = QLabel(
            "Importiert werden je nach Browser Lesezeichen und Verlauf. "
            "Passwörter, Cookies und private Daten werden absichtlich nicht kopiert."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.browser_combo = QComboBox()
        for name, root in BROWSER_IMPORTS.items():
            self.browser_combo.addItem(name, str(root))
        self.bookmarks_box = QCheckBox("Lesezeichen importieren")
        self.bookmarks_box.setChecked(True)
        self.history_box = QCheckBox("Verlauf importieren")
        self.history_box.setChecked(True)
        form.addRow("Browser:", self.browser_combo)
        form.addRow("", self.bookmarks_box)
        form.addRow("", self.history_box)
        layout.addLayout(form)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()

        buttons = QDialogButtonBox()
        import_button = buttons.addButton("📥 Importieren", QDialogButtonBox.ButtonRole.AcceptRole)
        close_button = buttons.addButton("Schließen", QDialogButtonBox.ButtonRole.RejectRole)
        import_button.clicked.connect(self.start_import)
        close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.browser_combo.currentIndexChanged.connect(self.check_available)
        self.check_available()

    def check_available(self):
        root = Path(self.browser_combo.currentData() or "")
        if root.exists():
            self.status.setText(f"✅ Gefunden: {root}")
        else:
            self.status.setText("⚠️ Dieser Browser wurde auf diesem PC nicht gefunden.")

    def start_import(self):
        name = self.browser_combo.currentText()
        root = Path(self.browser_combo.currentData() or "")
        if not root.exists():
            QMessageBox.warning(self, "Browser OS", "Der ausgewählte Browser wurde nicht gefunden.")
            return
        if not (self.bookmarks_box.isChecked() or self.history_box.isChecked()):
            QMessageBox.information(self, "Browser OS", "Wähle mindestens eine Datenart aus.")
            return

        result = import_browser_data(
            name,
            import_bookmarks=self.bookmarks_box.isChecked(),
            import_history=self.history_box.isChecked(),
        )
        if not result.get("found"):
            QMessageBox.warning(self, "Browser OS", "Es wurden keine Browser-Daten gefunden.")
            return

        self.status.setText(
            f"✅ Fertig. Profile: {result['profiles']} • "
            f"Lesezeichen gelesen: {result['bookmarks']} • "
            f"Verlauf gelesen: {result['history']}"
        )
        QMessageBox.information(
            self,
            "Browser OS",
            "Der Import ist abgeschlossen. Passwörter und Cookies wurden nicht übernommen.",
        )
        self.main.refresh_everything()


# ------------------------------------------------------------
# Website translator
# ------------------------------------------------------------

TRANSLATION_LANGUAGES = [
    ("de", "Deutsch"),
    ("en", "English"),
    ("fr", "Français"),
    ("es", "Español"),
    ("it", "Italiano"),
    ("pt", "Português"),
    ("nl", "Nederlands"),
    ("pl", "Polski"),
    ("tr", "Türkçe"),
    ("ru", "Русский"),
    ("uk", "Українська"),
    ("ar", "العربية"),
    ("hi", "हिन्दी"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("zh-CN", "简体中文"),
    ("zh-TW", "繁體中文"),
]


def translate_url_with_google(url, target_language):
    encoded_url = quote(url, safe="")
    return (
        "https://translate.google.com/translate?sl=auto&tl="
        f"{quote(target_language, safe='')}&u={encoded_url}"
    )

# ------------------------------------------------------------
# Settings dialogs
# ------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.setWindowTitle(
            "Browser OS Einstellungen"
            if get_language_code() == "de"
            else "Browser OS Settings"
        )
        self.resize(720, 650)

        tabs = QTabWidget()

        # Appearance
        appearance = QWidget()
        form = QFormLayout(appearance)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Purple Dark", "Midnight", "Ocean", "Light"])
        self.theme_combo.setCurrentText(settings.get("theme", "Purple Dark"))

        self.color_button = QPushButton(settings.get("accent", "#a855f7"))
        self.color_button.clicked.connect(self.pick_color)

        self.bg_color_button = QPushButton(settings.get("desktop_color", "#11131a"))
        self.bg_color_button.clicked.connect(self.pick_bg_color)

        self.bg_mode = QComboBox()
        self.bg_mode.addItems(["color", "image", "video"])
        self.bg_mode.setCurrentText(settings.get("wallpaper_mode", "color"))

        self.wallpaper_path = QLineEdit(settings.get("wallpaper_path", ""))
        browse = QPushButton("Auswählen…")
        browse.clicked.connect(self.choose_wallpaper)
        wp_row = QHBoxLayout()
        wp_row.addWidget(self.wallpaper_path)
        wp_row.addWidget(browse)

        form.addRow("Theme:", self.theme_combo)
        form.addRow("Akzentfarbe:", self.color_button)
        form.addRow("Desktopfarbe:", self.bg_color_button)
        form.addRow("Hintergrundtyp:", self.bg_mode)
        form.addRow("Bild / Video:", wp_row)

        self.start_menu_theme = QComboBox()
        self.start_menu_theme.addItems(["Glass", "Dark", "Light", "Neon"])
        self.start_menu_theme.setCurrentText(settings.get("start_menu_theme", "Glass"))

        self.start_menu_bg_color = QPushButton(settings.get("start_menu_background_color", "#151827"))
        self.start_menu_bg_color.clicked.connect(self.pick_start_menu_color)

        self.start_menu_bg_mode = QComboBox()
        self.start_menu_bg_mode.addItems(["color", "image"])
        self.start_menu_bg_mode.setCurrentText(settings.get("start_menu_background_mode", "color"))

        self.start_menu_bg_path = QLineEdit(settings.get("start_menu_background_path", ""))
        sm_browse = QPushButton("Auswählen…")
        sm_browse.clicked.connect(self.choose_start_menu_background)
        sm_row = QHBoxLayout()
        sm_row.addWidget(self.start_menu_bg_path, 1)
        sm_row.addWidget(sm_browse)

        form.addRow("Startmenü-Thema:", self.start_menu_theme)
        form.addRow("Startmenü-Hintergrund:", self.start_menu_bg_mode)
        form.addRow("Startmenü-Farbe:", self.start_menu_bg_color)
        form.addRow("Startmenü-Bild:", sm_row)

        # Start page
        start = QWidget()
        start_form = QFormLayout(start)

        self.search_combo = QComboBox()
        self.search_combo.addItems([
            "Google",
            "Bing",
            "Yahoo",
            "DuckDuckGo",
            "Brave Search",
            "Startpage",
            "Ecosia",
            "Eigene",
        ])
        self.search_combo.setCurrentText(settings.get("search_engine", "Google"))

        self.custom_search = QLineEdit(settings.get(
            "custom_search_url", "https://www.google.com/search?q={query}"
        ))

        def update_custom_search_state():
            custom = self.search_combo.currentText() == "Eigene"
            self.custom_search.setEnabled(custom)
            if not custom:
                built_in = {
                    "Google": "https://www.google.com/search?q={query}",
                    "Bing": "https://www.bing.com/search?q={query}",
                    "Yahoo": "https://search.yahoo.com/search?p={query}",
                    "DuckDuckGo": "https://duckduckgo.com/?q={query}",
                    "Brave Search": "https://search.brave.com/search?q={query}",
                    "Startpage": "https://www.startpage.com/sp/search?query={query}",
                    "Ecosia": "https://www.ecosia.org/search?q={query}",
                }
                if self.search_combo.currentText() in built_in:
                    self.custom_search.setText(
                        built_in[self.search_combo.currentText()]
                    )

        self.search_combo.currentTextChanged.connect(
            lambda _: update_custom_search_state()
        )
        update_custom_search_state()

        self.show_clock = QCheckBox("Uhr anzeigen")
        self.show_clock.setChecked(settings.get("show_clock", True))
        self.show_recent = QCheckBox("Letzte Webseiten anzeigen")
        self.show_recent.setChecked(settings.get("show_recent", True))
        self.show_pinned = QCheckBox("Angeheftete Apps anzeigen")
        self.show_pinned.setChecked(settings.get("show_pinned", True))
        self.show_widgets = QCheckBox("Widgets aktivieren")
        self.show_widgets.setChecked(settings.get("show_widgets", True))

        self.pinned_list = QListWidget()
        self.pinned_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        current_pinned = settings.get("pinned_apps", [])
        for app_id, (icon, name) in APP_INFO.items():
            item = QListWidgetItem(f"{icon}  {name}")
            item.setData(Qt.ItemDataRole.UserRole, app_id)
            self.pinned_list.addItem(item)
            if app_id in current_pinned:
                item.setSelected(True)

        pinned_buttons = QHBoxLayout()
        all_btn = QPushButton("Alle")
        none_btn = QPushButton("Keine")
        all_btn.clicked.connect(self.select_all_pinned)
        none_btn.clicked.connect(self.select_none_pinned)
        pinned_buttons.addWidget(all_btn)
        pinned_buttons.addWidget(none_btn)
        pinned_buttons.addStretch()

        start_form.addRow("Suchmaschine:", self.search_combo)
        start_form.addRow("Eigene Such-URL:", self.custom_search)
        start_form.addRow(
            "",
            QLabel(
                "Standardmodus: Diese Suchmaschine wird für neue Suchen verwendet."
                if settings.get("search_engine_mode", "standard") == "standard"
                else "Testmodus: Die zuletzt getestete Suchmaschine wurde nicht als Standard gespeichert."
            ),
        )
        start_form.addRow(self.show_clock)
        start_form.addRow(self.show_recent)
        start_form.addRow(self.show_pinned)
        start_form.addRow(self.show_widgets)
        start_form.addRow("Startseiten-Apps:", self.pinned_list)
        start_form.addRow(pinned_buttons)

        # General
        general = QWidget()
        general_form = QFormLayout(general)

        self.language_combo = QComboBox()

        for language_code, language_name in LANGUAGE_OPTIONS:
            self.language_combo.addItem(language_name, language_code)

        saved_language = settings.get("language", "auto")
        idx = self.language_combo.findData(saved_language)
        if idx < 0:
            idx = 0
        self.language_combo.setCurrentIndex(idx)

        current_language_code = get_language_code()
        if current_language_code in ("ar", "he", "fa", "ur"):
            self.language_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.auto_restore = QCheckBox()
        self.auto_restore.setChecked(settings.get("auto_restore", True))
        self.auto_save = QCheckBox()
        self.auto_save.setChecked(settings.get("auto_save", True))
        self.startup_mode = QComboBox()
        self.startup_mode.addItems(["desktop", "restore"])
        self.startup_mode.setCurrentText(settings.get("startup_mode", "desktop"))

        self.developer_mode = QCheckBox(
            "🛠️ Entwicklermodus aktivieren (F12 + Entwicklerwerkzeuge + Erweiterungen)"
        )
        self.developer_mode.setChecked(settings.get("developer_mode", False))

        privacy_label = QLabel("🌍 Kein Tracking • Keine Spyware • Open-Source Browser")
        privacy_label.setWordWrap(True)
        privacy_label.setStyleSheet("font-weight:600;")

        import_data_button = QPushButton("📥 Daten aus anderem Browser importieren")
        import_data_button.clicked.connect(lambda: self.main.open_browser_import())

        general_form.addRow("Sprache:", self.language_combo)

        self.browser_default_combo = QComboBox()
        previous_name = settings.get(
            "previous_browser_name",
            get_previous_default_browser(),
        )

        self.browser_default_combo.addItem(
            "🌍 Browser OS",
            "browseros",
        )
        self.browser_default_combo.addItem(
            f"↩️ {previous_name}",
            "previous",
        )

        browser_choice = settings.get(
            "browser_default_choice",
            "previous",
        )
        browser_index = self.browser_default_combo.findData(browser_choice)
        self.browser_default_combo.setCurrentIndex(
            browser_index if browser_index >= 0 else 1
        )

        browser_settings_button = QPushButton(
            "⚙️ Windows Standard-Apps öffnen"
        )
        browser_settings_button.clicked.connect(open_windows_default_apps)

        register_browser_button = QPushButton(
            "🌍 Browser OS für HTTP / HTTPS / HTML / PDF registrieren"
        )
        register_browser_button.clicked.connect(
            lambda: register_and_open_default_apps(self)
        )

        browser_support_label = QLabel(
            "🌍 Unterstützt: HTTP • HTTPS • HTML • HTM • XHTML • "
            "MHT • MHTML • SVG • PDF"
        )
        browser_support_label.setWordWrap(True)

        self.browser_status = QLabel(
            "ℹ️ Windows 11 lässt die endgültige Standard-Auswahl "
            "nur über die Windows-Standard-Apps zu."
        )
        self.browser_status.setWordWrap(True)

        choose_browseros_button = QPushButton(
            "⭐ Browser OS jetzt als Standard auswählen"
        )

        refresh_registration_button = QPushButton(
            "🔄 Browser OS erneut bei Windows registrieren"
        )
        refresh_registration_button.clicked.connect(
            lambda: (
                register_browser_windows(),
                update_browser_status(),
            )
        )

        def update_browser_status():
            if is_browseros_registered_as_default():
                self.browser_status.setText(
                    "✅ Browser OS ist aktuell der Windows-Standardbrowser "
                    "für HTTP und HTTPS."
                )
            else:
                self.browser_status.setText(
                    "ℹ️ Browser OS ist noch nicht der Windows-Standardbrowser. "
                    "Klicke auf „Browser OS jetzt als Standard auswählen“ "
                    "und anschließend in Windows auf „Standard festlegen“."
                )

        def choose_browseros():
            ok = register_browser_only(self)

            if ok:
                update_browser_status()

        choose_browseros_button.clicked.connect(choose_browseros)
        update_browser_status()

        remove_browser_button = QPushButton(
            "🧹 Browser OS aus Windows-Standard-Apps entfernen"
        )
        remove_browser_button.clicked.connect(
            lambda: remove_browser_windows_registration(self)
        )

        general_form.addRow(
            "",
            QLabel(
                "Automatisch (PC) verwendet die Standardsprache des Computers. "
                "Browser-Inhalte können unabhängig davon jede Sprache verwenden."
            ),
        )
        general_form.addRow("Standardbrowser:", self.browser_default_combo)
        general_form.addRow("", browser_support_label)
        general_form.addRow("", self.browser_status)
        general_form.addRow("", refresh_registration_button)
        general_form.addRow("", choose_browseros_button)
        general_form.addRow("", register_browser_button)
        general_form.addRow("", browser_settings_button)
        general_form.addRow("", remove_browser_button)

        general_form.addRow("Letzte Sitzung automatisch wiederherstellen:", self.auto_restore)
        general_form.addRow("Automatisch speichern:", self.auto_save)
        general_form.addRow("Startmodus:", self.startup_mode)
        general_form.addRow("", self.developer_mode)
        general_form.addRow("", import_data_button)
        general_form.addRow("", privacy_label)

        tabs.addTab(appearance, "🎨 Aussehen")
        tabs.addTab(start, "🏠 Startseite")
        tabs.addTab(general, "⚙️ Allgemein")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.color_button.text()), self)
        if color.isValid():
            self.color_button.setText(color.name())

    def pick_bg_color(self):
        color = QColorDialog.getColor(QColor(self.bg_color_button.text()), self)
        if color.isValid():
            self.bg_color_button.setText(color.name())

    def pick_start_menu_color(self):
        color = QColorDialog.getColor(QColor(self.start_menu_bg_color.text()), self)
        if color.isValid():
            self.start_menu_bg_color.setText(color.name())

    def choose_start_menu_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Startmenü-Hintergrund auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            self.start_menu_bg_path.setText(path)
            self.start_menu_bg_mode.setCurrentText("image")

    def choose_wallpaper(self):
        mode = self.bg_mode.currentText()
        filters = "Bilder (*.png *.jpg *.jpeg *.webp)" if mode == "image" else "Videos (*.mp4 *.webm *.mkv)"
        path, _ = QFileDialog.getOpenFileName(self, "Hintergrund auswählen", "", filters)
        if path:
            self.wallpaper_path.setText(path)

    def select_all_pinned(self):
        for i in range(self.pinned_list.count()):
            self.pinned_list.item(i).setSelected(True)

    def select_none_pinned(self):
        self.pinned_list.clearSelection()

    def save(self):
        settings["theme"] = self.theme_combo.currentText()
        settings["accent"] = self.color_button.text()
        settings["desktop_color"] = self.bg_color_button.text()
        settings["wallpaper_mode"] = self.bg_mode.currentText()
        settings["wallpaper_path"] = self.wallpaper_path.text().strip()
        settings["start_menu_theme"] = self.start_menu_theme.currentText()
        settings["start_menu_background_mode"] = self.start_menu_bg_mode.currentText()
        settings["start_menu_background_color"] = self.start_menu_bg_color.text().strip() or "#151827"
        settings["start_menu_background_path"] = self.start_menu_bg_path.text().strip()
        settings["search_engine"] = self.search_combo.currentText()

        built_in_search_urls = {
            "Google": "https://www.google.com/search?q={query}",
            "Bing": "https://www.bing.com/search?q={query}",
            "Yahoo": "https://search.yahoo.com/search?p={query}",
            "DuckDuckGo": "https://duckduckgo.com/?q={query}",
            "Brave Search": "https://search.brave.com/search?q={query}",
            "Startpage": "https://www.startpage.com/sp/search?query={query}",
            "Ecosia": "https://www.ecosia.org/search?q={query}",
        }

        if settings["search_engine"] == "Eigene":
            settings["custom_search_url"] = self.custom_search.text().strip()
        else:
            settings["custom_search_url"] = built_in_search_urls.get(
                settings["search_engine"],
                built_in_search_urls["Google"],
            )

        # Saving a search engine in Settings always makes it the STANDARD.
        settings["search_engine_mode"] = "standard"
        settings["setup_completed"] = True
        settings.pop("setup_test_engine", None)
        settings.pop("setup_test_url", None)

        settings["show_clock"] = self.show_clock.isChecked()
        settings["show_recent"] = self.show_recent.isChecked()
        settings["show_pinned"] = self.show_pinned.isChecked()
        settings["show_widgets"] = self.show_widgets.isChecked()
        settings["pinned_apps"] = [
            self.pinned_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.pinned_list.count())
            if self.pinned_list.item(i).isSelected()
        ]
        settings["auto_restore"] = self.auto_restore.isChecked()
        settings["auto_save"] = self.auto_save.isChecked()
        settings["startup_mode"] = self.startup_mode.currentText()
        settings["developer_mode"] = self.developer_mode.isChecked()
        settings["language"] = self.language_combo.currentData() or "auto"
        settings["browser_default_choice"] = self.browser_default_combo.currentData() or "previous"
        settings["previous_browser_name"] = get_previous_default_browser()
        if settings["browser_default_choice"] == "browseros":
            register_browser_windows()

        save_json(SETTINGS_FILE, settings)
        self.main.apply_theme()
        self.main.rebuild_desktop()
        self.accept()


# ------------------------------------------------------------
# App widgets
# ------------------------------------------------------------

class FileExplorerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.model = QFileSystemModel()
        self.model.setRootPath(str(Path.home()))

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(Path.home())))
        self.tree.doubleClicked.connect(self.open_item)

        top = QHBoxLayout()
        path = QLineEdit(str(Path.home()))
        go = QPushButton("Öffnen")
        go.clicked.connect(lambda: self.go_to(path.text()))
        top.addWidget(path, 1)
        top.addWidget(go)

        self.path_edit = path

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.tree)

    def go_to(self, path):
        p = Path(path).expanduser()
        if p.exists():
            self.path_edit.setText(str(p))
            self.tree.setRootIndex(self.model.index(str(p)))

    def open_item(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.go_to(path)
        else:
            open_external(path)


class NotesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.editor = QTextEdit()
        self.editor.setPlainText(
            NOTES_FILE.read_text(encoding="utf-8")
            if NOTES_FILE.exists()
            else ""
        )

        save_btn = QPushButton("💾 Speichern")
        save_btn.clicked.connect(self.save)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📝 Browser OS Notizen"))
        layout.addWidget(self.editor, 1)
        layout.addWidget(save_btn)

    def save(self):
        NOTES_FILE.write_text(self.editor.toPlainText(), encoding="utf-8")
        QMessageBox.information(self, APP_NAME, "Notizen gespeichert.")


class CalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setFont(QFont("Segoe UI", 20))

        layout = QVBoxLayout(self)
        layout.addWidget(self.display)

        buttons = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"],
            ["C", "(", ")", "⌫"],
        ]
        grid = QGridLayout()
        for r, row in enumerate(buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setMinimumHeight(55)
                btn.clicked.connect(lambda checked=False, t=text: self.press(t))
                grid.addWidget(btn, r, c)
        layout.addLayout(grid)

    def press(self, text):
        current = self.display.text()
        if text == "C":
            self.display.clear()
        elif text == "⌫":
            self.display.setText(current[:-1])
        elif text == "=":
            try:
                allowed = set("0123456789.+-*/() ")
                if not set(current) <= allowed:
                    raise ValueError("Ungültig")
                result = eval(current, {"__builtins__": {}}, {})
                self.display.setText(str(result))
            except Exception:
                self.display.setText("Fehler")
        else:
            self.display.setText(current + text)


class HistoryApp(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.list = QListWidget()
        self.refresh()

        clear = QPushButton("🧹 Verlauf löschen")
        clear.clicked.connect(self.clear_history)

        open_btn = QPushButton("🌍 Ausgewählten Eintrag öffnen")
        open_btn.clicked.connect(self.open_selected)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🕘 Browser-Verlauf"))
        layout.addWidget(self.list, 1)
        layout.addWidget(open_btn)
        layout.addWidget(clear)

    def refresh(self):
        self.list.clear()
        for item in history:
            row = QListWidgetItem(
                f"{item.get('time','')}  •  {item.get('title', item.get('url',''))}\n"
                f"{item.get('url','')}"
            )
            row.setData(Qt.ItemDataRole.UserRole, item.get("url", ""))
            self.list.addItem(row)

    def open_selected(self):
        item = self.list.currentItem()
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            self.main.open_app("browser", url=url)

    def clear_history(self):
        global history
        history = []
        save_json(HISTORY_FILE, history)
        self.refresh()


class BookmarksApp(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.list = QListWidget()
        self.refresh()

        open_btn = QPushButton("🌍 Öffnen")
        open_btn.clicked.connect(self.open_selected)

        delete_btn = QPushButton("🗑️ Entfernen")
        delete_btn.clicked.connect(self.delete_selected)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⭐ Lesezeichen"))
        layout.addWidget(self.list, 1)

        row = QHBoxLayout()
        row.addWidget(open_btn)
        row.addWidget(delete_btn)
        layout.addLayout(row)

    def refresh(self):
        self.list.clear()
        for item in bookmarks:
            row = QListWidgetItem(
                f"{item.get('title','')}\n{item.get('url','')}"
            )
            row.setData(Qt.ItemDataRole.UserRole, item)
            self.list.addItem(row)

    def open_selected(self):
        item = self.list.currentItem()
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            self.main.open_app("browser", url=data.get("url", ""))

    def delete_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        global bookmarks
        bookmarks = [b for b in bookmarks if b.get("url") != data.get("url")]
        save_json(BOOKMARKS_FILE, bookmarks)
        self.refresh()


class SessionsApp(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.list = QListWidget()
        self.refresh()

        restore_btn = QPushButton("🔄 Sitzung wiederherstellen")
        restore_btn.clicked.connect(self.restore_selected)

        delete_btn = QPushButton("🗑️ Löschen")
        delete_btn.clicked.connect(self.delete_selected)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("💾 Browser-Sitzungen"))
        layout.addWidget(self.list, 1)

        row = QHBoxLayout()
        row.addWidget(restore_btn)
        row.addWidget(delete_btn)
        layout.addLayout(row)

        info = QLabel(
            f"Ordner: {SESSIONS_DIR}\n"
            "Gespeicherte Sitzungen enthalten Tabs, Fenstergröße, Fensterposition, "
            "Zoom und – soweit die Webseite es zulässt – die Scrollposition."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

    def session_files(self):
        return sorted(
            SESSIONS_DIR.glob("*.bos_session.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def refresh(self):
        self.list.clear()
        for path in self.session_files():
            data = load_json(path, {})
            name = data.get("name", path.stem)
            count = len(data.get("tabs", []))
            row = QListWidgetItem(f"💾 {name}  •  {count} Tabs")
            row.setData(Qt.ItemDataRole.UserRole, str(path))
            self.list.addItem(row)

    def restore_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        data = load_json(path, {})
        self.main.restore_session(data)

    def delete_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        try:
            path.unlink()
        except Exception:
            pass
        self.refresh()


class TaskManagerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "PID", "Speicher", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self.refresh)

        info = QLabel("Browser OS Task Manager – Windows-Prozesse werden über tasklist gelesen.")
        info.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self.table, 1)
        layout.addWidget(refresh_btn)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        if platform.system() != "Windows":
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem(platform.system()))
            self.table.setItem(0, 3, QTableWidgetItem("Nicht-Windows"))
            return

        try:
            result = subprocess.run(
                ["tasklist", "/fo", "csv", "/nh"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in result.stdout.splitlines()[:150]:
                parts = []
                current = ""
                inside = False
                for char in line:
                    if char == '"':
                        inside = not inside
                    elif char == "," and not inside:
                        parts.append(current)
                        current = ""
                    else:
                        current += char
                parts.append(current)

                if len(parts) < 5:
                    continue
                row = self.table.rowCount()
                self.table.insertRow(row)
                values = [
                    parts[0].strip('"'),
                    parts[1].strip('"'),
                    parts[4].strip('"'),
                    "Läuft",
                ]
                for col, value in enumerate(values):
                    self.table.setItem(row, col, QTableWidgetItem(value))
        except Exception as exc:
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem("Fehler"))
            self.table.setItem(0, 1, QTableWidgetItem(str(exc)))



class SimpleLauncherApp(QWidget):
    """Simple local-app launcher used for media/folder shortcuts."""
    def __init__(self, title, folder, icon="📁"):
        super().__init__()
        self.folder = folder if isinstance(folder, str) and folder.startswith("shell:") else Path(folder).expanduser()
        title_label = QLabel(f"{icon}  {title}")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        info = QLabel(f"Ordner: {self.folder}")
        info.setWordWrap(True)
        open_btn = QPushButton("📂 Ordner öffnen")
        open_btn.clicked.connect(self.open_folder)
        create_btn = QPushButton("➕ Ordner erstellen")
        create_btn.clicked.connect(self.create_folder)

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(info)
        layout.addStretch(1)
        layout.addWidget(open_btn)
        layout.addWidget(create_btn)

    def open_folder(self):
        try:
            if isinstance(self.folder, str) and self.folder.startswith("shell:") and platform.system() == "Windows":
                os.startfile(self.folder)
            else:
                self.folder.mkdir(parents=True, exist_ok=True)
                open_external(self.folder)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Ordner konnte nicht geöffnet werden:\n{exc}")

    def create_folder(self):
        try:
            if isinstance(self.folder, str) and self.folder.startswith("shell:"):
                os.startfile(self.folder)
            else:
                self.folder.mkdir(parents=True, exist_ok=True)
            QMessageBox.information(self, APP_NAME, f"Ordner bereit:\n{self.folder}")
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Ordner konnte nicht erstellt werden:\n{exc}")


class MailWorker(QThread):
    """Background IMAP polling. Credentials live only in memory."""
    messagesUpdated = pyqtSignal(object)
    newMail = pyqtSignal(str, str)
    connected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, account, parent=None):
        super().__init__(parent)
        self.account = dict(account)
        self.stop_event = threading.Event()
        self.known_uids = set()
        self.initial_sync = True

    def stop(self):
        self.stop_event.set()

    @staticmethod
    def _decode(value):
        if not value:
            return ""
        parts = []
        try:
            for item, charset in decode_header(value):
                if isinstance(item, bytes):
                    try:
                        parts.append(item.decode(charset or "utf-8", errors="replace"))
                    except Exception:
                        parts.append(item.decode("utf-8", errors="replace"))
                else:
                    parts.append(str(item))
        except Exception:
            return str(value)
        return "".join(parts).strip()

    def _connect(self):
        host = self.account["imap_host"]
        port = int(self.account.get("imap_port", 993))
        box = imaplib.IMAP4_SSL(host, port, timeout=15)
        box.login(self.account["email"], self.account["password"])
        return box

    def _header(self, box, uid):
        status, data = box.uid(
            "fetch",
            uid,
            "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])",
        )
        if status != "OK" or not data:
            return {"uid": uid.decode() if isinstance(uid, bytes) else str(uid), "from": "", "subject": "", "date": ""}
        raw = b""
        for part in data:
            if isinstance(part, tuple) and isinstance(part[1], bytes):
                raw += part[1]
        msg = email_lib.message_from_bytes(raw)
        sender_name, sender_addr = parseaddr(self._decode(msg.get("From", "")))
        return {
            "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
            "from": self._decode(sender_name) or sender_addr or self._decode(msg.get("From", "")),
            "from_email": sender_addr,
            "subject": self._decode(msg.get("Subject", "")) or "(Kein Betreff)",
            "date": self._decode(msg.get("Date", "")),
        }

    def _headers(self, box, uids):
        result = []
        for uid in uids[-50:][::-1]:
            if self.stop_event.is_set():
                break
            try:
                result.append(self._header(box, uid))
            except Exception:
                continue
        return result

    def run(self):
        box = None
        try:
            box = self._connect()
            self.connected.emit()
        except Exception as exc:
            self.error.emit(self._friendly_error(exc))
            return

        try:
            while not self.stop_event.is_set():
                try:
                    status, _ = box.select("INBOX", readonly=True)
                    if status != "OK":
                        raise RuntimeError("Der Posteingang konnte nicht geöffnet werden.")

                    status, data = box.uid("search", None, "ALL")
                    if status != "OK":
                        raise RuntimeError("Die Mail-Liste konnte nicht abgerufen werden.")

                    all_uids = data[0].split() if data and data[0] else []
                    current_set = set(all_uids)
                    messages = self._headers(box, all_uids)
                    self.messagesUpdated.emit(messages)

                    if self.initial_sync:
                        self.known_uids = current_set
                        self.initial_sync = False
                    else:
                        new_uids = [uid for uid in all_uids if uid not in self.known_uids]
                        for uid in new_uids[-10:]:
                            if self.stop_event.is_set():
                                break
                            try:
                                header = self._header(box, uid)
                                self.newMail.emit(header.get("from", "Neue Mail"), header.get("subject", "Neue Nachricht"))
                            except Exception:
                                pass
                        self.known_uids = current_set

                except Exception as exc:
                    self.error.emit(self._friendly_error(exc))
                    try:
                        if box is not None:
                            box.logout()
                    except Exception:
                        pass
                    if self.stop_event.wait(5):
                        break
                    try:
                        box = self._connect()
                        self.connected.emit()
                    except Exception as reconnect_exc:
                        self.error.emit(self._friendly_error(reconnect_exc))
                        if self.stop_event.wait(25):
                            break
                        continue

                if self.stop_event.wait(30):
                    break
        finally:
            try:
                if box is not None:
                    box.logout()
            except Exception:
                pass

    @staticmethod
    def _friendly_error(exc):
        message = str(exc).strip() or type(exc).__name__
        lower = message.lower()
        if "authenticationfailed" in lower or "auth" in lower or "login" in lower or "invalid credentials" in lower:
            return (
                "Der Mailserver hat die Anmeldung abgelehnt. Das bedeutet nicht automatisch, "
                "dass dein Passwort falsch ist. Bei Gmail, Yahoo und Outlook.com können "
                "Drittanbieter-Logins möglicherweise ein App-Passwort verlangen. "
                "Nutze dafür 'Beim Anbieter anmelden' oder die vom Anbieter erlaubte IMAP/SMTP-Authentifizierung."
            )
        if "timed out" in lower or "timeout" in lower:
            return "Zeitüberschreitung beim Mailserver."
        return message


class MailDetailWorker(QThread):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, account, uid, parent=None):
        super().__init__(parent)
        self.account = dict(account)
        self.uid = str(uid).encode()

    def run(self):
        box = None
        try:
            port = int(self.account.get("imap_port", 993))
            if str(self.account.get("imap_security", "ssl")).lower() == "starttls":
                box = imaplib.IMAP4(self.account["imap_host"], port, timeout=15)
                box.starttls(ssl.create_default_context())
            else:
                box = imaplib.IMAP4_SSL(self.account["imap_host"], port, timeout=15)
            box.login(self.account["email"], self.account["password"])
            status, _ = box.select("INBOX", readonly=True)
            if status != "OK":
                raise RuntimeError("Posteingang konnte nicht geöffnet werden.")
            status, data = box.uid("fetch", self.uid, "(RFC822)")
            if status != "OK":
                raise RuntimeError("E-Mail konnte nicht geladen werden.")
            raw = None
            for part in data:
                if isinstance(part, tuple) and isinstance(part[1], bytes):
                    raw = part[1]
                    break
            if raw is None:
                raise RuntimeError("E-Mail-Inhalt ist leer.")
            msg = email_lib.message_from_bytes(raw)
            self.result.emit(self._parse_message(msg))
        except Exception as exc:
            self.error.emit(str(exc) or type(exc).__name__)
        finally:
            try:
                if box is not None:
                    box.logout()
            except Exception:
                pass

    @staticmethod
    def _decode(value):
        if not value:
            return ""
        out = []
        for item, charset in decode_header(value):
            if isinstance(item, bytes):
                try:
                    out.append(item.decode(charset or "utf-8", errors="replace"))
                except Exception:
                    out.append(item.decode("utf-8", errors="replace"))
            else:
                out.append(str(item))
        return "".join(out)

    def _parse_message(self, msg):
        body_parts = []
        html_parts = []
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in disposition.lower():
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                try:
                    decoded = payload.decode(charset, errors="replace")
                except Exception:
                    decoded = payload.decode("utf-8", errors="replace")
                if content_type == "text/plain":
                    body_parts.append(decoded)
                elif content_type == "text/html":
                    html_parts.append(decoded)
        else:
            payload = msg.get_payload(decode=True) or b""
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                decoded = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_parts.append(decoded)
            else:
                body_parts.append(decoded)

        body = "\n\n".join(body_parts).strip()
        if not body and html_parts:
            body = re.sub(r"<[^>]+>", " ", html_lib.unescape("\n".join(html_parts)))
            body = re.sub(r"\s+", " ", body).strip()

        sender_name, sender_addr = parseaddr(self._decode(msg.get("From", "")))
        return {
            "from": self._decode(sender_name) or sender_addr or self._decode(msg.get("From", "")),
            "from_email": sender_addr,
            "to": self._decode(msg.get("To", "")),
            "subject": self._decode(msg.get("Subject", "")) or "(Kein Betreff)",
            "date": self._decode(msg.get("Date", "")),
            "body": body or "(Kein lesbarer Nachrichtentext)",
        }


class MailSendWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, account, recipient, subject, body, parent=None):
        super().__init__(parent)
        self.account = dict(account)
        self.recipient = recipient
        self.subject = subject
        self.body = body

    def run(self):
        try:
            host = self.account["smtp_host"]
            port = int(self.account.get("smtp_port", 465))
            msg = EmailMessage()
            msg["From"] = self.account["email"]
            msg["To"] = self.recipient
            msg["Subject"] = self.subject or "(Kein Betreff)"
            msg.set_content(self.body)

            if self.account.get("smtp_security") == "starttls" or port == 587:
                with smtplib.SMTP(host, port, timeout=20) as server:
                    server.ehlo()
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                    server.login(self.account["email"], self.account["password"])
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context()) as server:
                    server.login(self.account["email"], self.account["password"])
                    server.send_message(msg)

            self.finished.emit(True, "E-Mail wurde gesendet.")
        except Exception as exc:
            self.finished.emit(False, str(exc) or type(exc).__name__)


class MailService(QObject):
    """Persistent mail service shared by mail windows; password is memory-only."""
    messagesUpdated = pyqtSignal(object)
    newMail = pyqtSignal(str, str)
    statusChanged = pyqtSignal(str)
    error = pyqtSignal(str)
    sendFinished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.detail_worker = None
        self.send_worker = None
        self.account = None
        self.logged_in = False
        self.notifications_enabled = bool(settings.get("mail_notifications", True))
        self.last_error = ""

        icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Browser OS Mails")

    def login(self, email_address, password, provider="Automatisch", custom=None):
        email_address = email_address.strip()
        if not email_address or not password:
            self.error.emit("Bitte E-Mail-Adresse und Passwort eingeben.")
            return

        try:
            account = build_mail_account(email_address, password, provider, custom or {})
        except Exception as exc:
            self.error.emit(str(exc))
            return

        self.logout(silent=True)
        self.account = account
        settings["mail_address"] = email_address
        save_json(SETTINGS_FILE, settings)

        self.worker = MailWorker(account, self)
        self.worker.messagesUpdated.connect(self.messagesUpdated.emit)
        self.worker.newMail.connect(self._new_mail)
        self.worker.connected.connect(lambda: self.statusChanged.emit("Verbunden"))
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def logout(self, silent=False):
        if self.worker is not None:
            try:
                self.worker.stop()
                self.worker.wait(3000)
            except Exception:
                pass
            self.worker = None
        self.account = None
        self.logged_in = False
        try:
            self.tray.hide()
        except Exception:
            pass
        if not silent:
            self.statusChanged.emit("Abgemeldet")

    def _on_worker_error(self, message):
        self.last_error = message
        self.error.emit(message)
        # An authentication/server error should not trigger endless popups.

    def _new_mail(self, sender, subject):
        self.logged_in = True
        self.newMail.emit(sender, subject)
        if self.notifications_enabled and QSystemTrayIcon.isSystemTrayAvailable():
            try:
                self.tray.show()
                self.tray.showMessage(
                    "📧 Neue E-Mail",
                    f"{sender}\n{subject}",
                    QSystemTrayIcon.MessageIcon.Information,
                    6000,
                )
            except Exception:
                pass

    def set_notifications(self, enabled):
        self.notifications_enabled = bool(enabled)
        settings["mail_notifications"] = self.notifications_enabled
        save_json(SETTINGS_FILE, settings)
        if not self.notifications_enabled:
            try:
                self.tray.hide()
            except Exception:
                pass

    def fetch_detail(self, uid):
        if not self.account:
            return
        self.detail_worker = MailDetailWorker(self.account, uid, self)
        self.detail_worker.result.connect(self._detail_result)
        self.detail_worker.error.connect(self.error.emit)
        self.detail_worker.finished.connect(self.detail_worker.deleteLater)
        self.detail_worker.start()

    def _detail_result(self, payload):
        app = QApplication.activeWindow()
        if app is not None:
            # MailApp instances listen through the global signal below.
            pass
        self.detailsLoaded(payload)

    detailsLoaded = pyqtSignal(object)

    def send(self, recipient, subject, body):
        if not self.account:
            self.error.emit("Bitte zuerst ein E-Mail-Konto anmelden.")
            return
        self.send_worker = MailSendWorker(self.account, recipient, subject, body, self)
        self.send_worker.finished.connect(self._send_result)
        self.send_worker.finished.connect(lambda *_: self.send_worker.deleteLater())
        self.send_worker.start()

    def _send_result(self, ok, message):
        self.sendFinished.emit(ok, message)
        if ok:
            self.statusChanged.emit(message)
        else:
            self.error.emit(message)


def build_mail_account(email_address, password, provider="Automatisch", custom=None):
    provider = provider or "Automatisch"
    domain = email_address.lower().split("@", 1)[-1] if "@" in email_address else ""

    profiles = {
        "Gmail": {
            "imap_host": "imap.gmail.com", "imap_port": 993, "imap_security": "ssl",
            "smtp_host": "smtp.gmail.com", "smtp_port": 465, "smtp_security": "ssl",
        },
        "Yahoo": {
            "imap_host": "imap.mail.yahoo.com", "imap_port": 993, "imap_security": "ssl",
            "smtp_host": "smtp.mail.yahoo.com", "smtp_port": 465, "smtp_security": "ssl",
        },
    }

    if provider == "Automatisch":
        if domain in ("gmail.com", "googlemail.com"):
            provider = "Gmail"
        elif domain in ("yahoo.com", "yahoo.de", "ymail.com", "rocketmail.com"):
            provider = "Yahoo"
        elif domain in ("outlook.com", "hotmail.com", "live.com", "msn.com"):
            provider = "Outlook.com"
        else:
            provider = "Benutzerdefiniert"

    if provider in profiles:
        cfg = profiles[provider].copy()
    elif provider == "Outlook.com":
        raise RuntimeError(
            "Outlook.com kann für Drittanbieter-Mailprogramme eine spezielle Anmeldung oder ein App-Passwort benötigen. "
            "Nutze 'Beim Anbieter anmelden' für den offiziellen Microsoft-Login."
        )
    elif provider == "Benutzerdefiniert":
        custom = custom or {}
        imap_host = str(custom.get("imap_host", "")).strip()
        smtp_host = str(custom.get("smtp_host", "")).strip()
        if not imap_host or not smtp_host:
            raise RuntimeError("Bitte IMAP- und SMTP-Server eintragen.")
        cfg = {
            "imap_host": imap_host,
            "imap_port": int(custom.get("imap_port", 993)),
            "imap_security": custom.get("imap_security", "ssl"),
            "smtp_host": smtp_host,
            "smtp_port": int(custom.get("smtp_port", 465)),
            "smtp_security": custom.get("smtp_security", "ssl"),
        }
    else:
        raise RuntimeError("Unbekannter Mail-Anbieter.")

    cfg["email"] = email_address
    cfg["password"] = password
    return cfg


class LocalMailApp(QWidget):
    """Real IMAP/SMTP mail client using only Python's standard library."""
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.service = getattr(main, "mail_service", None)
        if self.service is None:
            self.service = MailService(main)
            main.mail_service = self.service

        self.current_messages = []
        self.setMinimumSize(720, 560)

        title = QLabel("📧 Browser OS Mails")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        self.email_edit = QLineEdit(str(settings.get("mail_address", "")))
        self.email_edit.setPlaceholderText("E-Mail-Adresse")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Passwort / App-Passwort")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Automatisch", "Gmail", "Yahoo", "Outlook.com", "Benutzerdefiniert"])

        self.login_btn = QPushButton("🔐 Anmelden")
        self.login_btn.clicked.connect(self.login)
        self.logout_btn = QPushButton("🚪 Abmelden")
        self.logout_btn.clicked.connect(lambda: self.service.logout())
        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_now)
        self.compose_btn = QPushButton("✉️ Neue Mail")
        self.compose_btn.clicked.connect(self.compose_mail)
        self.web_login_btn = QPushButton("🌐 Beim Anbieter anmelden")
        self.web_login_btn.clicked.connect(self.web_login)

        self.notifications = QCheckBox("🔔 Desktop-Popups bei neuen E-Mails")
        self.notifications.setChecked(self.service.notifications_enabled)
        self.notifications.toggled.connect(self.service.set_notifications)

        self.status = QLabel("Nicht angemeldet")
        self.status.setWordWrap(True)

        login_form = QFormLayout()
        login_form.addRow("E-Mail:", self.email_edit)
        login_form.addRow("Passwort:", self.password_edit)
        login_form.addRow("Anbieter:", self.provider_combo)

        self.custom_group = QGroupBox("Benutzerdefinierte Server")
        custom_layout = QFormLayout(self.custom_group)
        self.imap_host = QLineEdit()
        self.imap_port = QSpinBox(); self.imap_port.setRange(1, 65535); self.imap_port.setValue(993)
        self.imap_security = QComboBox(); self.imap_security.addItems(["SSL", "STARTTLS"])
        self.smtp_host = QLineEdit()
        self.smtp_port = QSpinBox(); self.smtp_port.setRange(1, 65535); self.smtp_port.setValue(465)
        self.smtp_security = QComboBox(); self.smtp_security.addItems(["SSL", "STARTTLS"])
        custom_layout.addRow("IMAP:", self.imap_host)
        custom_layout.addRow("IMAP-Port:", self.imap_port)
        custom_layout.addRow("IMAP-Sicherheit:", self.imap_security)
        custom_layout.addRow("SMTP:", self.smtp_host)
        custom_layout.addRow("SMTP-Port:", self.smtp_port)
        custom_layout.addRow("SMTP-Sicherheit:", self.smtp_security)
        self.custom_group.setVisible(False)
        self.provider_combo.currentTextChanged.connect(lambda value: self.custom_group.setVisible(value == "Benutzerdefiniert"))

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.login_btn)
        top_buttons.addWidget(self.logout_btn)
        top_buttons.addWidget(self.refresh_btn)
        top_buttons.addWidget(self.compose_btn)
        top_buttons.addWidget(self.web_login_btn)

        self.login_info = QLabel(
            "Hinweis: Gmail, Outlook.com und Yahoo können normale Kontopasswörter bei "
            "Drittanbieter-Apps blockieren. Nutze dann <b>Beim Anbieter anmelden</b> "
            "oder ein vom Anbieter erlaubtes App-Passwort. Dein Passwort wird "
            "nicht in Browser-OS-Dateien gespeichert."
        )
        self.login_info.setWordWrap(True)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.open_selected)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Doppelklicke eine E-Mail, um sie zu öffnen.")

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.list)
        split.addWidget(self.preview)
        split.setSizes([270, 280])

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(login_form)
        layout.addWidget(self.custom_group)
        layout.addWidget(self.login_info)
        layout.addLayout(top_buttons)
        layout.addWidget(self.notifications)
        layout.addWidget(self.status)
        layout.addWidget(split, 1)

        self.service.messagesUpdated.connect(self.set_messages)
        self.service.detailsLoaded.connect(self.show_message)
        self.service.newMail.connect(self._received_mail)
        self.service.statusChanged.connect(self.status.setText)
        self.service.error.connect(self.show_error)

        self._sync_state()

    def _sync_state(self):
        if self.service.account:
            self.email_edit.setText(self.service.account.get("email", ""))
            self.status.setText("Verbunden")
        else:
            self.status.setText("Nicht angemeldet")

    def login(self):
        custom = {
            "imap_host": self.imap_host.text(),
            "imap_port": self.imap_port.value(),
            "imap_security": "starttls" if self.imap_security.currentText() == "STARTTLS" else "ssl",
            "smtp_host": self.smtp_host.text(),
            "smtp_port": self.smtp_port.value(),
            "smtp_security": "starttls" if self.smtp_security.currentText() == "STARTTLS" else "ssl",
        }
        self.status.setText("Verbinde …")
        self.service.login(
            self.email_edit.text(),
            self.password_edit.text(),
            self.provider_combo.currentText(),
            custom,
        )
        # Passwort wird absichtlich nicht in settings.json gespeichert.
        # Es bleibt nur im RAM, damit ein fehlgeschlagener Login erneut versucht werden kann.

    def web_login(self):
        provider = self.provider_combo.currentText()
        urls = {
            "Gmail": "https://mail.google.com/",
            "Yahoo": "https://mail.yahoo.com/",
            "Outlook.com": "https://outlook.live.com/mail/",
        }
        url = urls.get(provider)
        if not url:
            address = self.email_edit.text().strip().lower()
            if "@" not in address:
                QMessageBox.information(
                    self, APP_NAME,
                    "Wähle Gmail, Yahoo oder Outlook.com aus oder verwende die benutzerdefinierte IMAP/SMTP-Anmeldung."
                )
                return
            domain = address.rsplit("@", 1)[1]
            if domain in ("gmail.com", "googlemail.com"):
                url = "https://mail.google.com/"
            elif domain in ("yahoo.com", "yahoo.de", "ymail.com", "rocketmail.com"):
                url = "https://mail.yahoo.com/"
            elif domain in ("outlook.com", "hotmail.com", "live.com", "msn.com"):
                url = "https://outlook.live.com/mail/"
            else:
                QMessageBox.information(
                    self, APP_NAME,
                    "Für diesen Anbieter kenne ich keinen sicheren Web-Login. Verwende die benutzerdefinierte IMAP/SMTP-Konfiguration."
                )
                return

        try:
            self.main.open_app("browser", url=url)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Der Web-Login konnte nicht geöffnet werden:\n{exc}")

    def refresh_now(self):
        # The background worker polls every 30 seconds; restarting it forces an immediate check.
        if not self.service.account:
            self.status.setText("Bitte zuerst anmelden.")
            return
        account = dict(self.service.account)
        self.service.logout(silent=True)
        self.service.login(
            account["email"],
            account["password"],
            self.provider_combo.currentText(),
            {
                "imap_host": account.get("imap_host", ""),
                "imap_port": account.get("imap_port", 993),
                "imap_security": account.get("imap_security", "ssl"),
                "smtp_host": account.get("smtp_host", ""),
                "smtp_port": account.get("smtp_port", 465),
                "smtp_security": account.get("smtp_security", "ssl"),
            },
        )

    def set_messages(self, messages):
        self.current_messages = list(messages or [])
        self.list.clear()
        for message in self.current_messages:
            self.list.addItem(
                f"📨 {message.get('from', 'Unbekannt')}\n"
                f"{message.get('subject', '(Kein Betreff)')}\n"
                f"{message.get('date', '')}"
            )
        self.status.setText(f"{len(self.current_messages)} Nachrichten geladen")

    def open_selected(self, item):
        index = self.list.row(item)
        if 0 <= index < len(self.current_messages):
            uid = self.current_messages[index].get("uid")
            if uid:
                self.preview.setPlainText("E-Mail wird geladen …")
                self.service.fetch_detail(uid)

    def show_message(self, message):
        text = (
            f"Von: {message.get('from', '')} <{message.get('from_email', '')}>\n"
            f"An: {message.get('to', '')}\n"
            f"Datum: {message.get('date', '')}\n"
            f"Betreff: {message.get('subject', '')}\n"
            f"\n{'-' * 60}\n\n"
            f"{message.get('body', '')}"
        )
        self.preview.setPlainText(text)

    def _received_mail(self, sender, subject):
        self.status.setText(f"Neue Mail: {sender} – {subject}")

    def compose_mail(self):
        if not self.service.account:
            QMessageBox.information(self, APP_NAME, "Bitte zuerst ein E-Mail-Konto anmelden.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("✉️ Neue Mail")
        dialog.resize(620, 520)

        to = QLineEdit()
        to.setPlaceholderText("empfaenger@example.com")
        subject = QLineEdit()
        body = QTextEdit()
        body.setPlaceholderText("Nachricht …")

        form = QFormLayout()
        form.addRow("An:", to)
        form.addRow("Betreff:", subject)
        form.addRow("Text:", body)

        send = QPushButton("📤 Senden")
        cancel = QPushButton("Abbrechen")
        buttons = QHBoxLayout()
        buttons.addWidget(send)
        buttons.addWidget(cancel)

        layout = QVBoxLayout(dialog)
        layout.addLayout(form)
        layout.addLayout(buttons)

        cancel.clicked.connect(dialog.reject)

        def send_mail():
            recipient = to.text().strip()
            if not recipient or "@" not in recipient:
                QMessageBox.warning(dialog, APP_NAME, "Bitte eine gültige Empfänger-Adresse eingeben.")
                return
            send.setEnabled(False)
            send.setText("📤 Sende …")
            self.service.send(recipient, subject.text(), body.toPlainText())

        def sent_result(ok, message):
            send.setEnabled(True)
            send.setText("📤 Senden")
            if ok:
                QMessageBox.information(dialog, APP_NAME, message)
                dialog.accept()
            else:
                QMessageBox.warning(dialog, APP_NAME, f"Senden fehlgeschlagen:\n{message}")

        self.service.sendFinished.connect(sent_result)
        send.clicked.connect(send_mail)
        dialog.exec()
        try:
            self.service.sendFinished.disconnect(sent_result)
        except Exception:
            pass

    def show_error(self, message):
        self.status.setText(f"⚠️ {message}")


class CalendarApp(QWidget):
    def __init__(self):
        super().__init__()
        title = QLabel("📅 Kalender")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        note = QLabel("Lokaler Kalender ohne Konto. Ausgewähltes Datum: …")
        note.setWordWrap(True)
        self.note = note
        self.calendar.selectionChanged.connect(self.update_note)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.calendar, 1)
        layout.addWidget(note)
        self.update_note()

    def update_note(self):
        self.note.setText(f"Ausgewähltes Datum: {self.calendar.selectedDate().toString('dd.MM.yyyy')}")


class TerminalApp(QWidget):
    def __init__(self):
        super().__init__()
        title = QLabel("💻 Terminal")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        info = QLabel("Startet das Windows-Terminal bzw. die Eingabeaufforderung in einem echten externen Fenster.")
        info.setWordWrap(True)
        cmd = QPushButton("⌨️ CMD öffnen")
        cmd.clicked.connect(self.open_cmd)
        ps = QPushButton("🟦 PowerShell öffnen")
        ps.clicked.connect(self.open_powershell)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(info)
        layout.addStretch(1)
        layout.addWidget(cmd)
        layout.addWidget(ps)

    def open_cmd(self):
        try:
            subprocess.Popen(["cmd.exe"], cwd=str(Path.home()))
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"CMD konnte nicht geöffnet werden:\n{exc}")

    def open_powershell(self):
        try:
            subprocess.Popen(["powershell.exe"], cwd=str(Path.home()))
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"PowerShell konnte nicht geöffnet werden:\n{exc}")


class SystemInfoApp(QWidget):
    def __init__(self):
        super().__init__()
        title = QLabel("🖥️ Systeminfo")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        refresh = QPushButton("🔄 Aktualisieren")
        refresh.clicked.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.info, 1)
        layout.addWidget(refresh)
        self.refresh()

    def refresh(self):
        try:
            total, used, free = shutil.disk_usage(Path.home().anchor or str(Path.home()))
            lines = [
                f"Betriebssystem: {platform.system()} {platform.release()}",
                f"Version: {platform.version()}",
                f"Architektur: {platform.machine()}",
                f"Python: {platform.python_version()}",
                f"Computer: {platform.node()}",
                f"CPU: {os.cpu_count() or 1} logische Kerne",
                f"Festplatte frei: {free / (1024**3):.1f} GB",
                f"Festplatte gesamt: {total / (1024**3):.1f} GB",
            ]
            self.info.setPlainText("\n".join(lines))
        except Exception as exc:
            self.info.setPlainText(f"Systeminformationen konnten nicht gelesen werden.\n{exc}")


class GamesApp(QWidget):
    def __init__(self, main):
        super().__init__()
        title = QLabel("🎮 Spiele")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        info = QLabel("Browser OS Spielesammlung. Eigene Spiele und Webseiten können hier später ergänzt werden.")
        info.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(info)
        for label, url in [
            ("🧱 Minecraft Web", "https://www.minecraft.net/"),
            ("🎮 itch.io", "https://itch.io/"),
            ("🕹️ CrazyGames", "https://www.crazygames.com/"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, u=url: main.open_app("browser", url=u))
            layout.addWidget(btn)
        layout.addStretch(1)


class AboutApp(QWidget):
    def __init__(self):
        super().__init__()
        title = QLabel(f"🌍 Browser OS {VERSION}")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        text = QLabel(
            "Ein Browser mit Desktop-Umgebung, virtuellen Fenstern, Apps, Arbeitsbereichen, "
            "Sessions und anpassbarem Startbereich."
        )
        text.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addStretch(1)


class StoreApp(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        grid = QGridLayout(inner)

        apps = [
            ("🌍", "Browser", "browser"),
            ("📁", "Dateien", "files"),
            ("📝", "Notizen", "notes"),
            ("🧮", "Rechner", "calculator"),
            ("⚙️", "Einstellungen", "settings"),
            ("💾", "Sitzungen", "sessions"),
            ("🕘", "Verlauf", "history"),
            ("⭐", "Lesezeichen", "bookmarks"),
            ("📊", "Task Manager", "taskmanager"),
            ("📧", "Mails", "mail"),
            ("📥", "Downloads", "downloads"),
            ("🎵", "Musik", "music"),
            ("🎬", "Videos", "videos"),
            ("🖼️", "Bilder", "pictures"),
            ("📅", "Kalender", "calendar"),
            ("💻", "Terminal", "terminal"),
            ("🖥️", "Systeminfo", "systeminfo"),
            ("🎮", "Spiele", "games"),
            ("ℹ️", "Über Browser OS", "about"),
        ]

        for index, (icon, name, app_id) in enumerate(apps):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 16px;
                }
            """)
            box = QVBoxLayout(card)
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFont(QFont("Segoe UI Emoji", 34))
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            open_btn = QPushButton("Öffnen")
            open_btn.clicked.connect(lambda _, a=app_id: main.open_app(a))
            pin_btn = QPushButton("📌 Anheften")
            pin_btn.clicked.connect(lambda _, a=app_id: main.pin_app(a))

            box.addWidget(icon_label)
            box.addWidget(name_label)
            box.addWidget(open_btn)
            box.addWidget(pin_btn)

            row = index // 3
            col = index % 3
            grid.addWidget(card, row, col)

        scroll.setWidget(inner)

        title = QLabel("🛒 Browser OS App Store")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(scroll, 1)


# ------------------------------------------------------------
# Desktop / window manager
# ------------------------------------------------------------


class DesktopClockWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DesktopWidget")
        self.setStyleSheet("""
            QFrame#DesktopWidget {
                background: rgba(18, 22, 34, 225);
                border: 1px solid rgba(255,255,255,35);
                border-radius: 18px;
            }
        """)
        layout = QVBoxLayout(self)
        title = QLabel("🕒 Uhr")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.value = QLabel()
        self.value.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date = QLabel()
        self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(self.value)
        layout.addWidget(self.date)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def update_clock(self):
        now = datetime.now()
        self.value.setText(now.strftime("%H:%M:%S"))
        self.date.setText(now.strftime("%A, %d.%m.%Y"))


class DesktopSystemWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DesktopWidget")
        self.setStyleSheet("""
            QFrame#DesktopWidget {
                background: rgba(18, 22, 34, 225);
                border: 1px solid rgba(255,255,255,35);
                border-radius: 18px;
            }
        """)
        layout = QVBoxLayout(self)
        title = QLabel("🖥️ System")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.text = QLabel()
        self.text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(self.text)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
        self.refresh()

    def refresh(self):
        try:
            root = Path.home().anchor or str(Path.home())
            total, used, free = shutil.disk_usage(root)
            self.text.setText(
                f"OS: {platform.system()}\n"
                f"CPU: {os.cpu_count() or 1} Kerne\n"
                f"Speicher frei: {free / (1024**3):.1f} GB"
            )
        except Exception:
            self.text.setText("Systeminfos nicht verfügbar")


class DesktopQuickWidget(QFrame):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.setObjectName("DesktopWidget")
        self.setStyleSheet("""
            QFrame#DesktopWidget {
                background: rgba(18, 22, 34, 225);
                border: 1px solid rgba(255,255,255,35);
                border-radius: 18px;
            }
        """)
        layout = QVBoxLayout(self)
        title = QLabel("⚡ Schnellzugriff")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        for label, app_id in [
            ("🌍 Browser", "browser"),
            ("📁 Dateien", "files"),
            ("📝 Notizen", "notes"),
            ("📥 Downloads", "downloads"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, a=app_id: self.main.open_app(a))
            layout.addWidget(btn)


class Desktop(QWidget):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.setObjectName("Desktop")

        self.bg_label = QLabel(self)
        self.bg_label.lower()

        self.topbar = QFrame(self)
        self.topbar.setObjectName("TopBar")
        self.topbar.setStyleSheet("""
            QFrame#TopBar {
                background: rgba(12,14,22,210);
                border-bottom: 1px solid rgba(255,255,255,30);
            }
        """)

        top = QHBoxLayout(self.topbar)
        top.setContentsMargins(12, 6, 12, 6)

        self.brand = QLabel("🌍 Browser OS")
        self.brand.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        self.workspace_combo = QComboBox()
        self.workspace_combo.addItems(settings.get("workspaces", ["Normal"]))
        self.workspace_combo.setCurrentText(settings.get("current_workspace", "Normal"))
        self.workspace_combo.currentTextChanged.connect(self.change_workspace)

        self.search_btn = QPushButton("🔎 Suche")
        self.search_btn.clicked.connect(self.main.open_super_search)

        self.add_workspace_btn = QPushButton("＋")
        self.add_workspace_btn.setToolTip("Arbeitsbereich hinzufügen")
        self.add_workspace_btn.clicked.connect(self.main.add_workspace)

        self.edit_btn = QPushButton("✏️ Anpassen")
        self.edit_btn.clicked.connect(self.main.open_desktop_editor)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.clicked.connect(lambda: self.main.open_app("settings"))

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        top.addWidget(self.brand)
        top.addSpacing(10)
        top.addWidget(self.workspace_combo)
        top.addWidget(self.add_workspace_btn)
        top.addStretch()
        top.addWidget(self.search_btn)
        top.addWidget(self.edit_btn)
        top.addWidget(self.settings_btn)
        top.addWidget(self.clock)

        self.desktop_area = QWidget(self)
        self.desktop_area.setObjectName("DesktopArea")
        self.desktop_area.setStyleSheet("background: transparent;")

        self.taskbar = QFrame(self)
        self.taskbar.setObjectName("Taskbar")
        self.taskbar.setStyleSheet("""
            QFrame#Taskbar {
                background: rgba(12,14,22,232);
                border-top: 1px solid rgba(255,255,255,25);
            }
        """)
        self.taskbar_layout = QHBoxLayout(self.taskbar)
        self.taskbar_layout.setContentsMargins(10, 7, 10, 7)
        self.taskbar_layout.setSpacing(7)

        self.start_task_btn = QPushButton("🌍")
        self.start_task_btn.setToolTip("Startmenü")
        self.start_task_btn.clicked.connect(self.main.open_start_menu)
        self.taskbar_layout.addWidget(self.start_task_btn)

        self.home_task_btn = QPushButton("🏠")
        self.home_task_btn.setToolTip("Desktop")
        self.home_task_btn.clicked.connect(self.show_desktop)
        self.taskbar_layout.addWidget(self.home_task_btn)

        self.app_task_buttons = {}

        self.tiles = []
        self.desktop_widgets = []
        self.rebuild_tiles()
        self.build_desktop_widgets()

        self.desktop_area.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.desktop_area.customContextMenuRequested.connect(
            self.main.show_desktop_context_menu
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def build_desktop_widgets(self):
        for widget in self.desktop_widgets:
            widget.deleteLater()
        self.desktop_widgets = [
            DesktopClockWidget(self.desktop_area),
            DesktopSystemWidget(self.desktop_area),
            DesktopQuickWidget(self.main, self.desktop_area),
        ]
        for widget in self.desktop_widgets:
            widget.show()
            widget.raise_()
        QTimer.singleShot(30, self.position_desktop_widgets)

    def position_desktop_widgets(self):
        area_w = self.desktop_area.width()
        x = max(20, area_w - 315)
        y = 30
        heights = [150, 145, 220]
        for index, widget in enumerate(self.desktop_widgets):
            widget.setGeometry(x, y, 285, heights[index])
            y += heights[index] + 14
            widget.raise_()

    def resizeEvent(self, event):
        top_h = 48 if self.topbar.isVisible() else 0
        task_h = 56 if self.taskbar.isVisible() else 0

        if top_h:
            self.topbar.setGeometry(0, 0, self.width(), top_h)
        else:
            self.topbar.setGeometry(0, 0, self.width(), 0)

        self.desktop_area.setGeometry(
            0,
            top_h,
            self.width(),
            max(0, self.height() - top_h - task_h),
        )

        if task_h:
            self.taskbar.setGeometry(
                0,
                self.height() - task_h,
                self.width(),
                task_h,
            )
        else:
            self.taskbar.setGeometry(
                0,
                self.height(),
                self.width(),
                0,
            )

        self.bg_label.setGeometry(self.rect())
        self.bg_label.lower()

        self.refresh_tile_bounds()
        self.position_desktop_widgets()
        super().resizeEvent(event)

    def update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S  •  %d.%m.%Y"))

    def rebuild_tiles(self):
        for tile in self.tiles:
            tile.deleteLater()
        self.tiles = []

        for data in settings.get("desktop_tiles", []):
            app_id = data.get("id", "browser")
            tile = DesktopTile(data, app_id, self.desktop_area)
            tile.moved.connect(self.main.save_settings)
            tile.launch.connect(self.main.open_app)
            tile.customize.connect(self.main.customize_tile)
            tile.show()
            tile.raise_()
            self.tiles.append(tile)

        QTimer.singleShot(30, self.refresh_tile_bounds)

    def refresh_tile_bounds(self):
        for tile in self.tiles:
            max_x = max(0, self.desktop_area.width() - tile.width())
            max_y = max(0, self.desktop_area.height() - tile.height())
            tile.move(
                min(max_x, max(0, tile.x())),
                min(max_y, max(0, tile.y())),
            )
            tile.data["x"] = tile.x()
            tile.data["y"] = tile.y()

    def change_workspace(self, name):
        if not name:
            return
        self.main.switch_workspace(name)

    def show_desktop(self):
        self.main.set_browsing_chrome_state(False)

        for window in self.main.virtual_windows:
            if window.workspace == self.main.current_workspace:
                window.hide()

        self.main.refresh_taskbar()
        for tile in self.tiles:
            tile.show()
            tile.raise_()


# ------------------------------------------------------------
# Desktop editor
# ------------------------------------------------------------

class DesktopEditorDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.setWindowTitle("🏠 Startseite / Desktop anpassen")
        self.resize(760, 640)

        tabs = QTabWidget()

        # Apps tab
        apps = QWidget()
        apps_layout = QVBoxLayout(apps)
        apps_layout.addWidget(QLabel(
            "Wähle, welche Apps auf dem Desktop liegen. Position und Größe "
            "kannst du danach direkt per Ziehen oder in 'App anpassen' ändern."
        ))

        self.app_list = QListWidget()
        existing = settings.get("desktop_tiles", [])
        existing_ids = {x.get("id") for x in existing}
        for app_id, (icon, name) in APP_INFO.items():
            item = QListWidgetItem(f"{icon}  {name}")
            item.setData(Qt.ItemDataRole.UserRole, app_id)
            self.app_list.addItem(item)
            item.setSelected(app_id in existing_ids)

        apps_layout.addWidget(self.app_list, 1)

        # Startpage tab
        start = QWidget()
        start_form = QFormLayout(start)

        self.layout_name = QLineEdit("Meine Startseite")

        save_layout_btn = QPushButton("💾 Aktuelles Layout speichern")
        save_layout_btn.clicked.connect(self.save_layout)

        load_layout_btn = QPushButton("📂 Gespeichertes Layout laden")
        load_layout_btn.clicked.connect(self.load_layout)

        open_folder_btn = QPushButton("📁 Startseiten-Ordner öffnen")
        open_folder_btn.clicked.connect(lambda: open_external(LAYOUTS_DIR))

        start_form.addRow("Layoutname:", self.layout_name)
        start_form.addRow(save_layout_btn)
        start_form.addRow(load_layout_btn)
        start_form.addRow(open_folder_btn)

        tabs.addTab(apps, "📌 Desktop-Apps")
        tabs.addTab(start, "💾 Layouts")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def apply(self):
        selected = [
            self.app_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.app_list.count())
            if self.app_list.item(i).isSelected()
        ]

        current_by_id = {x.get("id"): x for x in settings.get("desktop_tiles", [])}
        new_tiles = []

        x = 30
        y = 90
        for app_id in selected:
            old = deep_copy(current_by_id.get(app_id, {}))
            icon, name = APP_INFO.get(app_id, ("📦", app_id))
            old["id"] = app_id
            old["icon"] = old.get("icon", icon)
            old["name"] = old.get("name", name)
            old["x"] = old.get("x", x)
            old["y"] = old.get("y", y)
            old["w"] = old.get("w", 150)
            old["h"] = old.get("h", 92)
            new_tiles.append(old)

            x += 175
            if x > 650:
                x = 30
                y += 110

        settings["desktop_tiles"] = new_tiles
        save_json(SETTINGS_FILE, settings)
        self.main.rebuild_desktop()
        self.accept()

    def save_layout(self):
        name = safe_file_name(self.layout_name.text())
        if not name:
            return
        payload = {
            "name": self.layout_name.text(),
            "theme": settings.get("theme"),
            "accent": settings.get("accent"),
            "desktop_color": settings.get("desktop_color"),
            "wallpaper_mode": settings.get("wallpaper_mode"),
            "wallpaper_path": settings.get("wallpaper_path"),
            "start_menu_theme": settings.get("start_menu_theme"),
            "start_menu_background_mode": settings.get("start_menu_background_mode"),
            "start_menu_background_color": settings.get("start_menu_background_color"),
            "start_menu_background_path": settings.get("start_menu_background_path"),
            "custom_apps": settings.get("custom_apps", []),
            "pinned_apps": settings.get("pinned_apps", []),
            "desktop_tiles": settings.get("desktop_tiles", []),
            "show_clock": settings.get("show_clock"),
            "show_recent": settings.get("show_recent"),
            "show_pinned": settings.get("show_pinned"),
            "show_widgets": settings.get("show_widgets"),
        }
        path = LAYOUTS_DIR / f"{name}.boslayout"
        save_json(path, payload)
        QMessageBox.information(self, APP_NAME, f"Layout gespeichert:\n{path}")

    def load_layout(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Browser OS Layout öffnen",
            str(LAYOUTS_DIR),
            "Browser OS Layout (*.boslayout)",
        )
        if not path:
            return

        payload = load_json(Path(path), {})
        for key in (
            "theme",
            "accent",
            "desktop_color",
            "wallpaper_mode",
            "wallpaper_path",
            "start_menu_theme",
            "start_menu_background_mode",
            "start_menu_background_color",
            "start_menu_background_path",
            "custom_apps",
            "pinned_apps",
            "desktop_tiles",
            "show_clock",
            "show_recent",
            "show_pinned",
            "show_widgets",
        ):
            if key in payload:
                settings[key] = payload[key]

        save_json(SETTINGS_FILE, settings)
        self.main.apply_theme()
        self.main.rebuild_desktop()
        QMessageBox.information(self, APP_NAME, "Layout geladen.")



class FirstRunSetupDialog(QDialog):
    """Simple first-start setup for Browser OS."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌍 Browser OS Setup")
        self.setMinimumSize(620, 500)
        self.selected_engine = settings.get("search_engine", "Google")

        layout = QVBoxLayout(self)

        title = QLabel("🌍 Browser OS Setup")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(
            "Wähle deine Suchmaschine. Du kannst sie als Standard für "
            "Browser OS speichern oder zuerst nur testen."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)


        # Default browser selection
        browser_group = QGroupBox("🌍 Standardbrowser")
        browser_layout = QVBoxLayout(browser_group)

        self.browser_choice = QComboBox()
        previous_name = settings.get(
            "previous_browser_name",
            get_previous_default_browser(),
        )

        self.browser_choice.addItem(
            f"🌍 Browser OS als Standardbrowser",
            "browseros",
        )
        self.browser_choice.addItem(
            f"↩️ {previous_name} beibehalten",
            "previous",
        )

        browser_choice_saved = settings.get(
            "browser_default_choice",
            "previous",
        )
        browser_index = self.browser_choice.findData(browser_choice_saved)
        self.browser_choice.setCurrentIndex(
            browser_index if browser_index >= 0 else 1
        )

        browser_layout.addWidget(self.browser_choice)

        browser_help = QLabel(
            "Windows 11 entscheidet die endgültige Standard-App über "
            "die Standard-Apps-Einstellungen. Browser OS registriert sich "
            "dort und öffnet direkt seine eigene Seite; dort bestätigst "
            "du die gewünschten Zuordnungen."
        )
        browser_help.setWordWrap(True)
        browser_layout.addWidget(browser_help)

        open_defaults = QPushButton("⚙️ Windows Standard-Apps öffnen")
        open_defaults.clicked.connect(open_windows_default_apps)
        browser_layout.addWidget(open_defaults)

        layout.addWidget(browser_group)

        group = QGroupBox("🔎 Suchmaschine")
        group_layout = QVBoxLayout(group)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems([
            "Google",
            "Bing",
            "Yahoo",
            "DuckDuckGo",
            "Brave Search",
            "Startpage",
            "Ecosia",
            "Eigene",
        ])
        self.engine_combo.setCurrentText(self.selected_engine)
        group_layout.addWidget(self.engine_combo)

        self.custom_url = QLineEdit(
            settings.get(
                "custom_search_url",
                "https://www.google.com/search?q={query}",
            )
        )
        self.custom_url.setPlaceholderText(
            "https://example.com/search?q={query}"
        )
        self.custom_url.setEnabled(self.engine_combo.currentText() == "Eigene")
        group_layout.addWidget(self.custom_url)

        layout.addWidget(group)

        self.mode_label = QLabel(
            "✅ Standard: Diese Suchmaschine wird für neue Suchen verwendet."
        )
        self.mode_label.setWordWrap(True)
        layout.addWidget(self.mode_label)

        info = QLabel(
            "💡 Mit „Nur testen“ wird die Suchmaschine geöffnet, ohne sie "
            "als Browser-OS-Standard festzulegen."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()

        buttons = QHBoxLayout()

        self.test_button = QPushButton("🧪 Nur testen")
        self.test_button.clicked.connect(self.test_engine)

        self.standard_button = QPushButton("⭐ Als Standard verwenden")
        self.standard_button.clicked.connect(self.use_as_standard)

        buttons.addWidget(self.test_button)
        buttons.addWidget(self.standard_button)

        layout.addLayout(buttons)

        self.engine_combo.currentTextChanged.connect(
            self.update_engine_ui
        )

    def update_engine_ui(self, value):
        self.custom_url.setEnabled(value == "Eigene")
        self.mode_label.setText(
            "✅ Standard: Diese Suchmaschine wird für neue Suchen verwendet."
            if value != "Eigene" or self.custom_url.text().strip()
            else "⚠️ Eigene Suchmaschine braucht eine Such-URL mit {query}."
        )

    def engine_url(self):
        engine = self.engine_combo.currentText()

        built_in = {
            "Google": "https://www.google.com/search?q={query}",
            "Bing": "https://www.bing.com/search?q={query}",
            "Yahoo": "https://search.yahoo.com/search?p={query}",
            "DuckDuckGo": "https://duckduckgo.com/?q={query}",
            "Brave Search": "https://search.brave.com/search?q={query}",
            "Startpage": "https://www.startpage.com/sp/search?query={query}",
            "Ecosia": "https://www.ecosia.org/search?q={query}",
        }

        if engine == "Eigene":
            return self.custom_url.text().strip()

        return built_in.get(engine, built_in["Google"])

    def test_engine(self):
        settings["browser_default_choice"] = self.browser_choice.currentData() or "previous"
        settings["previous_browser_name"] = get_previous_default_browser()
        save_json(SETTINGS_FILE, settings)

        engine = self.engine_combo.currentText()
        url = self.engine_url()

        if not url or "{query}" not in url:
            QMessageBox.warning(
                self,
                APP_NAME,
                "Für eine eigene Suchmaschine muss die URL {query} enthalten."
            )
            return

        # Remember only the temporary test choice. It is NOT made standard.
        settings["setup_test_engine"] = engine
        settings["setup_test_url"] = url
        save_json(SETTINGS_FILE, settings)

        QMessageBox.information(
            self,
            APP_NAME,
            f"🧪 {engine} wird getestet.\n\n"
            "Nach dem Setup kannst du sie jederzeit in Einstellungen "
            "als Standard auswählen."
        )

        self.done(2)

    def use_as_standard(self):
        engine = self.engine_combo.currentText()
        url = self.engine_url()

        if not url or "{query}" not in url:
            QMessageBox.warning(
                self,
                APP_NAME,
                "Für eine eigene Suchmaschine muss die URL {query} enthalten."
            )
            return

        settings["search_engine"] = engine
        settings["custom_search_url"] = url
        settings["search_engine_mode"] = "standard"
        settings["browser_default_choice"] = self.browser_choice.currentData() or "previous"
        settings["previous_browser_name"] = get_previous_default_browser()
        settings["setup_completed"] = True
        settings.pop("setup_test_engine", None)
        settings.pop("setup_test_url", None)

        save_json(SETTINGS_FILE, settings)
        self.accept()

# ------------------------------------------------------------
# Main OS
# ------------------------------------------------------------

class BrowserOS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🌍 Browser OS {VERSION}")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)

        self.virtual_windows = []
        self.task_buttons = {}
        self.current_workspace = settings.get("current_workspace", "Normal")
        self.mail_service = MailService(self)

        self.app_last_positions = {}
        self.app_counters = {}


        self.root = QWidget()
        self.root.setObjectName("Root")
        self.setCentralWidget(self.root)

        self.desktop = Desktop(self)
        layout = QVBoxLayout(self.root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.desktop)

        self.apply_theme()

        self.super_search_hotkey = None

        # First-start setup happens after the main window exists, so the
        # desktop can always be created first.
        QTimer.singleShot(150, self.run_first_start_setup)

        if settings.get("auto_restore", True) and settings.get("startup_mode") == "restore":
            QTimer.singleShot(500, self.restore_last_session_if_available)

        # Periodic autosave
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(15000)

    def get_web_profile(self):
        profile = getattr(self, "web_profile", None)

        if profile is None:
            profile = QWebEngineProfile("BrowserOSProfile", self)
            profile.setPersistentStoragePath(str(WEB_PROFILE_DIR))
            profile.setCachePath(str(CACHE_DIR))
            profile.downloadRequested.connect(self.handle_download)
            # Qt WebEngine 6.10+ provides a real Chrome/Firefox-compatible
            # Manifest V3 extension manager. It is optional so older PyQt6
            # installations can still start Browser OS normally.
            if WEBENGINE_EXTENSIONS_AVAILABLE:
                try:
                    profile.extensionManager()
                except Exception:
                    pass
            self.web_profile = profile

        return profile

    def run_first_start_setup(self):
        if settings.get("setup_completed", False):
            return

        dialog = FirstRunSetupDialog(self)

        result = dialog.exec()

        # Browser OS registration is prepared silently.
        # The browser and Windows Settings are NOT started automatically.
        if settings.get("browser_default_choice") == "browseros":
            register_browser_windows()

        if result == 2:
            # User chose "only test": open the selected search engine
            # without making it the standard search engine.
            test_url = settings.get("setup_test_url", "")
            if test_url:
                test_url = test_url.replace(
                    "{query}",
                    "Browser OS",
                )
                self.open_app("browser", url=test_url)

            settings["setup_completed"] = True
            settings["search_engine_mode"] = "test"
            save_json(SETTINGS_FILE, settings)

    def apply_theme(self):
        QApplication.instance().setStyleSheet(build_stylesheet())
        self.update_background()

    def update_background(self):
        mode = settings.get("wallpaper_mode", "color")
        path = settings.get("wallpaper_path", "")
        if mode == "image" and path and Path(path).exists():
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.desktop.bg_label.setPixmap(
                    pixmap.scaled(
                        self.desktop.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.desktop.bg_label.setStyleSheet("background:#111;")
                return
        self.desktop.bg_label.clear()
        self.desktop.bg_label.setStyleSheet(
            f"background:{settings.get('desktop_color','#11131a')};"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def save_settings(self):
        # Pull current tile positions from widgets
        tile_map = {x.get("id"): x for x in settings.get("desktop_tiles", [])}
        for tile in getattr(self.desktop, "tiles", []):
            data = tile_map.get(tile.app_id)
            if data is not None:
                data["x"] = tile.x()
                data["y"] = tile.y()
                data["w"] = tile.width()
                data["h"] = tile.height()
        settings["current_workspace"] = self.current_workspace
        save_json(SETTINGS_FILE, settings)

    def rebuild_desktop(self):
        self.apply_theme()
        self.desktop.workspace_combo.blockSignals(True)
        self.desktop.workspace_combo.clear()
        self.desktop.workspace_combo.addItems(settings.get("workspaces", ["Normal"]))
        self.desktop.workspace_combo.setCurrentText(self.current_workspace)
        self.desktop.workspace_combo.blockSignals(False)
        self.desktop.rebuild_tiles()
        self.desktop.update()

        # Update visibility based on workspace
        self.switch_workspace(self.current_workspace)

    def refresh_everything(self):
        self.rebuild_desktop()
        self.refresh_taskbar()

    def show_message(self, text):
        QMessageBox.information(self, APP_NAME, text)

    def pin_app(self, app_id):
        pinned = settings.setdefault("pinned_apps", [])
        if app_id not in pinned:
            pinned.append(app_id)
            save_json(SETTINGS_FILE, settings)
            self.show_message("App an die Startseite angeheftet.")
        else:
            self.show_message("Die App ist bereits angeheftet.")

    def unpin_app(self, app_id):
        pinned = settings.setdefault("pinned_apps", [])
        if app_id in pinned:
            pinned.remove(app_id)
            save_json(SETTINGS_FILE, settings)

    def customize_tile(self, tile):
        data = deep_copy(tile.data)
        dialog = TileEditDialog(data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.data()
            new_data["id"] = tile.app_id
            tile.data.update(new_data)
            tile.refresh()

            for item in settings.get("desktop_tiles", []):
                if item.get("id") == tile.app_id:
                    item.update(tile.data)

            save_json(SETTINGS_FILE, settings)

    def create_virtual_window(self, title, icon, content, width=900, height=620):
        window = VirtualWindow(
            self,
            title,
            icon,
            width,
            height,
            self.current_workspace,
        )
        window.set_content(content)
        window.closed.connect(self.on_virtual_window_closed)
        window.changed.connect(self.save_settings)
        window.show()
        window.raise_()
        self.virtual_windows.append(window)
        self.refresh_taskbar()
        self.hide_tiles_behind_window()
        return window

    def hide_tiles_behind_window(self):
        for tile in self.desktop.tiles:
            tile.raise_()

    def on_virtual_window_closed(self, window):
        if window in self.virtual_windows:
            self.virtual_windows.remove(window)
        self.refresh_taskbar()
        self.save_settings()

    def set_browsing_chrome_state(self, hidden):
        """Hide the OS topbar and bottom taskbar while the browser is maximized."""
        if hidden:
            self.desktop.topbar.hide()
            self.desktop.taskbar.hide()
        else:
            self.desktop.topbar.show()
            self.desktop.taskbar.show()

        # Recalculate desktop geometry so the browser gets the freed space.
        self.desktop.resize(
            self.desktop.width(),
            self.desktop.height(),
        )

    # Backward-compatible helper for older calls.
    def set_browsing_taskbar_state(self, hidden):
        self.set_browsing_chrome_state(hidden)

    def refresh_taskbar(self):
        for button in list(self.task_buttons.values()):
            button.deleteLater()
        self.task_buttons.clear()

        # Keep Startmenü + Desktop buttons as the first two widgets.
        while self.desktop.taskbar_layout.count() > 2:
            item = self.desktop.taskbar_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for index, window in enumerate(self.virtual_windows):
            if window.workspace != self.current_workspace:
                continue

            btn = QPushButton(window.title_label.text())
            btn.setMaximumWidth(180)
            btn.setToolTip("Fenster anzeigen / verstecken")
            btn.clicked.connect(
                lambda checked=False, w=window: self.toggle_window(w)
            )
            self.desktop.taskbar_layout.addWidget(btn)
            self.task_buttons[window] = btn

        spacer = QWidget()
        self.desktop.taskbar_layout.addWidget(spacer, 1)

        folder_btn = QPushButton("📁 Browser OS Ordner")
        folder_btn.clicked.connect(lambda: open_external(APP_DIR))
        self.desktop.taskbar_layout.addWidget(folder_btn)

        store_btn = QPushButton("🛒")
        store_btn.clicked.connect(lambda: self.open_app("store"))
        self.desktop.taskbar_layout.addWidget(store_btn)

    def toggle_window(self, window):
        if window.minimized or not window.isVisible():
            window.restore()
        else:
            window.hide()
            window.minimized = True
        window.raise_()
        self.refresh_taskbar()

    def open_browser_import(self):
        dialog = BrowserImportDialog(self, self)
        dialog.exec()
        self.refresh_everything()

    def open_app(self, app_id, url=None):
        content = None
        title = APP_INFO.get(app_id, ("📦", app_id))[1]
        icon = APP_INFO.get(app_id, ("📦", app_id))[0]
        width = 900
        height = 620


        if app_id == "browser":
            try:
                window = self.create_virtual_window(
                    "Browser",
                    "🌍",
                    QWidget(),
                    1180,
                    760,
                )

                browser = BrowserApp(self, window)

                old_layout = window.content.layout()
                if old_layout is None:
                    old_layout = QVBoxLayout(window.content)

                while old_layout.count():
                    item = old_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()

                old_layout.addWidget(browser)

                if url:
                    tab = browser.current_tab()
                    if tab:
                        tab.load(url)

                return window

            except Exception as exc:
                QMessageBox.critical(
                    self,
                    APP_NAME,
                    "Der Browser konnte nicht geöffnet werden.\n\n"
                    f"{type(exc).__name__}: {exc}\n\n"
                    "Browser OS selbst bleibt geöffnet.",
                )
                return None

        custom = find_custom_app(app_id)
        if custom is not None:
            return self.open_custom_app(custom)

        if app_id == "files":
            content = FileExplorerApp()
            title = "Dateien"
            width, height = 900, 600
        elif app_id == "notes":
            content = NotesApp()
            title = "Notizen"
            width, height = 760, 600
        elif app_id == "calculator":
            content = CalculatorApp()
            title = "Rechner"
            width, height = 420, 620
        elif app_id == "settings":
            dialog = SettingsDialog(self, self)
            dialog.exec()
            return None
        elif app_id == "mail":
            content = LocalMailApp(self)
            title = "Mails"
            width, height = 760, 600
        elif app_id == "downloads":
            content = SimpleLauncherApp("Downloads", DOWNLOADS_DIR, "📥")
            title = "Downloads"
            width, height = 600, 360
        elif app_id == "music":
            content = SimpleLauncherApp("Musik", Path.home() / "Music", "🎵")
            title = "Musik"
            width, height = 600, 360
        elif app_id == "videos":
            content = SimpleLauncherApp("Videos", Path.home() / "Videos", "🎬")
            title = "Videos"
            width, height = 600, 360
        elif app_id == "pictures":
            content = SimpleLauncherApp("Bilder", Path.home() / "Pictures", "🖼️")
            title = "Bilder"
            width, height = 600, 360
        elif app_id == "calendar":
            content = CalendarApp()
            title = "Kalender"
            width, height = 720, 620
        elif app_id == "terminal":
            content = TerminalApp()
            title = "Terminal"
            width, height = 520, 360
        elif app_id == "systeminfo":
            content = SystemInfoApp()
            title = "Systeminfo"
            width, height = 650, 520
        elif app_id == "trash":
            content = SimpleLauncherApp("Papierkorb", "shell:RecycleBinFolder", "🗑️")
            title = "Papierkorb"
            width, height = 600, 360
        elif app_id == "games":
            content = GamesApp(self)
            title = "Spiele"
            width, height = 620, 520
        elif app_id == "about":
            content = AboutApp()
            title = "Über Browser OS"
            width, height = 620, 360
        elif app_id == "sessions":
            content = SessionsApp(self)
            title = "Browser-Sitzungen"
            width, height = 680, 560
        elif app_id == "history":
            content = HistoryApp(self)
            title = "Verlauf"
            width, height = 760, 600
        elif app_id == "bookmarks":
            content = BookmarksApp(self)
            title = "Lesezeichen"
            width, height = 760, 600
        elif app_id == "taskmanager":
            content = TaskManagerApp()
            title = "Task Manager"
            width, height = 820, 600
        elif app_id == "store":
            content = StoreApp(self)
            title = "App Store"
            width, height = 720, 620
        else:
            QMessageBox.information(
                self,
                APP_NAME,
                f"App '{app_id}' ist nicht installiert.",
            )
            return None

        return self.create_virtual_window(
            title,
            icon,
            content,
            width,
            height,
        )

    def show_desktop_context_menu(self, local_pos):
        menu = QMenu(self)
        add = menu.addMenu("➕ Neu")
        for app_id in ("browser", "files", "notes", "mail", "downloads", "calendar", "terminal"):
            icon, name = APP_INFO[app_id]
            action = add.addAction(f"{icon} {name}")
            action.triggered.connect(lambda _, a=app_id: self.open_app(a))

        menu.addSeparator()
        refresh = menu.addAction("🔄 Desktop aktualisieren")
        refresh.triggered.connect(self.rebuild_desktop)
        customize = menu.addAction("✏️ Desktop anpassen")
        customize.triggered.connect(self.open_desktop_editor)
        menu.addAction("🔎 Suche").triggered.connect(self.open_super_search)
        menu.addSeparator()
        about = menu.addAction("ℹ️ Über Browser OS")
        about.triggered.connect(lambda: self.open_app("about"))

        try:
            global_pos = self.desktop.desktop_area.mapToGlobal(local_pos)
            menu.exec(global_pos)
        except Exception:
            menu.exec(QCursor.pos())

    def open_start_menu(self):
        dialog = StartMenuDialog(self, self)
        # Position above the taskbar/start button.
        try:
            btn = self.desktop.start_task_btn
            global_pos = btn.mapToGlobal(QPoint(0, 0))
            x = max(8, global_pos.x())
            y = max(8, global_pos.y() - dialog.height() - 8)
            dialog.move(x, y)
        except Exception:
            dialog.move(20, max(20, self.height() - dialog.height() - 80))
        dialog.exec()

    def save_custom_app(self, app):
        apps = settings.setdefault("custom_apps", [])
        existing = find_custom_app(app.get("id"))
        if existing is None:
            apps.append(app)
        else:
            existing.update(app)
        save_json(SETTINGS_FILE, settings)

    def open_custom_app(self, app):
        if not app:
            return None

        if app.get("type") == "pc":
            path = app.get("path", "")
            if not path or not Path(path).exists():
                QMessageBox.warning(self, APP_NAME, f"Die PC-App wurde nicht gefunden:\n{path}")
                return None
            try:
                suffix = Path(path).suffix.lower()
                if suffix == ".py":
                    subprocess.Popen([sys.executable, path], cwd=str(Path(path).parent))
                elif suffix in (".bat", ".cmd", ".lnk"):
                    os.startfile(path)
                else:
                    subprocess.Popen([path], cwd=str(Path(path).parent))
                return None
            except Exception as exc:
                QMessageBox.critical(self, APP_NAME, f"PC-App konnte nicht gestartet werden:\n{exc}")
                return None

        if app.get("type") == "web":
            url = app.get("url", "")
            if not url.startswith(("http://", "https://")):
                QMessageBox.warning(self, APP_NAME, "Diese Website-App hat keine gültige URL.")
                return None

            content = QFrame()
            content.setStyleSheet(f"background:{app.get('background_color', '#11131a')};")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            web = WebAppView(self, content)
            web.setUrl(QUrl(url))
            layout.addWidget(web)

            return self.create_virtual_window(
                app.get("name", "Website-App"),
                app.get("icon", "🌐"),
                content,
                int(app.get("width", 1100)),
                int(app.get("height", 720)),
            )

        return None

    def open_desktop_editor(self):
        dialog = DesktopEditorDialog(self, self)
        dialog.exec()

    def open_super_search(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("🔎 Browser OS Suche")
        dialog.resize(620, 500)

        layout = QVBoxLayout(dialog)

        search = QLineEdit()
        search.setPlaceholderText("Apps, URLs, Verlauf, Dateien …")
        search.setFocus()

        results = QListWidget()

        def do_search():
            query = search.text().strip().lower()
            results.clear()
            if not query:
                return

            for app_id, (icon, name) in APP_INFO.items():
                if query in name.lower() or query in app_id.lower():
                    item = QListWidgetItem(f"{icon} {name}")
                    item.setData(Qt.ItemDataRole.UserRole, ("app", app_id))
                    results.addItem(item)

            for app in get_custom_apps():
                name = app.get("name", "App")
                url = app.get("url", "")
                if query in name.lower() or query in url.lower():
                    item = QListWidgetItem(f"{app.get('icon','📦')} {name}")
                    item.setData(Qt.ItemDataRole.UserRole, ("custom", app.get("id")))
                    results.addItem(item)

            for item in history[:50]:
                text = f"{item.get('title','')} {item.get('url','')}".lower()
                if query in text:
                    row = QListWidgetItem(
                        f"🌍 {item.get('title', item.get('url',''))}\n"
                        f"{item.get('url','')}"
                    )
                    row.setData(Qt.ItemDataRole.UserRole, ("url", item.get("url", "")))
                    results.addItem(row)

        search.textChanged.connect(do_search)

        def open_result():
            item = results.currentItem()
            if not item:
                return
            kind, value = item.data(Qt.ItemDataRole.UserRole)
            dialog.accept()
            if kind == "app":
                self.open_app(value)
            elif kind == "custom":
                custom = find_custom_app(value)
                if custom:
                    self.open_custom_app(custom)
            else:
                self.open_app("browser", url=value)

        search.returnPressed.connect(open_result)
        results.itemDoubleClicked.connect(lambda _: open_result())

        layout.addWidget(search)
        layout.addWidget(results, 1)
        dialog.exec()

    def add_workspace(self):
        name, ok = self.simple_input("Neuer Arbeitsbereich", "Name:")
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        if name in settings.get("workspaces", []):
            return
        settings.setdefault("workspaces", []).append(name)
        save_json(SETTINGS_FILE, settings)

        self.desktop.workspace_combo.blockSignals(True)
        self.desktop.workspace_combo.addItem(name)
        self.desktop.workspace_combo.setCurrentText(name)
        self.desktop.workspace_combo.blockSignals(False)

        self.switch_workspace(name)

    def switch_workspace(self, name):
        if not name:
            return
        self.current_workspace = name
        settings["current_workspace"] = name
        save_json(SETTINGS_FILE, settings)

        for window in self.virtual_windows:
            if window.workspace == name:
                if window.minimized:
                    window.hide()
                else:
                    window.show()
            else:
                window.hide()

        self.refresh_taskbar()

        for tile in self.desktop.tiles:
            tile.raise_()

    def simple_input(self, title, label):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(label))
        edit = QLineEdit()
        layout.addWidget(edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        ok = dialog.exec() == QDialog.DialogCode.Accepted
        return edit.text(), ok

    def handle_download(self, download):
        try:
            DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
            filename = download.downloadFileName() or "download"
            path = DOWNLOADS_DIR / filename
            counter = 1
            stem = path.stem
            suffix = path.suffix
            while path.exists():
                path = DOWNLOADS_DIR / f"{stem} ({counter}){suffix}"
                counter += 1
            download.setDownloadDirectory(str(DOWNLOADS_DIR))
            download.setDownloadFileName(path.name)
            download.accept()

            QMessageBox.information(
                self,
                APP_NAME,
                f"Download gestartet:\n{path}",
            )
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Download-Fehler:\n{exc}")

    def capture_all_browser_windows(self, callback):
        # Browser windows are isolated child processes. The main Browser OS
        # intentionally does not inspect their Chromium tabs because doing
        # so would reintroduce the crash-prone WebEngine into the main process.
        callback({
            "created": now_string(),
            "workspace": self.current_workspace,
            "windows": [],
        })

    def autosave(self):
        if not settings.get("auto_save", True):
            return

        def save(data):
            save_json(WINDOW_STATE_FILE, data)

        self.capture_all_browser_windows(save)

    def restore_last_session_if_available(self):
        if WINDOW_STATE_FILE.exists():
            data = load_json(WINDOW_STATE_FILE, {})
            if data.get("windows"):
                self.restore_session(data)

    def restore_session(self, data):
        windows = data.get("windows", [])

        for entry in windows:
            tabs = entry.get("tabs", [])
            first_url = tabs[0].get("url", "browseros://home") if tabs else "browseros://home"
            window = self.open_app(
                "browser",
                url=first_url,
            )
            if not window:
                continue

            window.workspace = entry.get("workspace", self.current_workspace)
            window.setGeometry(
                int(entry.get("x", 60)),
                int(entry.get("y", 80)),
                int(entry.get("w", 1000)),
                int(entry.get("h", 680)),
            )

            content_layout = window.content.layout()
            browser = None
            for i in range(content_layout.count()):
                widget = content_layout.itemAt(i).widget()
                if isinstance(widget, BrowserApp):
                    browser = widget
                    break

            if browser is None:
                continue

            # First tab already exists.
            while browser.tabs.count() > 1:
                browser.close_current_tab(1)

            if tabs:
                first = tabs[0]
                first_tab = browser.tabs.widget(0)
                if isinstance(first_tab, BrowserTab):
                    first_tab.scroll_target = int(first.get("scroll_y", 0))
                    first_tab.load(first.get("url", "browseros://home"))
                    first_tab.view.setZoomFactor(float(first.get("zoom", 1.0)))

                for tab_data in tabs[1:]:
                    tab = browser.add_tab(tab_data.get("url", "browseros://home"))
                    tab.scroll_target = int(tab_data.get("scroll_y", 0))
                    tab.view.setZoomFactor(float(tab_data.get("zoom", 1.0)))

                # Restore the tab marked as active.
                active_index = 0
                for i, tab_data in enumerate(tabs):
                    if tab_data.get("active"):
                        active_index = i
                        break
                browser.tabs.setCurrentIndex(active_index)

            window.show()
            window.raise_()

        self.refresh_taskbar()

    def closeEvent(self, event):
        if settings.get("auto_save", True):
            self.autosave()

        save_json(SETTINGS_FILE, settings)

        reply = QMessageBox.question(
            self,
            APP_NAME,
            "Browser OS schließen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()




# ------------------------------------------------------------
# Launcher
# ------------------------------------------------------------

def main():
    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts,
        True,
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("Browser OS")

    # Never auto-start Browser OS from old startup registry entries.
    remove_browseros_autostart()

    if len(sys.argv) > 1 and sys.argv[1] == "--register-default":
        ok, message = register_browser_windows()

        QMessageBox.information(
            None,
            APP_NAME,
            message
            + "\n\n"
            "Browser OS wird danach NICHT automatisch gestartet. "
            "Öffne Windows → Standard-Apps selbst, wenn du die Auswahl bestätigen möchtest."
        )
        return 0

    # If Windows launches Browser OS for an URL/HTML/PDF file,
    # keep that argument and open it inside the Browser OS browser.
    launch_target = ""
    if len(sys.argv) > 1:
        possible_args = [
            arg for arg in sys.argv[1:]
            if arg and not arg.startswith("--")
        ]
        if possible_args:
            launch_target = possible_args[0].strip('"')

    window = BrowserOS()
    window.show()

    if launch_target:
        QTimer.singleShot(
            250,
            lambda: window.open_app("browser", url=launch_target),
        )

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        import traceback

        traceback.print_exc()

        try:
            QMessageBox.critical(
                None,
                APP_NAME,
                "Browser OS konnte nicht gestartet werden.\n\n"
                f"{type(exc).__name__}: {exc}\n\n"
                "Die vollständige Fehlermeldung wurde auch in der Konsole ausgegeben.",
            )
        except Exception:
            pass

        raise
