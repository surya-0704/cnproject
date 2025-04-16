import socket
import threading
import time
from config import HOST, PORT, BUFFER_SIZE, ENCODING
from utils import format_bid

clients = []  # list of (conn, name)
highest_bid = -1
highest_bidder = "None"
host_name = None
bidding_open = True
current_item = "None"

timeout_thread = None
timeout_lock = threading.Lock()
auction_timeout_duration = 150  # seconds


def broadcast(message):
    for conn, _ in clients:
        try:
            conn.send(message.encode(ENCODING))
        except:
            pass

def send_to(conn, message):
    try:
        conn.send(message.encode(ENCODING))
    except:
        pass

def get_client_name(conn):
    for c, name in clients:
        if c == conn:
            return name
    return "Unknown"

def assign_new_host():
    global host_name
    if clients:
        _, new_host = clients[0]
        host_name = new_host
        broadcast(f"[🎥] Host disconnected. {host_name} is the new host!")
    else:
        host_name = None

def end_auction_due_to_timeout():
    global bidding_open
    if bidding_open:
        bidding_open = False
        broadcast(f"[🏁] Auction Ended due to inactivity.")
        broadcast(f"[👑] Winner: {highest_bidder} with ₹{highest_bid}")

def start_or_reset_timeout():
    global timeout_thread

    def timeout_checker():
        time.sleep(auction_timeout_duration)
        with timeout_lock:
            if bidding_open:
                end_auction_due_to_timeout()

    if timeout_thread and timeout_thread.is_alive():
        # let it finish, just restart a new one
        pass

    timeout_thread = threading.Thread(target=timeout_checker, daemon=True)
    timeout_thread.start()

def countdown_timer(duration):
    global bidding_open
    for i in range(duration, 0, -1):
        time.sleep(1)
    bidding_open = False
    broadcast(f"[🏁] Auction Ended! Winner: {highest_bidder} with ₹{highest_bid}")

def handle_client(conn, addr):
    global highest_bid, highest_bidder, host_name, bidding_open

    print(f"[+] New connection from {addr}")
    send_to(conn, "Welcome to Bid War! Enter your name: ")
    name = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
    clients.append((conn, name))

    if not host_name:
        host_name = name
        send_to(conn, "[🎥] You are the initial host.")
        broadcast(f"[🎥] {host_name} is the host!")

    broadcast(f"[+] {name} joined the auction.")

    while True:
        try:
            data = conn.recv(BUFFER_SIZE).decode(ENCODING)
            if not data:
                break

            if data.startswith("BID:"):
                if not bidding_open:
                    send_to(conn, "[🚫] Auction has ended. No more bids allowed.")
                    continue
                elif highest_bid == -1 :
                    send_to(conn,"[🚫] Item is not annouced yet.")
                    continue
                elif name == host_name:
                    send_to(conn, "[🚫] You are the host can't place bid")
                    continue 
                elif name == highest_bidder:
                    send_to(conn,"[🚫] same person can't place bid twice")
                    continue
                try:
                    amount = int(data.split(":")[1])
                    if amount > highest_bid:
                        highest_bid = amount
                        highest_bidder = name
                        msg = format_bid(name, amount)
                        broadcast(f"[BID-UPDATE] {msg}")
                        start_or_reset_timeout()  # 🔥 Restart inactivity timeout
                    else:
                        send_to(conn, f"[⚠] Bid ₹{amount} too low. Current highest: ₹{highest_bid}")
                except:
                    send_to(conn, "[❌] Invalid bid format. Use BID:<amount>")

            elif data.startswith("HOST_REQ"):
                if name == host_name:
                    send_to(conn, "[ℹ️] You are already the host.")
                    continue

                # Find the current host's connection
                host_conn = None
                for c, n in clients:
                    if n == host_name:
                        host_conn = c
                        break

                if host_conn:
                    try:
                        send_to(host_conn, f"[🔁] {name} wants to become the host. Approve? (yes/no): ")
                        response = host_conn.recv(BUFFER_SIZE).decode(ENCODING).strip().lower()
                        if response == "yes":
                            host_name = name
                            broadcast(f"[🎥] Host changed! {host_name} is the new host.")
                        else:
                            send_to(conn, "[❌] Host request denied by current host.")
                    except:
                        send_to(conn, "[❌] Failed to reach current host.")
                else:
                    send_to(conn, "[⚠️] No host found to approve your request.")


            elif data.startswith("LIST"):
                send_to(conn, f"[📋] Current highest: ₹{highest_bid} by {highest_bidder}")

            elif data.startswith("END_AUCTION"):
                if name != host_name:
                    send_to(conn, "[❌] Only host can end the auction.")
                    continue
                bidding_open = False
                broadcast(f"[🏁] Auction Ended by Host!")
                broadcast(f"[👑] Winner: {highest_bidder} with ₹{highest_bid}")

            elif data.startswith("START_COUNTDOWN"):
                if name == host_name:
                    try:
                        duration = int(data.split()[1])
                        threading.Thread(target=countdown_timer, args=(duration,), daemon=True).start()
                    except:
                        send_to(conn, "[❌] Usage: START_COUNTDOWN <seconds>")
                else:
                    send_to(conn, "[❌] Only host can start countdown.")
            elif data.startswith("ITEM:"):
                if name != host_name:
                    send_to(conn, "[❌] Only host can set the auction item.")
                    continue

                try:
                    parts = data.split(":")
                    item_name = parts[1].strip()
                    min_bid = int(parts[2].strip())

                    if min_bid <= 0:
                        send_to(conn, "[⚠] Minimum bid must be greater than 0.")
                        continue

                    current_item = item_name
                    highest_bid = min_bid
                    highest_bidder = "None"
                    broadcast(f"[📦] Item for Auction: {item_name}, Minimum Bid: ₹{min_bid}")
                    start_or_reset_timeout()
                except:
                    send_to(conn, "[❌] Invalid item command format. Use: item")


        except Exception as e:
            print(f"[!] Error with {name}: {e}")
            break

    print(f"[-] {name} disconnected")
    clients.remove((conn, name))
    if name == host_name:
        assign_new_host()
    conn.close()

def start_server():
    raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_server.bind((HOST, PORT))
    raw_server.listen()
    print(f"[🎯 Server Started] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = raw_server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
