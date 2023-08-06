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

class VoiceChatServer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_stream = pyaudio.PyAudio()
        self.client_connections = []
        self.client_threads = []
        self.streams = []
        self.text_connections = []
        self.text_threads = []
        self.setWindowTitle("FeynPrep")
        self.start_button = QtWidgets.QPushButton("Start Connecting")
        self.stop_button = QtWidgets.QPushButton("End Connection")
        self.stop_button.setEnabled(False)
        self.status_label = QtWidgets.QLabel("Disconnected")
        self.chat_area = QtWidgets.QTextEdit()
        font = QtGui.QFont("Arial", 40, 30)  # Set font and size here
        self.chat_area.setFont(font)  # Apply the font to the QTextEdit widget
        self.text_edit = QtWidgets.QTextEdit()
        font = QtGui.QFont("Arial", 40, 30)  # Set font and size here
        self.text_edit.setFont(font)  # Apply the font to the QTextEdit widget
        self.text_edit.setMaximumHeight(100)  # Set maximum height for the text_edit widget
        self.send_button = QtWidgets.QPushButton("Send")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.chat_area)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.send_button)
        self.setLayout(layout)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.send_button.clicked.connect(self.send_text)
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

    def start(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(2)
        self.text_socket.bind((HOST, TEXT_PORT))
        self.text_socket.listen(2)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Connection enabled")
        threading.Thread(target=self._accept_connections).start()
        threading.Thread(target=self._accept_text_connections).start()

    def stop(self):
        self.server_socket.close()
        self.text_socket.close()
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
        for conn in self.text_connections:
            conn.close()
        self.text_connections.clear()
        for thread in self.text_threads:
            thread.join()
        self.text_threads.clear()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Disconnected")

    def _accept_connections(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Student 1 connected: {address}")
            self.client_connections.append(client_socket)
            client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
            self.client_threads.append(client_thread)
            self.streams.append(self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK))
            client_thread.start()

    def _accept_text_connections(self):
        while True:
            text_socket, address = self.text_socket.accept()
            print(f"Student 1 connected: {address}")
            self.text_connections.append(text_socket)
            text_thread = threading.Thread(target=self._handle_text_client, args=(text_socket,))
            self.text_threads.append(text_thread)
            text_thread.start()

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
                        self.streams[index].write(data)
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

    def _handle_text_client(self, text_socket):
        while True:
            try:
                data = text_socket.recv(1024)
                if not data:
                    break
                for conn in self.text_connections:
                    if conn != text_socket:
                        conn.sendall(data)
                self.chat_area.append("<b style='color: #409EFF;'>Student 1: </b>" + data.decode())
            except Exception as e:
                print(e)
                break
        text_socket.close()
        self.text_connections.remove(text_socket)
        self.text_threads.remove(threading.current_thread())

    def send_text(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            encoded_text = text.encode()
            for conn in self.text_connections:
                conn.sendall(encoded_text)
                self.chat_area.append("<b style='color: #67C23A;'>Student 2: </b>" + text)
            self.text_edit.clear()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    server = VoiceChatServer()
    server.showMaximized()
    app.exec_()
