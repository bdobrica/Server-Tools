#!/bin/sh
set -eu

# Default environment variables
: "${NODE_PORT:=3000}"
: "${NODE_ENV:=production}"
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
envsubst '\$NODE_PORT \$SSL_CERT \$SSL_KEY \$SSL_ROOT_CA' \
  < /etc/nginx/templates/nginx.conf \
  > /etc/nginx/nginx.conf

# Change to app directory
cd /var/www

# Check for required files
if [ ! -f "package.json" ]; then
  echo "ERROR: /var/www/package.json not found!"
  exit 1
fi

if [ ! -f "index.ts" ]; then
  echo "ERROR: /var/www/index.ts not found!"
  exit 1
fi

# Handle Node.js dependencies
echo "Installing Node.js dependencies..."

# Configure npm to use .node_modules instead of node_modules
npm config set modules-folder .node_modules

# Check if .node_modules exists and is populated
if [ -d "/var/www/.node_modules" ] && [ "$(ls -A /var/www/.node_modules 2>/dev/null)" ]; then
    echo "Using existing .node_modules in /var/www/.node_modules"
    # Still run npm install in case package.json changed
    npm install --production=false || echo "Warning: npm install encountered issues, continuing..."
else
    echo "Installing dependencies to /var/www/.node_modules"
    npm install --production=false || {
        echo "ERROR: Failed to install npm dependencies"
        exit 1
    }
fi

# Check if TypeScript config exists, create a basic one if not
if [ ! -f "tsconfig.json" ]; then
    echo "Creating basic tsconfig.json..."
    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["*.ts", "src/**/*"],
  "exclude": [".node_modules", "dist"]
}
EOF
fi

# Compile TypeScript
echo "Compiling TypeScript..."
if ! tsc; then
    echo "ERROR: TypeScript compilation failed"
    exit 1
fi

# Determine the main entry point
if [ -f "dist/index.js" ]; then
    MAIN_FILE="dist/index.js"
elif [ -f "index.js" ]; then
    MAIN_FILE="index.js"
else
    echo "ERROR: No compiled JavaScript file found (expected dist/index.js or index.js)"
    exit 1
fi

# Start Node.js application (background)
echo "Starting Node.js application on port ${NODE_PORT}..."
NODE_ENV="${NODE_ENV}" node "${MAIN_FILE}" &

# Wait a moment for Node.js to start
sleep 2

# Check if Node.js process is running
if ! pgrep -f "node.*${MAIN_FILE}" > /dev/null; then
    echo "ERROR: Node.js application failed to start"
    exit 1
fi

# Start Nginx (foreground)
echo "Starting Nginx..."
nginx -g 'daemon off;'
