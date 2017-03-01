FROM alpine:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>
# Build with:
#   docker build -t rrlabs/webserver:latest -f webserver.dockerfile .
# Run with:
#   docker run -d -ti --name webserver1 rrlabs/webserver

# Installing dependencies
RUN apk update || exit 1
RUN apk add apache2 apache2-utils bash php7-apache2 || exit 1

# Configuring
RUN mkdir /run/apache2 || exit 1
COPY test.php /var/www/localhost/htdocs
COPY limits.conf /etc/apache2/conf.d
COPY node_init /sbin

CMD /sbin/node_init
