# Code Review — site-builder (Revision 2)

**Reviewed:** 2026-02-15  
**Scope:** All Python source under `site-builder/site_builder/`, templates, `pyproject.toml`, tests, and `README.md`.  
**Previous review:** 2026-02-15 (Revision 1) — all issues addressed except test suite.

---

## 1. Overall Assessment

The project is a well-structured CLI tool for automating multi-site web hosting on bare-metal Linux servers. It provides Nginx reverse-proxy configuration (native or Docker), MariaDB/PostgreSQL database management (native or Docker), automated SSL certificate generation via an internal CA, and auto-detection of PHP, Python, and Node.js applications.

**Strengths:**
- Clean separation of concerns via abstract base classes (`NginxManager`, `DatabaseManager`) with concrete Docker/native implementations.
- Good use of the factory pattern (`manager_factory.py`, `ssl_manager_factory.py`) to decouple creation from usage.
- Persistent configuration via INI file so flags carry forward across runs.
- Modern packaging with `pyproject.toml`, proper entry-point, dynamic versioning from `__init__.__version__`, and `setuptools` back-end.
- Comprehensive README documentation with architecture diagrams, usage examples, and CLI reference.
- Input validation for SQL-facing parameters (`validate_database_name`, `validate_username`, `validate_privileges`) with whitelist-based privilege checking.
- Immutable `RuntimeInfo` NamedTuple returned from cached runtime detection, eliminating cache-mutation risk.
- `config.ini` and `password.txt` files written with `0o600` permissions.
- Correct Ed25519 `KeyUsage` (no `key_encipherment`), modern TLS protocols (`TLSv1.2 TLSv1.3`), and `datetime.now(timezone.utc)` throughout.

---

## 2. Resolved Issues from Revision 1

The following issues from the first review have been confirmed fixed:

| # | Issue | Status |
|---|-------|--------|
| 2.1 | SQL injection in DB managers | **Fixed** — `validate_database_name`, `validate_username`, `validate_privileges` added |
| 2.3 | CA password file missing `chmod 0o600` | **Fixed** — `password_file.chmod(0o600)` added in `validation.py` |
| 2.4 | `config.ini` missing file permissions | **Fixed** — `config_file.chmod(0o600)` added in `config_persistence.py` |
| 3.1 | Template var mismatch (`ENABLE_DATABASE` etc.) | **Fixed** — `ENABLE_DATABASE`, `DB_ROOT_PASSWORD` added to `template_vars`; template updated with separate `ENABLE_MYSQL_DATABASE`/`ENABLE_POSTGRES_DATABASE` blocks |
| 3.2 | `DB_MODE` not set for MariaDB template | **Fixed** — `manager_factory.py` sets `DB_MODE` in per-manager template vars |
| 3.3 | `DB_MODE` not set for PostgreSQL template | **Fixed** — same as above |
| 3.4 | IP suffix assigned before sorting | **Fixed** — `ip_suffix` now assigned after sort in `site_discovery.py` |
| 3.6 | Invalid YAML in docker-compose template | **Fixed** — socket bind moved to `volumes`; `depends_on` uses proper conditionals |
| 3.7 | MariaDB Docker `setup()` premature `FileNotFoundError` | **Fixed** — existence check removed |
| 3.8 | MariaDB Native `setup()` same issue | **Fixed** — existence check removed |
| 3.9 | `datetime.utcnow()` deprecation | **Fixed** — all calls now use `datetime.now(timezone.utc)` |
| 3.10 | Ed25519 incompatible `key_encipherment=True` | **Fixed** — set to `False` |
| 3.11 | TLSv1/TLSv1.1 in proxy SSL protocols | **Fixed** — now `TLSv1.2 TLSv1.3` |
| 4.1 | Mutable dict from `lru_cache` | **Fixed** — returns `RuntimeInfo(NamedTuple)` |
| 4.2 | `sys.path.append` fallback in factories | **Fixed** — removed; direct relative imports only |
| 5.1 | No PostgreSQL service in docker-compose template | **Fixed** — `{% if ENABLE_POSTGRES_DATABASE %}` block added |
| 5.3 | `http2` directive deprecated syntax | **Fixed** — now uses `http2 on;` as separate directive |
| 6.1 | Missing resources in `package-data` | **Fixed** — all resource dirs included |
| 6.3 | Version duplicated in `pyproject.toml` and `__init__.py` | **Fixed** — `pyproject.toml` uses `dynamic = ["version"]` with `version = {attr = "site_builder.__version__"}` |
| 7.1 | Mixed f-string and `%`-style logging | **Fixed** — all logging now uses `%`-style |

