#!/bin/bash

THRESHOLD=120
LASTCHANGE=$(date +%s)
BEFOREREMOVE=15
LOADBALANCER="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' loadbalancer)"

echo "Requests;Webservers"

while true; do
	CURRENT=$(curl -s http://${LOADBALANCER}/nginx_status | tail -n1 | cut -d' ' -f4)
	WEBSERVERS=$(docker ps | grep webserver | wc -l)
	echo "${CURRENT};${WEBSERVERS}"
	if [ "${CURRENT}" -gt "$((${WEBSERVERS}*${THRESHOLD}))" ]; then
		NAME="webserver$((${WEBSERVERS}+1))"
		docker run -d --name ${NAME} rrlabs/webserver &> /dev/null
		IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${NAME})"
		docker exec loadbalancer bash -c "echo 'server ${IP};' > /etc/nginx/servers/${IP}.conf" &> /dev/null
		sleep 0.5
		docker exec loadbalancer nginx -s reload &> /dev/null
		LASTCHANGE=$(date +%s)
	elif [[ "${CURRENT}" -lt "$((${WEBSERVERS}*${THRESHOLD}))" ]] && [[ "${WEBSERVERS}" -gt 2 ]] && [[ "$(date +%s)" -gt "$((${LASTCHANGE}+${BEFOREREMOVE}))" ]]; then
		NAME="webserver${WEBSERVERS}"
		IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${NAME})"
		docker exec loadbalancer rm -f /etc/nginx/servers/${IP}.conf &> /dev/null
		docker exec loadbalancer nginx -s reload &> /dev/null
		sleep 0.5
		docker kill ${NAME} &> /dev/null
		docker rm ${NAME} &> /dev/null
		LASTCHANGE=$(date +%s)
	fi
	sleep 1
done

