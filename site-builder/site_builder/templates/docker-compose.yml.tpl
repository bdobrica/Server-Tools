services:
{% if ENABLE_PROXY %}
    nginx:
        image: nginx:alpine
        container_name: nginx-proxy
        ports:
            - "80:80"
            - "443:443"
        networks:
            nginx-proxy:
                ipv4_address: {{ IP_PREFIX }}.1
        volumes:
            - type: bind
              source: "/etc/site-builder/nginx/sites-enabled"
              target: "/etc/nginx/conf.d"
              read_only: true
            - type: bind
              source: "{{ PROXY_SSL_PATH }}"
              target: "/var/ssl"
              read_only: true
            - type: bind
              source: "/mnt/www"
              target: "/var/www"
              read_only: true
        restart: unless-stopped
        depends_on:
{% for site in sites %}
            - web-{{ site.slug }}
{% endfor %}
{% endif %}
{% if ENABLE_DATABASE %}
    mariadb:
        image: mariadb:10.6
        container_name: mariadb-server
        environment:
            - MYSQL_ROOT_PASSWORD={{ DB_ROOT_PASSWORD }}
            - MYSQL_CHARACTER_SET_SERVER=utf8mb4
            - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
        networks:
            nginx-proxy:
                ipv4_address: {{ IP_PREFIX }}.254
        volumes:
            - type: bind
              source: "/etc/site-builder/mysql/my.cnf"
              target: "/etc/mysql/my.cnf"
              read_only: true
            - type: bind
              source: "/etc/site-builder/mysql/data"
              target: "/var/lib/mysql"
            - type: bind
              source: "/etc/site-builder/mysql/logs"
              target: "/var/log/mysql"
            - type: bind
              source: "/var/run/mysqld"
              target: "/var/run/mysqld"
        ports:
            - "3306:3306"
        restart: unless-stopped
{% endif %}

{% for site in sites %}
    web-{{ site.slug }}:
        build:
            context: {{ site.runtime.context }}
            dockerfile: Dockerfile
        image: {{ site.runtime.name }}:{{ site.runtime.version }}
        container_name: site-{{ site.slug }}
        networks:
            nginx-proxy:
                ipv4_address: {{ IP_PREFIX }}.{{ site.ip_suffix }}
        volumes:
            - type: bind
              source: "{{ PROXY_SSL_PATH }}/{{ site.domain }}/{{ site.name }}"
              target: "/var/ssl/www"
            - type: bind
              source: "{{ ROOT_CA_CRT }}"
              target: "/var/ssl/root/ca.crt"
            - type: bind
              source: "{{ site.web_root }}"
              target: "/var/www"
{% if ENABLE_DATABASE %}
        depends_on:
            - mariadb
{% else %}
            - type: bind
              source: "/var/run/mysqld/mysqld.sock"
              target: "/var/run/mysqld/mysqld.sock"
{% endif %}
        restart: unless-stopped
{% endfor %}

networks:
    nginx-proxy:
        ipam:
            config:
                - subnet: {{ IP_PREFIX }}.0/24
                  gateway: {{ IP_PREFIX }}.1