---

## 3. Remaining Issues

### 3.1 — Password Visible in Process List (Medium) — Carried from Rev 1

**Files:** `mariadb_docker.py`, `mariadb_native.py`

MariaDB passwords are still passed as command-line arguments (`-p{password}`). On multi-user systems they are visible via `ps aux`. PostgreSQL correctly uses the `PGPASSWORD` environment variable.

**Recommended fix:** Use `--defaults-extra-file` with a temporary credentials file for MariaDB operations.

### 3.2 — Private Keys Written Without Restrictive Permissions (Low) — Carried from Rev 1

**File:** `ssl_certificate_manager.py`

Site private keys (`client.key`) are written with `serialization.NoEncryption()` but no explicit `chmod 0o600` is set on the key file afterward. While the parent directory may be restricted, explicit key file permissions are a defense-in-depth best practice.

**Recommended fix:** Add `proxy_ssl_key.chmod(0o600)` after writing.

### 3.3 — `NginxDockerManager.generate_main_config()` Is Still a No-Op (Low) — Carried from Rev 1

**File:** `nginx_docker.py`

The method body is `pass`. Docker-compose generation for Nginx happens in `__main__.py`. This is functional but breaks the abstraction where managers own their configuration lifecycle.

**Recommended fix:** Move docker-compose Nginx service generation into this method, or document that docker-compose generation is centralized in `main()`.

### 3.4 — Inconsistent Logger Patterns (Low) — Carried from Rev 1

Some modules use module-level `logger = logging.getLogger(__name__)` (e.g., all database managers, `site_discovery.py`, `validation.py`), while others use `@cached_property` for `self.logger` (e.g., `NginxDockerManager`, `NginxNativeManager`, `DockerManager`, `PKGsManager`, `SSLCertificateManager`).

The `SSLCertificateManager.logger` additionally creates its own handler/formatter, which can cause duplicate or inconsistent log output if the root logger is already configured.

**Recommended fix:** Standardize on module-level `logger = logging.getLogger(__name__)` throughout. Remove the custom handler creation in `SSLCertificateManager.logger`.

### 3.5 — `DockerManager` Instantiated Redundantly (Low) — Carried from Rev 1

`_is_docker_installed()` in `NginxDockerManager`, `MariaDBDockerManager`, and `PostgreSQLDockerManager` each create a new `DockerManager()` instance. If Docker is not found, `setup()` creates yet another instance. The `cached_property` values on the first instance are not shared.

**Recommended fix:** Accept a shared `DockerManager` instance via constructor injection, or cache it as a class-level attribute.

### 3.6 — No Nginx Config Test Before Enabling Sites (Low) — Carried from Rev 1

`NginxNativeManager.reload()` correctly runs `nginx -t` before reloading. However, `generate_site_config()` writes and enables configs without any syntax validation. An invalid template could be written and enabled, and the error only surfaces at reload time.

**Recommended fix:** Run `nginx -t` once after all configs are written and enabled but before `reload()`, or validate individually after each write.

### 3.7 — Broad `except Exception` Handlers (Low) — Carried from Rev 1

`_certificate_needs_renewal()` in `ssl_certificate_manager.py` and `validate_paths()` in `validation.py` catch bare `except Exception`, which can mask unexpected errors (e.g., `MemoryError`, `KeyboardInterrupt` is not caught but `SystemExit` scenarios could be).

