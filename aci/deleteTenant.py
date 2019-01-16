#!/usr/bin/env python3
"""
    This script delete a tenant.

    Examples:
    # ./deleteTenant.py -t Tenant
"""

import getopt
import logging
import sys
import yaml
from functions import deleteTenant
from functions import login


def usage():
    print("Usage: {} [OPTIONS]".format(sys.argv[0]))
    print("  -v         Be verbose and enable debug")
    print("  -f         force (delete without asking)")
    print("  -t STRING  Tenant Name")
    sys.exit(1)


def main():
    debug = False
    name = None
    force = False

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
        opts, args = getopt.getopt(sys.argv[1:], "vft:")
    except getopt.GetoptError as err:
        logger.error("exception while parsing options", exc_info=debug)
        usage()
    for opt, arg in opts:
        if opt == "-v":
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == "-f":
            force = True
        elif opt == "-t":
            name = arg
        else:
            logger.error("unhandled option ({})".format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not name:
        logger.error("name not specified")
        sys.exit(1)

    # Login
    token, cookies = login(
        username=apic_username, password=apic_password, ip=apic_ip
    )
    if not token or not cookies:
        logging.error("authentication failed")
        sys.exit(1)

    if not force:
        confirm = input(f"Deleting tenant {name}. Continue? [no|yes]")  # nosec
        if confirm != "yes":
            print("Aborting...")
            sys.exit(0)

    if not deleteTenant(ip=apic_ip, token=token, cookies=cookies, name=name):
        logging.error(f"failed to delete tenant {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
