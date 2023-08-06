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
        self.chat_area = QtWidgets.QTextEdit()
        font = QtGui.QFont("Arial", 30)  # Set font and size here
        self.chat_area.setFont(font)  # Apply the font to the QTextEdit widget
        self.text_edit = QtWidgets.QLineEdit()
        font = QtGui.QFont("Arial", 30)  # Set font and size here
        self.text_edit.setFont(font)  # Apply the font to the QTextEdit widget
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
        layout.addWidget(self.chat_area)
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
                background-color: #1A1E34;
                color: #F5F5F5;
            }
            QPushButton {
                background-color: #282D46;
                border-style: none;
                color: #F5F5F5;
                font: bold 14px; /* Updated font size */
                padding: 10px; /* Updated padding */
                min-width: 120px; /* Updated minimum width */
            }
            QPushButton:hover {
                background-color: #383F60;
            }
            QLabel {
                font: bold 16px; /* Updated font size */
            }
            QLineEdit {
                background-color: #282D46;
                border-style: none;
                color: #F5F5F5;
                font: 20px; /* Updated font size */
                padding: 10px; /* Updated padding */
            }
            QTextEdit {
                background-color: #282D46;
                border-style: none;
                color: #F5F5F5;
                font: 20px; /* Updated font size */
                padding: 10px; /* Updated padding */
            }
        """)
        self.chat_area.setReadOnly(True)
        self.chat_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.chat_area.setAlignment(QtCore.Qt.AlignRight)

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
        text = self.text_edit.text().strip()
        if text:
            encoded_text = text.encode()
            self.text_socket.sendall(encoded_text)
            self.add_message_to_chat("<b style='color: #409EFF;'>You: </b>" + text)
            self.text_edit.clear()

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_button.setText("Unmute")
        else:
            self.mute_button.setText("Mute")

    def add_message_to_chat(self, message):
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml(message + "<br>")
        self.chat_area.setTextCursor(cursor)
        self.chat_area.ensureCursorVisible()

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
                self.add_message_to_chat("<b style='color: #67C23A;'>Server: </b>" + data.decode())
            except (OSError, ConnectionResetError):
                break

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    client = VoiceChatClient()
    client.show()
    app.exec_()
