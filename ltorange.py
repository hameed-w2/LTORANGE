#!/usr/bin/env python3
import socket
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

print_lock = Lock()
open_ports = []

def ltorange_ping_sweep(target):
    try:
        response = subprocess.call(["ping", "-c", "1", target], 
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        return response == 0
    except:
        return False

def ltorange_scan_port(target, port, banner_grab=False):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target, port))
        if result == 0:
            with print_lock:
                print(f"[+] Port {port} is open")
                open_ports.append(port)
                if banner_grab:
                    try:
                        sock.send(b"GET / HTTP/1.1\r\n\r\n")
                        banner = sock.recv(1024).decode().strip()
                        print(f"    Service: {banner.splitlines()[0]}")
                    except:
                        print("    (Banner grab failed)")
        sock.close()
    except:
        pass

def parse_ports(ports_str):
    """Handle formats: 80 / 20-80 / 22,80,443"""
    if '-' in ports_str:
        start, end = map(int, ports_str.split('-'))
        return list(range(start, end + 1))
    elif ',' in ports_str:
        return [int(p) for p in ports_str.split(',')]
    else:
        return [int(ports_str)]

def main():
    parser = argparse.ArgumentParser(description="LTORANGE - Lightweight Network Scanner")
    parser.add_argument("target", help="Target IP")
    parser.add_argument("-p", "--ports", help="Ports (e.g. '80' or '20-80' or '22,80,443')", default="1-1024")
    parser.add_argument("-t", "--threads", help="Thread count (default: 100)", type=int, default=100)
    parser.add_argument("-b", "--banner", help="Grab banners", action="store_true")
    args = parser.parse_args()

    print(f"[*] LTORANGE scanning {args.target}")

    if not ltorange_ping_sweep(args.target):
        print("[-] Target is unreachable")
        return

    ports = parse_ports(args.ports)
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        executor.map(lambda p: ltorange_scan_port(args.target, p, args.banner), ports)
    
    print(f"\n[+] Scan complete. Open ports: {sorted(open_ports)}")

if __name__ == "__main__":
    main()