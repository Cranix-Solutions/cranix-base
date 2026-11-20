#!/usr/bin/env bash

set -euo pipefail

DB_NAME="kea_dhcp4"

usage() {
    echo "Usage: $0 [-i <ip_address>] [-m <mac_address>]"
    echo "  -i  Search host by IPv4 address (e.g., 192.168.1.50)"
    echo "  -m  Search host by MAC address (e.g., 00:0c:29:ab:cd:ef)"
    exit 1
}

SEARCH_IP=""
SEARCH_MAC=""

while getopts ":i:m:h" opt; do
    case "${opt}" in
        i) SEARCH_IP="${OPTARG}" ;;
        m) SEARCH_MAC="${OPTARG}" ;;
        h) usage ;;
        \?) echo "Error: Unknown option -${OPTARG}" >&2; usage ;;
        :)  echo "Error: Option -${OPTARG} requires an argument." >&2; usage ;;
    esac
done

if [[ -z "${SEARCH_IP}" && -z "${SEARCH_MAC}" ]]; then
    echo "Error: You must provide either -i or -m." >&2
    usage
fi

WHERE_CLAUSE=""

if [[ -n "${SEARCH_IP}" ]]; then
    WHERE_CLAUSE="ipv4_address = INET_ATON('${SEARCH_IP}')"
elif [[ -n "${SEARCH_MAC}" ]]; then
    # Strip colons, hyphens, and dots, then convert to binary
    CLEAN_MAC="${SEARCH_MAC//[:.-]/}"
    WHERE_CLAUSE="dhcp_identifier_type = 0 AND dhcp_identifier = UNHEX('${CLEAN_MAC}')"
fi

QUERY="SELECT 
    host_id,
    INET_NTOA(ipv4_address) AS ipv4_address,
    hostname,
    dhcp4_subnet_id,
    LOWER(INSERT(INSERT(INSERT(INSERT(INSERT(HEX(dhcp_identifier), 11, 0, ':'), 9, 0, ':'), 7, 0, ':'), 5, 0, ':'), 3, 0, ':')) AS mac_address
FROM hosts
WHERE ${WHERE_CLAUSE};"

mariadb "${DB_NAME}" -t -e "${QUERY}"
