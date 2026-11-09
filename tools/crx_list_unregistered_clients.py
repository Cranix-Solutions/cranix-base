#!/usr/bin/python3
#
# Copyright (c) Peter Varkoly <peter@varkoly.de> Nuremberg, Germany.  All rights reserved.
#
# Lists the clients which got their IP address from a Kea DHCP pool but are not
# registered as a device in CRANIX. For every such client the IP address, the
# MAC address and the vendor name resolved from the MAC address is printed.
#

import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import time
from argparse import ArgumentParser
from urllib import request as urlrequest
from urllib import error as urlerror

KEA_CONFIG_FILE = "/etc/kea/kea-dhcp4.conf"
KEA_CTRL_SOCKET = "/run/kea/kea4-ctrl-socket"
OUI_FILES       = [ "/usr/share/hwdata/oui.txt", "/usr/share/hwdata/iab.txt" ]
OUI_URL         = "https://api.macvendors.com/"

_mac_regex = re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')

parser = ArgumentParser(description="List DHCP clients which are not registered as a CRANIX device.")
parser.add_argument("--csv",       action="store_true", help="Print the result as semicolon separated CSV.")
parser.add_argument("--json",      action="store_true", help="Print the result as JSON.")
parser.add_argument("--no-online", action="store_true", help="Do not query an online service for unknown MAC vendors.")
parser.add_argument("--oui-file",  action="append", default=[], help="Use this file as OUI database (can be given multiple times).")
args = parser.parse_args()

_oui_cache      = {}
_online_cache   = {}
_online_last    = 0.0


def normalize_mac(mac):
    """Returns the MAC address as upper case AA:BB:CC:DD:EE:FF or an empty string."""
    if not mac:
        return ""
    mac = mac.strip().upper()
    if _mac_regex.fullmatch(mac):
        return mac
    hexdigits = re.sub(r'[^0-9A-F]', '', mac)
    if len(hexdigits) == 12:
        return ":".join(hexdigits[i:i + 2] for i in range(0, 12, 2))
    return ""


