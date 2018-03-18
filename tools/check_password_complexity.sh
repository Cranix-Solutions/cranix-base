#!/bin/bash

. /etc/sysconfig/schoolserver

read pw2check

if [ ${#pw2check} -lt $SCHOOL_MINIMAL_PASSWORD_LENGTH ]; then
	echo "User password must contain minimum %s characters.##$SCHOOL_MINIMAL_PASSWORD_LENGTH"
	exit 1
fi
if [ ${#pw2check} -gt $SCHOOL_MAXIMAL_PASSWORD_LENGTH ]; then
	echo "User password must not contain more then %s characters.##$SCHOOL_MAXIMAL_PASSWORD_LENGTH"
	exit 2
fi
if [[ $pw2check =~ [[:upper:]] ]]; then
	a=1
else
	echo "User password must contain uppercase characters."
	exit 3
fi
if [[ $pw2check =~ [[:lower:]] ]]; then
	a=1
else
	echo "User password must contain lowercase characters."
	exit 4
fi
if [[ $pw2check =~ [[:digit:]] ]]; then
	a=1
else
	echo "User password must contain digits."
	exit 5
fi
#if [[ $pw2check =~ [#%=§] ]]; then
#	a=1
#else
#	echo "User password must contain one of these special chracters: #%=§"
#	exit 6
#fi

PWCHECK=$( echo ${pw2check} | /usr/sbin/cracklib-check )
if [ $? != 0 ]; then
	echo $PWCHECK
	exit 7
fi
exit 0