import paramiko
import time
from textwrap import dedent

def _run(ssh, cmd, timeout=None):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        rc = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        return rc, out, err
    except Exception as e:
        return 255, "", f"{type(e).__name__}: {e}"

def configure_vm(ip, user="ubuntu", password="ubuntu", install_gui=None):
    log = []
    host = ip.split("/")[0]
    log.append(f"ssh {host}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for _ in range(12):
        try:
            ssh.connect(hostname=host, username=user, password=password, timeout=10)
            break
        except Exception:
            time.sleep(10)
    else:
        log.append("ssh failed")
        return "\n".join(log)

    log.append("ssh ok")

    log.append("updates ...")
    for c in [
        "sudo apt-get update",
        "sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade",
        "sudo apt-get -y autoremove --purge",
        "sudo apt-get -y autoclean",
    ]:
        rc, out, err = _run(ssh, c)
        log.append(f"{c} -> rc={rc}")
        if "apt --fix-broken install" in (out + err):
            _run(ssh, "sudo apt-get -f install -y")

    rc, out, err = _run(ssh, "lsblk -dn -o NAME | grep -q '^sdb$' && echo yes || echo no")
    if "yes" in out:
        log.append("sdb found -> mount /data")
        lvm_script = dedent("""\
            #!/usr/bin/env bash
            set -e
            pvcreate /dev/sdb
            vgcreate data-vg /dev/sdb
            lvcreate -n data -l 100%FREE data-vg
            mkfs.ext4 /dev/data-vg/data
            mkdir -p /data
            mount /dev/data-vg/data /data
            UUID=$(blkid -s UUID -o value /dev/data-vg/data)
            echo "UUID=$UUID  /data  ext4  defaults  0  2" >> /etc/fstab
            mount -a
        """)
        try:
            chan = ssh.get_transport().open_session()
            chan.exec_command("sudo bash -s")
            chan.send(lvm_script)
            chan.shutdown_write()
            while not chan.exit_status_ready():
                time.sleep(0.2)
            chan.recv_exit_status()
        except Exception as e:
            log.append(f"/data error: {e}")
    else:
        log.append("no sdb")

    if install_gui is None:
        rc, out, err = _run(ssh, "test -f /etc/provision/install_gui && echo yes || echo no")
        install_gui = ("yes" in out)

    if install_gui:
        log.append("install gui ...")
        for c in [
            "sudo apt-get update",
            "sudo DEBIAN_FRONTEND=noninteractive apt-get -y install ubuntu-desktop",
            "sudo apt-get -y install xrdp",
            "sudo systemctl enable xrdp",
            "sudo systemctl start xrdp",
            f"sudo adduser {user} ssl-cert",
            f"echo 'gnome-session' | sudo tee /home/{user}/.xsession",
            f"sudo chown {user}:{user} /home/{user}/.xsession",
        ]:
            rc, out, err = _run(ssh, c)
            log.append(f"{c} -> rc={rc}")
    else:
        log.append("gui skipped")

    ssh.close()
    log.append("done")
    return "\n".join(log)
