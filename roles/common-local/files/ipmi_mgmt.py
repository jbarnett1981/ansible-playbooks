#!/usr/bin/env python

'''
Created `01/06/2016 03:06`

@author jbarnett@tableau.com
@version 0.1

ipmi_mgmt.py:

Library to control and configure settings of any IPMI standard enabled device

changelog:

0.1
---
First draft. Currently only support setting bootdev to network and powering on system.
'''
import argparse
import pyghmi
import os
import sys
from socket import gaierror
from pyghmi.ipmi import command

def get_args():
    '''
    Supports the command-line arguments listed below.
    '''
    parser = argparse.ArgumentParser(description='Process for setting bootdev and power state of remote BMC')

    credentials_parser = parser.add_argument_group('required login arguments')
    credentials_parser.add_argument('--username', required=True, help='username to authenticate to Remote BMC controller')
    credentials_parser.add_argument('--password', required=True, help='password to authenticate to Remote BMC controller')

    parser.add_argument('--bmc', required=True, help='IP or DNS of remote BMC to connect to')
    parser.add_argument('--bootdev', choices=['network', 'hd', 'safe', 'optical', 'setup', 'default'], default='default', help='Set bootdev for BMC controller')
    parser.add_argument('--power', choices=['on', 'off', 'shutdown', 'reset', 'boot'], help='Set power state for BMC controller')

    args = vars(parser.parse_args())

    if (args['bootdev'] == 'default' and not args['power']):
        parser.error('Must specify --bootdev and/or --power')

    return args

def set_bootdev(ipmicmd, option, persist=False):
    '''
    Set bootdev option for BMC
    '''
    result = ipmicmd.set_bootdev(option, persist)
    return result['bootdev']

def set_power(ipmicmd, option, wait=True):
    '''
    Set power state for BMC
    '''
    result = ipmicmd.set_power(option, wait)
    while True:
        status = ipmicmd.get_power()
        if status.items()[0][0] == 'powerstate':
            return status['powerstate']

def main():
    '''
    Main function
    '''
    args = get_args()

    if args['bootdev'] and args['power']:
        if args['power'] in ['on', 'reset', 'boot']:
            powerstate = 'on'
        else:
            powerstate = 'off'
        try:
            ipmicmd = command.Command(bmc=args['bmc'], userid=args['username'], password=args['password'])
        except gaierror:
            sys.exit('Unable to resolve provided BMC name')
        except pyghmi.exceptions.IpmiException:
            sys.exit('Invalid username or password')
        bootdev = set_bootdev(ipmicmd, args['bootdev'])
        power = set_power(ipmicmd, args['power'])
        if not (bootdev == args['bootdev'] and power == powerstate):
            sys.exit('There was an error configuring the BMC. Please check connection and try again')
        else:
            print('BMC configured successfully')
            sys.exit()

if __name__ == "__main__":
    main()