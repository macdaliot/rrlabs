#!/usr/bin/env python3
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://www.gnu.org/licenses/gpl.html'
__revision__ = '20170329'

import pysnmp, re, sys
from pysnmp.hlapi import *
from functions import *

# Default variables
sysName = '.1.3.6.1.2.1.1.5.0'
cdpCacheDeviceId = '.1.3.6.1.4.1.9.9.23.1.2.1.1.6'
cdpCacheDevicePort = '.1.3.6.1.4.1.9.9.23.1.2.1.1.7'
cdpCachePlatform = '.1.3.6.1.4.1.9.9.23.1.2.1.1.8'
ifDescr = '.1.3.6.1.2.1.2.2.1.2'
vtpVlanName = '.1.3.6.1.4.1.9.9.46.1.3.1.1.4.1'

def getFacts(host, SNMPAuth):
    output = {}
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                SNMPAuth,
                UdpTransportTarget((host, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(sysName)),
                lookupMib = False,
                lexicographicMode = False
            )
        )
        if errorIndication or errorStatus or errorIndex:
            logger.debug('error quering SNMP host "{}" for sysName'.format(host))
            return {}
    except Exception as err:
        logger.debug('cannot query SNMP host "{}" for sysName'.format(host), exc_info = False)
        return {}

    output =  {
        'uptime': None,
        'vendor': None,
        'os_version': None,
        'serial_number': None,
        'model': None,
        'hostname': str(varBinds[0][1]).split('.')[0],
        'fqdn': str(varBinds[0][1]),
        'interface_list': []
    }
    return output

def getInterfaces(host, SNMPAuth):
    interfaces = {}
    try:
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            SNMPAuth,
            UdpTransportTarget((host, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(ifDescr)),
            lookupMib = False,
            lexicographicMode = False
        ):
            if errorIndication or errorStatus or errorIndex:
                logger.debug('error quering SNMP host "{}" for ifDescr'.format(host))
                return {}
            interfaces[int(str(varBinds[0][0]).split('.')[-1])] = str(varBinds[0][1])
    except Exception as err:
        logger.debug('cannot query SNMP host "{}" for ifDescr'.format(host), exc_info = False)
        return {}

    return interfaces

def getCDPNeighbors(host, SNMPAuth, local_interfaces):
    neighbors = {}
    local_port = {}
    try:
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            SNMPAuth,
            UdpTransportTarget((host, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(cdpCacheDeviceId)),
            ObjectType(ObjectIdentity(cdpCacheDevicePort)),
            ObjectType(ObjectIdentity(cdpCachePlatform)),
            lookupMib = False,
            lexicographicMode = False
        ):
            if errorIndication or errorStatus or errorIndex:
                logger.debug('error quering SNMP host "{}" for CDP data'.format(host))
                return {}
            neighbor_id = int(str(varBinds[0][0]).split('.')[-2])
            neighbors.setdefault(local_interfaces[neighbor_id], [])
            neighbors[local_interfaces[neighbor_id]].append({
                'remote_system_name': re.findall(r'([^(\n]+).*', str(varBinds[0][1]))[0],
                'remote_port': str(varBinds[1][1]),
                'remote_port_description': str(varBinds[1][1]),
                'remote_system_description': str(varBinds[2][1])
            })
    except Exception as err:
        logger.debug('cannot query SNMP host "{}" for CDP data'.format(host), exc_info = False)
        return {}

    return neighbors

def getVLANs(host, SNMPAuth):
    vlans = {}
    try:
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            SNMPAuth,
            UdpTransportTarget((host, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(vtpVlanName)),
            lookupMib = False,
            lexicographicMode = False
        ):
            if errorIndication or errorStatus or errorIndex:
                logger.debug('error quering SNMP host "{}" for vtpVlanName'.format(host))
                return {}
            vlans[int(str(varBinds[0][0]).split('.')[-1])] = str(varBinds[0][1])
    except Exception as err:
        logger.debug('cannot query SNMP host "{}" for vtpVlanName'.format(host), exc_info = False)
        return {}

    return vlans

