import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
from blockchain_logger import initialize_blockchain_logger, get_blockchain_logger
from blockchain_integration import initialize_blockchain_integration, get_blockchain_integration

class BlockchainDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blockchain Surveillance Dashboard")
        self.geometry("900x600")
        
        # Initialize blockchain systems first
        initialize_blockchain_logger()
        initialize_blockchain_integration()
        
        self.logger = get_blockchain_logger()
        self.integration = get_blockchain_integration()
        self.create_widgets()
        self.refresh_stats()
        self.refresh_events()

    def create_widgets(self):
        tab_control = ttk.Notebook(self)
        self.tab_events = ttk.Frame(tab_control)
        self.tab_stats = ttk.Frame(tab_control)
        tab_control.add(self.tab_events, text='Events')
        tab_control.add(self.tab_stats, text='Statistics')
        tab_control.pack(expand=1, fill='both')

        columns = ("timestamp", "event_type", "severity", "description", "confidence", "session_id")
        self.tree = ttk.Treeview(self.tab_events, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=120)
        self.tree.pack(expand=1, fill='both', padx=10, pady=10)

        btn_refresh = ttk.Button(self.tab_events, text="Refresh Events", command=self.refresh_events)
        btn_refresh.pack(pady=5)

        self.stats_text = tk.Text(self.tab_stats, height=15, width=80, state='disabled')
        self.stats_text.pack(padx=10, pady=10)

        frame_actions = ttk.Frame(self.tab_stats)
        frame_actions.pack(pady=5)
        btn_verify = ttk.Button(frame_actions, text="Verify Chain", command=self.verify_chain)
        btn_export_chain = ttk.Button(frame_actions, text="Export Blockchain", command=self.export_chain)
        btn_export_session = ttk.Button(frame_actions, text="Export Session Logs", command=self.export_session)
        btn_verify.grid(row=0, column=0, padx=5)
        btn_export_chain.grid(row=0, column=1, padx=5)
        btn_export_session.grid(row=0, column=2, padx=5)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_events(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            events = self.logger.get_events_by_type("all", limit=100)
            for event in events:
                self.tree.insert('', 'end', values=(
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event.timestamp)),
                    event.event_type,
                    event.severity,
                    event.description,
                    f"{event.confidence_score:.2f}",
                    event.session_id
                ))
            self.status_var.set(f"Loaded {len(events)} events.")
        except Exception as e:
            self.status_var.set(f"Error loading events: {e}")

    def refresh_stats(self):
        try:
            stats = self.logger.get_statistics()
            self.stats_text.config(state='normal')
            self.stats_text.delete(1.0, tk.END)
            for k, v in stats.items():
                self.stats_text.insert(tk.END, f"{k}: {v}\n")
            self.stats_text.config(state='disabled')
            self.status_var.set("Statistics loaded.")
        except Exception as e:
            self.status_var.set(f"Error loading statistics: {e}")

    def verify_chain(self):
        try:
            valid = self.logger.verify_chain()
            messagebox.showinfo("Verify Chain", f"Blockchain is {'valid' if valid else 'INVALID'}.")
            self.status_var.set("Chain verification complete.")
        except Exception as e:
            messagebox.showerror("Verify Chain", f"Error: {e}")
            self.status_var.set(f"Error verifying chain: {e}")

    def export_chain(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        try:
            success = self.logger.export_chain(filepath)
            if success:
                messagebox.showinfo("Export Blockchain", f"Exported to {filepath}")
                self.status_var.set(f"Blockchain exported to {filepath}")
            else:
                messagebox.showerror("Export Blockchain", "Export failed.")
                self.status_var.set("Export failed.")
        except Exception as e:
            messagebox.showerror("Export Blockchain", f"Error: {e}")
            self.status_var.set(f"Error exporting blockchain: {e}")

    def export_session(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        try:
            success = self.integration.export_session_logs(filepath)
            if success:
                messagebox.showinfo("Export Session Logs", f"Exported to {filepath}")
                self.status_var.set(f"Session logs exported to {filepath}")
            else:
                messagebox.showerror("Export Session Logs", "Export failed.")
                self.status_var.set("Export failed.")
        except Exception as e:
            messagebox.showerror("Export Session Logs", f"Error: {e}")
            self.status_var.set(f"Error exporting session logs: {e}")

if __name__ == "__main__":
    app = BlockchainDashboard()
    app.mainloop()
