import subprocess
import time
import os


def monitor_traffic(interface='eth0', log_file='trafficinout.log'):
    """
    Monitors incoming and outgoing traffic on a specified network interface continuously and logs it to a file.

    :param interface: Network interface to monitor (default: 'eth0')
    :param log_file: Path to the log file (default: '/var/log/trafficinout.log')
    """
    print(f"Monitoring traffic on interface '{interface}' continuously...")
    print(f"Logs will be saved to '{log_file}'")

    try:
        # Open the log file for writing
        with open(log_file, 'a') as file:
            # Run tcpdump command to capture traffic
            cmd = ['sudo', 'tcpdump', '-i', interface, '-n', '-l']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            while True:
                line = process.stdout.readline()
                if line:
                    log_entry = line.decode().strip()
                    print(log_entry)
                    file.write(log_entry + '\n')

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    finally:
        process.terminate()
        process.wait()


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
