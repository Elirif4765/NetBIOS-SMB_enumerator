import subprocess
from impacket import nmb


def run_nbtscan(ip):
    nb = nmb.NetBIOS()
    scan_results = {'hostnames': set(), 'workgroups': set()}

    try:
        entries = nb.getnodestatus(nbname="*", destaddr=ip, timeout=1)
        if not entries:
            return None
        for entry in entries:
            name = entry['NAME'].strip().decode('latin-1', errors='ignore')
            if not name:
                continue

            name_type = entry['TYPE']
            is_group = bool(entry['NAME_FLAGS'] & 0x8000)

            if name_type == 0x00:
                if is_group and name:
                    scan_results['workgroups'].add(name)
                else:
                    scan_results['hostnames'].add(name)

        scan_results['hostnames'] = list(scan_results['hostnames'])
        scan_results['workgroups'] = list(scan_results['workgroups'])

        if scan_results['hostnames'] or scan_results['workgroups']:
            return scan_results

        return None
    
    except Exception:
        return None
        

def run_smbclient(ip):
    shares = []
    command = ["smbclient","-L",ip,"-N"]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    
    if result.returncode != 0:
        return None
    result = result.stdout.splitlines()
    for line in result:
        if 'Disk' in line:
            indie_words = line.strip().split()
            share_name = indie_words[0]
            if share_name != 'print$':
                shares.append(share_name)
    return shares