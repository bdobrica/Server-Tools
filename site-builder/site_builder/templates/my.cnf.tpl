[mysqld]
{% if DB_MODE == "docker" -%}
bind-address = 0.0.0.0
{% else -%}
bind-address = 127.0.0.1
{% endif -%}
port = 3306
socket = /var/run/mysqld/mysqld.sock
pid-file = /var/run/mysqld/mysqld.pid

{% if DB_MODE == "native" -%}
basedir = /usr
datadir = /var/lib/mysql
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
{% endif -%}

# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# InnoDB settings
innodb_buffer_pool_size = {{ DB_INNODB_BUFFER_POOL_SIZE | default('256M') }}
innodb_log_file_size = {{ DB_INNODB_LOG_FILE_SIZE | default('64M') }}
innodb_file_per_table = 1
innodb_flush_log_at_trx_commit = 1
innodb_flush_method = O_DIRECT

# Query cache
query_cache_type = 1
query_cache_size = {{ DB_QUERY_CACHE_SIZE | default('16M') }}

# Connection settings
max_connections = {{ DB_MAX_CONNECTIONS | default('100') }}
connect_timeout = 60
wait_timeout = 28800

# Logging
general_log = {{ DB_GENERAL_LOG | default('1') }}
general_log_file = /var/log/mysql/mysql.log
log_error = /var/log/mysql/error.log
slow_query_log = {{ DB_SLOW_QUERY_LOG | default('1') }}
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = {{ DB_LONG_QUERY_TIME | default('2') }}

{% if DB_MODE == "native" -%}
# Security
skip-name-resolve
local-infile = 0
{% endif -%}

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
socket = /var/run/mysqld/mysqld.sock

[mysqldump]
quick
quote-names
max_allowed_packet = 16M

[isamchk]
key_buffer = 16M
