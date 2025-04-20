import socket
import threading
import sys
import time
from config import HOST, PORT, BUFFER_SIZE, ENCODING
from video_stream_new import video_stream_client,video_stream_server,stop_streaming

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(BUFFER_SIZE).decode(ENCODING)
            # if msg.startswith("[🎥]") and "You are the initial host." in msg:
            #     video_stream_server()
            # if msg.startswith("[🎥]") and "You joined the auction." in msg:
            #     video_stream_client()
            if msg.startswith("[🎥]") and "You are the initial host." in msg:
                threading.Thread(target=video_stream_server, daemon=True).start()
            if msg.startswith("[🎥]") and "You joined the auction." in msg:
                threading.Thread(target=video_stream_client, daemon=True).start()

            if not msg:
                print("[✖] Server closed the connection.")
                break
            else:
                print(f"\n[📢] {msg}")

            # Check for host confirmation prompt
            if msg.startswith("[🔁]") and "Type YES to allow or NO to reject" in msg:
                decision = input("→ ").strip().lower()
                print("printing decision:",decision)
                if decision=="yes":
                    stop_streaming()
                time.sleep(1)
                sock.send(decision.encode(ENCODING))
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
  item             → (Host Only) Set item and minimum bid
  msg <message>    → Live chat
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
            print("[ ] Request sent!")
        elif user_input.lower() == "list":
            sock.send("LIST".encode(ENCODING))
        elif user_input.lower() == "end_auction":
            stop_streaming()
            sock.send("END_AUCTION".encode(ENCODING))
        elif user_input.lower().startswith("msg "):
            message = user_input[4:].strip()
            if message:
                sock.send(f"MSG:{message}".encode(ENCODING))
            else:
                print("[⚠] Message cannot be empty.")
        elif user_input.lower() == "item":
            print("[📦] Enter item name:")
            item_name = input("→ ").strip()
            if not item_name:
                print("[⚠] Item name cannot be empty.")
                continue

            print("[💰] Enter minimum bid:")
            min_bid_input = input("→ ").strip()
            if not min_bid_input.isdigit():
                print("[⚠] Invalid minimum bid. It must be a number.")
                continue

            msg = f"ITEM:{item_name}:{min_bid_input}"
            sock.send(msg.encode(ENCODING))

        else:
            sock.send(user_input.encode(ENCODING))

    sock.close()
    print("[👋] Disconnected.")

if __name__ == "__main__":
    client_program()
