import cv2
import socket
import threading
import pickle
import struct
import time

HOST = '10.200.255.105'
VIDEO_PORT = 9998

stop_event = threading.Event()  # Global event to control stopping

# --- VIDEO STREAM SERVER (HOST) ---
def handle_video_client(client_socket, addr, cap):
    print(f"[✅] Video stream client connected: {addr}")
    try:
        while cap.isOpened() and not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break

            data = pickle.dumps(frame)
            msg = struct.pack("Q", len(data)) + data
            client_socket.sendall(msg)
    except Exception as e:
        print(f"[❌ Client Error {addr}] {e}")
    finally:
        client_socket.close()
        print(f"[🔌] Disconnected: {addr}")

def video_stream_server():
    print("calling video stream server")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, VIDEO_PORT))
    server_socket.listen(5)
    print(f"[📹] Video streaming server listening on {HOST}:{VIDEO_PORT}")
    cap = cv2.VideoCapture(0)

    try:
        while not stop_event.is_set():
            server_socket.settimeout(1.0)
            try:
                client_socket, addr = server_socket.accept()
                thread = threading.Thread(target=handle_video_client, args=(client_socket, addr, cap))
                thread.start()
            except socket.timeout:
                continue
    except Exception as e:
        print(f"[❌ Server Error] {e}")
    finally:
        cap.release()
        server_socket.close()
        print("[🛑] Video stream server closed.")

# --- VIDEO CLIENT VIEWER ---
def video_stream_client():
    print("calling video stream client")
    time.sleep(5)  # Allow server to start
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, VIDEO_PORT))

    data = b""
    payload_size = struct.calcsize("Q")

    try:
        while not stop_event.is_set():
            while len(data) < payload_size:
                packet = client_socket.recv(4096)
                if not packet:
                    return
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += client_socket.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data)

            cv2.imshow("🎥 Live Video Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()  # Set the stop event on pressing 'q'
                break
    except Exception as e:
        print(f"[❌ Client Error] {e}")
    finally:
        client_socket.close()
        cv2.destroyAllWindows()


# --- STOP STREAM FUNCTION ---
def stop_streaming():
    print("[🛑] Stop streaming requested.")
    stop_event.set()

# --- MAIN ---
if __name__ == "__main__":
    threading.Thread(target=video_stream_server, daemon=True).start()
    video_stream_client()
