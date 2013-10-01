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

CONTROL_IFACE = 'eth0'
SETTINGS = 'settings'
HOSTS = 'vms'

parser = argparse.ArgumentParser(description='''Program for deployment some topology for test needing''')
parser.add_argument('configuration', help='Path to the configuration file with list of host or \'esxds\' type')
parser.add_argument('-v', '--verbose', action='store_false')
parser.add_argument('-c', '--count', default=2, type=int)
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
        return 1
    else:
        return hosts_list


def ping(host):
    if args.count <= 2:
        command = 'ping -c %s %s%s' % (args.count, host['address'], '' if not args.verbose else ' > /dev/null')
        host['is_available'] = False if os.system(command) else True
    else:
        command = ["/bin/ping", "-c %s" % args.count, host['address']]
        host['response'] = subprocess.Popen(command, stdout=subprocess.PIPE).stdout.readlines()
        host['is_available'] = bool(os.getenv('?'))


def ping_hosts(hosts_list):
    threads = [threading.Thread(target=ping, args=(host, )) for host in hosts_list.values()]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    return hosts_list


if args.configuration and os.path.exists(args.configuration):
    hosts = parse(args.configuration)
    print('Waiting for response...')
    hosts = ping_hosts(hosts)
    hosts_availability = False
    for name, data in hosts.items():
        if args.count <= 2:
            print("%s is%s available on %s" % (name, '' if data['is_available'] else ' NOT', data['address']))
        else:
            print(name.center(60, '-'))
            for ping_response in data['response']:
                print(ping_response.decode('UTF-8').replace('\n', ''))
        hosts_availability = data['is_available']
    exit(not hosts_availability)
else:
    print('Configuration not found on path: %s' % args.configuration)
    exit(1)

