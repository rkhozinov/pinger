#!/usr/bin/python
# coding=utf-8
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

try:
    import configparser
except:
    import ConfigParser as configparser
import os
import subprocess
import threading

DEFAULT_COUNT = 3
CONTROL_IFACE = 'eth0'
SETTINGS = 'settings'
HOSTS = 'vms'
LINE_WIDTH = 60

parser = argparse.ArgumentParser(description='''Program for deployment some topology for test needing''')
parser.add_argument('configuration', help='Path to the configuration file with list of host or \'esxds\' type')
parser.add_argument('-v', '--verbose', default=False)
parser.add_argument('-c', '--count', default=DEFAULT_COUNT, type=int)
args = parser.parse_args()


def convert(input, type):
    # todo: add existence validate
    # todo: add type validate
    pass


def parse(config_path):
    hosts_list = dict()
    config = configparser.RawConfigParser()
    try:
        if config.read(config_path):
            if config.has_section(SETTINGS) and config.has_option(SETTINGS, HOSTS):
                for hostname in [str.strip(x) for x in config.get(SETTINGS, HOSTS).split(',')]:
                    address = config.get(hostname, CONTROL_IFACE).split(',')[0].split('/')[0]
                    hosts_list[hostname] = dict(address=address)
        else:
            raise configparser.Error()
    except configparser.MissingSectionHeaderError:
        with open(config_path) as options:
            for option in options.readlines():
                name, address = option.split('=')
                hosts_list[name] = dict(address=address)
    except configparser.Error as error:
        print(error.message)
        exit(1)
    else:
        return hosts_list


def ping(host):
    command = ["/bin/ping", "-c %s" % args.count, host['address']]
    executor = subprocess.Popen(command, stdout=subprocess.PIPE)
    # Store response
    host['response'] = executor.stdout.readlines() if args.verbose else None
    executor.communicate()
    # Gets exit code
    host['is_available'] = bool(not executor.returncode)


def ping_hosts(hosts_list):
    threads = [threading.Thread(target=ping, args=(host, )) for host in hosts_list.values()]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    return hosts_list


if os.path.exists(args.configuration):
    hosts = parse(args.configuration)
    print('Waiting for response...')
    hosts = ping_hosts(hosts)
    hosts_available = list()

    for name, data in hosts.items():
        hosts_available.append(data['is_available'])
        if not args.verbose:
            print("%s is%s available on %s" %
                  (name, '' if data['is_available'] else ' NOT', data['address']))
        else:
            print(name.center(LINE_WIDTH, '-'))
            for ping_response in data['response']:
                print(ping_response.decode('UTF-8').replace('\n', ''))

    exit(0 if all(hosts_available) else 1)
else:
    print('Configuration not found on path: %s' % args.configuration)
    exit(1)