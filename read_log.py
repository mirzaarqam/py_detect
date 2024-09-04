import re
from datetime import datetime

def parse_line(line):
    # Regular expression to match the log line format
    regex = r'(?P<time>\d{2}:\d{2}:\d{2}\.\d+) IP (?P<src_ip>\d+\.\d+\.\d+\.\d+)\.(?P<src_port>\d+) > (?P<dst_ip>\d+\.\d+\.\d+\.\d+)\.(?P<dst_port>\d+): Flags \[(?P<flags>[^\]]+)\](?:,.*?TS val (?P<ts_val>\d+))?'
    match = re.match(regex, line)
    if match:
        return match.groupdict()
    return None

def filter_and_display(filename, dest_ip):
    with open(filename, 'r') as file:
        for line in file:
            parsed = parse_line(line)
            if parsed and parsed['flags'] == 'S':
                time = parsed['time']
                src = f"{parsed['src_ip']}:{parsed['src_port']}"
                if (dest_ip == parsed['dst_ip']):
                    dst = f"{parsed['dst_ip']}:{parsed['dst_port']}"
                    print(f"TIME: {time}, {src} > {dst}, FLAG: [S]")

# Replace 'trafficinout.log' with the path to your log file if different
destination_ip = input('Please Enter Destination IP: ')
filter_and_display('trafficinout.log',  destination_ip)
