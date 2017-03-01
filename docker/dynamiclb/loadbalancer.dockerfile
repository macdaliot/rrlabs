FROM alpine:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>
# Build with:
#   docker build -t rrlabs/loadbalancer:latest -f loadbalancer.dockerfile .
# Run with:
#   docker run -d -ti -e IP="1.2.3.4 5.6.7.8" --name loadbalancer rrlabs/loadbalancer

# Installing dependencies
RUN apk update || exit 1
RUN apk add bash nginx || exit 1

# Configuring
RUN mkdir /run/nginx || exit 1
RUN mkdir /etc/nginx/servers || exit 1
COPY nginx.conf /etc/nginx
COPY node_init /sbin

CMD /sbin/node_init
