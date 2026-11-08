import models
from database import SessionLocal

def nbts_names(nbts_data):
    if nbts_data is None:
        hostnames = ['Unknown']
        workgroups = ['Unknown']
    else:
        hostnames = nbts_data["hostnames"]
        workgroups = nbts_data["workgroups"]
    return hostnames, workgroups

def print_output(result):
    ip = result["ip"]
    port_status_139 = result["port_status"][139]
    port_status_445 = result["port_status"][445]
    nbts_data = result["nbts_data"]
    share_data = result["share_data"]
    hostnames, workgroups = nbts_names(nbts_data)
    
    print(f"{ip} - Host Names: {', '.join(hostnames)} | Workgroup Names: {', '.join(workgroups)} - PORT 139: {port_status_139} | PORT 445: {port_status_445}")

    if share_data is None:
        if port_status_445=='Open' or port_status_139=='Open':
            print("     [+] SMB Security: Requires Authentication (Access Denied)")
    elif len(share_data) == 0:
        print("     [-] No anonymous custom shares found")
    else:
        print("     [!] WARNING: ANONYMOUS SHARES FOUND!")
        for share in share_data:
            print(f"      -> {share}")
    print()

def create_host(result):
    ip = result["ip"]
    port_status_139 = result["port_status"][139]
    port_status_445 = result["port_status"][445]
    nbts_data = result["nbts_data"]
    share_data = result["share_data"]
    hostnames, workgroups = nbts_names(nbts_data)
    status = None

    if share_data is None:
        if port_status_445 == 'Open' or port_status_139 == 'Open':
            status = "SECURE"
        else:
            status = "CLOSED"
    elif len(share_data) == 0:
        status = "POTENTIAL RISK"
    else:
        status = "VULNERABLE"
    
    new_host = models.Hosts(ip=ip, port_139=port_status_139, port_445=port_status_445, hostnames=hostnames, workgroups=workgroups, shares=share_data, risk_status=status)
    
    return new_host

def write_db(scan_results, timestamp, interface, subnet, elapsed, count):
    with SessionLocal() as db:
        new_scan = models.Scans(scan_batch=timestamp, interface=interface, subnet=str(subnet), elapsed_seconds=elapsed, hosts_found=count, hosts=scan_results)
        db.add(new_scan)
        db.commit()