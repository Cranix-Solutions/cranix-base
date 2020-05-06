#!/bin/bash
#
# Copyright (c) 2017 Peter Varkoly Nürnberg, Germany.  All rights reserved.
#

if [ ! -e /etc/sysconfig/cranix ]; then
   echo "ERROR This ist not an CRANIX."
   exit 1
fi

. /etc/sysconfig/cranix

if [ -z "${CRANIX_HOME_BASE}" ]; then
   echo "ERROR CRANIX_HOME_BASE must be defined."
   exit 2
fi

if [ ! -d "${CRANIX_HOME_BASE}" ]; then
   echo "ERROR CRANIX_HOME_BASE must be a directory and must exist."
   exit 3
fi

abort() {
        TASK="delete_group-$( uuidgen -t )"
        mkdir -p /var/adm/cranix/opentasks/
        echo "name: $name" >> /var/adm/cranix/opentasks/$TASK
        exit 1
}


name=''

while read a
do
  b=${a/:*/}
  if [ "$a" != "${b}:" ]; then
     c=${a/$b: /}
  else
     c=""
  fi
  case $b in
    name)
      name="${c}"
    ;;
  esac
done

echo "name:        $name"

if [ -z "$name" ]; then
   echo "ERROR name must be defined."
   exit 4
fi

samba-tool group delete "$name"
if [ $? != 0 ]; then
   abort
fi

nameUp=`echo "$name" | tr "[:lower:]" "[:upper:]"`
nameLo=`echo "$name" | tr "[:upper:]" "[:lower:]"`
gdir=${CRANIX_HOME_BASE}/groups/${nameUp}

if [ -d "$gdir" ]; then
    rm -r "$gdir"
fi

if [ -d "${CRANIX_HOME_BASE}/${nameLo}"   ]; then
    rm -r "${CRANIX_HOME_BASE}/${nameLo}" 
fi
