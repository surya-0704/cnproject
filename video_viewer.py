import socket
import cv2
import pickle
import struct
import ssl
from config import HOST, VIDEO_PORT

def receive_video_stream():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # For dev only — you can enable cert validation in production

    # Connect to host's video stream
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = context.wrap_socket(raw_socket)
    conn.connect((HOST, VIDEO_PORT))

    data = b""
    payload_size = struct.calcsize("Q")

    print(f"[📺 Connecting] Securely receiving video stream from {HOST}:{VIDEO_PORT}...")

    try:
        while True:
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet:
                    return
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += conn.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data)
            cv2.imshow("🔴 Live Auction Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"[✖] Error receiving video: {e}")
    finally:
        conn.close()
        cv2.destroyAllWindows()
        print("[🚫] Video stream closed.")

if __name__ == "__main__":
    receive_video_stream()
