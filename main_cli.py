from scanner.scan_logic import run_full_scan
from scanner.database import engine
import scanner.models as models
from scanner.reporting import format_host_report

def main():   
    print(f"==[Scanning for SMB shares and live hosts]==\n")
    interface, subnet, elapsed, count = run_full_scan(50, print_output)
    print(f"==[Scan completed in {elapsed}s]==\n==[Interface: {interface} | Subnet: {subnet}]==\n==[Live Hosts found: {count}]==")

def print_output(result):
    print(format_host_report(result))

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=engine)
    main()