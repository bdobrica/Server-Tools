# Code Review — site-builder (Revision 3)

**Reviewed:** 2026-02-15  
**Scope:** All Python source under `site-builder/site_builder/`, templates, `pyproject.toml`, tests, and `README.md`.  
**Previous reviews:** Revision 1 (2026-02-15), Revision 2 (2026-02-15).

---

## 1. Overall Assessment

The project is a well-structured CLI tool for automating multi-site web hosting on bare-metal Linux servers. It provides Nginx reverse-proxy configuration (native or Docker), MariaDB/PostgreSQL database management (native or Docker), automated SSL certificate generation via an internal CA, and auto-detection of PHP, Python, and Node.js applications.

**Strengths:**
- Clean separation of concerns via abstract base classes (`NginxManager`, `DatabaseManager`) with concrete Docker/native implementations.
- Good use of the factory pattern (`manager_factory.py`, `ssl_manager_factory.py`) to decouple creation from usage.
- Persistent configuration via INI file so flags carry forward across runs.
- Modern packaging with `pyproject.toml`, proper entry-point, dynamic versioning from `__init__.__version__`, and `setuptools` back-end.
- Comprehensive README documentation with usage examples and CLI reference.
- Input validation for SQL-facing parameters (`validate_database_name`, `validate_username`, `validate_privileges`, `validate_password`) with whitelist-based privilege checking.
- Immutable `RuntimeInfo` NamedTuple returned from cached runtime detection, eliminating cache-mutation risk.
- `config.ini` and `password.txt` files written with `0o600` permissions.
- Correct Ed25519 `KeyUsage` (no `key_encipherment`), modern TLS protocols (`TLSv1.2 TLSv1.3`), and `datetime.now(timezone.utc)` throughout.
- `SiteBuilderArgs` Protocol type for CLI arguments, providing type safety and IDE support.
- Shared `DockerManager` instances via class-level `_shared_docker_manager` with constructor injection.
- Docker-compose template uses template variables for paths instead of hardcoded values.
- MariaDB native manager uses `--defaults-extra-file` with temporary credentials file to avoid password exposure in process list.
- Specific exception types caught instead of broad `except Exception`.

---

## 2. Resolved Issues from Revision 2

The following issues from Revision 2 have been confirmed fixed:

| # | Rev 2 § | Issue | Status |
|---|---------|-------|--------|
| 1 | §3.1 | MariaDB password visible in process list (native) | **Fixed** — `mariadb_native.py` now uses `_create_credentials_file()` context manager with `--defaults-extra-file` |
| 2 | §3.2 | Private keys written without `chmod 0o600` | **Fixed** — `proxy_ssl_key.chmod(0o600)` added after writing in `ssl_certificate_manager.py` |
| 3 | §3.3 | `NginxDockerManager.generate_main_config()` undocumented no-op | **Documented** — method now has a detailed docstring explaining the centralized design decision |
| 4 | §3.4 | `SSLCertificateManager` custom logger handler | **Fixed** — now uses module-level `logger = logging.getLogger(__name__)` |
| 5 | §3.5 | `DockerManager` instantiated redundantly | **Fixed** — all Docker managers use `_shared_docker_manager` class attribute with constructor injection |
| 6 | §3.7 | Broad `except Exception` handlers | **Fixed** — `validation.py` and `ssl_certificate_manager.py` now catch `(OSError, PermissionError)` and `(OSError, ValueError)` respectively |
| 7 | §3.8 | `args: Any` type annotations | **Fixed** — `SiteBuilderArgs(Protocol)` in `core/types.py`; used in factories and validation |
| 8 | §5.1 | `create_user()` password not validated | **Fixed** — `validate_password()` added to `validation.py`; rejects single quotes and empty/overlength passwords; all four DB managers call it |
| 9 | §5.2 | `PGPASSWORD` env replaces entire environment | **Fixed** — both `postgresql_docker.py` and `postgresql_native.py` now use `{**os.environ, "PGPASSWORD": ...}` |
| 10 | §5.3 | Docker-Compose socket bind when no database | **Fixed** — template now uses `{% if MYSQL_MODE == "native" %}` and `{% if POSTGRES_MODE == "native" %}` |
| 11 | §5.4 | Hardcoded paths in Docker-Compose template | **Fixed** — template uses `{{ MYSQL_CONFIG_PATH }}`, `{{ POSTGRES_CONFIG_PATH }}`, `{{ NGINX_SITES_ENABLED_PATH }}`, etc. |
| 12 | §5.5 | `_set_postgres_password()` runs `postgres psql` | **Fixed** — now uses `["sudo", "-u", "postgres", "psql", "-c", ...]` |
| 13 | §4 | README `--database-mode` discrepancy | **Fixed** — README completely rewritten with correct `--mysql-mode` / `--postgres-mode` flags |
| 14 | §4 | README only mentions MariaDB | **Fixed** — README now covers both MariaDB and PostgreSQL throughout |
| 15 | §4 | README Python version "3.7+" | **Fixed** — no longer mentioned; `pyproject.toml` correctly states `>=3.8` |
| 16 | §4 | README SSL cert naming `.pem` vs `.crt` | **Fixed** — no longer has incorrect naming |
| 17 | §4 | README deployment modes table MariaDB-only | **Fixed** — table removed; both databases documented |

---

## 3. Remaining Issues

### 3.1 — `nginx_docker.py` Missing `Optional` Import (High — Runtime Crash)

