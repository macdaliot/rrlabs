#!/usr/bin/env python3
"""
    This script configure one port to be used from a single-homed device or from
    a multi-homed device with active-standby links. Then a VLAN must be
    associated with the EPG using the addVLANToEPG.py script.

    Examples:
    # ./addSinglePort.py -v -n ESXi03:mgmt -T server -i 1/15 -f -l Leaf101
"""

import getopt
import logging
import sys
import yaml
from functions import addInterfaceProfile
from functions import getInterfaceProfiles
from functions import addInterfaceSelector
from functions import addInterfaceSelectorBlock
from functions import bindSwitchProfileToInterfaceProfile
from functions import getInterfaceSelectors
from functions import getInterfaceSelectorBlocks
from functions import getInterfacePolicyGroups
from functions import getSwitchProfiles
from functions import getSwitchProfilesFromInterfaceProfile
from functions import login


def usage():
    print("Usage: {} [OPTIONS]".format(sys.argv[0]))
    print("  -v         Be verbose and enable debug")
    print("  -n STRING  Interface Profile Name (i.e. ESXi03:mgmt)")
    print("  -d STRING  Interface Profile Description (optional)")
    print("  -T STRING  device|server|switch")
    print("  -i STRING  Interface Name (i.e. 1/15)")
    print("  -l STRING  Switch Profile (i.e. Leaf101)")
    print("  -f         Force: if interface profile exists then overwrite it")
    sys.exit(1)


def main():
    debug = False
    force = False
    name = None
    group = None
    description = None
    leaf = None
    device_type = None
    interface = None

    # Configure logging
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    # Reading config.yaml file
    with open("config.yaml", "r") as f:
        try:
            config = yaml.safe_load(f)
        except Exception as err:
            logger.error(
                "exception while reading config.yaml file", exc_info=debug
            )
    try:
        apic_ip = config["apic_ip"]
        apic_username = config["apic_username"]
        apic_password = config["apic_password"]
    except Exception as err:
        logger.error(
            "invalid config.yaml file: missing apic_ip, apic_username or apic_password"
        )

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vfn:d:T:i:l:")
    except getopt.GetoptError as err:
        logger.error("exception while parsing options", exc_info=debug)
        usage()
    for opt, arg in opts:
        if opt == "-v":
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == "-n":
            name = arg
        elif opt == "-T":
            device_type = arg
        elif opt == "-d":
            description = arg
        elif opt == "-l":
            leaf = arg
        elif opt == "-i":
            interface = arg
        elif opt == "-f":
            force = True
        else:
            logger.error("unhandled option ({})".format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not name:
        logger.error("name not specified")
        sys.exit(1)
    if not leaf:
        logger.error("leaf not specified")
        sys.exit(1)
    if not device_type or device_type not in ["switch", "device", "server"]:
        logger.error("device_type not specified or not valid")
        sys.exit(1)
    if not interface:
        logger.error("interface not specified")
        sys.exit(1)
    if device_type == "server":
        group = "SinglePort_Server"
    elif device_type == "device":
        group = "SinglePort_Device"
    elif device_type == "switch":
        group = "SinglePort_Switch"
    else:
        logger.error("device_type not valid")
        sys.exit(1)

    # Setting description
    if description:
        profile_description = description
    else:
        profile_description = f"Single ports connected to {name}"

    # Login
    token, cookies = login(
        username=apic_username, password=apic_password, ip=apic_ip
    )
    if not token or not cookies:
        logging.error("authentication failed")
        sys.exit(1)

    # Checking if interface policy group exists
    total, interface_policy_groups = getInterfacePolicyGroups(
        ip=apic_ip,
        token=token,
        cookies=cookies,
        name=group,
        class_name="infraAccPortGrp",
    )
    if total is 0:
        logging.error(f"interface policy group {group} does not exist")
        sys.exit(1)

    # Checking if switch profile exists
    total, switch_profiles = getSwitchProfiles(
        ip=apic_ip, token=token, cookies=cookies, name=leaf
    )
    if total is 0:
        logging.error(f"switch profile {leaf} does not exist")
        sys.exit(1)

    # Checking if interface profile exists
    total, interface_profiles = getInterfaceProfiles(
        ip=apic_ip, token=token, cookies=cookies, name=name
    )
    if total is 0 or force:
        # Adding interface profile
        if not addInterfaceProfile(
            ip=apic_ip,
            token=token,
            cookies=cookies,
            name=name,
            description=profile_description,
        ):
            logging.error(f"failed to create interface profile {name}")
            sys.exit(1)

    # Checking how many switch profiles are connected to the interface profile
    total, switch_profiles = getSwitchProfilesFromInterfaceProfile(
        ip=apic_ip, token=token, cookies=cookies, name=name
    )
    if total > 1:
        logging.error(
            f"interface profile {name} is bound to multiple switch profiles"
        )
    elif total == 1:
        connected_leaf = switch_profiles[0]["infraRtAccPortP"]["attributes"][
            "tDn"
        ].split("/")[-1][6:]
        if leaf != connected_leaf:
            logging.error(
                f"interface profile {name} is bound to a different switch profile {connected_leaf}"
            )
            sys.exit(1)
    else:
        # Binding interface profile with the switch profile
        if not bindSwitchProfileToInterfaceProfile(
            ip=apic_ip,
            token=token,
            cookies=cookies,
            name=leaf,
            interface_profile=name,
        ):
            logging.error(
                f"failed to bind switch profile {leaf} to interface profile {name}"
            )
            sys.exit(1)

    # Checking if interface selector exists
    total, interface_selectors = getInterfaceSelectors(
        ip=apic_ip, token=token, cookies=cookies, profile=name, name="ports"
    )
    if total is 0 or force:
        # Adding interface selector associated to the policy group
        if not addInterfaceSelector(
            ip=apic_ip,
            token=token,
            cookies=cookies,
            profile=name,
            name="ports",
            group=group,
            class_name="infraAccPortGrp",
        ):
            logging.error(f"failed to create interface selector {name}")
            sys.exit(1)

    # Checking if interface selector block exists
    total, interface_selector_blocks = getInterfaceSelectorBlocks(
        ip=apic_ip,
        token=token,
        cookies=cookies,
        profile=name,
        selector="ports",
        name=interface,
    )
    if total is 0:
        # Adding interface selector block
        if not addInterfaceSelectorBlock(
            ip=apic_ip,
            token=token,
            cookies=cookies,
            profile=name,
            selector="ports",
            name=interface,
            description=name,
        ):
            logging.error(
                f"failed to create interface selector block with {interface}"
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
