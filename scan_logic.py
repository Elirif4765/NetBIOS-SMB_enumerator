from tools import run_nmb, run_smb
from network_utils import scan_ports


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