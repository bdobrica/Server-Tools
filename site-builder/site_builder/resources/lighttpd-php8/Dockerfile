FROM alpine:3.22.2

ENV RUNTIME_VERSION=1.0.0

RUN apk --update add \
    openssl \
    ca-certificates \
    envsubst \
    lighttpd \
    php-common \
    php-dom \
    php-json \
    php-gd \
    php-curl \
    php-ctype \
    php-xml \
    php-simplexml \
    php-pdo \
    php-imap \
    php-cgi \
    php-soap \
    php-ldap \
    php-pdo_mysql \
    php-mysqli \
    php-fpm \
    php-fileinfo \
    php-session \
    php-tokenizer \
    php-iconv \
    php-xmlreader \
    php-zip \
    php-openssl \
    php-exif \
    php-imagick \
    php-intl \
    php-mbstring \
    fcgi \
    && rm -Rf /var/cache/apk/*

# ctype, simplexml required by expertas

RUN adduser www-data -G www-data -H -s /bin/false -D

RUN sed -e "s/^upload_max_filesize = .\+$/upload_max_filesize = 64M/g" \
    -e "s/^post_max_size = .\+$/post_max_size = 64M/g" \
    -e "s/^max_execution_time = .\+$/max_execution_time = 120/g" \
    -e "s/^memory_limit = .\+$/memory_limit = 256M/g" \
    -e "s/^zlib\.output_compression = .\+$/zlib.output_compression = On/g" \
    -e "s/^;zlib\.output_handler =.*$/zlib.output_handler = On/g" \
    -i /etc/php83/php.ini

RUN mkdir -p /etc/lighttpd/templates /run/lighttpd /var/www
RUN chown -R www-data /var/www && update-ca-certificates
COPY lighttpd.conf /etc/lighttpd/templates/lighttpd.conf

# App directory (your index.php will be mounted here at runtime)
WORKDIR /var/www

# Entry script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose HTTP/HTTPS
EXPOSE 443

ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]
