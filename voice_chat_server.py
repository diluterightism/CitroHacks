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

class VoiceChatServer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_stream = pyaudio.PyAudio()
        self.client_connections = []
        self.client_threads = []
        self.streams = []

        self.setWindowTitle("Voice Chat Server")

        self.start_button = QtWidgets.QPushButton("Start Server")
        self.stop_button = QtWidgets.QPushButton("Stop Server")
        self.stop_button.setEnabled(False)

        self.status_label = QtWidgets.QLabel("Server stopped.")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)

    def start(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(2)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Server started. Listening for connections...")

        threading.Thread(target=self._accept_connections).start()

    def stop(self):
        self.server_socket.close()

        for conn in self.client_connections:
            conn.close()
        self.client_connections.clear()

        for thread in self.client_threads:
            thread.join()
        self.client_threads.clear()

        for stream in self.streams:
            stream.stop_stream()
            stream.close()
        self.streams.clear()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Server stopped.")

    def _accept_connections(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Client connected: {address}")

            self.client_connections.append(client_socket)

            client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
            self.client_threads.append(client_thread)

            self.streams.append(self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK))

            client_thread.start()

    def _handle_client(self, client_socket):
        stream_index = self.client_connections.index(client_socket)

        while True:
            try:
                data = client_socket.recv(CHUNK)
                if not data:
                    break
                for index, conn in enumerate(self.client_connections):
                    if index != stream_index:
                        conn.sendall(data)
                self.streams[stream_index].write(data)
            except Exception as e:
                print(e)
                break

        client_socket.close()
        self.client_connections.remove(client_socket)
        self.client_threads.remove(threading.current_thread())
        self.streams[stream_index].stop_stream()
        self.streams[stream_index].close()
        self.streams.pop(stream_index)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    server = VoiceChatServer()
    server.show()
    app.exec_()
