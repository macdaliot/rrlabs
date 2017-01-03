#!/bin/bash

WRAPPER=/sbin/wrapper.py

function usage {
	echo "Usage: $0 [OPTIONS]"
	echo "  -a INTEGER"
	echo "     Number of ATM interfaces"
	echo "  -e INTEGER"
	echo "     Number of Ethernet interfaces"
	echo "  -g STRING"
	echo "     switcherd hostname or IP address"
	echo "  -i STRING"
	echo "     Device ID or UUID"
	echo "  -l INTEGER"
	echo "     Label"
	echo "  -m INTEGER"
	echo "     Configured memory"
	echo "  -s INTEGER"
	echo "     Number of serial interfaces"
	echo "  -t"
	echo "     Enable terminal server"
	echo "  -w STRING"
	echo "     Window title"
}

while getopts ":a:e:g:i:l:m:s:tw:" opt; do
	case $opt in
		a)
			ATM=${OPTARG}
			;;
		e)
			ETH=${OPTARG}
			;;
		g)
			SWITCHERD=${OPTARG}
			;;
		i)
			ID=${OPTARG}
			;;
		l)
			LABEL=${OPTARG}
			;;
		m)
			MEMORY=${OPTARG}
			;;
		s)
			SERIAL=${OPTARG}
			;;
		t)
			TS=1
			;;
		w)
			WINDOW=${OPTARG}
			;;
		*)
			echo "ERROR: unhandled option"
			usage
			exit 1
	esac
done

. /opt/image/ENV &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to load environment"
	exit 1
fi

# Checking paramters
if [ "${LABEL}" == "" ]; then
	echo "ERROR: missing label"
	exit 1
fi
if [ "${SWITCHERD}" == "" ]; then
	echo "ERROR: missing switcherid"
	exit 1
fi
case "${TYPE}" in
	iol)
		if [ "${ID}" == "" ]; then
			echo "ERROR: missing ID"
			exit 1
		fi
		;;
	*)
		echo "ERROR: unsupported node type"
		exit 1
esac

# Building the management switch
brctl addbr mgmt0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to add mgmt0 bridge"
	exit 1
fi
ip addr add 192.0.2.1/24 dev mgmt0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to set IP address of mgmt0 bridge"
	exit 1
fi
ip link set mgmt0 up &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to bring mgmt0 bridge up"
	exit 1
fi
tunctl -u root -g root -t veth0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to create veth0 interface"
	exit 1
fi
ip link set dev veth0 up &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to bring veth0 interface up"
	exit 1
fi
brctl addif mgmt0 veth0 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to attach veth0 to mgmt0 bridge"
	exit 1
fi
iptables -t nat -A POSTROUTING -o mgmt0 -j MASQUERADE &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to configure iptables (MASQUERADE)"
	exit 1
fi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8022:8023 -j DNAT --to 192.0.2.254:22-23 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to configure iptables (NAT ports 22:23)"
	exit 1
fi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to 192.0.2.254:80 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to configure iptables (NAT port 80)"
	exit 1
fi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8443 -j DNAT --to 192.0.2.254:443 &> /dev/null
if [ $? -ne 0 ]; then
	echo "ERROR: failed to configure iptables (NAT port 443)."
	exit 1
fi

case "${TYPE}" in
	iol)
		HNAME=$(cat /opt/image/iourc | grep "=" | head -n1 | sed 's/\ *=.*//')

		# Checking ID
		if [[ ! "${ID}" =~ ^[0-9]+$ ]] || [[ ${ID} -gt 1024 ]] || [[ ${ID} -lt 1 ]]; then
			echo "ERROR: ID is not a valid integer (must be between 1 and 1024)"
			exit 1
		fi

		# Setting hostname
		echo -e "127.0.0.1 localhost\n127.0.1.1 ${HNAME}\n127.0.0.127 xml.cisco.com" > /etc/hosts 2> /dev/null
		if [ $? -ne 0 ]; then
			echo "ERROR: failed to set /etc/hosts"
			exit 1
		fi
		echo "${HNAME}" > /etc/hostname 2> /dev/null && hostname ${HNAME} &> /dev/null
		if [ $? -ne 0 ]; then
			echo "ERROR: failed to set hostname"
			exit 1
		fi
		export HOSTNAME=${HNAME}

		mkdir -p /tmp/netio0 &> /dev/null
		if [ $? -ne 0 ]; then
			echo "ERROR: failed to create directory (/tmp/netio)"
			exit 1
		fi

		ARGS="-g ${SWITCHERD} -i ${ID} -l ${LABEL} -f /opt/image/iol.bin"
		if [ "${TS}" == "1" ]; then
			ARGS="${ARGS} -t"
		fi
		if [ "${TITLE}" != "" ]; then
			ARGS="${ARGS} -w ${TITLE}"
		fi
		ARGS="${ARGS} -- -q -n 4096"
		if [ "${ATM}" != "" ]; then
			ARGS="${ARGS} -a ${ATM}"
		fi
		if [ "${ETH}" != "" ]; then
			ARGS="${ARGS} -e ${ETH}"
		fi
		if [ "${MEMORY}" != "" ]; then
			ARGS="${ARGS} -m ${MEMORY}"
		fi
		if [ "${SERIAL}" != "" ]; then
			ARGS="${ARGS} -s ${SERIAL}"
		fi

		echo "INFO: starting wrapper: ${WRAPPER} ${ARGS}"
		${WRAPPER} ${ARGS}
		;;
esac


#${QEMU} -smp 1 -m 3072 -name xrv -uuid 1d76bafd-6d81-4002-a610-e36842793a7c -hda disk0.qcow2 -machine type=pc,accel=kvm,usb=off -serial telnet:0.0.0.0:2445,server,nowait -nographic -nodefconfig -nodefaults -rtc base=utc,driftfix=slew -global kvm-pit.lost_tick_policy=discard -no-hpet -realtime mlock=off -boot order=c


