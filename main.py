from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
import sys
import ctypes
from curl_cffi import requests

USERNAME = "YOUR_EPIC_GAME_USERNAME" ####################


# ---------------- API (FIX + BYPASS HEADERS) ----------------
def GetData():
    url = f"https://api.tracker.gg/api/v2/rocket-league/standard/profile/epic/{USERNAME}"

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "referer": "https://tracker.gg/",
        "origin": "https://tracker.gg",
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            impersonate="chrome124",
            timeout=10
        )

        if r.status_code != 200:
            return f"ERR {r.status_code}"

        data = r.json()

        for seg in data.get("data", {}).get("segments", []):
            if seg.get("metadata", {}).get("name") == "Ranked Doubles 2v2":
                return seg.get("stats", {}).get("rating", {}).get("value", "N/A")

        return "N/A"

    except Exception as e:
        return "ERR"


# ---------------- WINDOWS BLUR ----------------
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
        accent.AccentState = 3  # blur

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

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.font = QFont("Segoe UI", 11, QFont.Bold)

        self.mmr = "Loading..."

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)

        self.update_data()

        self.show()

        hwnd = int(self.winId())
        enable_blur(hwnd)

    # -------- API --------
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

    # -------- DRAW --------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # glass background
        p.setBrush(QColor(20, 20, 20, 160))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, 10, 10)

        # border
        p.setPen(QPen(QColor(255, 255, 255, 35), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)

        # text
        p.setFont(self.font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(12, 20 + self.font.pointSize(), f"MMR: {self.mmr}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Overlay()
    sys.exit(app.exec())