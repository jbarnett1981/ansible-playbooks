#!/bin/bash

# London is 10.242.0.0/18. Therefore first 3 octets should be between 10.242.0 - 10.242.63 inclusive. If not, host is not in London

# get default NIC
NIC=$(ip route ls | grep default | awk '{print $5}')

# get default NIC IP
IP=$(ip addr show dev $NIC | grep -Po 'inet \K[\d.]+')

# get 2nd octet
BASE2=$(echo $IP | cut -d"." -f2)

# get 3rd octet
BASE3=$(echo $IP | cut -d"." -f3)

if [ "$BASE2" -eq 242 ] && [ "$BASE3" -ge 0 -a "$BASE3" -le 63 ]; then
   ADSITE="TSI-EMEADataCenter"
else
   ADSITE="TSI-NADataCenter"
fi

echo $ADSITE