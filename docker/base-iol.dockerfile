FROM eveng/i386:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

# Build IOL base image with: docker build -t eveng/iol:latest -f base-iol.dockerfile .

COPY  node_init /sbin/node_init

