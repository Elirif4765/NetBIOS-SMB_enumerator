import customtkinter as ctk

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

class NetScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NetBIOS & SMB Enumerator")
        self.geometry("900x600")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill='both', expand=True)

        self.scan_tab = self.tabview.add("Run Scan")
        self.history_tab = self.tabview.add("Scan History")

        self.scans_list_frame = ctk.CTkScrollableFrame(self.history_tab, width=280, label_text="Past Scans")
        self.scans_list_frame.pack(side="left", padx=10, pady=10, fill='y')

        self.hosts_list_frame = ctk.CTkScrollableFrame(self.history_tab, label_text="Host Details")
        self.hosts_list_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)
        
        self.mainloop()

NetScannerApp()