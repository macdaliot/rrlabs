FROM eveng/qemu:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

COPY node /root
COPY start_node.sh /root

