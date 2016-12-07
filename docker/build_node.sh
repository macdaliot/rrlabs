#!/bin/bash

R="\033[0;31m"
Y="\033[1;33m"
G="\033[0;32m"
U="\033[0m"

IMAGE=$(basename $1)
SOURCE=$(dirname $1)
TMP="$(mktemp -dt eveimage_tmp.XXXXXXXXXX)"
LOG="/tmp/eveimage_build.log"
DOCKER="docker -H=tcp://127.0.0.1:4243"
QEMUIMG="/opt/qemu/bin/qemu-img"

function clean {
	rm -rf ${TMP} node
}

trap clean EXIT

if [ "$1" == "" ]; then
	echo -e "${R}Input file not specified.${U}"
	exit 1
fi

if [ ! -f "${SOURCE}/${IMAGE}" ]; then
	echo -e "${R}Input file (${SOURCE}/${IMAGE}) does not exist.${U}"
	exit 1
fi

rm -rf node &>> ${LOG} && mkdir -p node/{image,config} &>> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}Cannot create directory (node).${U}"
	exit 1
fi

case "${IMAGE}" in
	*.bin)
		TYPE="iol"
		DISKS=""
		NAME="iol:$(echo ${IMAGE} | sed 's/\.bin$//')"
		if [ ! -f "${SOURCE}/iourc" ]; then
			echo -e "${R}IOL license (${SOURCE}/iourc) not found.${U}"
			exit 1
		fi
		echo -e "Input file is IOL:"
		echo -e " - image: ${SOURCE}/${IMAGE}"
		echo -e " - license: ${SOURCE}/iourc"
		echo -e " - type: ${TYPE}"
		echo -e " - name: ${NAME}"
		cp "${SOURCE}/${IMAGE}" node/image/iol.bin &>> ${LOG}
		if [ $? -ne 0 ]; then
			echo -e "${R}Failed to copy IOL image.${U}"
		fi
		cp "${SOURCE}/iourc" node/image/iourc &>> ${LOG}
		if [ $? -ne 0 ]; then
			echo -e "${R}Failed to copy IOL license${U}"
		fi
		;;
	iosxrv*.ova)
		TYPE="xrv"
		DISKS="iosxrv-demo.vmdk"
		NAME="xrv:$(echo ${IMAGE} | sed 's/^.*-\([0-9.]*\)\..*$/\1/g')"
		tar -vxf ${SOURCE}/${IMAGE} -C ${TMP} iosxrv-demo.vmdk &>> ${LOG}
		if [ $? -ne 0 ]; then
			echo -e "${R}Failed to uncompress image.${U}"
		fi
		echo -e "Input file is XRv:"
		echo -e " - image: ${SOURCE}/${IMAGE}"
		echo -e " - type: ${TYPE}"
		echo -e " - name: ${NAME}"
		;;
	vios-*)
		TYPE="vios"
		DISKS="${IMAGE}"
		NAME="vios:$(echo ${IMAGE} | sed 's/vios-//; s/\.vmdk//')"
		cp -a ${SOURCE}/${IMAGE} ${TMP} &>> ${LOG}
		if [ $? -ne 0 ]; then
			echo -e "${R}Failed to copy image.${U}"
		fi
		echo -e "Input file is XRv:"
		echo -e " - image: ${SOURCE}/${IMAGE}"
		echo -e " - type: ${TYPE}"
		echo -e " - name: ${NAME}"
		;;
	vios_l2-*)
		TYPE="viosl2"
		DISKS="${IMAGE}"
		NAME="viosl2:$(echo ${IMAGE} | sed 's/vios_l2-//; s/\.vmdk//')"
		cp -a ${SOURCE}/${IMAGE} ${TMP} &>> ${LOG}
		if [ $? -ne 0 ]; then
			echo -e "${R}Failed to copy image.${U}"
		fi
		echo -e "Input file is XRv:"
		echo -e " - image: ${SOURCE}/${IMAGE}"
		echo -e " - type: ${TYPE}"
		echo -e " - name: ${NAME}"
		;;
	*)
		echo -e "${R}Input file (${SOURCE}/${IMAGE}) is not supported.${U}"
		exit 1
		;;
esac

echo -ne "Building environment... "
echo "TYPE=${TYPE}" > node/image/ENV 2> /dev/null
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
	exit 1
fi
find node -type f -exec chmod 644 {} \; &>> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
	exit 1
fi
find node -type f -exec chown root:root {} \; &>> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
	exit 1
fi
find node -type f -name "*.bin" -exec chmod 755 {} \; &>> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
	exit 1
fi

echo -e "${G}done${U}"

echo -ne "Converting disks... "
COUNT=0
for DISK in ${DISKS}; do
	${QEMUIMG} convert -f vmdk -O qcow2 ${TMP}/${DISK} node/image/disk${COUNT}.qcow2 &>> ${LOG}
	if [ $? -ne 0 ]; then
		echo -e "${R}failed${U}"
		exit 1
	fi
	COUNT=$((${COUNT} + 1))
done
echo -e "${G}done${U}"

echo -ne "Building Docker image... "
${DOCKER} build -t eveng/${NAME} -f eveng-${TYPE}.dockerfile . &>> ${LOG}
if [ $? -ne 0 ]; then
	echo -e "${R}failed${U}"
	exit 1
fi
echo -e "${G}done${U}"

rm -f ${LOG}
exit 0

