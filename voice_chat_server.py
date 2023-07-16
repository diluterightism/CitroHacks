###########################
#######FEYNMAN LEARN#######
##THIS IS THE SERVER FILE##
##CURRENTLY WORKS LOCALLY##
###########################



# importing libraries
import socket
import threading
import pyaudio
from PyQt5 import QtCore, QtGui, QtWidgets

# const declaration (ports, ip addresses, et cetera)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# HOST HAS TO BE IN THE SAME NETWORK FOR NOW UNLESS THE VARIABLE IS REPLACED MANUALLY
HOST = 'localhost' # This makes it so that the ip address of whatever device is grabbed.
PORT = 5000 # CHANGE THIS IF PORT 5000 IS TAKEN ON THE COMPUTER
TEXT_PORT = 5001 # SAME GOES HERE


# class definition for server
class VoiceChatServer(QtWidgets.QWidget):
    
    # Initialising widgets for the gui as well as setting up the sockets
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
        self.setWindowTitle("Voice Chat Server")
        self.start_button = QtWidgets.QPushButton("Start Server")
        self.stop_button = QtWidgets.QPushButton("Stop Server")
        self.stop_button.setEnabled(False)
        self.status_label = QtWidgets.QLabel("Server stopped")
        self.text_edit = QtWidgets.QTextEdit()
        self.send_button = QtWidgets.QPushButton("Send")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.send_button)
        self.setLayout(layout)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        self.send_button.clicked.connect(self.send_text)
        self.set_styles()
    
    # CSS code for gui styling 
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
                min-width: 100px;
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
    
    # Code for starting the server
    def start(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(2)
        self.text_socket.bind((HOST, TEXT_PORT))
        self.text_socket.listen(2)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Server started. Listening for connections...")
        threading.Thread(target=self._accept_connections).start()
        threading.Thread(target=self._accept_text_connections).start()
    
    # Code for terminating the server connections
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
        self.status_label.setText("Server stopped")
    
    # Accepts the connection request from the client 
    def _accept_connections(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Client connected: {address}")
            self.client_connections.append(client_socket)
            client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
            self.client_threads.append(client_thread)
            self.streams.append(self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK))
            client_thread.start()

    # Only for text messages to and from client
    def _accept_text_connections(self):
        while True:
            text_socket, address = self.text_socket.accept()
            print(f"Text client connected: {address}")
            self.text_connections.append(text_socket)
            text_thread = threading.Thread(target=self._handle_text_client, args=(text_socket,))
            self.text_threads.append(text_thread)
            text_thread.start()

    # Receiving and sending the audio
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
                        self.streams[index].write(data)  # Send the received audio to other clients
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
                self.text_edit.append(data.decode())
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
            self.text_edit.clear()

# Calling the functions and setting up QTwidgets
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0E1822"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#1F2B38"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#F5F5F5"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#F5F5F5"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#1F2B38"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#F5F5F5"))
    app.setPalette(palette)

    server = VoiceChatServer()
    server.show()
    app.exec_()
