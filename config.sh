#!/bin/bash

VAR_FILE="/root/vars.txt"

VARS=$(egrep "^[A-Z0-9_]+=" ${VAR_FILE} | cut -d'=' -f1)

# Load all vars
. ${VAR_FILE}

find /usr/src/rrlabs/linux -type f | while read line; do
	echo "Processing ${line}..."
	TEMPLATE="${line}"
	CONFIG=$(echo ${TEMPLATE} | sed 's/^\/usr\/src\/rrlabs\/linux//g')

	mv -f ${CONFIG} ${CONFIG}.bak
	cp -a ${TEMPLATE} ${CONFIG}

	for VAR in ${VARS}; do
		sed -i "s/%${VAR}%/${!VAR}/" ${CONFIG}
	done
done

