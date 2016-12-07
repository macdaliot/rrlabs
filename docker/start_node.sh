#!/bin/bash

QEMU=/usr/local/bin/qemu-system-x86_64

. /root/ENV &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to load environment."
	exit 1
fi

# Building the management switch
brctl addbr mgmt0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to add mgmt0 bridge."
	exit 1
fi
ip addr add 192.0.2.1/24 dev mgmt0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to set IP address of mgmt0 bridge."
	exit 1
fi
ip link set mgmt0 up &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to bring mgmt0 bridge up."
	exit 1
fi
tunctl -u root -g root -t veth0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to create veth0 interface."
	exit 1
fi
ip link set dev veth0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to bring veth0 interface up."
	exit 1
fi
brctl addif mgmt0 veth0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to attach veth0 to mgmt0 bridge."
	exit 1
fi
iptables -t nat -A POSTROUTING -o mgmt0 -j MASQUERADE &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to configure iptables (MASQUERADE)."
	exit 1
fi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8022:8023 -j DNAT --to 192.0.2.254:22-23 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to configure iptables (NAT ports 22:23)."
	exit 1
fi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to 192.0.2.254:80 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to configure iptables (NAT port 80)."
	exit 1
fi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8443 -j DNAT --to 192.0.2.254:443 &> /dev/null
if [ $? -ne 0 ]; then
	echo "Failed to configure iptables (NAT port 443)."
	exit 1
fi

case "${TYPE}" in
	iol)
		ID=$1
		HNAME=$(cat /root/iourc | grep "=" | head -n1 | sed 's/\ *=.*//')

		# Checking ID
		if [[ ! "${ID}" =~ ^[0-9]+$ ]] || [[ ${ID} -gt 1022 ]] || [[ ${ID} -lt 1 ]]; then
			echo "ID is not a valid integer (must be between 1 and 1022)."
			exit 1
		fi

		# Setting hostname
		echo -e "127.0.0.1 localhost\n127.0.1.1 ${HNAME}\n127.0.0.127 xml.cisco.com" > /etc/hosts 2> /dev/null
		if [ $? -ne 0 ]; then
			echo "Failed to set /etc/hosts."
			exit 1
		fi
		echo "${HNAME}" > /etc/hostname 2> /dev/null && hostname ${HNAME} &> /dev/null
		if [ $? -ne 0 ]; then
			echo "Failed to set hostname."
			exit 1
		fi
		export HOSTNAME=${HNAME}

		# Writing NETMAP
		for I in $(seq 0 63); do
			echo "${ID}:${I} 1023:${I}" >> /root/NETMAP
			if [ $? -ne 0 ]; then
				echo "Failed to write NETMAP."
				exit 1
			fi
		done
		;;
	*)
		;;
esac


#${QEMU} -smp 1 -m 3072 -name xrv -uuid 1d76bafd-6d81-4002-a610-e36842793a7c -hda disk0.qcow2 -machine type=pc,accel=kvm,usb=off -serial telnet:0.0.0.0:2445,server,nowait -nographic -nodefconfig -nodefaults -rtc base=utc,driftfix=slew -global kvm-pit.lost_tick_policy=discard -no-hpet -realtime mlock=off -boot order=c


