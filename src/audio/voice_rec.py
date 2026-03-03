import sys
import speech_recognition as sr
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# --- Configuration ---
# In a real repo, you might want to move this to config.py
SECRET_PASSPHRASE = "open the door"

class VoiceThread(QThread):
    result_signal = pyqtSignal(str, str)

    def run(self):
        recognizer = sr.Recognizer()
        while True:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    # Listen for audio
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                    
                    if text == SECRET_PASSPHRASE:
                        self.result_signal.emit("SUCCESS", text)
                    else:
                        self.result_signal.emit("DENIED", text)
                except Exception:
                    # Silence errors (timeout/no speech) to keep the loop running
                    pass

class DoorLockUI(QWidget):
    def __init__(self):  # Fixed: Double underscores
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Smart Voice Lock")
        self.setFixedSize(400, 300)
        self.layout = QVBoxLayout()

        self.label = QLabel("🎤 LISTENING...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        
        # Initial Styling
        self.setStyleSheet("background-color: #2c3e50; color: white; border-radius: 10px;")

        # Start the listener thread
        self.thread = VoiceThread()
        self.thread.result_signal.connect(self.update_ui)
        self.thread.start()

    def update_ui(self, status, text):
        if status == "SUCCESS":
            self.label.setText(f"🔓 ACCESS GRANTED\n\nWelcome back!")
            self.setStyleSheet("background-color: #27ae60; color: white;")
        else:
            self.label.setText(f"🔒 ACCESS DENIED\n\nPhrase: '{text}'")
            self.setStyleSheet("background-color: #c0392b; color: white;")

if __name__ == '__main__': # Fixed: Double underscores
    app = QApplication(sys.argv)
    ex = DoorLockUI()
    ex.show()
    sys.exit(app.exec())
