import socket
import cv2
import pickle
import struct
from config import HOST, VIDEO_PORT

def start_video_stream():
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.bind((HOST, VIDEO_PORT))
    raw_socket.listen(5)
    print(f"[📹 Video] Streaming on {HOST}:{VIDEO_PORT}")

    client_socket, addr = raw_socket.accept()
    print(f"[📺 Viewer Connected] {addr}")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[✖] Camera not accessible")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[✖] Frame capture failed")
                break

            data = pickle.dumps(frame)
            message = struct.pack("Q", len(data)) + data
            client_socket.sendall(message)
    except Exception as e:
        print(f"[✖] Streaming stopped: {e}")
    finally:
        cap.release()
        client_socket.close()
        raw_socket.close()
        print("[🚫] Video stream closed.")

if __name__ == "__main__":
    start_video_stream()
