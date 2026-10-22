FROM alpine:3.24

ENV RUNTIME_VERSION=1.1.1

# Refuse vulnerable packages if an Alpine mirror has not received the security update.
# PHP 8.5.12 fixes CVE-2026-109618 and CVE-2026-109619.
RUN apk add --no-cache \
    'php85>=8.5.12' \
    openssl \
    ca-certificates \
    envsubst \
    lighttpd \
    'php85-common>=8.5.12' \
    php85-dom \
    php85-gd \
    php85-curl \
    php85-ctype \
    php85-xml \
    php85-simplexml \
    php85-pdo \
    php85-pecl-imap \
    'php85-cgi>=8.5.12' \
    php85-soap \
    php85-ldap \
    php85-pdo_mysql \
    php85-mysqli \
    'php85-fpm>=8.5.12' \
    php85-fileinfo \
    php85-session \
    php85-tokenizer \
    php85-iconv \
    php85-xmlreader \
    php85-zip \
    php85-openssl \
    php85-exif \
    php85-pecl-imagick \
    php85-intl \
    php85-mbstring \
    fcgi

# ctype, simplexml required by expertas

RUN adduser www-data -G www-data -H -s /bin/false -D

RUN sed -e "s/^upload_max_filesize = .\+$/upload_max_filesize = 64M/g" \
    -e "s/^post_max_size = .\+$/post_max_size = 64M/g" \
    -e "s/^max_execution_time = .\+$/max_execution_time = 120/g" \
    -e "s/^memory_limit = .\+$/memory_limit = 256M/g" \
    -e "s/^zlib\.output_compression = .\+$/zlib.output_compression = On/g" \
    -e "s/^;zlib\.output_handler =.*$/zlib.output_handler = On/g" \
    -i /etc/php85/php.ini \
    && sed -e "s/^user = nobody$/user = www-data/g" \
    -e "s/^group = nobody$/group = www-data/g" \
    -i /etc/php85/php-fpm.d/www.conf

# Check the actual interpreter as well as the package constraints.
RUN php85 -r 'exit(PHP_VERSION_ID >= 80512 && PHP_VERSION_ID < 80600 ? 0 : 1);'

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
