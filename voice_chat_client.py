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

class VoiceChatClient(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.audio_stream = pyaudio.PyAudio()
        self.is_streaming = False

        self.setWindowTitle("Voice Chat Client")

        self.connect_button = QtWidgets.QPushButton("Connect")
        self.disconnect_button = QtWidgets.QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)

        self.status_label = QtWidgets.QLabel("Disconnected")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.connect_button.clicked.connect(self.connect)
        self.disconnect_button.clicked.connect(self.disconnect)

    def connect(self):
        if self.client_socket:
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))
        self.is_streaming = True

        threading.Thread(target=self._send_audio).start()
        threading.Thread(target=self._receive_audio).start()

        self.status_label.setText("Connected")
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)

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
        self.disconnect_button.setEnabled(False)

    def _send_audio(self):
        stream = self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while self.is_streaming:
            try:
                data = stream.read(CHUNK)
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

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    client = VoiceChatClient()
    client.show()
    app.exec_()
