#!/usr/bin/python3
# Copyright 2022 pvarkoly@cephalix.eu

import configparser
import json
import subpocess
import sys

printer = {}
printer = json.loads(sys.stdin.read())

#Remove printer from cups
subprocess.run(['/usr/sbin/lpadmin','-x',printer['name']])

#Remove printer from samba
config = configparser.ConfigParser(delimiters=('='))
config.read('/etc/samba/smb.conf')
if printer['name'] in config:
    config.remove_section(printer['name'])
    with open('/etc/samba/smb.conf','wt') as f:
        config.write(f)
