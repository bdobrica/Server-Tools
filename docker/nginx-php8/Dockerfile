FROM alpine:3.22.2

ENV RUNTIME_VERSION=1.0.0

RUN apk --update add \
    openssl \
    ca-certificates \
    nginx \
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
COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /scripts
COPY entrypoint.sh /scripts/entrypoint.sh
RUN mkdir -p /var/www && \
    mkdir -p /run/nginx && \
    chown -R www-data /run/nginx
RUN update-ca-certificates

ENTRYPOINT ["sh", "/scripts/entrypoint.sh"]
