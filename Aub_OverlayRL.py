import os
import sys
import json
import time
import random
import ctypes
from ctypes import wintypes

import psutil
from curl_cffi import requests as cffi_requests

from PySide6.QtCore import Qt, QTimer, QRectF, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QIcon, QGuiApplication,
    QAction, QActionGroup
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu, QInputDialog,
    QMainWindow, QLabel, QVBoxLayout, QFrame
)

try:
    import win32gui
    HAS_WIN32GUI = True
except ImportError:
    HAS_WIN32GUI = False


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def writable_path(filename):
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


CACHE_FILE = writable_path("cache.json")
CONFIG_FILE = writable_path("config.json")
ICON_FILE = resource_path("icone.ico")


GWL_EXSTYLE       = -20
WS_EX_TOPMOST     = 0x00000008
WS_EX_NOACTIVATE  = 0x08000000
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_APPWINDOW   = 0x00040000

HWND_TOPMOST   = -1
SWP_NOMOVE     = 0x0002
SWP_NOSIZE     = 0x0001
SWP_NOACTIVATE = 0x0010

WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_BLURBEHIND = 3


class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_uint),
        ("AccentFlags", ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_uint),
    ]


class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENT_POLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]


def enable_blur(hwnd):
    try:
        accent = ACCENT_POLICY()
        accent.AccentState = ACCENT_ENABLE_BLURBEHIND
        accent.AccentFlags = 0
        accent.GradientColor = 0
        accent.AnimationId = 0

        data = WINCOMPATTRDATA()
        data.Attribute = WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.pointer(accent)

        set_window_composition = ctypes.windll.user32.SetWindowCompositionAttribute
        set_window_composition(wintypes.HWND(hwnd), ctypes.pointer(data))
    except Exception:
        pass


