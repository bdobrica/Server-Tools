# Code Review — site-builder

**Reviewed:** 2026-02-15  
**Scope:** All Python source under `site-builder/site_builder/`, templates, `pyproject.toml`, tests, and `README.md`.

---

## 1. Overall Assessment

The project is a well-structured CLI tool for automating multi-site web hosting on bare-metal Linux servers. It provides Nginx reverse-proxy configuration (native or Docker), MariaDB/PostgreSQL database management (native or Docker), automated SSL certificate generation via an internal CA, and auto-detection of PHP, Python, and Node.js applications.

**Strengths:**
- Clean separation of concerns via abstract base classes (`NginxManager`, `DatabaseManager`) with concrete Docker/native implementations.
- Good use of the factory pattern (`manager_factory.py`, `ssl_manager_factory.py`) to decouple creation from usage.
- Persistent configuration via INI file so flags carry forward across runs.
- Modern packaging with `pyproject.toml`, proper entry-point, and `setuptools` back-end.
- Comprehensive README documentation with architecture diagrams, usage examples, and CLI reference.

**Weaknesses and areas for improvement are detailed below.**

---

## 2. Security Issues

### 2.1 — SQL / Command Injection in Database Managers (Critical)

**Files:** `mariadb_docker.py`, `mariadb_native.py`, `postgresql_docker.py`, `postgresql_native.py`

All `create_database()`, `create_user()`, and `grant_privileges()` methods build SQL strings with direct f-string interpolation of user-controlled values (`database_name`, `username`, `password`, `privileges`).

```python
# Example from mariadb_docker.py
f"CREATE DATABASE IF NOT EXISTS `{database_name}` ..."
f"CREATE USER IF NOT EXISTS '{username}'@'%' IDENTIFIED BY '{password}';"
f"GRANT {privileges} PRIVILEGES ON `{database_name}`.* TO '{username}'@'%'; ..."
```

Although these are currently only called internally, any future use with user-supplied input would allow SQL injection. The `privileges` parameter is passed directly without any validation — a caller could inject arbitrary SQL.

**Fix:** Validate `database_name`, `username`, and `privileges` against allow-lists or strict regex patterns before interpolation. Never pass `privileges` directly from external input without whitelisting.

### 2.2 — Password Visible in Process List (Medium)

Database passwords are passed as command-line arguments (`-p{password}`, `PGPASSWORD`). On multi-user systems they are visible via `ps aux`.

**Fix (MariaDB):** Use `--defaults-extra-file` with a temporary credentials file instead of `-p` on the command line.  
**Fix (PostgreSQL):** `PGPASSWORD` environment variable is reasonable, but consider `.pgpass` for native mode.

### 2.3 — CA Password Stored in Plaintext (Medium)

`validation.py` writes the generated CA password to `password.txt` with no file-permission restrictions:

```python
with password_file.open("w") as fp:
    fp.write(password)
```

**Fix:** Set restrictive permissions (`chmod 0o600`) immediately after writing, the same way `_store_root_password()` does in the database managers.

### 2.4 — Passwords Persisted in `config.ini` (Medium)

`save_config()` writes `root_ca_password`, `mysql_root_password`, `postgres_root_password`, and `database_root_password` to the INI file in plaintext. The file has no explicit permission restriction.

**Fix:** Either exclude secrets from `config.ini` (keep them only in their respective `password.txt` files), or at minimum set the file to `0o600` after writing.

### 2.5 — Private Key Written Without Encryption (Low)

In `ssl_certificate_manager.py`, site private keys are written with `serialization.NoEncryption()`. This is typical for server certificates, but the keys should have restrictive file permissions.

**Fix:** Add `proxy_ssl_key.chmod(0o600)` after writing the key file.

---

## 3. Bugs & Correctness Issues

### 3.1 — `docker-compose.yml.tpl` Uses `ENABLE_DATABASE` But Template Vars Set `ENABLE_MYSQL_DATABASE` / `ENABLE_POSTGRES_DATABASE`

**File:** `__main__.py` (lines ~260–267) and `docker-compose.yml.tpl`

The template checks `{% if ENABLE_DATABASE %}` but the code populates `ENABLE_MYSQL_DATABASE` and `ENABLE_POSTGRES_DATABASE` — neither named `ENABLE_DATABASE`. The entire MariaDB/PostgreSQL block in the docker-compose template will never render.

