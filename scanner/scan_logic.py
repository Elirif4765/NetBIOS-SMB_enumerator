from scanner.protocols import run_nmb, run_smb
from scanner.network_utils import scan_ports
from datetime import datetime
import concurrent.futures
from scanner.reporting import create_host, write_db
from scanner.network_utils import get_local_subnet


def scan_ip(ip):
    ip = str(ip)
    port_status = scan_ports(ip)
    if port_status[139] == 'Filtered' and port_status[445] == 'Filtered':
        return None
    nbts_data = run_nmb(ip)
    if port_status[139] == 'Open' or port_status[445] == 'Open':
        share_data = run_smb(ip)
    else:
        share_data = None
    return {
        "ip": ip,
        "port_status": port_status,
        "nbts_data": nbts_data,
        "share_data": share_data
    }

def run_full_scan(max_workers=50, callback=None):
    start_time = datetime.now()
    interface, subnet = get_local_subnet()
    count = 0
    scan_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(scan_ip, subnet.hosts()):
            if result is not None:
                count += 1
                new_host = create_host(result)
                scan_results.append(new_host)
                if callback:
                    callback(new_host)

    elapsed = int((datetime.now() - start_time).total_seconds())
    write_db(scan_results, start_time, interface, subnet, elapsed, count)
    return interface, subnet, elapsed, count