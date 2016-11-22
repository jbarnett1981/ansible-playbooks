#!/usr/bin/env python

"""
Cobbler external inventory script
=================================
modified by: Julian Barnett 06/06/16
"""

import argparse
import ConfigParser
import os
import re
from time import time
import xmlrpclib

try:
    import json
except ImportError:
    import simplejson as json

from six import iteritems

# NOTE -- this file assumes Ansible is being accessed FROM the cobbler
# server, so it does not attempt to login with a username and password.
# this will be addressed in a future version of this script.

orderby_keyname = 'owners'  # alternatively 'mgmt_classes'


class CobblerInventory(object):

    def __init__(self):

        """ Main execution path """
        self.conn = None

        self.inventory = dict()  # A list of groups and the hosts in that group
        self.inventory['cobbler'] = []
        self.cache = dict()  # Details about hosts in the inventory

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.update_cache()
        elif not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_inventory_from_cache()
            self.load_cache_from_cache()

        data_to_print = ""

        # Data to print
        if self.args.host:
            data_to_print += self.get_host_info()
        else:
            self.inventory['_meta'] = { 'hostvars': {} }
            for hostname in self.cache:
                self.inventory['_meta']['hostvars'][hostname] = self.cache[hostname]
            data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def _connect(self):
        if not self.conn:
            self.conn = xmlrpclib.Server(self.cobbler_host, allow_none=True)
            self.token = None
            if self.cobbler_username is not None:
                self.token = self.conn.login(self.cobbler_username, self.cobbler_password)

    def is_cache_valid(self):
        """ Determines if the cache files have expired, or if it is still valid """

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_inventory):
                    return True

        return False

    def read_settings(self):
        """ Reads the settings from the cobbler.ini file """

        config = ConfigParser.SafeConfigParser()
        config.read('/tmp/cobbler.ini')

        self.cobbler_host = config.get('cobbler', 'host')
        self.cobbler_username = None
        self.cobbler_password = None
        if config.has_option('cobbler', 'username'):
            self.cobbler_username = config.get('cobbler', 'username')
        if config.has_option('cobbler', 'password'):
            self.cobbler_password = config.get('cobbler', 'password')

        # Cache related
        cache_path = config.get('cobbler', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-cobbler.cache"
        self.cache_path_inventory = cache_path + "/ansible-cobbler.index"
        self.cache_max_age = config.getint('cobbler', 'cache_max_age')

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Cobbler')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to cobbler (default: False - use cache files)')
        self.args = parser.parse_args()

    def update_cache(self):
        """ Make calls to cobbler and save the output in a cache """

        self._connect()
        self.groups = dict()
        self.hosts = dict()
        if self.token is not None:
            data = self.conn.get_systems(self.token)
        else:
            data = self.conn.get_systems()
        for host in data:
            # Get the hostname and it to the cobbler group
            hostname = host['name'] #None
            ksmeta = None
            interfaces = host['interfaces']

            status = host['status']
            profile = host['profile']
            classes = host[orderby_keyname]

            # if status not in self.inventory:
            #     self.inventory[status] = []
            # self.inventory[status].append(dns_name)
            # print(self.inventory)

            # if profile not in self.inventory:
            #     self.inventory[profile] = []
            # self.inventory[profile].append(dns_name)

            # for cls in classes:
            #     if cls not in self.inventory:
            #         self.inventory[cls] = []
            #     self.inventory[cls].append(dns_name)
            if hostname not in self.inventory['cobbler']:
                self.inventory['cobbler'].append(hostname)

            # Since we already have all of the data for the host, update the host details as well

            # The old way was ksmeta only -- provide backwards compatibility

            self.cache[hostname] = host
            if "ks_meta" in host:
                for key, value in iteritems(host["ks_meta"]):
                    self.cache[hostname][key] = value

        self.write_to_cache(self.cache, self.cache_path_cache)
        self.write_to_cache(self.inventory, self.cache_path_inventory)

    def get_host_info(self):
        """ Get variables about a specific host """

        if not self.cache or len(self.cache) == 0:
            # Need to load index from cache
            self.load_cache_from_cache()

        if not self.args.host in self.cache:
            # try updating the cache
            self.update_cache()

            if not self.args.host in self.cache:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        return self.json_format_dict(self.cache[self.args.host], True)

    def push(self, my_dict, key, element):
        """ Pushed an element onto an array that may not have been defined in the dict """

        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def load_inventory_from_cache(self):
        """ Reads the index from the cache file sets self.index """

        cache = open(self.cache_path_inventory, 'r')
        json_inventory = cache.read()
        self.inventory = json.loads(json_inventory)

    def load_cache_from_cache(self):
        """ Reads the cache from the cache file sets self.cache """

        cache = open(self.cache_path_cache, 'r')
        json_cache = cache.read()
        self.cache = json.loads(json_cache)

    def write_to_cache(self, data, filename):
        """ Writes data in JSON format to a file """
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """ Converts 'bad' characters in a string to underscores so they can be used as Ansible groups """

        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

CobblerInventory()