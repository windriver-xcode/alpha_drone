#!/bin/bash

#Require sudo
if [ $EUID != 0 ]; then
    sudo "$0" "$@"
    exit $?
fi

echo "removing service..."
systemctl stop x11vnc.service
systemctl disable x11vnc.service
echo "done"

echo "removing x11vnc password file /etc/x11vnc.passwd"
rm /etc/x11vnc.passwd
echo "done"

echo "removing service from /lib/systemd/system/..."
rm /lib/systemd/system/x11vnc.service
echo "done"

echo "reloading services"
systemctl daemon-reload
echo "done"

echo "x11vnc service uninstalled sucessfully!"