import subprocess
import os
import time
from datetime import datetime

LOG_FILE = 'trafficdata.log'      # Current traffic log file
PROCESSED_DIR = 'processed'       # Directory to move processed log files
INTERFACE = 'ens33'                # Network interface to monitor (change as needed)
CAPTURE_DURATION = 60             # Log rotation interval (in seconds, 1 minute)

def capture_traffic(interface):
    """Capture traffic continuously and write it to the current log file."""
    print(f"Starting to capture traffic on interface '{interface}'...")

    # Ensure the processed directory exists
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    # Run tcpdump and capture traffic continuously
    cmd = ['sudo', 'tcpdump', '-i', interface, '-n', '-l']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        while True:
            with open(LOG_FILE, 'a') as log_file:
                start_time = time.time()

                while (time.time() - start_time) < CAPTURE_DURATION:
                    line = process.stdout.readline()
                    if line:
                        log_entry = line.decode().strip()
                        log_file.write(log_entry + '\n')

            # Rotate log file: move it to the processed directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_log_file = f'{PROCESSED_DIR}/trafficdata_{timestamp}.log'
            os.rename(LOG_FILE, new_log_file)
            print(f"Moved log file to {new_log_file}")

    except KeyboardInterrupt:
        print("\nTraffic capturing interrupted.")
    finally:
        process.terminate()
        process.wait()

if __name__ == '__main__':
    capture_traffic(INTERFACE)