def main():
    # Reading options
    hosts, working_dir = checkOpts()

    # Discover each host
    for host in hosts:
        device_info = {}
        snmp_version = host.vars['snmp_version'] if 'snmp_version' in host.vars else None
        snmp_community = host.vars['snmp_community'] if 'snmp_community' in host.vars else None
        snmp_auth = host.vars['snmp_auth'] if 'snmp_auth' in host.vars else None
        snmp_username = host.vars['snmp_username'] if 'snmp_username' in host.vars else None
        snmp_password = host.vars['snmp_password'] if 'snmp_password' in host.vars else None
        snmp_priv = host.vars['snmp_priv'] if 'snmp_priv' in host.vars else None
        snmp_privpassword = host.vars['snmp_privpassword'] if 'snmp_privpassword' in host.vars else None

        if not snmp_version:
            logging.warning('skipping host "{}" because snmp_version is not set'.format(host.vars['ansible_host']))

        if snmp_version == '2c':
            try:
                SNMPAuth = CommunityData(host.vars['snmp_community'])
            except Exception as err:
                logging.warning('skipping host "{}" because snmp_community is not set'.format(host.vars['ansible_host'], host.vars['snmp_community']), exc_info = False)
                continue
        elif str(snmp_version) == '3':
            if not snmp_auth:
                auth_protocol = usmNoAuthProtocol
            elif snmp_auth == 'sha' and snmp_username and snmp_password:
                auth_protocol = usmHMACSHAAuthProtocol
            elif snmp_auth == 'md5' and snmp_username and snmp_password:
                auth_protocol = usmHMACMD5AuthProtocol
            else:
                logging.warning('skipping host "{}" because snmp_auth, snmp_username or snmp_password are not set/not valid'.format(host.vars['ansible_host']))
                continue
            if not snmp_priv:
                priv_protocol = usmNoPrivProtocol
            elif snmp_priv == 'des' and snmp_privpassword:
                priv_protocol = usmDESPrivProtocol
            elif snmp_priv == '3des' and snmp_privpassword:
                priv_protocol = usm3DESEDEPrivProtocol
            elif snmp_priv == 'aes128' and snmp_privpassword:
                priv_protocol = usmAesCfb128Protocol
            elif snmp_priv == 'aes192' and snmp_privpassword:
                priv_protocol = usmAesCfb192Protocol
            elif snmp_priv == 'aes256' and snmp_privpassword:
                priv_protocol = usmAesCfb256Protocol
            else:
                logging.warning('skipping host "{}" because snmp_priv or snmp_privpassword are not set/not valid'.format(host.vars['ansible_host']))
                continue

            if snmp_auth and snmp_priv:
                SNMPAuth = UsmUserData(snmp_username, snmp_password, authProtocol = auth_protocol, privProtocol = priv_protocol)
            elif snmp_auth:
                SNMPAuth = UsmUserData(snmp_username, snmp_password, authProtocol = auth_protocol)
            else:
                logging.warning('skipping host "{}" because snmp_priv requires snmp_auth'.format(host.vars['ansible_host']))
                continue
        else:
            logging.warning('skipping host "{}" because snmp_version "{}" is not supported'.format(host.vars['ansible_host'], host.vars['snmp_version']))
            continue

        logger.debug('connecting to "{}"'.format(host.vars['ansible_host']))
        facts = getFacts(host.vars['ansible_host'], SNMPAuth)
        local_interfaces = getInterfaces(host.vars['ansible_host'], SNMPAuth)
        cdp_neighbors = getCDPNeighbors(host.vars['ansible_host'], SNMPAuth, local_interfaces)
        vlans = getVLANs(host.vars['ansible_host'], SNMPAuth)

        if facts and local_interfaces:
            device_info['facts'] = facts
            for interface_id, interface_name in local_interfaces.items():
                if interface_name not in ignore_snmp_interfaces:
                    device_info['facts']['interface_list'].append(interface_name)
        else:
            logger.error('skipping not respondig host "{}"'.format(host.vars['ansible_host']))
            continue
        if cdp_neighbors:
            device_info['cdp_neighbors'] = cdp_neighbors
        if vlans:
            device_info['vlans'] = vlans

        writeDeviceInfo(device_info, '{}/{}'.format(working_dir, device_info['facts']['hostname'].lower()))

if __name__ == "__main__":
    main()
    sys.exit(0)
