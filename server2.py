import socket
import threading
import time
from config import HOST, PORT, BUFFER_SIZE, ENCODING
from utils import format_bid
import functools
print = functools.partial(print, flush=True)
# from video_stream_new import video_stream_server

clients = []  # list of (conn, name)
highest_bid = -1
highest_bidder = "None"
host_name = None
bidding_open = True
current_item = "None"

timeout_thread = None
timeout_lock = threading.Lock()
shared_lock = threading.Lock()
auction_timeout_duration = 300  # seconds


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
    with shared_lock:
        if bidding_open:
            bidding_open = False
            broadcast(f"[🏁] Auction Ended due to inactivity.")
            if highest_bidder == "None":
                broadcast(f"[🏁] Item unsold!")
            else:
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
    with shared_lock:
        bidding_open = False
    broadcast(f"[🏁] Auction Ended! Winner: {highest_bidder} with ₹{highest_bid}")

def handle_client(conn, addr):
    global highest_bid, highest_bidder, host_name, bidding_open, current_item

    try:
        print(f"[+] New connection from {addr}")  # This should print when new clients connect
        send_to(conn, "Welcome to Bid War! Enter your name: ")
        name = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        clients.append((conn, name))

        if not host_name:
            host_name = name
            send_to(conn, "[🎥] You are the initial host.")
            broadcast(f"[🎥] {host_name} is the host!")
            # video_stream_server()

        broadcast(f"[+] {name} joined the auction.")

        while True:
            try:
                data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                if not data:
                    break

                if data.startswith("BID:"):
                    with shared_lock:
                        if not bidding_open:
                            send_to(conn, "[🚫] Auction has ended. No more bids allowed.")
                            continue
                        elif highest_bid == -1:
                            send_to(conn, "[🚫] Item is not announced yet.")
                            continue
                        elif name == host_name:
                            send_to(conn, "[🚫] You are the host, can't place a bid.")
                            continue
                        elif name == highest_bidder:
                            send_to(conn, "[🚫] Same person can't place consecutive bids.")
                            continue

                        try:
                            amount = int(data.split(":")[1])
                            if amount > highest_bid:
                                highest_bid = amount
                                highest_bidder = name
                                msg = format_bid(name, amount)
                                broadcast(f"[BID-UPDATE] {msg}")
                                start_or_reset_timeout()
                            else:
                                send_to(conn, f"[⚠] Bid ₹{amount} too low. Current highest: ₹{highest_bid}")
                        except:
                            send_to(conn, "[❌] Invalid bid format. Use BID:<amount>")

                elif data.startswith("MSG:"):
                    message = data[4:].strip()
                    if message:
                        sender = get_client_name(conn)
                        broadcast(f"@{sender} : {message}")
                    else:
                        send_to(conn, "[⚠] Cannot send empty message.")

                elif data.startswith("HOST_REQ"):
                    if name == host_name:
                        send_to(conn, "[ℹ️] You are already the host.")
                        continue

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
                                # video_stream_server()
                            else:
                                send_to(conn, "[❌] Host request denied by current host.")
                        except:
                            send_to(conn, "[❌] Failed to reach current host.")
                    else:
                        send_to(conn, "[⚠️] No host found to approve your request.")

                elif data.startswith("LIST"):
                    if highest_bidder == "None":
                        send_to(conn, "[🚫] No bids till now.")
                        continue
                    send_to(conn, f"[📋] Current highest: ₹{highest_bid} by {highest_bidder}")

                elif data.startswith("END_AUCTION"):
                    with shared_lock:
                        if name != host_name:
                            send_to(conn, "[❌] Only host can end the auction.")
                            continue
                        bidding_open = False

                    broadcast(f"[🏁] Auction Ended by Host!")

                    with shared_lock:
                        if highest_bidder == "None" or highest_bid == -1:
                            broadcast("[❌] No valid bids were placed. Item unsold.")
                        else:
                            broadcast(f"[👑] Winner: {highest_bidder} with ₹{highest_bid}")

                        # Disconnect all clients
                        for c, n in list(clients):
                            try:
                                if c != conn:
                                    send_to(c, "[🔌] Disconnecting from server...")
                                c.close()
                            except:
                                pass

                        clients.clear()
                        host_name = None
                        highest_bid = -1
                        highest_bidder = "None"
                        current_item = "None"
                    break  # Also exit current thread for host

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
                    with shared_lock:
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
                            bidding_open = True
                            broadcast(f"[📦] Item for Auction: {item_name}, Minimum Bid: ₹{min_bid}")
                            start_or_reset_timeout()
                        except:
                            send_to(conn, "[❌] Invalid item command format. Use: ITEM:<item_name>:<min_bid>")

            except Exception as e:
                print(f"[!] Error with {name}: {e}")
                break

        print(f"[-] {name} disconnected")
        broadcast(f"[-] {name} disconnected")
        print("Current Clients:", [n for _, n in clients])

        with shared_lock:
            clients[:] = [(c, n) for c, n in clients if c != conn]

        if name == host_name:
            assign_new_host()

        try:
            conn.close()
        except:
            pass

    except Exception as e:
        print(f"[!] Error with client {addr}: {e}")

def start_server():
    raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_server.bind((HOST, PORT))
    raw_server.listen()
    print(f"[🎯 Server Started] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = raw_server.accept()
        print(f"[+] Accepted connection from {addr}")  # This should now print when clients connect
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