**Recommended fix:** Catch specific exceptions (`ValueError`, `OSError`, `cryptography.exceptions.InvalidKey`, etc.).

### 3.8 — Type Annotations Use `Any` for `args` (Low) — Carried from Rev 1

Every function accepting CLI arguments uses `args: Any`. A `TypedDict`, `dataclass`, or `Protocol` would improve type safety, IDE support, and documentation.

### 3.9 — No Unit Test Suite (Medium) — Carried from Rev 1

The only tests are manual integration scripts (`test_postgres_config_detection.py`, `test_postgres_mock.py`) at the repository root. There are no `pytest`-based unit tests despite `pytest` being listed as a dev dependency in `pyproject.toml`.

**Recommended fix:** Create a `tests/` directory with pytest-based tests, targeting at minimum:
- **Site discovery**: mock filesystem with `tmp_path`, verify correct site detection, sorting, and IP assignment
- **Runtime detection**: test each entry file type (`index.php`, `index.py`, `index.ts`) and custom `.runtime/Dockerfile`
- **Input validation**: test `validate_database_name`, `validate_username`, `validate_privileges` with valid and malicious inputs
- **Configuration persistence**: round-trip `save_config` → `load_config` to verify all fields survive serialization
- **SSL certificate lifecycle**: generate CA, generate site cert, verify renewal detection
- **Template rendering**: render `nginx.conf.tpl`, `docker-compose.yml.tpl`, `my.cnf.tpl`, `postgresql.conf.tpl` with known vars and validate output structure

---

## 4. README vs. Code Discrepancies (Remaining)

| README States | Actual Code | Severity |
|---|---|---|
| `--database-mode docker` in usage example | No `--database-mode` flag exists; actual flags are `--mysql-mode` and `--postgres-mode` | Medium |
| `--database-mode MODE` in CLI options section | Same — flag does not exist | Medium |
| Architecture diagram shows only "MariaDB" | Code supports both MariaDB and PostgreSQL | Low |
| "Python 3.7+" in Prerequisites | `pyproject.toml` requires `>=3.8`; code uses `cached_property` (3.8+) and walrus operator (3.8+) | Low |
| SSL certificate files listed as `<subdomain>.pem` / `<subdomain>.key` in `.cert/` dirs | Site discovery checks for `<subdomain>.crt` and `<subdomain>.key` (not `.pem`) | Low |
| Project structure shows only `lighttpd-php8/` and `nginx-php8/` under `resources/` | `resources/` also contains `nginx-py312/`, `nginx-njs24/`, `nginx-hdnd-php8/` | Low |
| Deployment modes table shows only MariaDB for Database | PostgreSQL is equally supported | Low |
| Custom Templates section lists only `nginx.conf.tpl`, `docker-compose.yml.tpl`, `my.cnf.tpl` | `postgresql.conf.tpl` is also present | Low |

---

## 5. New Observations (This Revision)

### 5.1 — `create_user()` Password Not Validated (Medium)

While `username` and `database_name` are validated in `create_user()`, the `password` parameter is interpolated directly into the SQL string without validation. A password containing a single quote (`'`) would break the SQL syntax or could be exploited.

**Files:** `mariadb_docker.py`, `mariadb_native.py`, `postgresql_docker.py`, `postgresql_native.py`

```python
f"CREATE USER IF NOT EXISTS '{username}'@'%' IDENTIFIED BY '{password}';"
```

**Recommended fix:** Either validate/escape the password (reject or escape single quotes), or use a mechanism that avoids SQL interpolation for the password (e.g., `--init-file` for MariaDB, or `ALTER USER ... PASSWORD` via a PGPASSWORD-authenticated session for PostgreSQL).

### 5.2 — `PGPASSWORD` Env Var Replaces Entire Environment (Medium)

**Files:** `postgresql_docker.py`, `postgresql_native.py`

