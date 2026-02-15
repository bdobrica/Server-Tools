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
              source: "{{ NGINX_SITES_ENABLED_PATH }}"
              target: "/etc/nginx/conf.d"
              read_only: true
            - type: bind
              source: "{{ PROXY_SSL_PATH }}"
              target: "/var/ssl"
              read_only: true
            - type: bind
              source: "{{ WEB_PATH }}"
              target: "/var/www"
              read_only: true
        restart: unless-stopped
        depends_on:
{% for site in sites %}
            - web-{{ site.slug }}
{% endfor %}
{% endif %}
{% if ENABLE_MYSQL_DATABASE %}
    mariadb:
        image: mariadb:10.6
        container_name: mariadb-server
        environment:
            - MYSQL_ROOT_PASSWORD={{ MYSQL_ROOT_PASSWORD }}
            - MYSQL_CHARACTER_SET_SERVER=utf8mb4
            - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
        networks:
            nginx-proxy:
                ipv4_address: {{ IP_PREFIX }}.254
        volumes:
            - type: bind
              source: "{{ MYSQL_CONFIG_PATH }}/my.cnf"
              target: "/etc/mysql/my.cnf"
              read_only: true
            - type: bind
              source: "{{ MYSQL_CONFIG_PATH }}/data"
              target: "/var/lib/mysql"
            - type: bind
              source: "{{ MYSQL_CONFIG_PATH }}/logs"
              target: "/var/log/mysql"
            - type: bind
              source: "/var/run/mysqld"
              target: "/var/run/mysqld"
        ports:
            - "3306:3306"
        restart: unless-stopped
{% endif %}
{% if ENABLE_POSTGRES_DATABASE %}
    postgres:
        image: postgres:15-alpine
        container_name: postgres-server
        environment:
            - POSTGRES_PASSWORD={{ POSTGRES_ROOT_PASSWORD }}
            - POSTGRES_USER=postgres
            - PGDATA=/var/lib/postgresql/data/pgdata
        networks:
            nginx-proxy:
                ipv4_address: {{ IP_PREFIX }}.253
        volumes:
            - type: bind
              source: "{{ POSTGRES_CONFIG_PATH }}/postgresql.conf"
              target: "/etc/postgresql/postgresql.conf"
              read_only: true
            - type: bind
              source: "{{ POSTGRES_CONFIG_PATH }}/data"
              target: "/var/lib/postgresql/data"
            - type: bind
              source: "{{ POSTGRES_CONFIG_PATH }}/logs"
              target: "/var/log/postgresql"
        ports:
            - "5432:5432"
        restart: unless-stopped
        command: postgres -c config_file=/etc/postgresql/postgresql.conf
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
{% if MYSQL_MODE == "native" %}
            - type: bind
              source: "/var/run/mysqld/mysqld.sock"
              target: "/var/run/mysqld/mysqld.sock"
{% endif %}
{% if POSTGRES_MODE == "native" %}
            - type: bind
              source: "/var/run/postgresql"
              target: "/var/run/postgresql"
{% endif %}
{% if ENABLE_MYSQL_DATABASE or ENABLE_POSTGRES_DATABASE %}
        depends_on:
{% if ENABLE_MYSQL_DATABASE %}
            - mariadb
{% endif %}
{% if ENABLE_POSTGRES_DATABASE %}
            - postgres
{% endif %}
{% endif %}
        restart: unless-stopped
{% endfor %}

networks:
    nginx-proxy:
        ipam:
            config:
                - subnet: {{ IP_PREFIX }}.0/24
                  gateway: {{ IP_PREFIX }}.1
