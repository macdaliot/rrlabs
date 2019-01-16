#!/usr/bin/env python3
"""
    This script adds a set of basic policies.

    Examples:
    # ./addPolicies.py
"""

import getopt
import logging
import sys
import yaml
from functions import addPolicies
from functions import login


def usage():
    print("Usage: {} [OPTIONS]".format(sys.argv[0]))
    print("  -v         Be verbose and enable debug")
    sys.exit(1)


def main():
    debug = False

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
        aep_l2 = config["aep_l2"]
    except Exception as err:
        logger.error(
            "invalid config.yaml file: missing apic_ip, apic_username, apic_password or aep_l2"
        )

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "v")
    except getopt.GetoptError as err:
        logger.error("exception while parsing options", exc_info=debug)
        usage()
    for opt, arg in opts:
        if opt == "-v":
            debug = True
            logger.setLevel(logging.DEBUG)
        else:
            logger.error("unhandled option ({})".format(opt))
            usage()

    # Login
    token, cookies = login(
        username=apic_username, password=apic_password, ip=apic_ip
    )
    if not token or not cookies:
        logging.error("authentication failed")
        sys.exit(1)

    if not addPolicies(ip=apic_ip, token=token, cookies=cookies, aep=aep_l2):
        logging.error("failed to add common policies")
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
