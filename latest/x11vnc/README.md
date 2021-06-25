# x11vnc server

auto start x11vnc server on boot for Wind River Linux xfce

## install

```bash
sudo x11vnc -storepasswd /etc/x11vnc.passwd
sudo chown root.root /etc/x11vnc.passwd
sudo chmod 600 /etc/x11vnc.passwd
sudo ./install.sh
```

## customize

edit file /lib/systemd/system/x11vnc.service

Any changes in the script will be applied after the next reboot.  
In order to apply changes immediately, you can run (as root)

```bash
sudo systemctl daemon-reload
sudo systemctl restart x11vnc.service
```

## status

```bash
sudo systemctl status x11vnc.service
```

## uninstall

```bash
sudo ./uninstall.sh
```
