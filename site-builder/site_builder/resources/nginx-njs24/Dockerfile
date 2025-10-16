# Node.js + Nginx (SSL) single-container image
FROM node:24-alpine

ENV RUNTIME_VERSION=1.0.0

# System deps including nginx
RUN apk update && apk add --no-install-recommends \
    ca-certificates \
    curl \
    envsubst \
    nginx \
    && rm -rf /var/cache/apk/*

# Install TypeScript globally
RUN npm install -g typescript ts-node

# Nginx setup
RUN mkdir -p /etc/nginx/templates /run/nginx
RUN update-ca-certificates
COPY nginx.conf /etc/nginx/templates/nginx.conf

# App directory (your index.ts and package.json will be mounted here at runtime)
WORKDIR /var/www

# Entry script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose HTTP/HTTPS
EXPOSE 443

ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]
