# NetBIOS Host Discoverer & SMB Shares Enumerator

A lightweight Python network reconnaissance tool (with both CLI and GUI interfaces) that scans a local subnet to identify hosts, extract NetBIOS metadata, and check for SMB shares that can be listed without a password, storing all scan history in a local SQLite database.

## Overview

Legacy or misconfigured network devices can expose internal file shares over TCP ports 139/445 via unauthenticated SMB sessions, and leak hostnames/workgroups over UDP port 137 (NetBIOS Name Service). This tool automates host discovery and attempts anonymous SMB share enumeration across a subnet using Python sockets together with `nmb` and `smbconnection` from `impacket`, without relying on heavyweight frameworks like Nmap NSE scripts or Metasploit. Results are displayed in real-time (via terminal or a CustomTkinter desktop interface) and persisted to a relational database using SQLAlchemy 2.0.

## Features

- **Dual interface (GUI & CLI)** — launch a desktop GUI built with `customtkinter` (`main_gui.py`) featuring live scan logs, adjustable thread sliders (10–200 threads), and an interactive **Scan History** viewer with color-coded host cards, or run headless in the terminal (`main_cli.py`)
- **Auto subnet detection** — uses sockets and `psutil` to determine the active network interface and local CIDR block automatically
- **Ghost Host filtering** — skips hosts when both port 139 and port 445 checks time out and are classified as `Filtered`
- **Multithreaded scanning** — uses `ThreadPoolExecutor` (50 worker threads by default in CLI, or 10–200 configurable via the GUI slider) to process host scans concurrently
- **NetBIOS metadata extraction** — uses `nmb` from `impacket` to pull hostname and workgroup information of a target IP
- **Anonymous SMB share enumeration** — uses `smbconnection` from `impacket` to list disk shares with anonymous access (null username and password), while filtering out administrative shares like `print$`; listing a share does not by itself prove that files inside it are readable (strong contender for future scope honestly)
- **Automated risk classification** — categorizes discovered hosts as `VULNERABLE`, `POTENTIAL RISK`, `SECURE`, or `CLOSED` based on port states and anonymous share accessibility
- **Persistent SQLite database storage** — uses SQLAlchemy 2.0 ORM to log scan batches (`scans` table) and associated host records (`host_results` table) into `report.db` with relational cascading and JSON-serialized metadata
- **Real-time logging & persistence** — streams a live summary to the active UI as hosts are discovered and commits the structured batch results to the database once the scan finishes

## Project Structure

```text
├── main_cli.py            # Terminal entry point
├── main_gui.py            # CustomTkinter GUI entry point
├── requirements.txt       # Project dependencies
└── scanner/               # Core scanning and persistence package
    ├── __init__.py
    ├── database.py        # SQLAlchemy engine & SQLite session setup
    ├── models.py          # Declarative ORM models (Scans, Hosts)
    ├── network_utils.py   # Interface/subnet detection & TCP port scanning
    ├── protocols.py       # Impacket NetBIOS & SMB enumeration
    ├── reporting.py       # Report formatting, risk classification & DB writes
    └── scan_logic.py      # Multithreaded scan orchestration
```

## Requirements

- Python 3.10+ (for modern union type annotations used in SQLAlchemy 2.0 models)
- Linux / Windows (tested on Kali Linux / Ubuntu / Windows)
- `customtkinter`
- `impacket`
- `psutil`
- `sqlalchemy` (2.0+)

```bash
pip install -r requirements.txt
```

## Usage

**Option 1: Desktop GUI**
```bash
python3 main_gui.py
```
Opens the **NetBIOS & SMB Enumerator** window (or run the standalone `NetScanner.exe` from the Releases page on Windows). Use the **Run Scan** tab to adjust worker threads and view real-time output, or switch to the **Scan History** tab to inspect past scan batches and color-coded host vulnerability cards.

**Option 2: Command-Line Interface (CLI)**
```bash
python3 main_cli.py
```
Both entry points automatically initialize `report.db` in the working directory if it does not exist, detect the primary network interface and local subnet, scan the subnet's host addresses using a thread pool, stream live results, and commit the scan batch and host records to `report.db`. The TCP connection timeout is 0.5 seconds per port; the `nmb` and `smbconnection` timeout is 2 seconds each.

## Example Output

```text
==[Scanning for SMB shares and live hosts]==

192.168.56.130 - Host Names: METASPLOITABLE | Workgroup Names: WORKGROUP - PORT 139: Open | PORT 445: Open
     [!] WARNING: ANONYMOUS SHARES FOUND!
      -> tmp
      -> opt

==[Scan completed in 6s]==
==[Interface: eth0 | Subnet: 192.168.56.0/24]==
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
5. **Threaded Execution** – Scan hosts concurrently using `ThreadPoolExecutor` (50 threads in CLI or 10–200 via the GUI slider); as each host finishes, build ORM `Hosts` instances and fire the UI callback
6. **Dual Output & Persistence** – Stream a live summary for each discovered host to the terminal or GUI log box and commit the completed scan batch and linked host records to `report.db` in a single transaction

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