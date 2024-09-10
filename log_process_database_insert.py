import mysql.connector
import os
import re
import time

PROCESSED_DIR = 'processed'  # Directory containing processed log files
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
    # Extract source and destination IPs, ports, flags, and length using regex
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


def process_logs():
    """Process all log files in the processed directory and insert data into the database."""
    db_connection = get_database_connection()
    db_cursor = db_connection.cursor()

    try:
        while True:
            # List all log files in the processed directory
            log_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.log')]

            for log_file in log_files:
                file_path = os.path.join(PROCESSED_DIR, log_file)
                print(f"Processing {file_path}...")

                # Read and process each log file
                with open(file_path, 'r') as file:
                    for line in file:
                        log_entry = line.strip()
                        insert_log_entry(db_cursor, log_entry)
                    db_connection.commit()

                # Delete the log file after processing
                os.remove(file_path)
                print(f"Deleted processed log file: {file_path}")

            # Sleep for a bit before checking again
            time.sleep(10)

    except Exception as e:
        print(f"Error processing logs: {e}")

    finally:
        db_cursor.close()
        db_connection.close()


if __name__ == '__main__':
    process_logs()