Similarly, the template references `DB_ROOT_PASSWORD` but the code sets `MYSQL_ROOT_PASSWORD` and `POSTGRES_ROOT_PASSWORD`.

**Fix:** Either:
- Add `ENABLE_DATABASE` and `DB_ROOT_PASSWORD` keys to `template_vars` in `__main__.py`, or
- Update the template to use `ENABLE_MYSQL_DATABASE` / `ENABLE_POSTGRES_DATABASE` and render separate MariaDB/PostgreSQL service blocks.

### 3.2 — `my.cnf.tpl` Uses `DB_MODE` But Template Vars Never Set It

The MariaDB template checks `{% if DB_MODE == "docker" %}` but `template_vars` contains `MYSQL_MODE` (set to `args.mysql_mode`). The template conditions will always evaluate to the `else` branch.

**Fix:** Either pass `DB_MODE` into the template vars before rendering, or update the template to use `MYSQL_MODE`.

### 3.3 — `postgresql.conf.tpl` Uses `DB_MODE` — Same Issue

Same problem as 3.2 but for the PostgreSQL template. `DB_MODE` is never set; `POSTGRES_MODE` is used in the code.

### 3.4 — IP Suffix Assigned Before Sorting

`site_discovery.py` assigns `ip_suffix` incrementally as sites are discovered, but then sorts the list alphabetically at the end. This means `ip_suffix` values are based on filesystem enumeration order, not the final sorted order, producing inconsistent IP assignments across runs if the filesystem returns entries in different orders.

**Fix:** Assign `ip_suffix` values *after* sorting, or compute them from the sorted index.

### 3.5 — `--database-mode` CLI Flag Documented but Code Uses `--mysql-mode` / `--postgres-mode`

The README documents `--database-mode` as a CLI option, but the actual arguments are `--mysql-mode` and `--postgres-mode`. Running `site-builder --database-mode docker` would be an unrecognized argument error.

**Fix:** Update the README to reflect the actual CLI flags, or add a `--database-mode` convenience flag.

### 3.6 — Docker Compose Template Has Invalid YAML Under `else` Branch

In `docker-compose.yml.tpl`, when `ENABLE_DATABASE` is false:

```yaml
{% else %}
            - type: bind
              source: "/var/run/mysqld/mysqld.sock"
              target: "/var/run/mysqld/mysqld.sock"
{% endif %}
```

This `else` branch puts a volume bind entry under a `depends_on` key, which is invalid YAML for docker-compose. The `depends_on` key expects service names, not volume binds.

**Fix:** Move the socket volume bind into the `volumes` section and use the `else` branch of a separate `{% if %}` for volumes, not `depends_on`.

### 3.7 — MariaDB Docker `setup()` Raises If Config File Doesn't Exist Yet

`mariadb_docker.py` `setup()` raises `FileNotFoundError` if `self.config_file` is missing, but `generate_config()` is called later in `__main__.py`. The config file won't exist on a fresh setup, causing `setup()` to fail before `generate_config()` has a chance to create it.

**Fix:** Remove the existence check from `setup()`, or reorder operations in `main()` so config generation happens before `setup()`.

### 3.8 — Same Issue in MariaDB Native `setup()`

`mariadb_native.py` `setup()` has the same premature `FileNotFoundError` check.

### 3.9 — `datetime.utcnow()` Deprecation Warning

`ssl_certificate_manager.py` uses `datetime.utcnow()` which is deprecated since Python 3.12 and emits `DeprecationWarning`. Meanwhile `_certificate_needs_renewal()` already uses `datetime.now(timezone.utc)`.

**Fix:** Replace all `datetime.utcnow()` calls with `datetime.now(timezone.utc)`.

### 3.10 — Ed25519 Key Usage Incompatible with `key_encipherment`

The SSL manager sets `key_encipherment=True` in `KeyUsage`, but Ed25519 keys cannot perform key encipherment (they are signature-only keys). While the `cryptography` library may not reject this, it produces technically invalid certificates.

**Fix:** Set `key_encipherment=False` for Ed25519 keys, or switch to RSA/ECDSA if key encipherment is required.

### 3.11 — `nginx.conf.tpl` Allows TLSv1 and TLSv1.1 for Proxy SSL

