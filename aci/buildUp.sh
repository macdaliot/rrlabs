#!/bin/bash

# echo -n "Adding base policies... "
# ./addPolicies.py
# if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
#
# cat build_FEXs.csv | tail -n+2 | grep -v "^$" | while read line; do
#   LEAF=$(echo $line | cut -d, -f1)
#   FEXID=$(echo $line | cut -d, -f2)
#   PORT1=$(echo $line | cut -d, -f3)
#   PORT2=$(echo $line | cut -d, -f4)
#   echo -n "Adding FEX ${FEXID} to ${LEAF}... "
#   ./addFex.py -i "${FEXID}" -l "${LEAF}" -p "${PORT1}" -p "${PORT2}"
#   if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
# done
#
# cat build_vpcs.csv | tail -n+2 | grep -v "^$" | while read line; do
#   IFPROFILE=$(echo $line | cut -d, -f1)
#   PROTOCOL=$(echo $line | cut -d, -f2)
#   NAME=$(echo $line | cut -d, -f3)
#   LEAF=$(echo $line | cut -d, -f4)
#   PORT=$(echo $line | cut -d, -f5)
#   echo -n "Adding vPC ${NAME}... "
#   ./addPortChannel.py -t vpc -T "${IFPROFILE}" -a "${PROTOCOL}" -n "${NAME}" -l "${LEAF}" -p "${PORT}"
#   if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
# done
#
# cat build_single_ports.csv | tail -n+2 | grep -v "^$" | while read line; do
#   IFPROFILE=$(echo $line | cut -d, -f1)
#   NAME=$(echo $line | cut -d, -f2)
#   LEAF=$(echo $line | cut -d, -f3)
#   PORT=$(echo $line | cut -d, -f4)
#   echo -n "Adding single port ${NAME}... "
#   ./addSinglePort.py -n "${NAME}" -T "${IFPROFILE}" -i "${PORT}" -l "${LEAF}"
#   if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
# done
#
# cat build_fex_ports.csv | tail -n+2 | grep -v "^$" | while read line; do
#   IFPROFILE=$(echo $line | cut -d, -f1)
#   NAME=$(echo $line | cut -d, -f2)
#   LEAF=$(echo $line | cut -d, -f3)
#   PORT=$(echo $line | cut -d, -f4)
#   echo -n "Adding FEX port ${NAME}... "
#   ./addPortToFEX.py -F "${LEAF}" -n "${NAME}" -T "${IFPROFILE}" -p "${PORT}"
#   if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
# done

cat build_tenants.csv | tail -n+2 | grep -v "^$" | while read line; do
  TENANT=$(echo $line | cut -d, -f1)
  DESCRIPTION=$(echo $line | cut -d, -f2)
  echo -n "Adding tenant ${TENANT}... "
  ./addTenant.py -t "${TENANT}" -d "${DESCRIPTION}"
  if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
done

cat build_networks.csv | tail -n+2 | grep -v "^$" | while read line; do
  TENANT=$(echo $line | cut -d, -f1)
  NAME=$(echo $line | cut -d, -f2)
  VLAN=$(echo $line | cut -d, -f3)
  MAC=$(echo $line | cut -d, -f4)
  SUBNET=$(echo $line | cut -d, -f5)
  if [ "${MAC}" != "" ]; then
    MAC_OPT=" -m ${MAC}"
  else
    MAC_OPT=""
  fi
  if [ "${SUBNET}" != "" ]; then
    SUBNET_OPT=" -s ${SUBNET}"
  else
    SUBNET_OPT=""
  fi
  echo -n "Adding Bridge Domain ${NAME}... "
  ./addNetwork.py -t "${TENANT}" -n "${NAME}" -q "${VLAN}"${MAC_OPT}${SUBNET_OPT}
  if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
done

cat build_static3out.csv | tail -n+2 | grep -v "^$" | while read line; do
  TENANT=$(echo $line | cut -d, -f1)
  NAME=$(echo $line | cut -d, -f2)
  MODE=$(echo $line | cut -d, -f3)
  VLAN=$(echo $line | cut -d, -f4)
  VIP=$(echo $line | cut -d, -f5)
  LEAF1=$(echo $line | cut -d, -f6)
  LEAF1_IP=$(echo $line | cut -d, -f7)
  LEAF1_PORT=$(echo $line | cut -d, -f8)
  LEAF2=$(echo $line | cut -d, -f9)
  LEAF2_IP=$(echo $line | cut -d, -f10)
  LEAF2_PORT=$(echo $line | cut -d, -f11)
  echo -n "Adding L3Out ${NAME}... "
  ./addStaticL3Out.py -b -n "${NAME}" -t "${TENANT}" -m "${MODE}" -i "${VLAN}" -I "${VIP}" -l "${LEAF1},${LEAF1_IP},${LEAF1_PORT}" -l "${LEAF2},${LEAF2_IP},${LEAF2_PORT}"
  if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
done

cat build_ports2EPG.csv | tail -n+2 | grep -v "^$" | while read line; do
  TENANT=$(echo $line | cut -d, -f1)
  MODE=$(echo $line | cut -d, -f2)
  VLAN=$(echo $line | cut -d, -f3)
  IFTYPE=$(echo $line | cut -d, -f4)
  GROUP=$(echo $line | cut -d, -f5)
  LEAF=$(echo $line | cut -d, -f6)
  PORT=$(echo $line | cut -d, -f7)
  FEX=$(echo $line | cut -d, -f8)
  case $IFTYPE in
    vpc)
      echo -n "Adding VLAN ${VLAN} to ${GROUP}... "
      ./addPortToEpg.py -t "${TENANT}" -m "${MODE}" -i "${VLAN}" -a vpc -g "${GROUP}"
      if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
    ;;
    single)
      if [ "${FEX}" == "" ]; then
        echo -n "Adding VLAN ${VLAN} to ${LEAF}:${PORT}... "
        ./addPortToEpg.py -t "${TENANT}" -m "${MODE}" -i "${VLAN}" -a single -l "${LEAF}" -p "${PORT}"
        if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
      else
        echo -n "Adding VLAN ${VLAN} to ${LEAF}:Fex${FEX}:${PORT}... "
        ./addPortToEpg.py -t "${TENANT}" -m "${MODE}" -i "${VLAN}" -a single -l "${LEAF}" -p "${PORT}" -f "${FEX}"
        if [ $? -eq 0 ]; then echo "OK"; else echo "FAIL"; exit 1; fi
      fi
    ;;
    *)
      echo "Port type must be single or vpc"
      exit 1
    ;;
  esac
done
