import subprocess
import mysql.connector
import time
import os
import re  # Added to help with extracting IPs and ports

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
    # Example log format: "IP 192.168.1.2.12345 > 192.168.1.3.80: Flags [S], seq 1234, length 60"
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)\.(\d+) > (\d+\.\d+\.\d+\.\d+)\.(\d+): Flags \[(.*?)\](.*length (\d+))?", log_entry)

    if not match:
        return  # If the log entry doesn't match the expected format, skip it

    source_ip = match.group(1)  # Source IP
    source_port = match.group(2)  # Source Port
    destination_ip = match.group(3)  # Destination IP
    destination_port = match.group(4)  # Destination Port
    flags = match.group(5)  # TCP Flags
    info = match.group(6).strip() if match.group(6) else ''  # Remaining part of the log (e.g., seq, ack, ttl, etc.)
    length = match.group(7) if match.group(7) else '0'  # Packet length (default to '0' if not found)

    # Skip traffic involving the excluded IP
    if source_ip == EXCLUDED_IP or destination_ip == EXCLUDED_IP:
        print(f"Skipping traffic from or to {EXCLUDED_IP}")
        return  # Don't log or save this entry

    # Insert into the database
    insert_query = """
    INSERT INTO logs (time, source_ip, source_port, destination_ip, destination_port, flag, info, length)
    VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (source_ip, source_port, destination_ip, destination_port, flags, info, length))


def monitor_traffic(interface='eth0', log_file='trafficinout.log'):
    """
    Monitors incoming and outgoing traffic on a specified network interface continuously and logs it to a file and a database.

    :param interface: Network interface to monitor (default: 'eth0')
    :param log_file: Path to the log file (default: 'trafficinout.log')
    """
    print(f"Monitoring traffic on interface '{interface}' continuously...")
    print(f"Logs will be saved to '{log_file}'")

    try:
        # Open the log file for writing
        with open(log_file, 'a') as file:
            # Establish database connection
            db_connection = get_database_connection()
            db_cursor = db_connection.cursor()

            # Run tcpdump command to capture traffic
            cmd = ['sudo', 'tcpdump', '-i', interface, '-n', '-l']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            while True:
                line = process.stdout.readline()
                if line:
                    log_entry = line.decode().strip()
                    print(log_entry)

                    # Write log to file
                    file.write(log_entry + '\n')

                    # Insert log entry into database
                    insert_log_entry(db_cursor, log_entry)
                    db_connection.commit()

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    finally:
        process.terminate()
        process.wait()
        db_cursor.close()
        db_connection.close()


if __name__ == '__main__':
    interface = input("Enter network interface to monitor (e.g., 'eth0', 'wlan0'): ")
    log_file = 'trafficinout.log'

    # Ensure the log file path is writable
    try:
        with open(log_file, 'a'):
            pass
    except PermissionError:
        print(
            f"Permission denied: Cannot write to '{log_file}'. You may need to run this script with elevated privileges.")
        exit(1)

    monitor_traffic(interface, log_file)