```
proxy_ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
```

TLSv1 and TLSv1.1 are deprecated and considered insecure.

**Fix:** Use `TLSv1.2 TLSv1.3` for `proxy_ssl_protocols`.

---

## 4. Design & Architecture Issues

### 4.1 — `lru_cache` on `get_default_runtime()` With Mutable Return Value

`runtime_management.py` uses `@lru_cache()` on `get_default_runtime()`, which returns a `dict` containing a `Path` object. Since dicts are mutable, callers could inadvertently modify the cached result, affecting subsequent calls.

**Fix:** Return a `namedtuple` or `dataclass(frozen=True)` instead of a dict, or return a copy from the cache.

### 4.2 — `ImportError` Fallback with `sys.path.append` in Factories

`manager_factory.py` and `ssl_manager_factory.py` have `except ImportError` blocks that manipulate `sys.path`:

```python
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from database import ...
```

This is fragile and unnecessary since the package is always invoked via `python -m site_builder` or as an installed package. These fallback blocks should be removed.

### 4.3 — Inconsistent Logger Patterns

Some modules use `logging.getLogger(__name__)` at module level, others use `@cached_property` for `self.logger`, and the SSL manager creates its own handler. This inconsistency makes log configuration unpredictable.

**Fix:** Standardize on module-level `logger = logging.getLogger(__name__)` throughout. Remove the custom handler from `SSLCertificateManager.logger`.

### 4.4 — `DockerManager` Created Multiple Times

`_is_docker_installed()` in both `NginxDockerManager` and database Docker managers creates a new `DockerManager()` instance each time. If Docker is not installed, `setup()` creates another instance.

**Fix:** Inject a single shared `DockerManager` instance, or cache it.

### 4.5 — No Nginx Config Test Before Enabling Sites

`NginxNativeManager.reload()` runs `nginx -t` before reloading, which is good. However, there is no validation at the `generate_site_config()` stage. An invalid template could be written and enabled before the reload fails.

**Fix:** Run `nginx -t` after writing all configs and before calling `enable_site()`, or at least before `reload()`.

### 4.6 — `NginxDockerManager.generate_main_config()` Is a No-Op

The method body is `pass`. The docker-compose generation happens in `__main__.py` instead. This breaks the abstraction — the manager should own its configuration lifecycle.

**Fix:** Move docker-compose generation for Nginx into this method.

---

## 5. Template Issues

### 5.1 — Docker-Compose Template Has No PostgreSQL Service

The template only defines a `mariadb` service block. If PostgreSQL is enabled in Docker mode, no corresponding service is rendered.

**Fix:** Add a `{% if ENABLE_POSTGRES_DATABASE %}` block with a PostgreSQL service definition.

### 5.2 — Hardcoded Paths in Templates

The docker-compose template hardcodes paths like `/etc/site-builder/nginx/sites-enabled`, `/etc/site-builder/mysql/...`, `/var/run/mysqld`, and `/mnt/www`. These should use template variables from the configuration.

### 5.3 — `http2` Directive Deprecated in Newer Nginx

The `nginx.conf.tpl` uses `listen 443 ssl http2;` which is deprecated in Nginx ≥ 1.25.1. The `http2` directive is now a separate line.

**Fix:** Use `http2 on;` as a separate directive to support modern Nginx versions.

---

## 6. Packaging & Configuration Issues

### 6.1 — Missing Resources in `package-data`

`pyproject.toml` only includes `resources/lighttpd-php8/*` and `resources/nginx-php8/*`:

```toml
[tool.setuptools.package-data]
site_builder = [
    "templates/*",
    "resources/lighttpd-php8/*",
    "resources/nginx-php8/*",
]
```

The `nginx-py312/`, `nginx-njs24/`, and `nginx-hdnd-php8/` resource directories are not included. The installed package will be missing these runtime images.

**Fix:** Add all resource directories:
```toml
site_builder = [
    "templates/*",
    "resources/lighttpd-php8/*",
    "resources/nginx-php8/*",
    "resources/nginx-py312/*",
    "resources/nginx-njs24/*",
    "resources/nginx-hdnd-php8/*",
]
```

### 6.2 — `requires-python = ">=3.8"` but Uses 3.8+ Incompatible Features

