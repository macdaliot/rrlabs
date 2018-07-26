# Ansible Playbook for EVE-NG

This playbook validates an Ubuntu 16.04 installation, installs EVE-NG and all related files/images.

## Prerequisites

sudo apt-get -y install openssh-server python
sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo systemctl reload sshd
sudo usermod -p $(echo eve | openssl passwd -1 -stdin) root
