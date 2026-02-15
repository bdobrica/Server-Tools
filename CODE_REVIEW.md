# Code Review — site-builder (Revision 6)

**Reviewed:** 2026-02-15  
**Scope:** All Python source under `site-builder/site_builder/`, templates, `pyproject.toml`, tests, and `README.md`.  
**Previous reviews:** Revision 1–5 (2026-02-15).

---

## 1. Overall Assessment

The project is a well-structured CLI tool for automating multi-site web hosting on bare-metal Linux servers. It provides Nginx reverse-proxy configuration (native or Docker), MariaDB/PostgreSQL database management (native or Docker), automated SSL certificate generation via an internal CA, and auto-detection of PHP, Python, and Node.js applications.

**Strengths:**
- Clean separation of concerns via abstract base classes (`NginxManager`, `DatabaseManager`) with concrete Docker/native implementations.
- Good use of the factory pattern (`manager_factory.py`, `ssl_manager_factory.py`) to decouple creation from usage.
- Persistent configuration via INI file so flags carry forward across runs.
- Modern packaging with `pyproject.toml`, proper entry-point, dynamic versioning from `__init__.__version__`, and `setuptools` back-end.
- Comprehensive and accurate README documentation with usage examples, CLI reference, and correct resource listings.
- Input validation for SQL-facing parameters (`validate_database_name`, `validate_username`, `validate_privileges`, `validate_password`) with whitelist-based privilege checking.
- Immutable `RuntimeInfo` NamedTuple returned from cached runtime detection, eliminating cache-mutation risk.
- `config.ini` and `password.txt` files written with `0o600` permissions.
- Correct Ed25519 `KeyUsage` (no `key_encipherment`), modern TLS protocols (`TLSv1.2 TLSv1.3`), and `datetime.now(timezone.utc)` throughout.
- `SiteBuilderArgs` Protocol type for CLI arguments, providing type safety and IDE support.
- Shared `DockerManager` instances via class-level `_shared_docker_manager` with constructor injection.
- Docker-compose template uses template variables for paths instead of hardcoded values.
- MariaDB managers avoid password exposure: native uses `--defaults-extra-file`, Docker uses `MYSQL_PWD` env var via `docker compose exec -e`.
- Specific exception types caught instead of broad `except Exception`.
- Consistent module-level `logger = logging.getLogger(__name__)` across all modules.

---

## 2. Resolved Issues from Revision 5

| # | Rev 5 § | Issue | Status |
|---|---------|-------|--------|
| 1 | §4 | README resources listing incomplete (missing nginx-njs24, nginx-hdnd-php8) | **Fixed** — all 5 resource directories now listed in project structure and Docker images sections |
| 2 | §4 | README Docker images section lists only 3 images | **Fixed** — all 5 images documented |
| 3 | §4 | README testing section references wrong test file names | **Fixed** — now correctly lists `test_postgres_config_detection.py` and `test_postgres_mock.py` |

---

## 3. Remaining Issues

### 3.1 — No Nginx Config Test Before Enabling Sites (Low) — Carried from Rev 2

`NginxNativeManager.reload()` correctly runs `nginx -t`, but invalid configs can be written and enabled before the reload check catches them.

### 3.2 — No Unit Test Suite (Medium) — Carried from Rev 2

No `pytest`-based tests exist despite `pytest` being listed as a dev dependency in `pyproject.toml`.

---

## 4. Summary of Remaining Fixes (by Priority)

### Medium
1. **No unit test suite** — no pytest tests despite dev dependency (§3.2)

### Low
2. **No nginx config test before enabling** — errors only surfaced at reload (§3.1)
