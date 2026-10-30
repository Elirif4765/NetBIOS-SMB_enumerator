from impacket import nmb, smbconnection


def run_nmb(ip):
    nb = nmb.NetBIOS()
    hostnames = set()
    workgroups = set()

    try:
        entries = nb.getnodestatus(nbname="*", destaddr=ip, timeout=2)
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
                    workgroups.add(name)
                else:
                    hostnames.add(name)

        if not hostnames and not workgroups:
            return None

        return {
            'hostnames': list(hostnames),
            'workgroups': list(workgroups)
        }

    except Exception:
        return None
        


def run_smb(ip):
    shares = []
    ports = [445, 139]
    conn = None

    for port in ports:
        remote_name = ip if port == 445 else "*SMBSERVER"
        try:
            conn = smbconnection.SMBConnection(remoteName=remote_name, remoteHost=ip, sess_port=port, timeout=2)
            break
        except:
            continue

    if conn is None:
        return None

    try:
        conn.login(user="", password="")
        all_shares = conn.listShares()

        for share in all_shares:
            share_name = share['shi1_netname'].rstrip('\x00')
            share_type = share['shi1_type']

            if (share_type & 0xF) == 0 and share_name != "print$":
                shares.append(share_name)

        return shares

    except Exception:
        return None