**File:** `nginx_docker.py`

The class uses `Optional[DockerManager]` on lines 19 and 25, but `Optional` is not imported. The import on line 6 is:
```python
from typing import Any, Dict, List
```

This will cause a `NameError: name 'Optional' is not defined` when the module is imported in Docker mode.

**Fix:** Change to `from typing import Any, Dict, List, Optional`.

### 3.2 — `postgresql_docker.py` `setup()` Has Orphaned Duplicate Code (High — Syntax Error)

**File:** `postgresql_docker.py` (around line 117)

The `setup()` method appears to have leftover code from a previous version appended after the fixed implementation:

```python
def setup(self) -> None:
    """Set up Docker-based PostgreSQL service."""
    if not self._is_docker_installed():
        logger.info("Docker not found, installing...")
        self.docker_manager.setup()

    # Configuration will be generated later by generate_config()
    logger.info("Docker-based PostgreSQL manager setup complete")
        docker_manager = DockerManager()        # ← orphaned code
        docker_manager.setup()
    ...
```

The indented block after `logger.info(...)` is syntactically invalid and will cause an `IndentationError` on module import.

**Fix:** Remove the orphaned code block (lines starting with `docker_manager = DockerManager()` through the end of the old `setup()` body).

### 3.3 — `docker_manager.py` Uses `self.logger` But Has No Logger Property (Medium — Runtime Crash)

**File:** `docker_manager.py`

`_setup_debian()` (line 48) and `_setup_redhat()` (line 99) use `self.logger.info(...)`, but `DockerManager` defines no `logger` instance attribute or `@cached_property`. The module-level `logger` exists but is not referenced. This will cause `AttributeError: 'DockerManager' object has no attribute 'logger'` when Docker is being installed.

Additionally, `logger = logging.getLogger(__name__)` is duplicated on lines 11 and 14.

**Fix:** Replace all `self.logger` calls with module-level `logger` calls, and remove the duplicate logger line.

### 3.4 — `nginx_docker.py` `generate_site_config()` Uses `self.logger` (Medium — Runtime Crash)

**File:** `nginx_docker.py` (line 149)

```python
self.logger.info("Generated nginx config for %s", site["name"])
```

The base class `NginxManager` has no `logger` property, and the module-level `logger` is not used. This will cause `AttributeError` when generating site configs in Docker mode.

**Fix:** Change `self.logger.info(...)` to `logger.info(...)`.

### 3.5 — `pkgs_manager.py` Duplicate Logger Definition (Low)

**File:** `pkgs_manager.py` (lines 9 and 11)

```python
logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)
```

Harmless but indicates an incomplete cleanup from the logger consolidation.

**Fix:** Remove the duplicate line.

### 3.6 — `mariadb_docker.py` Still Uses `-p{password}` on Command Line (Low)

**File:** `mariadb_docker.py`

While `mariadb_native.py` was fixed with `_create_credentials_file()`, the Docker variant still passes `-p{self.root_password}` as a `docker compose exec` argument. The password is visible in the host's process list via `ps aux`.

**Fix:** Consider using `docker compose exec -e MYSQL_PWD=... -T mariadb mysql -uroot -e ...` to pass the password via environment variable (which is not visible in `ps`), or use `--defaults-extra-file` inside the container.

### 3.7 — No Nginx Config Test Before Enabling Sites (Low) — Carried from Rev 2

Same as Rev 2 §3.6. `NginxNativeManager.reload()` correctly runs `nginx -t`, but invalid configs can be written and enabled before the reload check catches them.

### 3.8 — No Unit Test Suite (Medium) — Carried from Rev 2

Same as Rev 2 §3.9. No `pytest`-based tests exist despite `pytest` being listed as a dev dependency.

---

## 4. README vs. Code Discrepancies (Remaining)

| README States | Actual Code | Severity |
|---|---|---|
| Project structure lists `lighttpd-php8/`, `nginx-php8/`, `nginx-py312/` under resources | `resources/` also contains `nginx-njs24/` and `nginx-hdnd-php8/` | Low |
| Docker images section lists only 3 images (lighttpd-php8, nginx-php8, nginx-py312) | 5 images exist including nginx-njs24 and nginx-hdnd-php8 | Low |
| Testing section references `test_postgresql_simple.py`, `test_postgresql_support.py`, `test_postgresql.py` | Actual test files are `test_postgres_config_detection.py` and `test_postgres_mock.py` | Low |

---

## 5. Summary of Remaining Fixes (by Priority)

### High (Runtime Crashes)
1. **`nginx_docker.py` missing `Optional` import** — `NameError` on import in Docker mode (§3.1)
2. **`postgresql_docker.py` orphaned code in `setup()`** — `IndentationError` on import (§3.2)

### Medium (Runtime Crashes Under Specific Conditions)
3. **`docker_manager.py` uses `self.logger`** — `AttributeError` when Docker is being installed (§3.3)
4. **`nginx_docker.py` uses `self.logger`** — `AttributeError` when generating site configs in Docker mode (§3.4)
5. **No unit test suite** — no pytest tests despite dev dependency (§3.8)

### Low
6. **`pkgs_manager.py` duplicate logger** — cosmetic (§3.5)
7. **`mariadb_docker.py` password on command line** — `-p{password}` visible in process list (§3.6)
8. **No nginx config test before enabling** — errors only at reload (§3.7)
9. **README incomplete resource listing and incorrect test file names** (§4)
