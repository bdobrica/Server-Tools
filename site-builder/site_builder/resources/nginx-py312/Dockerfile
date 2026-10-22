# FastAPI + Nginx (SSL) single-container image
FROM python:3.13.17-alpine3.24

ENV RUNTIME_VERSION=1.1.0

# System deps
RUN apk add --no-cache \
    ca-certificates \
    curl \
    envsubst \
    nginx

# Alpine supplies the www-data group, but not the application user.
RUN adduser -D -G www-data -h /var/www -s /bin/sh www-data

# Nginx setup
RUN mkdir -p /etc/nginx/templates /run/nginx /var/www
RUN chown -R www-data /var/www /var/lib/nginx && update-ca-certificates
COPY nginx.conf /etc/nginx/templates/nginx.conf

# App directory (your index.py will be mounted here at runtime)
WORKDIR /var/www

# Entry script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose HTTP/HTTPS
EXPOSE 443

ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]
