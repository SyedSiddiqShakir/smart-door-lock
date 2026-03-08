#cd project/smart-door-lock
#source venv310/bin/activate
#cd src
#python test.py
import sys
import speech_recognition as sr
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

SECRET_PASSPHRASE = "2073"

class VoiceThread(QThread):
    result_signal = pyqtSignal(str, str)

    def run(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = False

        self.result_signal.emit("LISTENING", "")
        with sr.Microphone(device_index=0) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                self.result_signal.emit("PROCESSING", "")
                text = recognizer.recognize_google(audio).lower()
                if text == SECRET_PASSPHRASE:
                    self.result_signal.emit("SUCCESS", text)
                else:
                    self.result_signal.emit("DENIED", text)
            except sr.WaitTimeoutError:
                self.result_signal.emit("TIMEOUT", "")
            except sr.UnknownValueError:
                self.result_signal.emit("UNKNOWN", "")
            except sr.RequestError as e:
                self.result_signal.emit("ERROR", str(e))

class DoorLockUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Smart Voice Lock")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()
        self.label = QLabel("🎤 LISTENING...\n\nSay the passphrase", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        self.label.setWordWrap(True)
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.thread = VoiceThread()
        self.thread.result_signal.connect(self.update_ui)
        self.thread.start()

    def update_ui(self, status, text):
        styles = {
            "LISTENING":  ("background-color: #2c3e50; color: white;",  "LISTENING...\n\nSay the passphrase"),
            "PROCESSING": ("background-color: #2980b9; color: white;",  "PROCESSING...\n\nRecognizing speech"),
            "SUCCESS":    ("background-color: #27ae60; color: white;",  "ACCESS GRANTED\n\nWelcome back!"),
            "DENIED":     ("background-color: #c0392b; color: white;",  f"ACCESS DENIED\n\nHeard: '{text}'"),
            "TIMEOUT":    ("background-color: #e67e22; color: white;",  "TIMED OUT\n\nNo speech detected"),
            "UNKNOWN":    ("background-color: #c0392b; color: white;",  "COULDN'T UNDERSTAND\n\nTry again"),
            "ERROR":      ("background-color: #8e44ad; color: white;",  f"ERROR\n\n{text}"),
        }
        style, message = styles.get(status, styles["LISTENING"])
        self.setStyleSheet(style)
        self.label.setText(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DoorLockUI()
    ex.show()
    sys.exit(app.exec())
