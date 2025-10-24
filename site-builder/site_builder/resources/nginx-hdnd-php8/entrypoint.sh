#!/bin/sh
set -eu

# Default environment variables
: "${PHP_FPM_PORT:=9000}"
: "${SSL_CERT:=/var/ssl/www/client.pem}"
: "${SSL_KEY:=/var/ssl/www/client.key}"
: "${SSL_ROOT_CA:=/var/ssl/root/ca.crt}"

export PHP_FPM_PORT SSL_CERT SSL_KEY SSL_ROOT_CA

# Quick sanity checks
if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ] || [ ! -f "$SSL_ROOT_CA" ]; then
  echo "ERROR: SSL cert, key or root CA not found at:"
  echo "  SSL_CERT=$SSL_CERT"
  echo "  SSL_KEY=$SSL_KEY"
  echo "  SSL_ROOT_CA=$SSL_ROOT_CA"
  exit 1
fi

# Render nginx config from template using env vars
echo "Rendering Nginx config..."
envsubst '$PHP_FPM_PORT $SSL_CERT $SSL_KEY $SSL_ROOT_CA' \
  < /etc/nginx/templates/nginx.conf \
  > /etc/nginx/nginx.conf

# Start PHP-FPM (background)
echo "Starting PHP-FPM..."
php-fpm83 -D

# Start Nginx (foreground)
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
