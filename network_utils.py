import subprocess, ipaddress, socket


def get_local_subnet():
    command = "ip addr show eth0 | grep 'inet '"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    cidr_string = result.stdout.strip().split()[1]
    subnet = ipaddress.ip_network(cidr_string, strict=False)
    return subnet


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