The code uses the walrus operator (`:=`, 3.8+), `cached_property` from `functools` (3.8+), and `match` expressions or `|` union types in some places. The `datetime.utcnow()` deprecation is Python 3.12. However, `cached_property` was added in 3.8, so the minimum version is effectively correct, but should be verified with CI testing.

### 6.3 — Version Duplicated

The version `1.0.1` is defined in both `__init__.py` and `pyproject.toml`. Consider using `dynamic` versioning or a single source of truth.

---

## 7. Code Quality & Style

### 7.1 — Mixed f-string and `%`-style Logging

Some log calls use f-strings:
```python
logger.info(f"Generated new CA password and saved to {password_file}")
```
Others use `%`-style:
```python
logger.info("Generated nginx config for %s", site["name"])
```

`%`-style is preferred for logging because arguments are only formatted if the log level is active, avoiding unnecessary string formatting overhead.

**Fix:** Replace all f-string log calls with `%`-style.

### 7.2 — Broad `except Exception` Handling

Several places catch `except Exception` too broadly (e.g., `_certificate_needs_renewal`, `validate_paths`), which can mask unexpected errors.

**Fix:** Catch specific exceptions where possible.

### 7.3 — Type Annotations Use `Any` for `args`

Every function accepting CLI arguments uses `args: Any`. A `TypedDict` or `dataclass` would provide type safety and IDE support.

### 7.4 — Missing `__all__` in Some `__init__.py` Files

`docker/__init__.py` and `pkgs/__init__.py` define `__all__`, but some re-exports could benefit from being more explicit.

### 7.5 — No Unit Test Suite

The only tests are manual integration scripts (`test_postgres_config_detection.py`, `test_postgres_mock.py`) that run outside of any test framework. There are no `pytest` tests despite `pytest` being listed as a dev dependency.

**Fix:** Create a proper `tests/` directory with pytest-based unit tests, especially for:
- Site discovery and runtime detection
- Configuration persistence (load/save round-trip)
- SSL certificate generation and renewal logic
- Template rendering correctness
- Input validation

---

## 8. README vs. Code Discrepancies

| README States | Actual Code |
|---|---|
| `--database-mode` flag | `--mysql-mode` and `--postgres-mode` (separate flags) |
| MariaDB only | Both MariaDB and PostgreSQL supported |
| SSL certs stored as `.pem` / `.key` in `.cert/` dirs | Internal certs stored as `client.crt` / `client.key` / `client.pem` under proxy SSL path; site `.cert/` discovery looks for `<subdomain>.key` and `<subdomain>.crt` |
| `--renew-crts` flag name | Correct |
| Certificate stored as `<subdomain>.pem` | Discovery checks for `<subdomain>.crt` |

**Fix:** Update the README architecture section to reflect dual database support and correct the SSL certificate file naming.

---

## 9. Summary of Required Fixes (by Priority)

### Critical
1. Template variable mismatch (`ENABLE_DATABASE` vs `ENABLE_MYSQL_DATABASE`/`ENABLE_POSTGRES_DATABASE`, `DB_MODE` vs `MYSQL_MODE`/`POSTGRES_MODE`, `DB_ROOT_PASSWORD` vs `MYSQL_ROOT_PASSWORD`/`POSTGRES_ROOT_PASSWORD`)
2. Invalid YAML in docker-compose template (`depends_on` / volume bind mixing)
3. `setup()` fails on fresh install due to premature config file existence check
4. Missing resource directories in `pyproject.toml` package data

### High
5. SQL injection risk in database manager methods — validate inputs
6. CA password file written without restrictive permissions
7. Config file written without restrictive permissions (contains passwords)
8. IP suffix inconsistency after sort in site discovery
9. Add PostgreSQL service to docker-compose template

### Medium
10. Replace deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`
11. Fix `key_encipherment` incompatibility with Ed25519
12. Update `proxy_ssl_protocols` to exclude TLSv1/TLSv1.1
13. Standardize logging pattern across all modules
14. README / CLI flag discrepancies

### Low
15. Remove `sys.path` manipulation fallbacks in factory modules
16. Replace f-string logging with `%`-style
17. Add proper pytest test suite
18. Consolidate version definition (single source of truth)
19. Return immutable type from cached `get_default_runtime()`
20. Support modern Nginx `http2 on;` directive
