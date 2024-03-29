#!/bin/bash

ADMINPW=$1
while ! smbclient -L admin -U Administrator%"$ADMINPW"
do
	echo -n "Passwort des Administrators:"
	read ADMINPW
done

. /etc/sysconfig/cranix

for i in $( lpc status | grep ':$' | sed 's/://' )
do
	#Check if this printer is in the DB
	INDB=$( echo "select name from Printers where name='$i'" | mysql CRX )
	if [ -z "${INDB}" ]; then
		continue
	fi

	lower=$( echo $i | tr [:upper:] [:lower:] )
	if [ $lower != $i ];
       	then
		systemctl stop cups
                sed -i "s/${i}/${lower}/" /etc/samba/smb.conf
		sed -i "s/${i}>/${lower}>/" /etc/cups/printers.conf
		sed -i "s/Info ${i}$/Info ${lower}/" /etc/cups/printers.conf
		mv /etc/cups/ppd/$i.ppd /etc/cups/ppd/${lower}.ppd
	fi
done
