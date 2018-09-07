This are my Ansible playbooks to setup a home device from scratch. Instead of documenting step by step, I find Ansible playbooks self-explanatory documents.

Two files are needed:

 - hosts: the Ansible inventory
 - secrets.yaml: the data used by the playbook

 ## The "hosts" file

The `hosts` file is a simple Ansible inventory file, like the following:

~~~
[pi_gateway]
devicename ansible_host=192.168.2.1 ansible_user=root ansible_unprivuser=pi ansible_password=raspberry
~~~

Mind that `devicename` will be used as hostname of the configured device. Also mind that playbooks will configure SSH to allow `root` login via public key authentication. The `ansible_password` will be used only for the first login, assuming the `ansible_unprivuser` has privileges to became root via sudo.

To setup a new Raspberry PI, just login with user `pi` and password `raspberry`, then enable SSH:

~~~
$ sudo systemctl start ssh
$ logout
~~~

The `pi` will be removed at the end.

## The "secrets.yaml" file

The `secrets.yaml` file defines how a device must be configured. Currently the following files and roles are defined:

- `secrets-gateway.yaml` for the `playbook-gateway.yaml` playbook (including roles: `raspbian`, `debian`, `customization`, `gateway`, `netdata`, `websever`)

### The "secrets-gateway.yaml" file

This is an example of the setting for the `secrets-gateway.yaml` file:

~~~
---
root:
  # use mkpasswd --method=sha-512
  password: password
  hash: hashOfThePasswordGeneratedByTheCommandAbove
networks:
  internal:
    network: 192.168.2.0/24
    ip: 192.168.2.1
    netmask: 255.255.255.0
    interface: eth0
    domain: mydomain.local
    dhcprange: 192.168.2.10,192.168.2.254
    hosts:
      - hostname: mypc
        ip: 192.168.2.70
        mac: 00:01:02:03:04:05
  external:
    network: 192.168.1.0/24
    ip: 192.168.1.100
    netmask: 255.255.255.0
    gateway: 192.168.1.1
    interface: eth1
    domain: mydomain.it.cx
ddns:
  afraid:
    server: freedns.afraid.org
    username: username
    password: password
    domain: mydomain.it.cx
  opendns:
    server: updates.opendns.com
    username: example@example.com
    password: password
    domain: Home
~~~

## The roles

The following roles has been defined:

- `raspbian`: connects to a new installed Raspberry PI with Raspbian, enable SSH and allow `root` authentication via public key.
- `debian`: upgrade the whole OS setting hostname and other basic configurations.
- `customization`: set some environment I personally use (Bash, VIM, ...).
- `gateway`: configure the device with dual network interfaces, enabling the firewall and setting IPv6 tunnel to be used with TIM broadband.
- `netdata`: install NetData to monitor the device.
- `webserver`: install Apache and configure it to be secure.
