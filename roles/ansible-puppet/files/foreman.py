#!/usr/bin/env python

'''
Created `05/26/2016 05:02`

@author jbarnett@tableau.com
@version 0.2

foreman.py:

Adds and removes systems to specified foreman/puppet hostgroup.

changelog:

0.2
---
Created Foreman class to manage functions and vars throughout REST API calls
'''
import os
import argparse
import sys
import time
import requests

def get_args():
    '''
    Supports the command-line arguments listed below.
    '''
    parser = argparse.ArgumentParser(description='Process for adding hosts to specific hostgroups in Foreman')

    credentials_parser = parser.add_argument_group('required login arguments')
    credentials_parser.add_argument('--username', required=True, help='username to authenticate to Foreman')
    credentials_parser.add_argument('--password', required=True, help='password to authenticate to Foreman')
    credentials_parser.add_argument('--apiurl', required=True, help='API URL to authenticate to Foreman')

    subparsers = parser.add_subparsers(help='commands')

    list_parser = subparsers.add_parser('list', help='list command. Prints to stdout')
    list_parser.set_defaults(which='list')
    list_parser.add_argument('groups', help='List Foreman hostgroups')

    add_parser = subparsers.add_parser('add', help='list command. Prints to stdout')
    add_parser.set_defaults(which='add')
    add_parser.add_argument('--hostname', required=True, help='hostname to modify')
    add_parser.add_argument('--hostgroup', required=True, help='Foreman hostgroup')

    args = vars(parser.parse_args())

    return args


class Foreman:
    def __init__(self, username, password, server):
        '''
        Connection class for Foreman API
        '''
        if not os.environ.has_key("REQUESTS_CA_BUNDLE"):
            sys.exit("REQUESTS_CA_BUNDLE environment not set. Please ensure this environment var is available and points to the path of the dev.tsi.lan cert file")
        self.username = username
        self.password = password
        self.server = server
        self.auth = (self.username, self.password)
        self.params = {'per_page':10000}

    def get_hostgroups(self):
        '''
        Function that returns all Foreman hostgroup names and ids
        '''
        api_suffix = '/hostgroups'
        url = self.server + api_suffix
        group_dict = {}

        # generate API call
        r = requests.get(url, params=self.params, auth=self.auth, verify=True)
        hostgroups = r.json()['results']
        for hostgroup in hostgroups:
            group_dict[hostgroup['title']] = hostgroup['id']
        return group_dict

    def get_host_id(self, hostname):
        '''
        Function that returns Foreman id from hostname string
        '''
        api_suffix = '/hosts?search=%s' % hostname
        url = self.server + api_suffix
        i = 1
        while i < 91:
            try:
                # generate API call
                r = requests.get(url, params=self.params, auth=self.auth, verify=True)
                hostid = r.json()['results'][0]['id']
                return hostid
            except IndexError:
                print("\nInvalid hostname. Please check hostname and try again (attempt # %s)" % i)
                time.sleep(10)
                i += 1

    def get_groupid(self, groupname):
        '''
        Function that returns Foreman id from hostgroup string
        '''
        hostgroups = self.get_hostgroups()
        try:
            return hostgroups[groupname]
        except KeyError:
            for item in hostgroups.items():
                if groupname == item[0].split('/')[-1]:
                    return item[1]

    def get_groupname(self, groupid):
        '''
        Function that returns Foreman name from hostgroup id
        '''
        hostgroups = self.get_hostgroups()
        for item in hostgroups.items():
            if int(groupid) == item[1]:
                groupname = item[0].split('/')[-1]
                return groupname

    def update_hostgroup(self, host, group):
        '''
        Function to update hostgroup (id) of a host (id)
        '''
        hostid = self.get_host_id(host)
        if hostid == None:
            sys.exit("Host not found")
        if not is_number(group):
            group = self.get_groupid(group)
        api_suffix = '/hosts/%s' % hostid
        url = self.server + api_suffix
        payload = {'host': {'hostgroup_id':str(group)}}
        # generate API call
        r = requests.put(url, auth=self.auth, verify=True, json=payload)
        if r.status_code == '200' and r.json()['hostgroup_id'] == group:
            return


def is_number(num):
    ''' Test if value can be converted to a number and if so return True '''
    try:
        int(num)
        return True
    except ValueError:
        return False

def main():
    '''
    Main function
    '''
    args = get_args()
    # from requests.auth import HTTPBasicAuth
    requests.packages.urllib3.disable_warnings()

    fapi = Foreman(args['username'], args['password'], args['apiurl'])

    if args['which'] == 'list' and args['groups']:
    # list hostgroups within Foreman
        hostgroups = fapi.get_hostgroups()

        print("\n{0:50}{1}".format("Hostgroup", "ID"))
        print("{0:50}{1}".format("---------", "--\n"))
        for groupname, groupid in hostgroups.items():
            print("{0:50}{1}".format(groupname,groupid))

    if args['which'] == 'add':
        # add specified host to specified hostgroup
        hostname = args['hostname']
        groupname = args['hostgroup']
        fapi.update_hostgroup(hostname, groupname)
        if is_number(groupname):
            groupname = fapi.get_groupname(groupname)
        print("Host successfully added to %s hostgroup" % groupname)

if __name__ == "__main__":
    main()
