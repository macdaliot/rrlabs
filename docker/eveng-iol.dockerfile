FROM eveng/iol:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

# Adding images
COPY node /opt
COPY start_node.sh /sbin

