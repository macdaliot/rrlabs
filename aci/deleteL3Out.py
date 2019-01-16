#!/usr/bin/env python3
"""
    This script delete a L3Out.

    Examples:
    # ./deleteL3Out.py -n FW1:dmz -t Prod
"""

import getopt
import logging
import sys
import yaml
from functions import deleteL3OutNodeProfile
from functions import getL3Outs
from functions import getL3OutNodeProfiles
from functions import login


def usage():
    print("Usage: {} [OPTIONS]".format(sys.argv[0]))
    print("  -v         Be verbose and enable debug")
    print("  -n STRING  name (i.e. FW1:dmz)")
    print("  -t STRING  tenant")
    print("  -f         force (delete without asking)")
    sys.exit(1)


def main():
    debug = False
    force = False
    tenant = None
    name = None

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
            "invalid config.yaml file: missing apic_ip, apic_username, apic_password or domain_l3"
        )

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vfn:t:")
    except getopt.GetoptError as err:
        logger.error("exception while parsing options", exc_info=debug)
        usage()
    for opt, arg in opts:
        if opt == "-v":
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == "-n":
            name = arg
        elif opt == "-t":
            tenant = arg
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
    if not tenant:
        logger.error("tenant not specified")
        sys.exit(1)
    l3out_name = f"L3OUT_{tenant}"

    # Login
    token, cookies = login(
        username=apic_username, password=apic_password, ip=apic_ip
    )
    if not token or not cookies:
        logging.error("authentication failed")
        sys.exit(1)

    # Checking if L3Out exists
    total, l3outs = getL3Outs(
        ip=apic_ip,
        token=token,
        cookies=cookies,
        tenant=tenant,
        name=l3out_name,
    )
    if total is 0:
        logging.error(f"L3Out {l3out_name} not found")
        sys.exit(1)

    # Checking if Node Profile exists
    total, l3outs_nodes = getL3OutNodeProfiles(
        ip=apic_ip,
        token=token,
        cookies=cookies,
        tenant=tenant,
        l3out=l3out_name,
        name=name,
    )
    if total is 0:
        logging.error(f"L3Out profile {name} not found")
        sys.exit(1)

    # Deleting node profile
    if not force:
        confirm = input(  # nosec
            f"Deleting L3Out node profile {name}. Continue? [no|yes]"
        )
        if confirm != "yes":
            print("Aborting...")
            sys.exit(0)
    if not deleteL3OutNodeProfile(
        ip=apic_ip,
        token=token,
        cookies=cookies,
        name=name,
        l3out=l3out_name,
        tenant=tenant,
    ):
        logging.error("failed to delete L3Out node profile")
        sys.exit(1)

    # Checking if L3Out is empty
    total, l3outs_nodes = getL3OutNodeProfiles(
        ip=apic_ip,
        token=token,
        cookies=cookies,
        tenant=tenant,
        l3out=l3out_name,
    )
    print(total)
    if total is 0:
        logging.error(
            f"L3OUT {l3out_name} is empty, traffic is blackholed for L3 Bridge Domains"
        )


if __name__ == "__main__":
    main()
    sys.exit(0)
