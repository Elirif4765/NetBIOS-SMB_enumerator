import subprocess


def run_nbtscan(ip):
    scan_results = {}
    command = ["nbtscan","-q",ip]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    result = result.stdout.strip()
    if result=='':
        return None
    nbtscan_parts = result.split()
    if(len(nbtscan_parts)>3):
        scan_results["hostname"]= nbtscan_parts[1]
        scan_results["workgroup"] = nbtscan_parts[3]
        return scan_results
    else:
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