#!/bin/bash

LIST=$(cat apparati.txt | sed 's/#.*//g' | sed 's/[^\.;a-z0-9]//g' | grep -v ^$)
OUTPUT="apparati.csv"
. /home/andrea/scan.conf
export MIBDIRS=/home/andrea/.snmp/mibs

echo "Hostname;IP;Model;Description;Physical ID;Serial Number;OS Version" > ${OUTPUT}

for DEV in ${LIST}; do
	IP=$(echo ${DEV} | cut -d ";" -f 1)
	TEMPLATE=$(echo ${DEV} | cut -d ";" -f 2)

	case "${TEMPLATE}" in
		"ciscostack")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			snmptable -mALL -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -Cf ';' ${IP} 1.3.6.1.2.1.47.1.1.1 | egrep ";chassis;" | cut -d ";" -f 1,6,8,10,12 | while read LINE; do
				DESCRIPTION=$(echo $LINE | cut -d ';' -f 1)
				SWITCHID=$(echo $LINE | cut -d ';' -f 2)
				OSVERSION=$(echo $LINE | cut -d ';' -f 3)
				SERIAL=$(echo $LINE | cut -d ';' -f 4)
				MODEL=$(echo $LINE | cut -d ';' -f 5)
				echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
			done
		;;
		"ciscovss")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			snmptable -mALL -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -Cf ';' ${IP} 1.3.6.1.2.1.47.1.1.1 | egrep ";module;" | cut -d ";" -f 1,6,8,10,12 | while read LINE; do
				DESCRIPTION=$(echo $LINE | cut -d ';' -f 1)
				SWITCHID=$(echo $LINE | cut -d ';' -f 2)
				OSVERSION=$(echo $LINE | cut -d ';' -f 3)
				SERIAL=$(echo $LINE | cut -d ';' -f 4)
				MODEL=$(echo $LINE | cut -d ';' -f 5)
				echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
			done
		;;
		"cisconexus")
			HOSTNAME=$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')
			OSVERSION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.1 | sed -n 's/.*, Version \([^,]*\), .*/\1/g')"
			snmptable -mALL -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -Cf ';' ${IP} 1.3.6.1.2.1.47.1.1.1 | egrep ";chassis;" | cut -d ";" -f 1,6,8,10,12 | while read LINE; do
				DESCRIPTION=$(echo $LINE | cut -d ';' -f 1)
				SWITCHID=
				SERIAL=$(echo $LINE | cut -d ';' -f 4)
				MODEL=$(echo $LINE | cut -d ';' -f 5)
				cat ${OUTPUT} | grep ${SERIAL} > /dev/null 2>&1
				if [ $? -ne 0 ]; then
					# Serial does not exists (avoid duplicated dual homed FEX)
					echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
				fi
			done
		;;
		"ciscomds")
			HOSTNAME=$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')
			OSVERSION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.1 | sed -n 's/.*, Version \([^,]*\), .*/\1/g')"
			snmptable -mALL -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -Cf ';' ${IP} 1.3.6.1.2.1.47.1.1.1 | egrep ";chassis;" | cut -d ";" -f 1,6,8,10,12 | while read LINE; do
				DESCRIPTION=$(echo $LINE | cut -d ';' -f 1)
				SWITCHID=
				SERIAL=$(echo $LINE | cut -d ';' -f 4)
				MODEL=$(echo $LINE | cut -d ';' -f 5)
				cat ${OUTPUT} | grep ${SERIAL} > /dev/null 2>&1
				if [ $? -ne 0 ]; then
					# Serial does not exists (avoid duplicated dual homed FEX)
					echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
				fi
			done
		;;
		"citrixns")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			DESCRIPTION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.5951.6.2.2 | sed 's/^.*: "\(.*\)"$/\1/g')"
			SWITCHID=
			OSVERSION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.5951.6.2.3 | sed 's/^.*: "\(.*\)"$/\1/g')"
			SERIAL="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.5951.6.2.16 | sed 's/^.*: "\(.*\)"$/\1/g')"
			MODEL="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.5951.6.2.1 | sed 's/^.*: "\(.*\)"$/\1/g')"
			echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
		;;
		"ciscoisr")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			OSVERSION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.1 | sed -n '1h;1!H;${g;s/.*, Version \([^,]*\), .*/\1/p}')"
			snmptable -mALL -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -Cf ';' ${IP} 1.3.6.1.2.1.47.1.1.1 | egrep ";chassis;" | cut -d ";" -f 1,6,8,10,12 | while read LINE; do
				DESCRIPTION=$(echo $LINE | cut -d ';' -f 1)
				SWITCHID=
				SERIAL=$(echo $LINE | cut -d ';' -f 4)
				MODEL=$(echo $LINE | cut -d ';' -f 5)
				echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
			done
		;;
		"infoblox")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			OSVERSION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.7779.3.1.1.2.1.7 | sed 's/^.*: "\(.*\)"$/\1/g')"
			DESCRIPTION="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.1 | sed 's/^.*: "\(.*\)"$/\1/g')"
			SWITCHID=
			SERIAL="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.7779.3.1.1.2.1.6 | sed 's/^.*: "\(.*\)"$/\1/g')"
			MODEL="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.7779.3.1.1.2.1.4 | sed 's/^.*: "\(.*\)"$/\1/g')"
			echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
		;;
		"ciscowlc")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			snmptable -mALL -v3 -l authNoPriv -a SHA -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -Cf ';' ${IP} 1.3.6.1.2.1.47.1.1.1 | egrep ";Chassis;|;Cisco AP;" | cut -d ";" -f 1,9,10,12 | while read LINE; do
				DESCRIPTION=$(echo $LINE | cut -d ';' -f 1)
				SWITCHID=
				OSVERSION=$(echo $LINE | cut -d ';' -f 2)
				SERIAL=$(echo $LINE | cut -d ';' -f 3)
				MODEL=$(echo $LINE | cut -d ';' -f 4)
				echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
			done
		;;
		"cpfirewall")
			HOSTNAME="$(snmpwalk -v3 -l authNoPriv -a MD5 -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.2.1.1.5 | sed 's/^.*: "\(.*\)"$/\1/g')"
			DESCRIPTION="$(snmpwalk -v3 -l authNoPriv -a MD5 -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.2620.1.1.21 | sed 's/^.*: "\(.*\)"$/\1/g')"
			SWITCHID=
			OSVERSION="$(snmpwalk -v3 -l authNoPriv -a MD5 -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.2620.1.6.5.1 | sed 's/^.*: "\(.*\)"$/\1/g') $(snmpwalk -v3 -l authNoPriv -a MD5 -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.2620.1.6.4.1 | sed 's/^.*: "\(.*\)"$/\1/g')"
			SERIAL="$(snmpwalk -v3 -l authNoPriv -a MD5 -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.2620.1.6.16.3 | sed 's/^.*: "\(.*\)"$/\1/g')"
			MODEL="$(snmpwalk -v3 -l authNoPriv -a MD5 -A ${SNMPV3PASSWORD} -u ${SNMPV3USER} -O v ${IP} 1.3.6.1.4.1.2620.1.6.16.7 | sed 's/^.*: "\(.*\)"$/\1/g')"
			echo "${HOSTNAME};${IP};${MODEL};${DESCRIPTION};${SWITCHID};${SERIAL};${OSVERSION}" >> ${OUTPUT}
		;;
		*)
			echo "Invalid template ${TEMPLATE}"
			exit 1
		;;
	esac
done
