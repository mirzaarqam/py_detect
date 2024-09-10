import mysql.connector
import os
import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROCESSED_DIR = 'processed'  # Directory containing processed log files
LOG_FILE = 'trafficdata_file.log'  # Log file name to watch
EXCLUDED_IP = '192.168.1.100'  # Define the IP address to be excluded


def get_database_connection():
    """Establishes and returns a connection to the MySQL database."""
    return mysql.connector.connect(
        host='192.168.1.100',
        database='trafficlogs',
        user='ubuntu',
        password='123456@a'
    )


def insert_log_entry(cursor, log_entry):
    """Inserts a log entry into the MySQL database."""
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)\.(\d+) > (\d+\.\d+\.\d+\.\d+)\.(\d+): Flags \[(.*?)\](.*length (\d+))?",
                      log_entry)

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
        if event.src_path.endswith(LOG_FILE):
            print(f"Log file {LOG_FILE} modified, processing...")
            process_log_file(event.src_path)

    def on_created(self, event):
        """Called when the log file is created."""
        if event.src_path.endswith(LOG_FILE):
            print(f"Log file {LOG_FILE} created, processing...")
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


if __name__ == '__main__':
    monitor_log_directory()
