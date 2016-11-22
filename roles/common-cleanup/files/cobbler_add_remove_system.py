#!/usr/bin/env python

'''
Created `01/06/2016 09:00`

@author jbarnett@tableau.com
@version 0.1

cobbler_add_remove_system.py:

Adds and removes systems to cobbler and assigns them appropriate kickstart/preseed profile.

changelog:

0.1
---
First draft
'''

import xmlrpclib
import argparse
import sys

def get_args():
    '''
    Supports the command-line arguments listed below.
    '''
    parser = argparse.ArgumentParser(description='Process for adding or removing systems to/from Cobbler')
    subparsers = parser.add_subparsers(help='commands')

    credentials_parser = parser.add_argument_group('required login arguments')
    credentials_parser.add_argument('--username', required=True, help='username to authenticate to Cobbler')
    credentials_parser.add_argument('--password', required=True, help='password to authenticate to Cobbler')
    credentials_parser.add_argument('--apiurl', required=True, help='API URL to authenticate to Cobbler')

    show_parser = subparsers.add_parser('show', help='show command. Prints to stdout')
    show_parser.set_defaults(which='show')
    show_parser.add_argument('-p', '--profiles', action="store_true", help='show cobbler profiles')
    show_parser.add_argument('-d', '--distros', action="store_true", help='show cobbler distros')
    show_parser.add_argument('-i', '--images', action="store_true", help='show cobbler images')
    show_parser.add_argument('-r', '--repos', action="store_true", help='show cobbler repos')
    show_parser.add_argument('-s', '--systems', action="store_true", help='show cobbler systems')

    add_parser = subparsers.add_parser('add', help='add command. Prints to stdout')
    add_parser.set_defaults(which='add')
    add_parser.add_argument('-s', '--system', required=True, action="store_true", help='add system to cobbler')
    add_parser.add_argument('-n', '--name', required=True, help='specify system hostname')
    add_parser.add_argument('-m', '--macaddress', required=True, help='specify system MAC address')
    add_parser.add_argument('-p', '--profile', required=True, help='specify profile to assign to system')
    add_parser.add_argument('-k', '--ksmeta', required=False, help='specify kickstart metadata')

    remove_parser = subparsers.add_parser('remove', help='remove command. Prints to stdout')
    remove_parser.set_defaults(which='remove')
    remove_parser.add_argument('-s', '--system', required=True, action="store_true", help='remove system from cobbler')
    remove_parser.add_argument('-n', '--name', required=True, help='specify system hostname to remove')

    args = vars(parser.parse_args())

    return args

def server_add(server, token, hostname, macaddress, profile, ksmeta=None):
    '''
    Add server to cobbler
    '''
    try:
        system_id = server.new_system(token)
        server.modify_system(system_id,"name", hostname, token)
        server.modify_system(system_id,"hostname", "", token)
        server.modify_system(system_id,'modify_interface', {
                "macaddress-eth0"   : macaddress,
        }, token)
        server.modify_system(system_id,"profile", profile, token)
        server.modify_system(system_id,"ks_meta", ksmeta, token)
        server.save_system(system_id, token)
        server.sync(token)
    except xmlrpclib.Fault as e:
        if 'invalid profile name' in e.faultString:
            sys.exit("Adding system failed. Invalid profile name. Please try again.")


def server_delete(server, token, hostname):
    '''
    Remove server from cobbler
    '''
    try:
        server.remove_system(hostname, token)
        server.sync(token)
    except xmlrpclib.Fault as e:
        pass

def main():
    '''
    Main function
    '''
    args = get_args()

    # global vars
    COBBLER_API_URL = args['apiurl']
    COBBLER_USER = args['username']
    COBBLER_PASS = args['password']
    COMMAND_ARGS=['show', 'add', 'remove']
    SHOW_ARGS = ['profiles', 'distros', 'images', 'repos', 'systems']

    if args['which'] in COMMAND_ARGS:
        try:
            server = xmlrpclib.Server(COBBLER_API_URL, allow_none=True)
            token = server.login(COBBLER_USER,COBBLER_PASS)
        except xmlrpclib.Fault as e:
            if 'login failed' in e.faultString:
                sys.exit("Login Failed. Please check credentials and try again.")

        if args['which'] == 'show':
            for i in args:
                if args[i] == True:
                    command = getattr(server, "get_" + i)
            data = command()
            for i in data:
                print(i['name'])

        elif args['which'] == 'add':

            server_add(server, token, args['name'], args['macaddress'], args['profile'], args['ksmeta'])

        elif args['which'] == 'remove':
            server_delete(server, token, args['name'])

    sys.exit()

if __name__ == "__main__":
    main()