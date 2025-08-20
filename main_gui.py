# main_gui.py
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from create_vm import create_vm
from configure_vm import configure_vm

MASK_CHOICES = [
    ("/16 (255.255.0.0)", 16),
    ("/17 (255.255.128.0)", 17),
    ("/18 (255.255.192.0)", 18),
    ("/19 (255.255.224.0)", 19),
    ("/20 (255.255.240.0)", 20),
    ("/21 (255.255.248.0)", 21),
    ("/22 (255.255.252.0)", 22),
    ("/23 (255.255.254.0)", 23),
    ("/24 (255.255.255.0)", 24),
    ("/25 (255.255.255.128)", 25),
    ("/26 (255.255.255.192)", 26),
    ("/27 (255.255.255.224)", 27),
    ("/28 (255.255.255.240)", 28),
    ("/29 (255.255.255.248)", 29),
    ("/30 (255.255.255.252)", 30),
    ("/32 (255.255.255.255)", 32),
]

def run_in_thread(fn):
    t = threading.Thread(target=fn, daemon=True)
    t.start()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Proxmox VM Creator")
        self.geometry("650x620")

        pad = {'padx': 8, 'pady': 6}

        frm = ttk.Frame(self)
        frm.pack(fill="x", **pad)

        ttk.Label(frm, text="VM-Name").grid(row=0, column=0, sticky="w")
        self.txt_name = ttk.Entry(frm)
        self.txt_name.grid(row=0, column=1, sticky="ew")
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="IP-Adresse").grid(row=1, column=0, sticky="w")
        self.txt_ip = ttk.Entry(frm)
        self.txt_ip.grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Subnetzmaske").grid(row=1, column=2, sticky="w")
        self.cmb_mask = ttk.Combobox(frm, state="readonly",
                                     values=[label for (label, _) in MASK_CHOICES])
        default_idx = [p for (_, p) in MASK_CHOICES].index(24)
        self.cmb_mask.current(default_idx)
        self.cmb_mask.grid(row=1, column=3, sticky="ew")

        ttk.Label(frm, text="Gateway").grid(row=2, column=0, sticky="w")
        self.txt_gw = ttk.Entry(frm)
        self.txt_gw.grid(row=2, column=1, sticky="ew")

        ttk.Label(frm, text="Benutzer").grid(row=3, column=0, sticky="w")
        self.txt_user = ttk.Entry(frm)
        self.txt_user.insert(0, "ubuntu")
        self.txt_user.grid(row=3, column=1, sticky="ew")

        ttk.Label(frm, text="Passwort").grid(row=3, column=2, sticky="w")
        self.txt_pw = ttk.Entry(frm, show="*")
        self.txt_pw.insert(0, "ubuntu")
        self.txt_pw.grid(row=3, column=3, sticky="ew")

        ttk.Label(frm, text="RAM (MB)").grid(row=4, column=0, sticky="w")
        self.spn_ram = ttk.Spinbox(frm, from_=512, to=262144, increment=256)
        self.spn_ram.set(2048)
        self.spn_ram.grid(row=4, column=1, sticky="ew")

        ttk.Label(frm, text="CPU-Kerne").grid(row=4, column=2, sticky="w")
        self.spn_cores = ttk.Spinbox(frm, from_=1, to=64)
        self.spn_cores.set(2)
        self.spn_cores.grid(row=4, column=3, sticky="ew")

        self.var_add_disk = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(frm, text="Zusatzdisk hinzufügen", variable=self.var_add_disk,
                              command=self._toggle_disk)
        chk.grid(row=5, column=0, sticky="w")

        ttk.Label(frm, text="Grösse (GB)").grid(row=5, column=2, sticky="w")
        self.spn_disk = ttk.Spinbox(frm, from_=1, to=2048)
        self.spn_disk.set(10)
        self.spn_disk.grid(row=5, column=3, sticky="ew")

        self.var_install_gui = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="GUI installieren (ubuntu-desktop + xrdp)",
                        variable=self.var_install_gui).grid(row=6, column=0, columnspan=2, sticky="w")

        self.btn_start = ttk.Button(frm, text="VM erstellen", command=self.on_start)
        self.btn_start.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        out_frame = ttk.LabelFrame(self, text="Ausgabe")
        out_frame.pack(fill="both", expand=True, **pad)
        self.txt_log = tk.Text(out_frame, height=18)
        self.txt_log.pack(fill="both", expand=True, padx=6, pady=6)

    def _toggle_disk(self):
        state = "normal" if self.var_add_disk.get() else "disabled"
        self.spn_disk.configure(state=state)

    def log(self, text: str):
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.update_idletasks()

    def on_start(self):
        name = self.txt_name.get().strip()
        ip_only = self.txt_ip.get().strip()
        gw = self.txt_gw.get().strip()

        if not name or not ip_only or not gw:
            messagebox.showerror("Fehler", "Bitte Name, IP und Gateway angeben.")
            return

        label = self.cmb_mask.get()
        try:
            prefix = next(p for (lbl, p) in MASK_CHOICES if lbl == label)
        except StopIteration:
            prefix = 24

        ip_cidr = f"{ip_only}/{prefix}"

        user = self.txt_user.get().strip() or "ubuntu"
        pw = self.txt_pw.get().strip() or "ubuntu"

        try:
            memory = int(self.spn_ram.get())
            cores = int(self.spn_cores.get())
        except ValueError:
            messagebox.showerror("Fehler", "RAM und Kerne müssen Zahlen sein.")
            return

        if self.var_add_disk.get():
            try:
                disk_gb = int(self.spn_disk.get())
            except ValueError:
                messagebox.showerror("Fehler", "Disk-Grösse muss eine Zahl sein.")
                return
        else:
            disk_gb = 0

        install_gui = self.var_install_gui.get()

        self.btn_start.config(state="disabled")
        self.log("Starte automatische Erstellung...")

        def worker():
            try:
                vmid = create_vm(
                    name=name,
                    ip=ip_cidr,
                    gw=gw,
                    user=user,
                    password=pw,
                    memory=memory,
                    cores=cores,
                    disk_gb=disk_gb
                )
                self.log(f"VM '{name}' (VMID: {vmid}) erstellt und gestartet.")

                self.log("Starte Konfiguration in der VM...")
                summary = configure_vm(ip=ip_cidr, user=user, password=pw, install_gui=install_gui)
                self.log(summary)

                if install_gui:
                    self.log("Hinweis: RDP-Verbindung ggf. nach Neustart nutzen.")

                messagebox.showinfo("Fertig", f"VM '{name}' (VMID: {vmid}) konfiguriert.")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
                self.log(f"Fehler: {e}")
            finally:
                self.btn_start.config(state="normal")

        run_in_thread(worker)

if __name__ == "__main__":
    App().mainloop()
