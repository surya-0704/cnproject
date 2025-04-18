import cv2
import socket
import threading
import pickle
import struct
import time

HOST = '10.200.245.118'
VIDEO_PORT = 9998

# --- VIDEO STREAM SERVER (HOST) ---
def video_stream_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, VIDEO_PORT))
    server_socket.listen(1)
    print(f"[📹] Video streaming server listening on {HOST}:{VIDEO_PORT}")

    client_socket, addr = server_socket.accept()
    print(f"[✅] Video stream client connected: {addr}")

    cap = cv2.VideoCapture(0)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            data = pickle.dumps(frame)
            msg = struct.pack("Q", len(data)) + data
            client_socket.sendall(msg)
    except Exception as e:
        print(f"[❌ Server Error] {e}")
    finally:
        cap.release()
        client_socket.close()
        server_socket.close()
        print("[🛑] Video stream closed.")


# --- VIDEO CLIENT VIEWER ---
def video_stream_client():
    time.sleep(1)  # Allow server to start first
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, VIDEO_PORT))

    data = b""
    payload_size = struct.calcsize("Q")

    try:
        while True:
            while len(data) < payload_size:
                packet = client_socket.recv(4096)
                if not packet:
                    break
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
                break
    except Exception as e:
        print(f"[❌ Client Error] {e}")
    finally:
        client_socket.close()
        cv2.destroyAllWindows()


# --- MAIN ---
if __name__ == "_main_":
    threading.Thread(target=video_stream_server, daemon=True).start()
    video_stream_client()