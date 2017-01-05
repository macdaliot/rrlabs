FROM eveng/i386:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

# Build IOL base image with: docker build -t eveng/iol:latest -f base-iol.dockerfile .

COPY  node_init /sbin/node_init

#COPY start_node.sh /sbin
#COPY iol_wrapper.py /sbin/wrapper.py
#COPY functions.py /usr/lib/python3.4/functions.py

