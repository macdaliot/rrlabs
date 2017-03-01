#!/bin/bash

CONNS=10000
TIMEOUT=2

SERVER=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $1 2> /dev/null)
if [ $? -ne 0 ]; then
	SERVER=$1
fi

echo "Requests;Replies;Errors;Rate"
for i in 200 250 300 350 400 450 500 550 600 650 700 750 800 850 900 950 1000; do
	ERRORS=$(httperf --server ${SERVER} --port 80 --uri=/test.php --num-conns ${CONNS} --rate ${i} --timeout ${TIMEOUT} 2> /dev/null | grep "Errors: total" | sed 's/^Errors: total \([0-9]*\) .*$/\1/g')
	echo "${CONNS};$((${CONNS} - ${ERRORS}));${ERRORS};$i"
	sleep 10
done
