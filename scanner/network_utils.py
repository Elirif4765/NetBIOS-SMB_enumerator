import ipaddress, socket, psutil


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
    except OSError:
        primary_ip = None
    finally:
        s.close()
    return primary_ip


def get_local_subnet():
    primary_ip = get_local_ip()
    if not primary_ip:
        raise RuntimeError("No active network connection found")
    
    interfaces = psutil.net_if_addrs()

    for intf_name, addresses in interfaces.items():
        ip_addr = None
        netmask = None

        for addr in addresses:
            if addr.family == socket.AF_INET:
                if addr.address == primary_ip:
                    ip_addr = addr.address
                    netmask = addr.netmask
                    break

        if ip_addr and netmask:
            cidr_string = f"{ip_addr}/{netmask}"
            subnet = ipaddress.ip_network(cidr_string, strict=False)
            return (intf_name, subnet)
        
    raise RuntimeError(f"Could not find an interface")


def scan_ports(ip):
    port_status = {}
    ports = [139,445]
    for port in ports:
        socks = None
        try:
            socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socks.settimeout(0.5)
            socks.connect((ip, port))
            port_status[port] = 'Open'
        except socket.timeout:
            port_status[port] = 'Filtered'
        except (ConnectionRefusedError, OSError):
            port_status[port] = 'Closed'
        finally:
            if socks:
                socks.close()
    return port_status