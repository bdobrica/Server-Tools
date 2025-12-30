# FastAPI + Nginx (SSL) single-container image
FROM python:3.12-slim-trixie

ENV RUNTIME_VERSION=1.0.1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    envsubst \
    nginx \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

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
