from datetime import datetime
import concurrent.futures
from reporting import print_output, write_report
from network_utils import get_local_subnet
from scan_logic import scan_ip


def main():   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.txt"
    
    interface, subnet = get_local_subnet()
    print(f"==[Scanning {interface}: {str(subnet)} for SMB shares and live hosts]==\n")
    start_time = datetime.now()
    count = 0

    with open(filename, "w") as log:
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            try:
                for result in executor.map(scan_ip, subnet.hosts()):
                    if result is not None:
                        count += 1
                        print_output(result)
                        write_report(result, log)

            except KeyboardInterrupt:
                print("\nScan interrupted by user. Cancelling pending tasks...")
                executor.shutdown(wait=False, cancel_futures=True)

    elapsed = (datetime.now()-start_time).seconds
    print(f"==[Scan completed in {elapsed}s]==\n==[Live Hosts found: {count}]==")

if __name__ == "__main__":
    main()