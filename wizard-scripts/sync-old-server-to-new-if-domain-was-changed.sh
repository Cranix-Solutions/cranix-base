#!/bin/bash
#Some test
ping -c 1 new-cranix  || {
        echo "The new server can not be reached"
        echo "The new server must be reachable with the name 'new-cranix'"
        exit
}

mkdir -p users
ssh new-cranix "mkdir -p /tmp/import-old/users"

#Start sync homes
nohup rsync -aAv /home/ new-cranix:/home/ &

#Import SQL and other data based stuff
ssh new-cranix "mysqldump --databases CRX > CRX-orig.sql"
mysqldump --databases CRX > CRX.sql
scp CRX.sql new-cranix:/tmp/import-old/
ssh new-cranix "mysql < /tmp/import-old/CRX.sql"
ssh new-cranix "systemctl restart cranix-api-provider"
sleep 1
ssh new-cranix /usr/share/cranix/tools/wait-for-api.sh
ssh new-cranix "crx_api.sh PUT devices/refreshConfig"
ssh new-cranix "crx_api.sh PUT softwares/saveState"
ssh new-cranix "systemctl stop cron salt-master"
rsync -aAv /etc/salt/pki/ new-cranix:/etc/salt/pki/
ssh new-cranix "systemctl start cron salt-master"

#Get all users with oll needed parameters and create these on the new server
for U in $( crx_api.sh GET users/all | jq '.[] | .uid' | sed 's/"//g' )
do
    pdbedit -e tdbsam:users/$U.tdb $U
    uidNumber=$( ldbsearch -H /var/lib/samba/private/sam.ldb cn=$U uidNumber | gawk '/uidNumber:/ { print $2}' )
    role=$( crx_api_text.sh GET users/byUid/$U/role )
    echo -e "$uidNumber\n$role" > users/$U.data
    scp users/$U.tdb new-cranix:/tmp/import-old/users/
    ssh new-cranix "pdbedit -i tdbsam:/tmp/import-old/users/$U.tdb"
    ssh new-cranix "/usr/share/cranix/tools/add_user_rfc2307.sh  $U $role $uidNumber"
    ssh new-cranix "/usr/bin/samba-tool user setexpiry --noexpiry $U"
    if [ -z "${DOIT}" ]; then
        echo "Wie sieht es aus? (N)ext/(D)o it/(E)xit"
        read answer
        case "$answer" in
                E)
                        exit
                        ;;
                D)
                        export DOIT="DOIT"
                        ;;
        esac
    fi
    uidNumber=""
    role=""
done

ssh new-cranix /usr/share/cranix/tools/sync-arecords-to-samba.py
ssh new-cranix /usr/share/cranix/tools/sync-ptrrecords-to-samba.py
