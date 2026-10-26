

def nbts_names(nbts_data):
    if nbts_data is None:
        hostname = 'Unknown'
        workgroup = 'Unknown'
    else:
        hostname = nbts_data["hostname"]
        workgroup = nbts_data["workgroup"]
    return hostname, workgroup

def print_output(result):
    ip = result["ip"]
    port_status_139 = result["port_status"][139]
    port_status_445 = result["port_status"][445]
    nbts_data = result["nbts_data"]
    share_data = result["share_data"]
    hostname, workgroup = nbts_names(nbts_data)
    
    print(f"{ip} - Host:{hostname} Workgroup:{workgroup} - PORT 139: {port_status_139} | PORT 445: {port_status_445}")

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

def write_report(result, log):
    ip = result["ip"]
    port_status_139 = result["port_status"][139]
    port_status_445 = result["port_status"][445]
    nbts_data = result["nbts_data"]
    share_data = result["share_data"]
    hostname, workgroup = nbts_names(nbts_data)
    
    print("=" * 60, file=log)
    print(f"SECURITY AUDIT REPORT FOR TARGET: {ip}", file=log)
    print("=" * 60, file=log)
    print(f"[*] NetBIOS Hostname : {hostname}", file=log)
    print(f"[*] NetBIOS Workgroup: {workgroup}", file=log)
    print(f"[*] Port 139 Status  : {port_status_139}", file=log)
    print(f"[*] Port 445 Status  : {port_status_445}", file=log)
    print("-" * 60, file=log)

    if share_data is None:
        if port_status_445 == 'Open' or port_status_139 == 'Open':
            print("[+] SMB Security Assessment:", file=log)
            print("    Status: SECURE (Requires Authentication)", file=log)
            print("    Notice: Target rejected anonymous share listing requests.", file=log)

    elif len(share_data) == 0:
        print("[-] SMB Security Assessment:", file=log)
        print("    Status: POTENTIAL RISK (Anonymous Session Allowed)", file=log)
        print("    Notice: Connected successfully, but no custom disk shares were found.", file=log)
    else:
        print("[!] VULNERABILITY ALERT: Anonymous Share Enumeration Successful!", file=log)
        print("    Risk Level: HIGH", file=log)
        print("    The following custom file shares are readable without password verification:", file=log)
        for share in share_data:
            print(f"     -> {share}", file=log)
    print("\n\n", file=log)