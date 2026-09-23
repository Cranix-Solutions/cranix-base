#!/bin/bash
INTERFACE=$1
IMAGE=$2
mkdir -p /run/cranix
/usr/sbin/udp-sender --pid-file /run/cranix/multicast-imaging.pid \
	--log /run/cranix/multicast-imaging.log \
	--nokbd --interface ${INTERFACE} \
	--file ${IMAGE} --min-receivers 1 --min-wait 5 --max-wait 10
