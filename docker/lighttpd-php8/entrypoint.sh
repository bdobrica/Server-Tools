#!/bin/sh
php-fpm83 -D && lighttpd -D -f /etc/lighttpd/lighttpd.conf
