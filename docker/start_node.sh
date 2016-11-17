#!/bin/bash

QEMU=/usr/local/bin/qemu-system-x86_64

. /root/ENV &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to load environment."
	exit 1
fi

${QEMU} -smp 1 -m 3072 -name xrv -uuid 1d76bafd-6d81-4002-a610-e36842793a7c -hda disk0.qcow2 -machine type=pc,accel=kvm,usb=off -serial telnet:0.0.0.0:2445,server,nowait -nographic -nodefconfig -nodefaults -rtc base=utc,driftfix=slew -global kvm-pit.lost_tick_policy=discard -no-hpet -realtime mlock=off -boot order=c


