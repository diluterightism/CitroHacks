import socket
import threading
import pyaudio

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
HOST = 'localhost'
PORT = 5000

class VoiceChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_stream = pyaudio.PyAudio()
        self.client_connections = []
        self.client_threads = []
        self.streams = []
        
    def start(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(2)
        
        print("Server started. Listening for connections...")
        
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
        
    def stop(self):
        self.server_socket.close()
        for conn in self.client_connections:
            conn.close()
        for thread in self.client_threads:
            thread.join()
        self.audio_stream.terminate()


# Client Code

import socket
import threading
import pyaudio
import tkinter as tk

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
HOST = 'localhost'
PORT = 5000

class VoiceChatClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_stream = pyaudio.PyAudio()
        self.is_streaming = False
        
        self.root = tk.Tk()
        self.root.title("Voice Chat")
        
        self.start_button = tk.Button(self.root, text="Start", command=self.start_chat)
        self.start_button.pack(pady=10)
        
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_chat)
        self.stop_button.pack(pady=5)
        
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(pady=5)
        
        self.root.mainloop()
        
    def start_chat(self):
        self.client_socket.connect((HOST, PORT))
        self.is_streaming = True
        threading.Thread(target=self._send_audio).start()
        threading.Thread(target=self._receive_audio).start()
        self.status_label.config(text="Chatting...")
        
    def stop_chat(self):
        self.is_streaming = False
        self.client_socket.close()
        self.audio_stream.terminate()
        self.status_label.config(text="Chat Stopped")
        
    def _send_audio(self):
        stream = self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        while self.is_streaming:
            data = stream.read(CHUNK)
            self.client_socket.sendall(data)
        
        stream.stop_stream()
        stream.close()
        
    def _receive_audio(self):
        stream = self.audio_stream.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        
        while self.is_streaming:
            data = self.client_socket.recv(CHUNK)
            stream.write(data)
        
        stream.stop_stream()
        stream.close()
        
if __name__ == "__main__":
    server = VoiceChatServer()
    threading.Thread(target=server.start).start()
    
    client = VoiceChatClient()
    client.stop_chat()
    
    server.stop()
