#!/bin/bash

/usr/bin/grep -q AllowEncodedSlashes /etc/apache2/vhosts.d/admin_include.conf || \
	sed -i '/ProxyRequests     Off/i\        AllowEncodedSlashes NoDecode' /etc/apache2/vhosts.d/admin_include.conf
/usr/bin/grep -q AllowEncodedSlashes /etc/apache2/vhosts.d/cranix_include.conf || \
	sed -i '/ProxyRequests     Off/i\        AllowEncodedSlashes NoDecode' /etc/apache2/vhosts.d/cranix_include.conf
/usr/bin/systemctl reload apache2
