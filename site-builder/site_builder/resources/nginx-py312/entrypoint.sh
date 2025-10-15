#!/bin/sh
set -eu

# Default environment variables
: "${UVICORN_HOST:=127.0.0.1}"
: "${UVICORN_PORT:=8000}"
: "${UVICORN_WORKERS:=1}"
: "${UVICORN_LOG_LEVEL:=warning}"
: "${SSL_CERT:=/var/ssl/www/server.pem}"
: "${SSL_KEY:=/var/ssl/www/server.key}"
: "${SSL_ROOT_CA:=/var/ssl/root/ca.crt}"

# Quick sanity checks
if [ ! -f "${SSL_CERT}" ] || [ ! -f "${SSL_KEY}" ] || [ ! -f "${SSL_ROOT_CA}" ]; then
  echo "ERROR: SSL cert, key or root CA not found at:"
  echo "  SSL_CERT=${SSL_CERT}"
  echo "  SSL_KEY=${SSL_KEY}"
  echo "  SSL_ROOT_CA=${SSL_ROOT_CA}"
  exit 1
fi

# Render nginx config from template using env vars
echo "Rendering Nginx config..."
envsubst '\$UVICORN_PORT \$SSL_CERT \$SSL_KEY \$SSL_ROOT_CA' \
  < /etc/nginx/templates/nginx.conf \
  > /etc/nginx/nginx.conf

# Start Uvicorn (background)
echo "Starting Uvicorn on ${UVICORN_HOST}:${UVICORN_PORT}..."
cd /var/www
# Expecting /var/www/index.py that exposes FastAPI instance as 'app'
if [ ! -f "index.py" ]; then
  echo "ERROR: /var/www/index.py not found!"
  exit 1
fi

# Check if there are requirements.txt and install dependencies
echo "Installing Python dependencies from requirements.txt..."

# As /var/www/.venv might be mounted from outside, we create venv in /var/www/.venv
# and install dependencies there
if [ -d "/var/www/.venv" ]; then
    echo "Using existing virtual environment in /var/www/.venv"
    . /var/www/.venv/bin/activate
else
    echo "Creating new virtual environment in /var/www/.venv"
    python3 -m venv /var/www/.venv
    . /var/www/.venv/bin/activate
    python3 -m pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt || true
    else
        echo "No requirements.txt found. Installing FastAPI and Uvicorn by default."
        python3 -m pip install fastapi uvicorn[standard] || true
    fi
fi

# Start Uvicorn with specified parameters
uvicorn index:app \
  --host "${UVICORN_HOST}" \
  --port "${UVICORN_PORT}" \
  --workers "${UVICORN_WORKERS}" \
  --log-level "${UVICORN_LOG_LEVEL}" &

# Start Nginx (foreground)
echo "Starting Nginx..."
nginx -g 'daemon off;'
