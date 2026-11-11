import scanner.models as models
from scanner.database import SessionLocal

def nbts_names(nbts_data):
    if nbts_data is None:
        hostnames = ['Unknown']
        workgroups = ['Unknown']
    else:
        hostnames = nbts_data["hostnames"]
        workgroups = nbts_data["workgroups"]
    return hostnames, workgroups

def format_host_report(result):
    hostnames = ", ".join(result.hostnames)
    workgroups = ", ".join(result.workgroups)

    lines = [
        f"{result.ip} - Host Names: {hostnames} | Workgroup Names: {workgroups} - "
        f"PORT 139: {result.port_139} | PORT 445: {result.port_445}"
    ]

    if result.shares is None:
        if result.port_445 == 'Open' or result.port_139 == 'Open':
            lines.append("     [+] SMB Security: Requires Authentication (Access Denied)")
    elif len(result.shares) == 0:
        lines.append("     [-] No anonymous custom shares found")
    else:
        lines.append("     [!] WARNING: ANONYMOUS SHARES FOUND!")
        for share in result.shares:
            lines.append(f"      -> {share}")

    return "\n".join(lines) + "\n"

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