# NetBIOS Host Discoverer & SMB Shares Enumerator

A lightweight Python network reconnaissance tool that scans a local subnet to identify hosts, extract NetBIOS metadata, and check for SMB shares that can be listed without a password, storing all scan history in a local SQLite database.

## Overview

Legacy or misconfigured network devices can expose internal file shares over TCP ports 139/445 via unauthenticated SMB sessions, and leak hostnames/workgroups over UDP port 137 (NetBIOS Name Service). This tool automates host discovery and attempts anonymous SMB share enumeration across a subnet using Python sockets together with `nmb` and `smbconnection` from `impacket`, without relying on heavyweight frameworks like Nmap NSE scripts or Metasploit. Results are displayed in real-time and persisted to a relational database using SQLAlchemy 2.0.

## Features

- **Auto subnet detection** — uses sockets and `psutil` to determine the active network interface and local CIDR block automatically
- **Ghost Host filtering** — skips hosts when both port 139 and port 445 checks time out and are classified as `Filtered`
- **Multithreaded scanning** — uses `ThreadPoolExecutor` with up to 50 worker threads (which can be customized) to process host scans concurrently
- **NetBIOS metadata extraction** — uses `nmb` from `impacket` to pull hostname and workgroup information of a target IP
- **Anonymous SMB share enumeration** — uses `smbconnection` from `impacket` to list disk shares with anonymous access (null username and password), while filtering out the administrative shares like `print$`; listing a share does not by itself prove that files inside it are readable (strong contender for future scope honestly)
- **Automated risk classification** — categorizes discovered hosts as `VULNERABLE`, `POTENTIAL RISK`, `SECURE`, or `CLOSED` based on port states and anonymous share accessibility
- **Persistent SQLite database storage** — uses SQLAlchemy 2.0 ORM to log scan batches (`scans` table) and associated host records (`host_results` table) into `report.db` with relational cascading and JSON-serialized metadata
- **Dual output** — prints a live summary to the terminal as hosts are discovered and commits the structured batch results to the database via the main thread once the scan finishes

## Requirements

- Python 3.10+ (for modern union type annotations used in SQLAlchemy 2.0 models)
- Linux / Windows (tested on Kali Linux / Ubuntu)
- `impacket`
- `psutil`
- `sqlalchemy` (2.0+)

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py
```

The script automatically initializes `report.db` if it does not exist, detects the primary network interface and local subnet, scans the subnet's host addresses using a thread pool, prints live results to the terminal, and commits the scan batch and host records to `report.db` in the working directory. The TCP connection timeout is 0.5 seconds per port; the `nmb` and `smbconnection` timeout is 2 seconds each.

## Example Output

```text
==[Scanning eth0: 192.168.56.0/24 for SMB shares and live hosts]==

192.168.56.130 - Host Names: METASPLOITABLE | Workgroup Names: WORKGROUP - PORT 139: Open | PORT 445: Open
     [!] WARNING: ANONYMOUS SHARES FOUND!
      -> tmp
      -> opt

==[Scan completed in 6s]==
==[Live Hosts found: 1]==
```

## Database Schema (`report.db`)

Scan data is modeled using SQLAlchemy 2.0 Declarative mapping across two linked tables with foreign key enforcement (`PRAGMA foreign_keys=ON`):

- **`scans`**: Tracks metadata for each execution (`id`, `scan_batch` timestamp, `interface`, `subnet`, `elapsed_seconds`, and `hosts_found`).
- **`host_results`**: Stores per-host findings linked via `scan_id` (`ip`, `port_139`, `port_445`, JSON arrays for `hostnames`, `workgroups`, and `shares`, plus the calculated `risk_status`).

## How It Works

1. **Discovery** – Determine the primary outbound IP via a UDP socket probe and match it against `psutil` interface addresses to get the active interface and CIDR range
2. **Port Check** – Perform TCP connection checks on ports 139 and 445 with a 0.5-second timeout, classifying each as `Open`, `Closed`, or `Filtered`
3. **Ghost Host Drop** – Skip a host if both port checks are classified as `Filtered`
4. **Deep Enumeration** – Use `.getnodestatus()` from `impacket.nmb` for NetBIOS information and, if either SMB port is open, use `.listShares()` from `impacket.smbconnection` to attempt anonymous share listing
5. **Threaded Execution** – Use up to 50 worker threads to scan hosts concurrently; the main thread processes results and builds ORM host instances; any number of threads can be used as per needs
6. **Dual Output & Persistence** – Print a live terminal summary for each host and commit the completed scan batch and linked host records to `report.db` in a single transaction

## Tested Scenarios

| Target State | Result |
|---|---|
| Both ports are `Filtered` | Host is skipped before deeper enumeration |
| Both ports are closed, with no NetBIOS response | Host can still appear in the output with `Unknown` hostname/workgroup (`CLOSED`); SMB share enumeration is skipped |
| Either port is open, but anonymous login is rejected | Flagged as `SECURE` (Requires Authentication) |
| Anonymous login succeeds, but no custom shares exist | Flagged as `POTENTIAL RISK` |
| Anonymous share listing returns accessible shares | Share names are listed and host is flagged as `VULNERABLE` |
| Ports closed but NetBIOS reachable on UDP 137 | Host may still be identified through `impacket.nmb` |

## Remediation Guidance

For any host where anonymous SMB share listing succeeds:

- Disable guest/anonymous SMB access (for example, review `restrict anonymous` and `guest ok` settings in `smb.conf`)
- Block ports 137/139/445 at the perimeter firewall for untrusted subnets
- Use supported SMB versions and configure SMB signing/encryption according to the environment's security requirements; disable SMBv1 where possible

## Disclaimer

This tool is intended for authorized security auditing and educational use in environments you own or have explicit permission to test (e.g. isolated lab subnets). Do not run it against networks without authorization.