def load_oui_database():
    global _oui_cache
    if _oui_cache:
        return
    files = args.oui_file if args.oui_file else OUI_FILES
    for oui_file in files:
        if not os.path.isfile(oui_file):
            continue
        with open(oui_file, "r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                if "(hex)" not in line:
                    continue
                prefix, vendor = line.split("(hex)", 1)
                prefix = re.sub(r'[^0-9A-Fa-f]', '', prefix).upper()
                vendor = vendor.strip()
                if len(prefix) >= 6 and vendor and prefix[:6] not in _oui_cache:
                    _oui_cache[prefix[:6]] = vendor


def lookup_vendor_online(mac):
    global _online_last
    if mac in _online_cache:
        return _online_cache[mac]
    vendor = "Unknown"
    # Respect the rate limit of the public service (one request per second).
    wait = 1.0 - (time.time() - _online_last)
    if wait > 0:
        time.sleep(wait)
    try:
        req = urlrequest.Request(OUI_URL + mac, headers={ "User-Agent": "CRANIX" })
        with urlrequest.urlopen(req, timeout=5) as response:
            vendor = response.read().decode("utf-8", errors="ignore").strip() or "Unknown"
    except (urlerror.URLError, urlerror.HTTPError, TimeoutError, OSError):
        vendor = "Unknown"
    finally:
        _online_last = time.time()
    _online_cache[mac] = vendor
    return vendor


def get_vendor(mac):
    if not mac:
        return "Unknown"
    first_octet = int(mac[0:2], 16)
    if first_octet & 0x01:
        return "Multicast"
    if first_octet & 0x02:
        return "Locally administered"
    load_oui_database()
    prefix = re.sub(r'[^0-9A-F]', '', mac)[:6]
    if prefix in _oui_cache:
        return _oui_cache[prefix]
    if not args.no_online:
        return lookup_vendor_online(mac)
    return "Unknown"


def exec_kea_command(kea_command):
    subp = subprocess.run(
        [ "/usr/bin/socat", "UNIX:" + KEA_CTRL_SOCKET, "-,ignoreeof" ],
        input=json.dumps(kea_command),
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        encoding="utf-8",
        check=True
    )
    return json.loads(subp.stdout)


def read_kea_pools():
    """Returns a list of (subnet-id, ip_network) tuples for all configured pools."""
    with open(KEA_CONFIG_FILE, encoding="utf-8") as fp:
        kea_config = json.load(fp)
    pools = []
    for subnet in kea_config.get("Dhcp4", {}).get("subnet4", []):
        subnet_id = subnet.get("id")
        for pool in subnet.get("pools", []):
            pool_range = pool.get("pool", "")
            if " - " not in pool_range:
                continue
            first, last = [ x.strip() for x in pool_range.split(" - ", 1) ]
            try:
                first_ip = int(ipaddress.IPv4Address(first))
                last_ip  = int(ipaddress.IPv4Address(last))
            except ipaddress.AddressValueError:
                continue
            pools.append((subnet_id, (first_ip, last_ip)))
    return pools


def read_kea_leases(subnet_ids):
    """Returns the list of leases known by Kea for the given subnet ids."""
    leases = []
    for subnet_id in subnet_ids:
        kea_command = {
            "command": "lease4-get-all",
            "service": [ "dhcp4" ],
            "arguments": { "subnet-id": subnet_id }
        }
        try:
            result = exec_kea_command(kea_command)
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as err:
            print("ERROR: Cannot query the Kea DHCP server: {0}".format(err), file=sys.stderr)
            sys.exit(1)
        if result.get("result") != 0:
            continue
        leases.extend(result.get("arguments", {}).get("leases", []))
    return leases


def read_registered_macs():
    """Returns the set of MAC addresses of all devices registered in CRANIX."""
    api = "/usr/sbin/crx_api.sh"
    if not os.path.isfile(api):
        api = shutil.which("crx_api.sh") or api
    try:
        subp = subprocess.run([ api, "GET", "devices/all" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=True)
        devices = json.loads(subp.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as err:
        print("ERROR: Cannot read the registered devices from the CRANIX API: {0}".format(err), file=sys.stderr)
        sys.exit(1)
    macs = set()
    for device in devices:
        for key in ("mac", "wlanMac"):
            mac = normalize_mac(device.get(key, ""))
            if mac:
                macs.add(mac)
    return macs


def is_active_lease(lease):
    if lease.get("state", 0) != 0:
        return False
    valid_lft = lease.get("valid-lft", 0)
    if valid_lft in (0, 0xFFFFFFFF):
        return True
    return lease.get("cltt", 0) + valid_lft > time.time()


def is_in_pool(ip, pools):
    try:
        ip_int = int(ipaddress.IPv4Address(ip))
    except ipaddress.AddressValueError:
        return False
    for _, (first_ip, last_ip) in pools:
        if first_ip <= ip_int <= last_ip:
            return True
    return False


def print_table(clients):
    headers = ("IP", "MAC", "VENDOR", "HOSTNAME")
    rows = [ (c["ip"], c["mac"], c["vendor"], c["hostname"]) for c in clients ]
    widths = [ len(h) for h in headers ]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))
    fmt = "  ".join("{0:<" + str(width) + "}" for width in widths)
    print(fmt.format(*headers))
    print(fmt.format(*[ "-" * width for width in widths ]))
    for row in rows:
        print(fmt.format(*row))


def main():
    if os.geteuid() != 0:
        print("WARNING: The Kea control socket is only readable by root.", file=sys.stderr)

    pools = read_kea_pools()
    if not pools:
        print("No DHCP pools configured in " + KEA_CONFIG_FILE, file=sys.stderr)
        sys.exit(0)

    registered_macs = read_registered_macs()
    subnet_ids = sorted({ subnet_id for subnet_id, _ in pools })

    clients = []
    for lease in read_kea_leases(subnet_ids):
        if not is_active_lease(lease):
            continue
        ip = lease.get("ip-address", "")
        if not is_in_pool(ip, pools):
            continue
        mac = normalize_mac(lease.get("hw-address", ""))
        if not mac or mac in registered_macs:
            continue
        clients.append({
            "ip":       ip,
            "mac":      mac,
            "vendor":   get_vendor(mac),
            "hostname": lease.get("hostname", "")
        })

    clients.sort(key=lambda client: ipaddress.IPv4Address(client["ip"]))

    if args.json:
        print(json.dumps(clients, indent=4, ensure_ascii=False))
    elif args.csv:
        print("ip;mac;vendor;hostname")
        for client in clients:
            print("{ip};{mac};{vendor};{hostname}".format(**client))
    else:
        print_table(clients)


if __name__ == "__main__":
    main()
