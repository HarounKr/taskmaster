import time
from datetime import datetime

if __name__ == "__main__":
    while True:
        print(f"Heure actuelle : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(1)
