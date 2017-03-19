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
RUN apk add bash mariadb mariadb-client memcached nginx openssh python3 || exit 1
RUN pip3 install --upgrade pip || exit 1
RUN pip3 install Flask-SQLAlchemy python3-memcached || exit 1

# Configuring
COPY api.py /usr/bin
COPY api_modules.py /usr/lib/python3.5/
#COPY bootstrap.py /sbin/bootstrap.py

# Cleaning
RUN find /var/cache/apk/ -type f -delete || exit 1

