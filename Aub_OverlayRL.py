from PySide6.QtWidgets import (
    QApplication, QWidget, QInputDialog,
    QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QIcon, QAction
import sys
import ctypes
import os
import json
import random
from curl_cffi import requests

USERNAME = None
CACHE_FILE = "cache.json"

IMPERSONATE_LIST = ["chrome124", "chrome120", "edge101"]

cache = {}


# ---------------- CACHE ----------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass


cache = load_cache()


# ---------------- API ----------------
def GetData():
    global USERNAME, cache

    if not USERNAME:
        return "..."

    if USERNAME in cache:
        return cache[USERNAME]

    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/epic/{USERNAME}"

    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://tracker.gg/rocket-league/",
        "origin": "https://tracker.gg",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            impersonate=random.choice(IMPERSONATE_LIST),
            timeout=10
        )

        if r.status_code != 200:
            print("API ERROR:", r.status_code, r.text[:200])
            return "BLOCKED"

        data = r.json()

        for seg in data.get("data", {}).get("segments", []):
            if seg.get("metadata", {}).get("name") == "Ranked Doubles 2v2":
                mmr = seg.get("stats", {}).get("rating", {}).get("value", "N/A")

                cache[USERNAME] = mmr
                save_cache(cache)

                return mmr

        return "N/A"

    except Exception as e:
        print("EXCEPTION:", e)
        return "ERR"


# ---------------- BLUR ----------------
def enable_blur(hwnd):
    try:
        class ACCENT(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId", ctypes.c_int),
            ]

        class DATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.c_void_p),
                ("SizeOfData", ctypes.c_size_t),
            ]

        accent = ACCENT()
        accent.AccentState = 3

        data = DATA()
        data.Attribute = 19
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        data.SizeOfData = ctypes.sizeof(accent)

        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except:
        pass


# ---------------- OVERLAY ----------------
class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        # ❌ IMPORTANT FIX : NO Qt.Tool
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.font = QFont("Segoe UI", 11, QFont.Bold)
        self.mmr = "Loading..."

        # timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)

        self.update_data()
        self.show()

        hwnd = int(self.winId())
        enable_blur(hwnd)

        # ---------------- SYSTEM TRAY ----------------
        self.tray = QSystemTrayIcon(self)

        # tu peux mettre une icône ici : QIcon("icon.ico")
        self.tray.setIcon(QIcon())

        menu = QMenu()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.exit_app)

        hide_action = QAction("Hide")
        hide_action.triggered.connect(self.hide)

        show_action = QAction("Show")
        show_action.triggered.connect(self.show)

        menu.addAction(show_action)
        menu.addAction(hide_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    # ---------------- EXIT CLEAN ----------------
    def exit_app(self):
        self.tray.hide()
        QApplication.quit()

    # ---------------- API ----------------
    def update_data(self):
        self.mmr = GetData()

        fm = QFontMetrics(self.font)
        text = f"MMR: {self.mmr}"

        w = fm.horizontalAdvance(text) + 30
        h = fm.height() + 18

        self.setFixedSize(w, h)

        self.move(
            QApplication.primaryScreen().geometry().width() - w - 20,
            20
        )

        self.update()

    # ---------------- DRAW ----------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        p.setBrush(QColor(20, 20, 20, 120))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, 14, 14)

        p.setPen(QPen(QColor(255, 255, 255, 25), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)

        p.setFont(self.font)
        p.setPen(QColor(255, 255, 255))

        fm = QFontMetrics(self.font)
        text = f"MMR: {self.mmr}"

        x = 12
        y = (self.height() + fm.ascent() - fm.descent()) // 2

        p.drawText(x, y, text)


# ---------------- START ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    username, ok = QInputDialog.getText(
        None,
        "Rocket League Overlay",
        "Enter Epic username:"
    )

    if not ok or not username.strip():
        sys.exit()

    USERNAME = username.strip()

    w = Overlay()
    sys.exit(app.exec())