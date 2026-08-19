import threading
import time

active_bots = []

def check_bots():
    print(f"check_bots sees: {active_bots}")
    threading.Timer(1.0, check_bots).start()

check_bots()

if __name__ == "__main__":
    active_bots = [] # Reassignment
    active_bots.append("Bot 1")
    time.sleep(3)
