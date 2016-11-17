#!/bin/bash

R="\033[0;31m"
Y="\033[1;33m"
G="\033[0;32m"
U="\033[0m"

IMAGE=$1
TMP="$(mktemp -dt eveimage_tmp.XXXXXXXXXX)"
LOG="/tmp/eveimage_build.log"
QEMU="/opt/qemu/bin/qemu-img"

function clean {
	rm -rf ${TMP} node
}

trap clean EXIT

if [ "${IMAGE}" == "" ]; then
	echo -e "${R}Input file not specified.${U}"
	exit 1
fi

if [ ! -f "${IMAGE}" ]; then
	echo -e "${R}Input file (${IMAGE}) does not exist.${U}"
	exit 1
fi

rm -rf node &> ${LOG} && mkdir -p node &> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}Cannot create directory (node).${U}"
	exit 1
fi

case "${IMAGE}" in
	iosxrv*.ova)
		TYPE="xrv"
		DISKS="iosxrv-demo.vmdk"
		NAME="xrv:$(echo ${IMAGE} | sed 's/^.*-\([0-9.]*\)\..*$/\1/g')"
		echo -e "Input file is XRv:"
		tar -vxf ${IMAGE} -C ${TMP} iosxrv-demo.vmdk &> ${LOG}
		echo -e " - image: ${IMAGE}"
		echo -e " - type: ${TYPE}"
		echo -e " - name: ${NAME}"
		;;
	*)
		echo -e "${R}Input file (${IMAGE}) is not supported.${U}"
		exit 1
		;;
esac

echo -ne "Building environment... "
echo "TYPE=${TYPE}" > node/ENV 2> /dev/null
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
fi
echo -e "${G}done${U}"

echo -ne "Converting disks... "
COUNT=0
for DISK in ${DISKS}; do
	${QEMU} convert -f vmdk -O qcow2 ${TMP}/${DISK} node/disk${COUNT}.qcow2 &> ${LOG}
	if [ $? -ne 0 ]; then
		echo -e "${R}failed${U}"
		exit 1
	fi
	COUNT=$((${COUNT} + 1))
done
echo -e "${G}done${U}"

echo -ne "Building Docker image... "
docker -H=tcp://127.0.0.1:4243 build -t eveng/${NAME} -f eve-xrv.dockerfile . &> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
	exit 1
fi
echo -e "${G}done${U}"

rm -f ${LOG}
exit 0

