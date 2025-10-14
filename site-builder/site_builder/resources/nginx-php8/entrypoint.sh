#!/bin/sh

php-fpm83 -D && exec nginx -g 'daemon off;'
