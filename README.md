#Dieses File wurde Komplett von ChatGPT geschrieben.

# 🖥️ Python Proxmox VM Automatisierung

Dieses Projekt wurde im Rahmen meiner Semesterarbeit erstellt.  
Es automatisiert die Erstellung und Konfiguration von **Ubuntu-Clients** auf einem **Proxmox-Server** mittels Python.

## 🚀 Funktionen
- GUI (`main_gui.py`) zur Eingabe aller Parameter
- Automatisierte Erstellung einer neuen VM über **Proxmox API**
- Netzwerk- und Hardware-Konfiguration mit **Cloud-Init**
- Vollautomatische Grundkonfiguration via SSH:
  - System-Updates
  - Optionale GUI-Installation

## 📂 Projektstruktur
```
├── main_gui.py       # GUI zur Eingabe von Parametern (Name, IP, Maske, RAM, CPU, Disk)
├── create_vm.py      # Erstellt die VM auf Proxmox (Cloning, Cloud-Init, Hardware)
├── configure_vm.py   # Führt Updates und weitere Konfigurationen in der VM aus
```

## ⚙️ Voraussetzungen
- Proxmox-Server mit aktivierter API
- Python 3.x
- Installierte Abhängigkeiten:
  ```bash
  pip install proxmoxer paramiko tkinter
  ```
- Cloud-Init fähiges Ubuntu-Template im Proxmox

## ▶️ Verwendung
1. Repository klonen:
   ```bash
   git clone https://github.com/<DeinGithubUser>/<RepoName>.git
   cd <RepoName>
   ```

2. GUI starten:
   ```bash
   python main_gui.py
   ```

3. Parameter eintragen (Name, IP, Maske, Gateway, Ressourcen).

4. Mit einem Klick wird:
   - die VM erstellt (`create_vm.py`)
   - und direkt danach konfiguriert (`configure_vm.py`).

## 🛠️ Beispiel Screenshots
*(Hier kannst du später Screenshots deiner GUI einfügen)*

## 📖 Hintergrund
Die Arbeit entstand im Rahmen meiner Semesterarbeit an der ABB Technikerschule.  
Ziel war es, die **vollständige Automatisierung** der VM-Erstellung und Grundkonfiguration zu entwickeln.

---

✍️ Autor: *Marvin Künzli*
