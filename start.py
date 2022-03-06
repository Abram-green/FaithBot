import sys
import os
import threading
import time
from config import *

def start():
    def start_bot(name):
        print(f"Start: {name}")
        os.system(f"nohup python3 {name} &")

    t = threading.Thread(target=start_bot, args=("bot.py", ))
    t.start()
    t.join()
    while True:
        pass

def stop():
    os.system("pkill -f bot.py")
    print("Script stop")

def restart():
    stop()
    start()

if __name__ == "__main__":
    start()