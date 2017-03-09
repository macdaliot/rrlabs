FROM alpine:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>
LABEL author = "Andrea Dainese <andrea.dainese@gmail.com>"
LABEL copyright = "Andrea Dainese <andrea.dainese@gmail.com>"
LABEL description = "The API and controller module"
LABEL license = "https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode"
LABEL version = "20170309"

LABEL build = "docker build -t dainok/controller:latest -f controller.dockerfile ."
LABEL usage.0 = "docker volume create --name controller_data"
LABEL usage.1 = "docker run -ti --rm --name controller --volume controller_data:/data --name controller_data dainok/controller /bin/bash"

#ENTRYPOINT /sbin/rc
EXPOSE :80 :443 :5005

# Installing dependencies
RUN apk update || exit 1
RUN apk add bash mariadb mariadb-client nginx openssh python3 || exit 1

# Configuring
#COPY bootstrap.py /sbin/bootstrap.py

# Cleaning
RUN find /var/cache/apk/ -type f -delete || exit 1

