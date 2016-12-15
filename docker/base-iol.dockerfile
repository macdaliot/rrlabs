FROM eveng/i386:latest
MAINTAINER Andrea Dainese <andrea.dainese@gmail.com>

# Build with: docker build -t eveng/iol:latest -f base-iol.dockerfile .

#RUN tdnf -y install openssl &> /dev/null || exit 1
#RUN ln -s /usr/lib/libcrypto.so.1.0.2 /usr/lib/libcrypto.so.4 &> /dev/null || exit 1

# Cleaning
#WORKDIR "/root/"
#RUN tdnf clean all &> /dev/null || exit 1
#RUN history -c &> /dev/null || exit 1
