import subprocess
import os
import time
from datetime import datetime
import mysql.connector
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

LOG_FILE = 'trafficdata.log'      # Current traffic log file
PROCESSED_DIR = 'processed'       # Directory to move processed log files
INTERFACE = 'ens33'               # Network interface to monitor (change as needed)
CAPTURE_DURATION = 60             # Log rotation interval (in seconds, 1 minute)
EXCLUDED_IP = '192.168.1.100'     # Define the IP address to be excluded
DB_HOST = '192.168.1.100'         # MySQL host
DB_NAME = 'trafficlogs'           # Database name
DB_USER = 'ubuntu'                # Database user
DB_PASS = '123456@a'              # Database password
PROCESSED_LOG_FILE = 'trafficdata_file.log'  # New log file name after rotation

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
            new_log_file = f'{PROCESSED_DIR}/{PROCESSED_LOG_FILE}'
            os.rename(LOG_FILE, new_log_file)
            print(f"Moved log file to {new_log_file}")

    except KeyboardInterrupt:
        print("\nTraffic capturing interrupted.")
    finally:
        process.terminate()
        process.wait()


def get_database_connection():
    """Establishes and returns a connection to the MySQL database."""
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def insert_log_entry(cursor, log_entry):
    """Inserts a log entry into the MySQL database."""
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)\.(\d+) > (\d+\.\d+\.\d+\.\d+)\.(\d+): Flags \[(.*?)\](.*length (\d+))?", log_entry)

    if not match:
        return  # If the log entry doesn't match the expected format, skip it

    source_ip = match.group(1)  # Source IP
    source_port = match.group(2)  # Source Port
    destination_ip = match.group(3)  # Destination IP
    destination_port = match.group(4)  # Destination Port
    flags = match.group(5)  # TCP Flags
    info = match.group(6).strip() if match.group(6) else ''  # Remaining part of the log
    length = match.group(7) if match.group(7) else '0'  # Packet length

    # Skip traffic involving the excluded IP
    if source_ip == EXCLUDED_IP or destination_ip == EXCLUDED_IP:
        print(f"Skipping traffic from or to {EXCLUDED_IP}")
        return

    # Insert into the database
    insert_query = """
    INSERT INTO logs (time, source_ip, source_port, destination_ip, destination_port, flag, info, length)
    VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (source_ip, source_port, destination_ip, destination_port, flags, info, length))


def process_log_file(file_path):
    """Reads and processes all log entries in the new log file."""
    db_connection = get_database_connection()
    db_cursor = db_connection.cursor()

    try:
        with open(file_path, 'r') as file:
            for line in file:
                log_entry = line.strip()
                insert_log_entry(db_cursor, log_entry)

        # Commit new entries to the database
        db_connection.commit()

    except Exception as e:
        print(f"Error processing logs: {e}")

    finally:
        db_cursor.close()
        db_connection.close()


class LogFileHandler(FileSystemEventHandler):
    """Custom handler to process the log file when it is created or modified."""

    def on_modified(self, event):
        """Called when the log file is modified."""
        if event.src_path.endswith(PROCESSED_LOG_FILE):
            print(f"Log file {PROCESSED_LOG_FILE} modified, processing...")
            process_log_file(event.src_path)

    def on_created(self, event):
        """Called when the log file is created."""
        if event.src_path.endswith(PROCESSED_LOG_FILE):
            print(f"Log file {PROCESSED_LOG_FILE} created, processing...")
            process_log_file(event.src_path)


def monitor_log_directory():
    """Monitors the directory for changes in the log file."""
    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, PROCESSED_DIR, recursive=False)

    print(f"Monitoring {PROCESSED_DIR} for changes...")

    observer.start()

    try:
        while True:
            time.sleep(10)  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


def start_capture_and_monitor():
    """Starts both capturing traffic and monitoring logs in separate threads."""
    capture_thread = threading.Thread(target=capture_traffic, args=(INTERFACE,))
    monitor_thread = threading.Thread(target=monitor_log_directory)

    # Start both threads
    capture_thread.start()
    monitor_thread.start()

    # Wait for both
    #
    # threads to complete
    capture_thread.join()
    monitor_thread.join()


if __name__ == '__main__':
    start_capture_and_monitor()
