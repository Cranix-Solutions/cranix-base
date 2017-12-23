#!/bin/bash
# (c) 2017 Péter Varkoly <peter@varkoly.de> - all rights reserved

. /etc/sysconfig/schoolserver

user=$1
mkdir -m 700 -p $SCHOOL_HOME_BASE/groups/LINKED/$user/
chown $user $SCHOOL_HOME_BASE/groups/LINKED/$user/
rm -f $SCHOOL_HOME_BASE/groups/LINKED/$user/*

for g in  $( oss_api_text.sh GET users/byUid/$user/groups )
do
    if [ -d "$SCHOOL_HOME_BASE/groups/$g" ]
    then
        ln -s "$SCHOOL_HOME_BASE/groups/$g" "$SCHOOL_HOME_BASE/groups/LINKED/$user/$g"
    fi
done

