#!/bin/bash
# /usr/local/sbin/update_dnsmasq.sh

DNSMASQ_IP=$(egrep -e "^dhcp-range=[0-9a-f:]+, [0-9a-f:]+, 64, " /etc/dnsmasq.conf | cut -d'=' -f2 | cut -d ',' -f1)
CURRENT_IP=$(ip -f inet6 addr show dev eth1 | grep global | sed 's/^.*inet6 \([0-9a-f:]\+\)\/64.*/\1/g')

if [ "${DNSMASQ_IP}" != "${CURRENT_IP}000" ]; then
	logger -p daemon.info -t SCRIPT "Updating dnsmasq.conf IPv6 DHCP range"
	sed -i "s/dhcp-range=[0-9a-f:]\+, [0-9a-f:]\+, 64, .*$/dhcp-range=${CURRENT_IP}000, ${CURRENT_IP}fff, 64, 168h/g" /etc/dnsmasq.conf
	if [ $? -ne 0 ]; then
		logger -p daemon.error -t SCRIPT "Failed to update dnsmasq.conf IPv6 DHCP range"
		exit 1
	fi

	systemctl reload dnsmasq
	if [ $? -ne 0 ]; then
		logger -p daemon.error -t SCRIPT "Failed to reload dnsmasq.conf"
		exit 1
	fi
fi

