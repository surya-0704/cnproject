# utils.py

from datetime import datetime

def timestamp():
    return datetime.now().strftime("[%H:%M:%S]")

def format_bid(user, amount):
    return f"{timestamp()} {user} placed a bid of ₹{amount}"
