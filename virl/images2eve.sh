#!/bin/bash

usage() {
	echo "Copy $0 to the VIRL server and execute it from the \"virl\" user:"
	echo "	-p root password of EVE server"
	echo "	-i IP of the EVE server"
	exit 1
}

if [ "$(whoami)" != "virl" ]; then
	usage
fi

which glance &> /dev/null
if [ $? -ne 0 ]; then
	echo "glance not found"
	exit 1
fi
which sshpass &> /dev/null
if [ $? -ne 0 ]; then
	echo "sshpass not found"
	exit 1
fi

password=""
ip=""
while getopts ":p:i:" OPT; do
	case "${OPT}" in
		p)
			password=${OPTARG}
			;;
		i)
			ip=${OPTARG}
			;;
		*)
			usage
			;;
	esac
done

if [ "${password}" == "" ]; then
	usage
fi
if [ "${ip}" == "" ]; then
	usage
fi

echo sshpass -p "${password}" ssh -oStrictHostKeyChecking=no root@${ip} ls / &> /dev/null
if [ $? -ne 0 ]; then
	echo "root password of remote server is not correct"
	exit 1
fi

for image in $(glance image-list | tail -n +4 | head -n -1 | cut -d'|' -f2 | sed 's/ //g'); do
	name=$(glance image-show ${image} | grep name | cut -d'|' -f3 | sed 's/^ *//g' | sed 's/ *$//g')
	release=$(glance image-show ${image} | grep release | cut -d'|' -f3 | sed 's/^ *//g' | sed 's/ *$//g')
	case $name in
		"NX-OSv 9000")
			type=nxosv9k
			file=sataa.qcow2
			;;
		"NX-OSv")
			type=titanium
			file=virtioa.qcow2
			;;
		"IOSvL2")
			type=viosl2
			file=virtioa.qcow2
			;;
		"IOSv")
			type=vios
			file=virtioa.qcow2
			;;
		"IOS XRv 9000")
			type=xrv9k
			file=virtioa.qcow2
			;;
		"IOS XRv")
			type=xrv
			file=hda.qcow2
			;;
		"CSR1000v")
			type=csr1000v
			file=virtioa.qcow2
			;;
		"ASAv")
			type=asav
			file=virtioa.qcow2
			;;
		*)
			echo "image \"${name}\" (${image}) not supported"
			continue
			;;
	esac
	if [ ! -f /var/lib/glance/images/${image} ]; then
		echo "image \"${name}\" (${image}) not found in /var/lib/glance/images/"
		continue
	fi

	sshpass -p "${password}" ssh -oStrictHostKeyChecking=no root@${ip} ls /opt/unetlab/addons/qemu/${type}-${release} &> /dev/null
	if [ $? -eq 0 ]; then
		echo "image \"${name}\" (${image}) already exists on remote server"
		continue
	fi

	sshpass -p "${password}" ssh -oStrictHostKeyChecking=no root@${ip} mkdir -p /opt/unetlab/addons/qemu/${type}-${release} $> /dev/null
	if [ $? -ne 0 ]; then
		echo "cannot create directory \"/opt/unetlab/addons/qemu/${type}-${release}\""
		exit 1
	fi

	echo "copying /var/lib/glance/images/$image to root@${ip}:/opt/unetlab/addons/qemu/${type}-${release}/${file}..."
	sudo sshpass -p "${password}" scp -oStrictHostKeyChecking=no /var/lib/glance/images/${image} root@${ip}:/opt/unetlab/addons/qemu/${type}-${release}/${file}
	if [ $? -ne 0 ]; then
		echo "cannot copy file to \"/opt/unetlab/addons/qemu/${type}-${release}\""
		exit 1
	fi
done
