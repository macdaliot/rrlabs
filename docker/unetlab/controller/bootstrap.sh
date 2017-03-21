#!/bin/bash

shutdown() {
	echo -n "Shutting down... "
	killall -s SIGTERM mysqld memcached &> /data/logs/shutdown.log
}

echo -n "Starting controller... "

trap shutdown SIGTERM SIGHUP &> /dev/null

if [ ! -d /data/logs ]; then
	mkdir /data/logs || exit 1
fi

# Starting MariaDB
if [ ! -d /data/database/mysql ]; then
	/usr/bin/mysql_install_db --datadir="/data/database" --user="mysql" &> /data/logs/mariadb_install.log
	if [ $? -ne 0 ]; then
		echo "ERROR: failed to initialize MariaDB"
		cat /data/logs/mysql_install_db.log
		exit 1
	fi
fi
mkdir -p /run/mysqld &> /dev/null
/usr/bin/mysqld --basedir=/usr --datadir=/data/database --plugin-dir=/usr/lib/mysql/plugin --user=mysql --pid-file=/run/mysqld/mariadb.pid --socket=/run/mysqld/mysqld.sock --port=3306 &> /data/logs/mariadb.log &
MARIADB_PID=$!

# Starting Memcached
/usr/bin/memcached -m 64 -p 11211 -u memcached -l 127.0.0.1 &> /data/logs/memcached.log &
MEMCACHED_PID=$!

echo "done"

wait $MARIADB_PID $MEMCACHED_PID

echo "done"
