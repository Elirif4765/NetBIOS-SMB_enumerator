# NetBIOS Host Discoverer & SMB Shares Enumerator

A lightweight Python network reconnaissance tool that scans a local subnet to identify hosts, extract NetBIOS metadata, and check for SMB shares that can be listed without a password.

## Overview

Legacy or misconfigured network devices can expose internal file shares over TCP ports 139/445 via unauthenticated SMB sessions, and leak hostnames/workgroups over UDP port 137 (NetBIOS Name Service). This tool automates host discovery and attempts anonymous SMB share enumeration across a subnet using Python sockets together with `nmb` and `smbconnection` from `impacket`, without relying on heavyweight frameworks like Nmap NSE scripts or Metasploit.

## Features

- **Auto subnet detection** — uses `psutil` to determine the local CIDR block automatically
- **Ghost Host filtering** — skips hosts when both port 139 and port 445 checks time out and are classified as `Filtered`
- **Multithreaded scanning** — uses `ThreadPoolExecutor` with up to 50 worker threads (which can be customized)to process host scans concurrently
- **NetBIOS metadata extraction** — uses `nmb` from `impacket` to pull hostname and workgroup information of a target IP
- **Anonymous SMB share enumeration** — uses `smbconnection` from `impacket` to list disk shares with anonymous access (null username and password), while filtering out the administrative shares like `print$`; listing a share does not by itself prove that files inside it are readable (strong contendor for future scope honestly)
- **Timestamped report** — writes processed host details to a report file named `report_<timestamp>.txt`
- **Dual output** — prints a concise summary to the terminal and writes a more detailed report to disk; report writes are handled by the main thread

## Requirements

- Python 3.x
- Linux (tested on Kali Linux / Ubuntu)
- `impacket` library

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py
```

The script attempts to detect the local subnet from `eth0`, scans the subnet's host addresses using a thread pool, prints results to the terminal, and writes a report to `report_<timestamp>.txt` in the working directory. The TCP connection timeout is 0.5 seconds per port; the `nmb` and `smbconnection` timeout is 2 seconds each.

## Example Output

```text
192.168.56.130 - Host:METASPLOITABLE Workgroup:METASPLOITABLE - PORT 139: Open | PORT 445: Open
     [!] WARNING: ANONYMOUS SHARES FOUND!
      -> tmp
      -> opt
```

## How It Works

1. **Discovery** – Parse local interface configuration to get the CIDR range from `eth0`
2. **Port Check** – Perform TCP connection checks on ports 139 and 445 with a 0.5-second timeout, classifying each as `Open`, `Closed`, or `Filtered`
3. **Ghost Host Drop** – Skip a host if both port checks are classified as `Filtered`
4. **Deep Enumeration** – Use `.getnodestatus()` from `impacket.nmb` for NetBIOS information and, if either SMB port is open, use `.listShares()` from `impacket.smbconnection` to attempt anonymous share listing
5. **Threaded Execution** – Use up to 50 worker threads to scan hosts concurrently; the main thread processes results and writes report entries; any number of threads can be used as per needs.
6. **Dual Output** – Print a terminal summary and write a detailed record to the timestamped report

## Tested Scenarios

| Target State | Result |
|---|---|
| Both ports are `Filtered` | Host is skipped before deeper enumeration |
| Both ports are closed, with no NetBIOS response | Host can still appear in the output with unknown hostname/workgroup; SMB share enumeration is skipped |
| Both ports open and anonymous share listing succeeds | Share names are listed and flagged for review |
| Ports closed but NetBIOS reachable on UDP 137 | Host may still be identified through `impacket.nmb` |

## Remediation Guidance

For any host where anonymous SMB share listing succeeds:

- Disable guest/anonymous SMB access (for example, review `restrict anonymous` and `guest ok` settings in `smb.conf`)
- Block ports 137/139/445 at the perimeter firewall for untrusted subnets
- Use supported SMB versions and configure SMB signing/encryption according to the environment's security requirements; disable SMBv1 where possible

## Disclaimer

This tool is intended for authorized security auditing and educational use in environments you own or have explicit permission to test (e.g. isolated lab subnets). Do not run it against networks without authorization.