def apply_overlay_styles(hwnd):
    try:
        user32 = ctypes.windll.user32
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= (
            WS_EX_TOPMOST
            | WS_EX_NOACTIVATE
            | WS_EX_LAYERED
            | WS_EX_TRANSPARENT
        )
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        user32.SetWindowPos(
            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
    except Exception:
        pass


def apply_appwindow_style(hwnd):
    try:
        user32 = ctypes.windll.user32
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
    except Exception:
        pass


def push_topmost(hwnd):
    try:
        ctypes.windll.user32.SetWindowPos(
            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
    except Exception:
        pass


def is_rl_running():
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if name == "rocketleague.exe":
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def is_rl_focused():
    if not HAS_WIN32GUI:
        return True
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or ""
        return "Rocket League" in title
    except Exception:
        return False


def detect_team_color():
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        sample_points = [
            (int(screen_w * 0.905), int(screen_h * 0.915)),
            (int(screen_w * 0.915), int(screen_h * 0.935)),
            (int(screen_w * 0.925), int(screen_h * 0.955)),
            (int(screen_w * 0.890), int(screen_h * 0.945)),
            (int(screen_w * 0.940), int(screen_h * 0.925)),
            (int(screen_w * 0.880), int(screen_h * 0.920)),
        ]

        hdc = user32.GetDC(0)
        if not hdc:
            return None

        blue_hits = 0
        orange_hits = 0

        for x, y in sample_points:
            raw = gdi32.GetPixel(hdc, x, y)
            if raw == 0xFFFFFFFF or raw < 0:
                continue
            r = raw & 0xFF
            g = (raw >> 8) & 0xFF
            b = (raw >> 16) & 0xFF

            if b > 140 and b > r + 40 and b > g + 20:
                blue_hits += 1
            elif r > 180 and g > 60 and g < 170 and b < 90 and r > b + 80:
                orange_hits += 1

        user32.ReleaseDC(0, hdc)

        if blue_hits >= 2 and blue_hits > orange_hits:
            return "blue"
        if orange_hits >= 2 and orange_hits > blue_hits:
            return "orange"
        return None
    except Exception:
        return None


IMPERSONATIONS = ["chrome124", "chrome120", "edge101"]
CACHE_TTL_SECONDS = 30


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def fetch_mmr(username):
    cache = load_cache()
    entry = cache.get(username)
    if entry and (time.time() - entry.get("timestamp", 0) < CACHE_TTL_SECONDS):
        return entry.get("mmr")

    url = (
        "https://api.tracker.gg/api/v2/rocket-league/standard/profile/"
        f"epic/{username}"
    )
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://rocketleague.tracker.network/",
        "origin": "https://rocketleague.tracker.network",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
    }

    try:
        imp = random.choice(IMPERSONATIONS)
        resp = cffi_requests.get(url, headers=headers, impersonate=imp, timeout=15)
        if resp.status_code != 200:
            return entry.get("mmr") if entry else None
        payload = resp.json()
    except Exception:
        return entry.get("mmr") if entry else None

    try:
        segments = payload["data"]["segments"]
        mmr = None
        for seg in segments:
            meta = seg.get("metadata") or {}
            attrs = seg.get("attributes") or {}
            name = meta.get("name") or ""
            playlist = attrs.get("playlist") or ""
            if "Ranked Doubles 2v2" in name or "Ranked Doubles 2v2" in playlist:
                rating = seg["stats"]["rating"]["value"]
                mmr = float(rating)
                break
        if mmr is None:
            return entry.get("mmr") if entry else None

        cache[username] = {"mmr": mmr, "timestamp": time.time()}
        save_cache(cache)
        return mmr
    except Exception:
        return entry.get("mmr") if entry else None


class SessionTracker:
    def __init__(self):
        self.streak = 0
        self.wins = 0
        self.losses = 0
        self._last_mmr = None

    def update(self, mmr):
        if mmr is None:
            return False
        if self._last_mmr is None:
            self._last_mmr = mmr
            return False
        if mmr > self._last_mmr:
            self.streak = self.streak + 1 if self.streak > 0 else 1
            self.wins += 1
            self._last_mmr = mmr
            return True
        if mmr < self._last_mmr:
            self.streak = self.streak - 1 if self.streak < 0 else -1
            self.losses += 1
            self._last_mmr = mmr
            return True
        return False

    def reset(self):
        self.streak = 0
        self.wins = 0
        self.losses = 0
        self._last_mmr = None


TEAM_TINTS = {
    "blue":    (40, 80, 170, 150),
    "orange":  (200, 110, 30, 150),
    "neutral": (20, 20, 20, 150),
}

TEAM_BORDER = {
    "blue":    (120, 170, 255, 90),
    "orange":  (255, 170, 90, 90),
    "neutral": (255, 255, 255, 30),
}


class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.mmr = None
        self.streak = 0
        self.wins = 0
        self.losses = 0
        self.team = "neutral"

        self.font = QFont("Segoe UI", 11, QFont.Bold)
        self._position_window()

    def _segments(self):
        mmr_text = f"MMR: {int(self.mmr)}" if self.mmr is not None else "MMR: --"

        if self.streak > 0:
            streak_text = f"🔥 Win Streak: {self.streak}"
            streak_color = QColor(80, 220, 100)
        elif self.streak < 0:
            streak_text = f"🧊 Loss Streak: {abs(self.streak)}"
            streak_color = QColor(220, 80, 80)
        else:
            streak_text = "Streak: 0"
            streak_color = QColor(160, 160, 160)

        sep = "   "
        return [
            (mmr_text, QColor(255, 255, 255)),
            (sep, None),
            (f"W:{self.wins}", QColor(80, 220, 100)),
            (" ", None),
            (f"L:{self.losses}", QColor(220, 80, 80)),
            (sep, None),
            (streak_text, streak_color),
        ]

    def _position_window(self):
        fm = QFontMetrics(self.font)
        total_w = sum(fm.horizontalAdvance(text) for text, _ in self._segments())
        text_h = fm.height()

        padding_x = 18
        padding_y = 10
        w = total_w + padding_x * 2
        h = text_h + padding_y * 2

        screen = QGuiApplication.primaryScreen().geometry()
        offset_right = 100
        x = screen.width() - w - offset_right
        y = 20
        self.setGeometry(x, y, w, h)

    def set_data(self, mmr, streak, wins, losses):
        self.mmr = mmr
        self.streak = streak
        self.wins = wins
        self.losses = losses
        self._position_window()
        self.update()

    def set_team(self, team):
        if team not in TEAM_TINTS:
            team = "neutral"
        if team != self.team:
            self.team = team
            self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        border_radius = 14

        bg_rgba = TEAM_TINTS.get(self.team, TEAM_TINTS["neutral"])
        border_rgba = TEAM_BORDER.get(self.team, TEAM_BORDER["neutral"])

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(*bg_rgba))
        painter.drawRoundedRect(rect, border_radius, border_radius)

        painter.setBrush(Qt.NoBrush)
        pen = painter.pen()
        pen.setColor(QColor(*border_rgba))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, border_radius, border_radius)

        painter.setFont(self.font)
        fm = QFontMetrics(self.font)

        padding_x = 18
        baseline_y = (self.height() + fm.ascent() - fm.descent()) // 2
        cursor_x = padding_x

        for text, color in self._segments():
            if color is None:
                cursor_x += fm.horizontalAdvance(text)
                continue
            painter.setPen(color)
            painter.drawText(QPoint(cursor_x, baseline_y), text)
            cursor_x += fm.horizontalAdvance(text)

    def apply_native_styles(self):
        hwnd = int(self.winId())
        apply_overlay_styles(hwnd)
        enable_blur(hwnd)

    def keep_topmost(self):
        if self.isVisible():
            push_topmost(int(self.winId()))


