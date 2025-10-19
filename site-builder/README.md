# Site Builder

Site Builder is a Python tool that generates Nginx and Docker configurations for web services with automatic SSL certificate management.

## Features

- Automatic site discovery from web directory structure
- SSL certificate generation and management with custom CA
- Nginx configuration generation (native or Docker mode)
- Database setup and configuration (MariaDB/MySQL and PostgreSQL support)
- Independent database mode configuration (MySQL and PostgreSQL can run simultaneously)
- Docker Compose generation for containerized deployments
- Factory pattern for clean service manager initialization

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

# Use Docker mode for Nginx and MySQL, native PostgreSQL
site-builder --nginx-mode docker --mysql-mode docker --postgres-mode native --web-path /var/www

# Use only PostgreSQL database in Docker mode, no MySQL
site-builder --mysql-mode none --postgres-mode docker --web-path /var/www

# Specify custom SSL CA path and database passwords
site-builder --root-ca-path /etc/ssl/custom-ca --mysql-root-password mypassword --postgres-root-password pgpassword --web-path /var/www

# Use native mode for all services (default)
site-builder --nginx-mode native --mysql-mode native --postgres-mode native --web-path /var/www

# Docker mode for all services
site-builder --nginx-mode docker --mysql-mode docker --postgres-mode docker --web-path /var/www
```

### Configuration Options

#### Basic Configuration
- `--web-path`: Path to web root directory (default: /mnt/www/)
- `--root-ca-path`: Path to root CA directory (default: /etc/site-builder/ssl)
- `--docker-compose-path`: Docker compose file path (default: /etc/site-builder/docker/docker-compose.yml)

#### Nginx Configuration  
- `--nginx-mode`: Nginx deployment mode - `docker` or `native` (default: native)
- `--nginx-config-path`: Nginx sites-available path (default: /etc/nginx/sites-available)
- `--nginx-enabled-path`: Nginx sites-enabled path (default: /etc/nginx/sites-enabled)

#### Database Configuration
- `--mysql-mode`: MySQL/MariaDB deployment mode - `docker`, `native`, or `none` (default: native)
- `--mysql-config-path`: MySQL configuration path (default: /etc/mysql)
- `--mysql-root-password`: MySQL root password (generated if not provided)
- `--postgres-mode`: PostgreSQL deployment mode - `docker`, `native`, or `none` (default: native)  
- `--postgres-config-path`: PostgreSQL configuration path (default: /etc/postgresql)
- `--postgres-root-password`: PostgreSQL root password (generated if not provided)

#### SSL Certificate Configuration
- `--root-ca-password`: Root CA password (if not provided, will read from password.txt)
- `--renew-keys`: Force renewal of SSL private keys
- `--renew-csrs`: Force renewal of certificate signing requests
- `--renew-crts`: Force renewal of SSL certificates
- `--auto-renew-days`: Auto-renew certificates expiring within N days (default: 30)
- `--country`: Country code for SSL certificates (default: RO)
- `--state`: State/Province for SSL certificates (default: Bucharest)
- `--organisation`: Organisation for SSL certificates (default: Perseus Reverse Proxy)

#### Network Configuration
- `--ip-prefix`: IP prefix for containers (default: 192.168.100)
- `--ip-start`: Starting IP suffix for containers (default: 2)

### Advanced Examples

```bash
# Mixed deployment: Docker databases with native Nginx
site-builder --nginx-mode native --mysql-mode docker --postgres-mode docker --web-path /var/www

# Only MySQL database with SSL certificate renewal
site-builder --mysql-mode native --postgres-mode none --renew-crts --web-path /var/www

# Custom network configuration for Docker containers
site-builder --nginx-mode docker --mysql-mode docker --ip-prefix 10.0.1 --ip-start 10 --web-path /var/www
```

## Architecture

### Factory Pattern
Site Builder uses a factory pattern to create and manage service instances:

- `create_nginx_manager()`: Creates NginxDockerManager or NginxNativeManager
- `create_database_managers()`: Creates database managers for MySQL/PostgreSQL in Docker or native mode
- `create_ssl_manager()`: Creates SSL certificate manager for CA and site certificates

### Database Support
The tool supports multiple database configurations:

- **Independent Mode Selection**: MySQL and PostgreSQL can be configured independently (e.g., MySQL in Docker, PostgreSQL native)
- **Simultaneous Operation**: Both databases can run simultaneously in different modes
- **Dynamic Configuration**: Database configurations are generated based on the selected modes
- **Password Management**: Automatic password generation or use provided passwords

### Service Deployment Modes

#### Native Mode
- Services run directly on the host system
- Uses system package manager installations
- Configuration files placed in standard system locations
- Suitable for dedicated servers

#### Docker Mode  
- Services run in Docker containers
- Automated Docker Compose generation
- Isolated service environments
- Easier deployment and scaling

## Development

### Package Structure
```
site_builder/
├── core/                    # Core functionality and factories
│   ├── manager_factory.py   # Service manager factories
│   ├── site_discovery.py    # Web site auto-discovery
│   └── ssl_manager_factory.py
├── database/               # Database service managers
│   ├── mariadb_docker.py   # MariaDB Docker manager
│   ├── mariadb_native.py   # MariaDB native manager
│   ├── postgresql_docker.py # PostgreSQL Docker manager
│   └── postgresql_native.py # PostgreSQL native manager
├── nginx/                  # Nginx service managers
│   ├── nginx_docker.py     # Nginx Docker manager
│   └── nginx_native.py     # Nginx native manager
└── resources/              # Docker images and templates
    ├── lighttpd-php8/      # Lightweight web server with PHP 8
    ├── nginx-php8/         # Nginx web server with PHP 8
    └── nginx-py312/        # Nginx with Python 3.12
```

### Docker Images
The package includes pre-configured Docker images:
- `lighttpd-php8`: Lightweight web server with PHP 8
- `nginx-php8`: Nginx web server with PHP 8  
- `nginx-py312`: Nginx with Python 3.12 support

These are automatically included as package resources and used in generated Docker Compose configurations.

### Testing
```bash
# Run the included test files
python test_postgresql_simple.py
python test_postgresql_support.py
python test_postgresql.py
```

## Recent Improvements

### Version 2024.10 Updates

1. **Enhanced Database Support**
   - Added full PostgreSQL support alongside existing MariaDB/MySQL
   - Independent database mode configuration (`--mysql-mode` and `--postgres-mode`)
   - Support for simultaneous multi-database deployments

2. **Improved Factory Pattern**
   - Clean separation of service creation logic
   - Flexible configuration path management
   - Better error handling and validation

3. **Configuration Management**
   - Dynamic Docker configuration paths based on `docker-compose-path`
   - Improved template variable management
   - Enhanced logging with detailed service mode reporting

4. **Bug Fixes**
   - Fixed undefined `args.database_mode` reference in main function
   - Corrected hardcoded configuration paths in factory functions
   - Improved path resolution for Docker mode configurations

## License

MIT License
