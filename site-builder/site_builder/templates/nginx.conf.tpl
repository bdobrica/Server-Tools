{% if site.use_ssl %}
server {
    listen 80;
    server_name {{ site.name }} www.{{ site.name }};
    return 301 https://{{ site.name }}$request_uri;
}
{% endif %}

server {
    {% if site.use_ssl %}
    listen [::]:443 ssl http2;
    listen 443 ssl http2;
    {% else %}
    listen 80;
    listen [::]:80;
    {% endif %}

    server_name {{ site.name }} www.{{ site.name }};

    {% if site.use_ssl %}
    ssl_certificate           /mnt/www/{{ site.domain }}/.cert/{{ site.name }}.crt;
    ssl_certificate_key       /mnt/www/{{ site.domain }}/.cert/{{ site.name }}.key;

    ssl_session_cache  builtin:1000  shared:SSL:10m;
    ssl_protocols  TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4;
    ssl_prefer_server_ciphers on;
    {% endif %}

    access_log /var/log/nginx/{{ site.name }}-access.log;
    error_log /var/log/nginx/{{ site.name }}-error.log;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass https://{{ IP_PREFIX }}.{{ site.ip_suffix }};

        proxy_ssl_certificate         {{ PROXY_SSL_PATH }}/{{ site.domain }}/{{ site.name }}/client.crt;
        proxy_ssl_certificate_key     {{ PROXY_SSL_PATH }}/{{ site.domain }}/{{ site.name }}/client.key;
        proxy_ssl_protocols           TLSv1 TLSv1.1 TLSv1.2;
        proxy_ssl_ciphers             HIGH:!aNULL:!MD5;
        proxy_ssl_trusted_certificate {{ ROOT_CA_CRT }};
        proxy_ssl_name                {{ site.name }};

        proxy_ssl_verify        on;
        proxy_ssl_verify_depth  2;
        proxy_ssl_session_reuse on;
    }
}
