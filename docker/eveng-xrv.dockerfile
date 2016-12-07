FROM eveng/qemu:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

COPY node /opt
COPY start_node.sh /sbin

