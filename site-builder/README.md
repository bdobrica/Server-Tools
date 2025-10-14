# Site Builder

Site Builder is a Python tool that generates Nginx and Docker configurations for web services with automatic SSL certificate management.

## Features

- Automatic site discovery from web directory structure
- SSL certificate generation and management with custom CA
- Nginx configuration generation (native or Docker mode)
- Database setup and configuration (MariaDB support)
- Docker Compose generation for containerized deployments

## Installation

### From PyPI (when available)

```bash
pip install site-builder
```

### Development Installation

1. Clone the repository:
```bash
git clone https://github.com/bdobrica/Server-Tools.git
cd Server-Tools/site-builder
```

2. Install in development mode:
```bash
pip install -e .
```

Or use the provided setup script:
```bash
./setup-dev.sh
```

### Building from Source

```bash
pip install build
python -m build
pip install dist/site_builder-*.whl
```

## Usage

After installation, you can use the `site-builder` command:

```bash
site-builder --help
```

### Basic Usage

```bash
# Generate configurations for sites in /var/www with default settings
site-builder --web-path /var/www

# Use Docker mode for Nginx
site-builder --nginx-mode docker --web-path /var/www

# Specify custom SSL CA path
site-builder --root-ca-path /etc/ssl/custom-ca --web-path /var/www
```

### Configuration Options

- `--web-path`: Path to web root directory (default: /mnt/www/)
- `--nginx-mode`: Nginx deployment mode - `docker` or `native` (default: native)
- `--database-mode`: Database deployment mode - `docker`, `native`, or `none` (default: native)
- `--root-ca-path`: Path to root CA directory (default: /etc/site-builder/ssl)
- `--nginx-config-path`: Nginx sites-available path (default: /etc/nginx/sites-available)

## Development

The package includes Docker images for web services:
- `lighttpd-php8`: Lightweight web server with PHP 8
- `nginx-php8`: Nginx web server with PHP 8

These are automatically included as package resources and can be used in generated Docker Compose configurations.

## License

MIT License
