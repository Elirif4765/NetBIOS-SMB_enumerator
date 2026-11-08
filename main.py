from datetime import datetime
import concurrent.futures
from reporting import print_output, create_host, write_db
from network_utils import get_local_subnet
from scan_logic import scan_ip
from database import engine
import models

models.Base.metadata.create_all(bind=engine)


def main():   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    interface, subnet = get_local_subnet()
    print(f"==[Scanning {interface}: {str(subnet)} for SMB shares and live hosts]==\n")
    start_time = datetime.now()
    count = 0

    scan_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        try:
            for result in executor.map(scan_ip, subnet.hosts()):
                if result is not None:
                    count += 1
                    print_output(result)
                    scan_results.append(create_host(result))

        except KeyboardInterrupt:
            print("\nScan interrupted by user. Cancelling pending tasks...")
            executor.shutdown(wait=False, cancel_futures=True)

    elapsed = int((datetime.now()-start_time).total_seconds())
    write_db(scan_results, timestamp, interface, subnet, elapsed, count)

    print(f"==[Scan completed in {elapsed}s]==\n==[Live Hosts found: {count}]==")

if __name__ == "__main__":
    main()