class StatusWindow(QMainWindow):
    def __init__(self, on_quit):
        super().__init__()
        self._on_quit = on_quit
        self.setWindowTitle("RL MMR Overlay")
        self.setWindowIcon(QIcon(ICON_FILE))
        self.setFixedSize(380, 170)

        central = QFrame()
        central.setStyleSheet(
            "QFrame { background-color: #14161c; }"
            "QLabel#title { color: #ffffff; font-family: 'Segoe UI'; font-size: 14px; font-weight: 600; }"
            "QLabel#status { font-family: 'Segoe UI'; font-size: 13px; font-weight: 600; }"
            "QLabel#hint { color: #8a8f9c; font-family: 'Segoe UI'; font-size: 11px; }"
            "QLabel#team { color: #c8ccd6; font-family: 'Segoe UI'; font-size: 11px; }"
        )
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        title = QLabel("Aub_OverlayRL")
        title.setObjectName("title")

        self.status_label = QLabel("⚠ Rocket League not detected")
        self.status_label.setObjectName("status")
        self.status_label.setStyleSheet("color: #ff9b3d;")

        self.team_label = QLabel("Team tint: Auto")
        self.team_label.setObjectName("team")

        hint = QLabel("Launch Rocket League — overlay will appear in-game. Right-click the tray icon to change team tint.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.team_label)
        layout.addWidget(hint)
        self.setCentralWidget(central)

    def set_running(self, running):
        if running:
            self.status_label.setText("🎮 Rocket League Running")
            self.status_label.setStyleSheet("color: #50dc64;")
        else:
            self.status_label.setText("⚠ Rocket League not detected")
            self.status_label.setStyleSheet("color: #ff9b3d;")

    def set_team_mode(self, mode_label):
        self.team_label.setText(f"Team tint: {mode_label}")

    def closeEvent(self, event):
        self._on_quit()
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_appwindow_style(int(self.winId()))


class AppController:
    def __init__(self, app, username):
        self.app = app
        self.username = username

        self.overlay = OverlayWindow()
        self.tracker = SessionTracker()

        self.status_window = StatusWindow(on_quit=self.quit)
        self.status_window.show()

        self.team_mode = "auto"

        self.tray = QSystemTrayIcon(QIcon(ICON_FILE))
        self.tray.setToolTip("RL MMR Overlay")
        menu = QMenu()

        team_menu = QMenu("Team tint", menu)
        self._team_actions = {}
        group = QActionGroup(team_menu)
        group.setExclusive(True)
        for key, label in [("auto", "Auto"), ("blue", "Blue"), ("orange", "Orange"), ("off", "Off")]:
            act = QAction(label, team_menu)
            act.setCheckable(True)
            act.setActionGroup(group)
            act.triggered.connect(lambda _checked=False, k=key: self.set_team_mode(k))
            team_menu.addAction(act)
            self._team_actions[key] = act
        self._team_actions["auto"].setChecked(True)
        menu.addMenu(team_menu)

        reset_action = QAction("Reset session", menu)
        reset_action.triggered.connect(self.reset_session)
        menu.addAction(reset_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

        self._rl_running = False
        self._was_running = False

        self.data_timer = QTimer()
        self.data_timer.setInterval(30000)
        self.data_timer.timeout.connect(self.refresh_data)

        self.rl_timer = QTimer()
        self.rl_timer.setInterval(3000)
        self.rl_timer.timeout.connect(self.check_rl_process)

        self.fg_timer = QTimer()
        self.fg_timer.setInterval(500)
        self.fg_timer.timeout.connect(self.check_foreground_and_topmost)

        self.team_timer = QTimer()
        self.team_timer.setInterval(1500)
        self.team_timer.timeout.connect(self.update_team_tint)

        self.check_rl_process()
        self.rl_timer.start()
        self.fg_timer.start()
        self.team_timer.start()

    def set_team_mode(self, mode):
        self.team_mode = mode
        labels = {"auto": "Auto", "blue": "Blue", "orange": "Orange", "off": "Off"}
        self.status_window.set_team_mode(labels.get(mode, "Auto"))
        if mode == "blue":
            self.overlay.set_team("blue")
        elif mode == "orange":
            self.overlay.set_team("orange")
        elif mode == "off":
            self.overlay.set_team("neutral")

    def reset_session(self):
        self.tracker.reset()
        self.overlay.set_data(self.overlay.mmr, 0, 0, 0)

    def update_team_tint(self):
        if self.team_mode != "auto":
            return
        if not self._rl_running or not is_rl_focused():
            return
        team = detect_team_color()
        if team is not None:
            self.overlay.set_team(team)

    def check_rl_process(self):
        running = is_rl_running()
        self._rl_running = running
        self.status_window.set_running(running)

        if running and not self._was_running:
            self.tracker.reset()
            self.refresh_data()
            self.data_timer.start()
        elif not running and self._was_running:
            self.data_timer.stop()
            self.overlay.hide()
            self.overlay.set_team("neutral")

        self._was_running = running

    def check_foreground_and_topmost(self):
        if not self._rl_running:
            if self.overlay.isVisible():
                self.overlay.hide()
            return

        if is_rl_focused():
            if not self.overlay.isVisible():
                self.overlay.show()
                self.overlay.apply_native_styles()
            self.overlay.keep_topmost()
        else:
            if self.overlay.isVisible():
                self.overlay.hide()

    def refresh_data(self):
        mmr = fetch_mmr(self.username)
        if mmr is not None:
            self.tracker.update(mmr)
        self.overlay.set_data(mmr, self.tracker.streak, self.tracker.wins, self.tracker.losses)

    def quit(self):
        try:
            self.data_timer.stop()
            self.rl_timer.stop()
            self.fg_timer.stop()
            self.team_timer.stop()
            self.tray.hide()
        except Exception:
            pass
        self.app.quit()


def load_username():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                u = data.get("username")
                if u:
                    return u
        except Exception:
            pass
    return ""


def save_username(username):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": username}, f, indent=2)
    except Exception:
        pass


def ask_username(default=""):
    text, ok = QInputDialog.getText(
        None,
        "Aub_OverlayRL — Epic username",
        "Enter your Epic Games username (in-game name):",
        text=default,
    )
    if not ok:
        return ""
    return text.strip()


def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("aub.overlayrl.app")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(ICON_FILE))

    username = load_username()
    if not username:
        username = ask_username()
        if not username:
            return 0
        save_username(username)

    controller = AppController(app, username)
    _ = controller
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())