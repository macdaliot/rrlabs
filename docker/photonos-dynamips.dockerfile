FROM vmware/photon:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

# Build with: docker build -t eveng/dynamips:latest -f photonos-dynamips.dockerfile .

# Installing dependencies
RUN tdnf -y install autoconf automake binutils bridge-utils diffutils gawk gcc git glib-devel glibc-devel gzip iproute2 iptables libtool linux-api-headers make ncurses-devel sed tar util-linux-devel zlib-devel &> /dev/null || exit 1
RUN mkdir /usr/src/ || exit 1

# Installing Dynamips
WORKDIR "/usr/src/"
RUN git clone https://github.com/GNS3/dynamips || exit 1
WORKDIR "/usr/src/dynamips/"

RUN exit 1


# Installing QEMU
#RUN curl -s http://wiki.qemu-project.org/download/qemu-2.7.0.tar.bz2 | tar -xj -C /usr/src || exit 1
#WORKDIR "/usr/src/qemu-2.7.0/"
#RUN ./configure --prefix=/usr/local --target-list="x86_64-softmmu" --enable-vnc --disable-xen --enable-curses --enable-kvm --audio-drv-list="oss" --enable-uuid &> /dev/null || exit 1
#RUN make &> /dev/null || exit 1
#RUN make install &> /dev/null || exit 1

# Cleaning
WORKDIR "/root/"
RUN rm -rf /usr/src/ &> /dev/null || exit 1
RUN tdnf -y erase autoconf automake gcc gdbm git glibc-devel glib-devel libgcc-devel libgomp-devel libstdc++-devel linux-api-headers m4 make ncurses-devel pcre-devel perl python2 python2-libs util-linux-devel zlib-devel &> /dev/null || exit 1
RUN tdnf clean all &> /dev/null || exit 1
RUN history -c &> /dev/null || exit 1
