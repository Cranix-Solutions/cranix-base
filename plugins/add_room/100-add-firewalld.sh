#!/bin/bash

abort() {
        TASK="add_room-$( uuidgen -t )"
        mkdir -p /var/adm/cranix/opentasks/
        echo "name: $name" >> /var/adm/cranix/opentasks/$TASK
        echo "startip: $startip" >> /var/adm/cranix/opentasks/$TASK
        echo "netmask: $netmask" >> /var/adm/cranix/opentasks/$TASK
        echo "hwconf: $hwconf" >> /var/adm/cranix/opentasks/$TASK
        exit 1
}

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
    startip)
      startip="${c}"
    ;;
    netmask)
      netmask="${c}"
    ;;
    hwconf)
      hwconf="${c}"
    ;;
  esac
done

/usr/bin/firewall-cmd --new-zone=${name}
/usr/bin/firewall-cmd --zone=${name} --set-description="Zone for Room ${name}"
/usr/bin/firewall-cmd --zone=${name} --add-source="${startip}/${netmask}"
/usr/bin/firewall-cmd --zone=${name} --set-target=ACCEPT
/usr/bin/firewall-offline-cmd --new-zone=${name}
/usr/bin/firewall-offline-cmd --zone=${name} --set-description="Zone for Room ${name}"
/usr/bin/firewall-offline-cmd --zone=${name} --add-source="${startip}/${netmask}"
/usr/bin/firewall-offline-cmd --zone=${name} --set-target=ACCEPT

