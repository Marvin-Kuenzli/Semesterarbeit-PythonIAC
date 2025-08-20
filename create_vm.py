from proxmoxer import ProxmoxAPI
import time, re

def _wait_task(proxmox, node, upid, timeout=900, interval=2):
    start = time.time()
    while time.time() - start < timeout:
        t = proxmox.nodes(node).tasks(upid).status.get()
        if t.get("status") == "stopped":
            if t.get("exitstatus") == "OK":
                return
            raise RuntimeError(f"Task failed: {t.get('exitstatus')}")
        time.sleep(interval)
    raise TimeoutError("Task did not finish in time")

def _ensure_stopped(proxmox, node, vmid, timeout=180, interval=2):
    info = proxmox.nodes(node).qemu(vmid).status.current.get()
    if info.get("status") == "running":
        upid = proxmox.nodes(node).qemu(vmid).status.stop.post()
        if upid:
            _wait_task(proxmox, node, upid, timeout=max(timeout, 180), interval=interval)
        start = time.time()
        while time.time() - start < timeout:
            st = proxmox.nodes(node).qemu(vmid).status.current.get()
            if st.get("status") == "stopped":
                return
            time.sleep(interval)
        raise TimeoutError("VM wurde nicht rechtzeitig gestoppt")

def _first_disk_key(cfg: dict) -> str | None:
    for prefix in ("scsi", "virtio", "sata", "ide"):
        k = f"{prefix}0"
        if k in cfg:
            return k
    return None

def _parse_size_g(entry: str) -> int | None:
    m = re.search(r"size=(\d+)([GMK])", entry)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    if unit == "G":
        return val
    if unit == "M":
        return max(1, val // 1024)
    if unit == "K":
        return max(1, val // (1024 * 1024))
    return None

def create_vm(name, ip, gw, user="ubuntu", password="ubuntu", memory=2048, cores=2, disk_gb=10):
    proxmox = ProxmoxAPI(
        host="192.168.110.2",
        user="root@pam",
        password="ProxmoxRoot123",
        verify_ssl=False,
        timeout=120,
        port=8006
    )

    node = "SR-PROX-01"
    template_vmid = 9000
    storage = "local-lvm"
    bridge = "vmbr0"

    new_vmid = int(proxmox.cluster.nextid.get())

    upid = proxmox.nodes(node).qemu(template_vmid).clone.post(
        newid=new_vmid, name=name, full=1, target=node, storage=storage
    )
    _wait_task(proxmox, node, upid)

    _ensure_stopped(proxmox, node, new_vmid)

    cfg = proxmox.nodes(node).qemu(new_vmid).config.get()
    disk_key = _first_disk_key(cfg)
    if not disk_key:
        raise RuntimeError("Keine primäre Disk gefunden.")
    current_g = _parse_size_g(cfg[disk_key]) or 0

    proxmox.nodes(node).qemu(new_vmid).config.post(scsihw="virtio-scsi-pci")

    if disk_gb != 0:
        proxmox.nodes(node).qemu(new_vmid).config.post(
            scsi1=f"{storage}:{int(disk_gb)}"
            )
        time.sleep(10)    
        
    proxmox.nodes(node).qemu(new_vmid).config.post(
        memory=int(memory),
        balloon=0,
        sockets=1,
        cores=int(cores),
        cpu="host",
        numa=0,
        net0=f"virtio,bridge={bridge}",
        ide2=f"{storage}:cloudinit",
        serial0="socket",
        vga="serial0",
        boot="order=scsi0;ide2;net0"
    )

    proxmox.nodes(node).qemu(new_vmid).config.post(
        ciuser=user,
        cipassword=password,
        ipconfig0=f"ip={ip},gw={gw}",
        nameserver="1.1.1.1 8.8.8.8"
    )

    proxmox.nodes(node).qemu(new_vmid).status.start.post()
    return new_vmid
