# Ansible Playbook for EVE-NG

This playbook validates an Ubuntu 16.04 installation, installs EVE-NG and all related files/images.

## Prerequisites

By default Ubuntu server does not come up with SSH and root user is not allowed to login. Prepare the system with the following commands:

~~~
sudo apt-get -y install openssh-server python
sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo systemctl reload sshd
sudo usermod -p $(echo eve | openssl passwd -1 -stdin) root
~~~

Python is also required for Ansible.

## Images and license

Of course images and licenses are not included. Create the following directories:

- images
- images/iol
- images/dynamips
- images/qemu

Check the following example:

~~~
images/iol/iourc
images/iol/L2-ADVENTERPRISEK9-M-15.2-IRON-20151103.bin
images/iol/L3-ADVIPSERVICES-M-15.1-2.9S.bin
images/iol/L3-ADVENTERPRISEK9-M-15.4-2T.bin
images/iol/L3-ADVENTERPRISEK9-M-15.2-M5.3.bin
images/iol/L2-ADVENTERPRISEK9-M-15.2-20150703.bin
images/iol/L3-ADVENTERPRISEK9-M-15.4-1T.bin
images/iol/L3-ADVENTERPRISEK9-M-15.5-2T.bin
images/iol/L2-ADVIPSERVICESK9-M-15.2-IRON-20151103.bin
images/iol/L3-ADVENTERPRISEK9-M-15.2-S7.bin
images/dynamips/c7200-adventerprisek9-mz.153-3.XB12.image
images/dynamips/c1710-bk9no3r2sy-mz.124-23.image
images/dynamips/c3725-adventerprisek9-mz.124-15.T14.image
images/dynamips/c7200-adventerprisek9-mz.152-4.S7.image
images/dynamips/c7200-spservicesk9-mz.152-4.S7.image
images/qemu/vios-15.6.3/virtioa.qcow2
images/qemu/titanium-7.3.0.1/virtioa.qcow2
images/qemu/csr1000vng-16.6.1/virtioa.qcow2
images/qemu/xrv-6.1.3/hda.qcow2
images/qemu/csr1000v-universalk9-15.4-3S/hda.qcow2
images/qemu/viosl2-15.2/virtioa.qcow2
images/qemu/asav-961/virtioa.qcow2
images/qemu/nxosv9k-7.0.3.I7.1/sataa.qcow2
~~~
