from scanner.database import SessionLocal, engine
import scanner.models as models
import threading
from sqlalchemy import select
from scanner.scan_logic import run_full_scan
import customtkinter as ctk
from scanner.reporting import format_host_report


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")


class NetScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NetBIOS & SMB Enumerator")
        self.geometry("1280x720")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill='both', expand=True)

        self.scan_tab = self.tabview.add("Run Scan")
        self.history_tab = self.tabview.add("Scan History")

        self.scans_list_frame = ctk.CTkScrollableFrame(self.history_tab, width=280, label_text="Past Scans")
        self.scans_list_frame.pack(side="left", padx=10, pady=10, fill='y')

        self.hosts_list_frame = ctk.CTkScrollableFrame(self.history_tab, label_text="Host Details")
        self.hosts_list_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        self.load_scans()

        controls_frame = ctk.CTkFrame(self.scan_tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        self.thread_lbl = ctk.CTkLabel(controls_frame, text="Threads: 50", font=('Arial', 14))
        self.thread_lbl.pack(side="left", padx=10)

        self.thread_slider = ctk.CTkSlider(
            controls_frame, 
            from_=10, 
            to=200, 
            number_of_steps=19, 
            command=lambda val: self.update_value(val)
        )
        self.thread_slider.set(50)
        self.thread_slider.pack(side="left", pady=10)
        
        self.start_btn = ctk.CTkButton(
            controls_frame,
            text="Start Scan",
            command = self.start_scan
        )
        self.start_btn.pack(side="left", padx=15, pady=10)

        self.log_box = ctk.CTkTextbox(self.scan_tab, font=('Courier', 13))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.mainloop()

    def update_value(self, value):
        self.thread_lbl.configure(text=f"Threads: {int(value)}")

    def start_scan(self):
        threads = int(self.thread_slider.get())

        self.start_btn.configure(state="disabled", text="Scanning...")
        self.log_box.delete("1.0", "end")

        scan_thread = threading.Thread(
            target = self.run_scan_background,
            args=(threads, ),
            daemon=True
        )
        scan_thread.start()

    def run_scan_background(self, threads):
        self.log_box.insert("end", f"==[Scanning for SMB shares and live hosts]==\n\n")

        interface, subnet, elapsed, count = run_full_scan(threads, self.log)

        self.log_box.insert("end", f"==[Scan completed in {elapsed}s]==\n==[Interface: {interface} | Subnet: {subnet}]==\n==[Live Hosts found: {count}]==\n" )
        self.log_box.see("end")

        self.start_btn.configure(state="normal", text="Start Scan")
        self.load_scans()

    def log(self, result):
        report_text = format_host_report(result) + "\n"
        self.log_box.insert("end", report_text)

    def load_scans(self):
        for widget in self.scans_list_frame.winfo_children():
            widget.destroy()
        with SessionLocal() as db:
            scans = db.scalars(select(models.Scans).order_by(models.Scans.id.desc())).all()

            for scan in scans:
                has_vuln = any(h.risk_status == "VULNERABLE" for h in scan.hosts)

                time = scan.scan_batch.strftime("%d %b %Y, %I:%M %p")
                btn_text = f"{time}\n{scan.interface}: {scan.subnet} • ({scan.hosts_found} hosts)"
                if has_vuln:
                    btn_text = "[!] " + btn_text
                    btn_color = "#b82e2e"

                else:
                    btn_color = "#1f538d"

                btn = ctk.CTkButton(
                    self.scans_list_frame,
                    text = btn_text,
                    fg_color = btn_color,
                    command = lambda s_id=scan.id: self.display_hosts(s_id)
                )
                btn.pack(padx=5, pady=5, fill="x")

    def display_hosts(self, scan_id):
        for widget in self.hosts_list_frame.winfo_children():
            widget.destroy()

        with SessionLocal() as db:
            scan = db.get(models.Scans, scan_id)
            if not scan:
                return

            if not scan.hosts:
                empty_lbl = ctk.CTkLabel(
                    self.hosts_list_frame,
                    text="No live hosts were found in this scan",
                    font=('Arial', 24)
                )
                empty_lbl.pack(pady=20)
                return

            for host in scan.hosts:
                status_color = {
                    "VULNERABLE": "#d32f2f",
                    "POTENTIAL RISK": "#f57c00",
                    "SECURE": "#388e3c",
                    "CLOSED": "#757575",
                }.get(host.risk_status, "#ffffff")

                card = ctk.CTkFrame(
                    self.hosts_list_frame,
                    border_width=2,
                    border_color=status_color
                )
                card.pack(fill="x", padx=10, pady=10)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="both", padx=10, pady=8)

                ip_label = ctk.CTkLabel(
                    top_row,
                    text=host.ip,
                    font=('Arial', 16, 'bold')
                )
                ip_label.pack(side="left")

                badge = ctk.CTkLabel(
                    top_row,
                    text=f"[{host.risk_status}]",
                    text_color = status_color,
                    font=('Arial', 13, "bold")
                )
                badge.pack(side="right")

                hostnames = ", ".join(host.hostnames)
                workgroups = ", ".join(host.workgroups)
                info_text = f"Hostnames: {hostnames} | Workgroups: {workgroups} | Port 139: {host.port_139} | Port 445: {host.port_445}"
                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(fill="both", padx=10, pady=5)
                info_lbl = ctk.CTkLabel(info_frame, text=info_text, font=('Arial', 12))
                info_lbl.pack(anchor="w", padx=2, pady=2)

                if host.shares:
                    shares_text = "Anonymous shares: " + ", ".join(host.shares)
                    shares_lbl = ctk.CTkLabel(
                        info_frame,
                        text=shares_text,
                        text_color = "#ff5252",
                        font=('Arial', 12, 'bold')
                    )
                    shares_lbl.pack(anchor="w", padx=2, pady=(2,8))

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=engine)
    NetScannerApp()