PostgreSQL commands pass `env={"PGPASSWORD": self.root_password}` to `subprocess.run()`. This **replaces** the entire environment rather than appending to it. Critical environment variables like `PATH`, `HOME`, `LANG`, etc. are lost, which can cause commands to fail in certain environments.

```python
env = {"PGPASSWORD": self.root_password}
subprocess.run(cmd, check=True, env=env)
```

**Recommended fix:** Merge with the current environment:
```python
import os
env = {**os.environ, "PGPASSWORD": self.root_password}
```

### 5.3 — Docker-Compose Template: Socket Bind When No Database (Low)

In `docker-compose.yml.tpl`, when neither MySQL nor PostgreSQL database is enabled in Docker mode, the template adds a MySQL socket bind volume to every site container:

```yaml
{% if not ENABLE_DATABASE %}
            - type: bind
              source: "/var/run/mysqld/mysqld.sock"
              target: "/var/run/mysqld/mysqld.sock"
{% endif %}
```

This assumes a native MariaDB socket exists at `/var/run/mysqld/mysqld.sock`, which may not be true if the user runs with `--mysql-mode none --postgres-mode none`.

**Recommended fix:** Only add the socket bind when MySQL is in native mode (`MYSQL_MODE == "native"`), and add a similar PostgreSQL socket bind when PostgreSQL is in native mode. Skip entirely when both are `none`.

### 5.4 — Hardcoded Paths in Docker-Compose Template (Low) — Noted in Rev 1

Paths like `/etc/site-builder/nginx/sites-enabled`, `/etc/site-builder/mysql/...`, `/etc/site-builder/postgres/...` are hardcoded. If the user specifies a custom `--site-builder-config-path`, these paths will be wrong.

**Recommended fix:** Pass these paths as template variables derived from the CLI arguments.

### 5.5 — `_set_postgres_password()` Runs `postgres psql` (Low)

**File:** `postgresql_native.py`

```python
cmd = ["postgres", "psql", "-c", f"ALTER USER postgres PASSWORD '{self.root_password}';"]
```

This runs `postgres psql` which is incorrect — `postgres` is the server daemon, not a client wrapper. The correct command is either `sudo -u postgres psql -c ...` (since native PostgreSQL typically uses peer auth for the `postgres` OS user) or `psql -U postgres -c ...` with appropriate authentication.

**Recommended fix:** Use `["sudo", "-u", "postgres", "psql", "-c", ...]` or detect peer authentication mode.

---

## 6. Summary of Remaining Fixes (by Priority)

### Medium
1. **`create_user()` password not validated/escaped** — SQL injection/breakage via single quote in password (§5.1)
2. **`PGPASSWORD` env replaces entire environment** — PostgreSQL commands may fail in restricted environments (§5.2)
3. **No unit test suite** — no pytest tests despite dev dependency (§3.9)
4. **README `--database-mode` discrepancy** — documented flag does not exist (§4)

### Low
5. **MariaDB password visible in process list** — use `--defaults-extra-file` (§3.1)
6. **Private keys missing `chmod 0o600`** — defense-in-depth (§3.2)
7. **`NginxDockerManager.generate_main_config()` no-op** — abstraction leak (§3.3)
8. **Inconsistent logger patterns** — some module-level, some `@cached_property` (§3.4)
9. **`DockerManager` instantiated redundantly** — no caching/sharing (§3.5)
10. **No nginx config test before enabling** — errors only at reload (§3.6)
11. **Broad `except Exception` handlers** — may mask errors (§3.7)
12. **`args: Any` type annotations** — no type safety on CLI args (§3.8)
13. **Docker-Compose socket bind assumes native MySQL exists** — incorrect when `--mysql-mode none` (§5.3)
14. **Hardcoded paths in Docker-Compose template** — breaks custom `--site-builder-config-path` (§5.4)
15. **`_set_postgres_password()` incorrect command** — `postgres psql` instead of `sudo -u postgres psql` (§5.5)
16. **README minor discrepancies** — Python version, cert names, architecture diagram, template list (§4)
