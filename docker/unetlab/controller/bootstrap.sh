#!/bin/bash

shutdown() {
	echo "Shutting down..."
	ps -ef
	killall -s SIGTERM mysqld memcached &> /data/logs/shutdown.log
}

trap shutdown SIGTERM SIGHUP

if [ ! -d /data/logs ]; then
	mkdir /data/logs || exit 1
fi

# Starting MariaDB
if [ ! -d /data/database/mysql ]; then
	/usr/bin/mysql_install_db --datadir="/data/database" --user="mysql" &> /data/logs/mysql_install_db.log
	if [ $? -ne 0 ]; then
		echo "ERROR: failed to initialize MariaDB"
		cat /data/logs/mysql_install_db.log
		exit 1
	fi
fi
/usr/bin/mysqld_safe --datadir="/data/database" --nowatch &> /data/logs/mysqld_safe.log
if [ $? -ne 0 ]; then
	echo "ERROR: failed to start MariaDB"
	cat /data/logs/mysqld_safe.log
	exit 1
fi

# Starting Memcached
/usr/bin/memcached -m 64 -p 11211 -u memcached -l 127.0.0.1 &> /data/logs/memcached.log
if [ $? -ne 0 ]; then
	echo "ERROR: failed to start Memcached"
	cat /data/logs/memcached.log
	exit 1
fi

echo "Controller started"

while true; do
	sleep 10000
done
