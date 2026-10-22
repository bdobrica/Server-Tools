# Changelog

## [1.1.1] - 2026-10-22

### Fixed
- Run PHP-FPM workers as www-data:www-data to match application file ownership and the other runtime templates.

## [1.1.0] - 2026-10-22

### Changed
- Upgrade to Alpine 3.24 and PHP 8.5, requiring PHP 8.5.12 or later to fix CVE-2026-109618 and CVE-2026-109619.
- Use versioned PHP packages, PHP 8.5 configuration paths, and php-fpm85.
