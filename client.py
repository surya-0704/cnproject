import socket
import threading
from config import HOST, PORT, BUFFER_SIZE, ENCODING

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(BUFFER_SIZE).decode(ENCODING)
            if msg:
                print(f"\n[📢] {msg}")
        except:
            print("[✖] Lost connection to server.")
            break

def client_program():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    print("\n[🧑‍💻] Connected to auction server.")

    thread = threading.Thread(target=receive_messages, args=(sock,))
    thread.daemon = True
    thread.start()

    print(""" 
[📜 Available Commands]
  bid <amount>     → Place a bid (e.g., bid 100)
  host             → Request to become host
  list             → Show current highest bid
  end_auction      → (Host Only) End the auction
  exit             → Exit the auction
    """)

    while True:
        user_input = input("→ ").strip()
        if not user_input:
            continue

        if user_input.lower() == "exit":
            break
        elif user_input.lower().startswith("bid"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1].isdigit():
                sock.send(f"BID:{parts[1]}".encode(ENCODING))
            else:
                print("[⚠] Invalid bid. Usage: bid <amount>")
        elif user_input.lower() == "host":
            sock.send("HOST_REQ".encode(ENCODING))
        elif user_input.lower() == "list":
            sock.send("LIST".encode(ENCODING))
        elif user_input.lower() == "end_auction":
            sock.send("END_AUCTION".encode(ENCODING))
        else:
            sock.send(user_input.encode(ENCODING))

    sock.close()
    print("[👋] Disconnected.")

if __name__ == "__main__":
    client_program()
