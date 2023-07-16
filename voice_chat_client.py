import socket
import threading
import pyaudio
from PyQt5 import QtCore, QtGui, QtWidgets

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
HOST = 'localhost'
PORT = 5000
TEXT_PORT = 5001

class VoiceChatClient(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.audio_stream = pyaudio.PyAudio()
        self.is_streaming = False
        self.is_muted = False

        self.setWindowTitle("Voice Chat Client")

        self.connect_button = QtWidgets.QPushButton("Connect")
        self.begin_voice_call_button = QtWidgets.QPushButton("Begin Voice Call")
        self.begin_voice_call_button.setEnabled(False)
        self.stop_voice_call_button = QtWidgets.QPushButton("Stop Voice Call")
        self.stop_voice_call_button.setEnabled(False)
        self.disconnect_button = QtWidgets.QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)

        self.status_label = QtWidgets.QLabel("Disconnected")
        self.text_edit = QtWidgets.QTextEdit()
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setEnabled(False)

        self.mute_button = QtWidgets.QPushButton("Mute")
        self.mute_button.setVisible(False)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.connect_button)
        layout.addWidget(self.begin_voice_call_button)
        layout.addWidget(self.stop_voice_call_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.send_button)
        layout.addWidget(self.mute_button)
        self.setLayout(layout)

        self.connect_button.clicked.connect(self.connect)
        self.begin_voice_call_button.clicked.connect(self.begin_voice_call)
        self.stop_voice_call_button.clicked.connect(self.stop_voice_call)
        self.disconnect_button.clicked.connect(self.disconnect)
        self.send_button.clicked.connect(self.send_text)
        self.mute_button.clicked.connect(self.toggle_mute)

        self.set_styles()

    def set_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0E1822;
            }
            QPushButton {
                background-color: #1F2B38;
                border-style: none;
                color: #F5F5F5;
                font: bold 12px;
                padding: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #2F3B48;
            }
            QLabel {
                color: #F5F5F5;
                font: bold 14px;
            }
            QTextEdit {
                background-color: #1F2B38;
                border-style: none;
                color: #F5F5F5;
                font: 12px;
                padding: 8px;
            }
        """)

    def connect(self):
        if self.client_socket:
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))

        self.status_label.setText("Connected")
        self.connect_button.setEnabled(False)
        self.begin_voice_call_button.setEnabled(True)
        self.disconnect_button.setEnabled(True)
        self.send_button.setEnabled(True)

        self.text_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_socket.connect((HOST, TEXT_PORT))
        threading.Thread(target=self._receive_text).start()

    def begin_voice_call(self):
        if self.is_streaming:
            return

        self.is_streaming = True
        threading.Thread(target=self._send_audio).start()
        threading.Thread(target=self._receive_audio).start()

        self.begin_voice_call_button.setEnabled(False)
        self.stop_voice_call_button.setEnabled(True)
        self.mute_button.setVisible(True)

    def stop_voice_call(self):
        self.is_streaming = False

        self.stop_voice_call_button.setEnabled(False)
        self.begin_voice_call_button.setEnabled(True)
        self.mute_button.setVisible(False)
        self.is_muted = False
        self.mute_button.setText("Mute")

    def disconnect(self):
        if not self.client_socket:
            return

        self.is_streaming = False
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        self.client_socket = None
        self.audio_stream.terminate()

        self.status_label.setText("Disconnected")
        self.connect_button.setEnabled(True)
        self.begin_voice_call_button.setEnabled(False)
        self.stop_voice_call_button.setEnabled(False)
        self.disconnect_button.setEnabled(False)
        self.send_button.setEnabled(False)

        self.text_socket.shutdown(socket.SHUT_RDWR)
        self.text_socket.close()
        self.text_socket = None

    def send_text(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            encoded_text = text.encode()
            self.text_socket.sendall(encoded_text)
            self.text_edit.clear()

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_button.setText("Unmute")
        else:
            self.mute_button.setText("Mute")

    def _send_audio(self):
        stream = self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while self.is_streaming:
            try:
                data = stream.read(CHUNK)
                if not self.is_muted:
                    self.client_socket.sendall(data)
            except (OSError, BrokenPipeError):
                break

        stream.stop_stream()
        stream.close()

    def _receive_audio(self):
        stream = self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

        while self.is_streaming:
            try:
                data = self.client_socket.recv(CHUNK)
                stream.write(data)
            except (OSError, ConnectionResetError):
                break

        stream.stop_stream()
        stream.close()

    def _receive_text(self):
        while True:
            try:
                data = self.text_socket.recv(1024)
                if not data:
                    break
                self.text_edit.append(data.decode())
            except (OSError, ConnectionResetError):
                break

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0E1822"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#1F2B38"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#F5F5F5"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#F5F5F5"))
    app.setPalette(palette)

    client = VoiceChatClient()
    client.show()
    app.exec_()
