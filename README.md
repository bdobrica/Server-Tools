# Server Tools - Web Server Configuration Package

A comprehensive bare-metal server configuration package for setting up isolated web hosting environments on Debian and RedHat-based distributions. This tool automates the deployment of web services using Docker containers with Nginx reverse proxy and MariaDB database backend.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────┐
│                 Internet                 │
└─────────────────────┬────────────────────┘
                      │
              ┌───────▼────────┐
              │ Nginx Proxy    │ (Native or Docker)
              │ - SSL/TLS      │
              │ - Load Balance │
              └───────┬────────┘
                      │ Self-signed SSL
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ Host A  │   │ Host B  │   │ Host C  │ (Docker Containers)
   │ Docker  │   │ Docker  │   │ Docker  │
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
              ┌───────▼────────┐
              │ MariaDB        │ (Native or Docker)
              │ - Shared DB    │
              │ - Unix Socket  │
              └────────────────┘
```

### Key Features

- **🔒 Security**: SSL/TLS encryption between proxy and containers using self-signed certificates
- **🏠 Isolation**: Each website runs in its own Docker container
- **⚖️ Load Balancing**: Nginx reverse proxy distributes traffic
- **🗄️ Shared Database**: Common MariaDB instance accessible to all containers
- **🚀 Flexibility**: Native or containerized deployment for both proxy and database
- **🧪 Testing**: Comprehensive chroot-based testing environment

## 📁 Project Structure

```
Server-Tools/
├── site-builder/                   # Main configuration package
│   ├── pyproject.toml              # Package configuration
│   ├── requirements.txt            # Python dependencies
│   └── site_builder/               # Main package directory
│       ├── __main__.py             # CLI entry point
│       ├── config_generator/       # Configuration file generators
│       ├── core/                   # Core functionality
│       ├── database/               # Database management
│       ├── docker/                 # Docker container management
│       ├── nginx/                  # Nginx configuration
│       ├── pkgs/                   # Package management
│       ├── resources/              # Docker image definitions
│       │   ├── lighttpd-php8/      # Lighttpd + PHP 8 container
│       │   └── nginx-php8/         # Nginx + PHP 8 container
│       ├── ssl_certificate_manager/# SSL certificate handling
│       └── templates/              # Jinja2 configuration templates
└── test/                           # Testing environment
    ├── setup-chroot.sh             # Full chroot setup
    ├── setup-simple-chroot.sh      # Lightweight chroot setup
    └── chroot-run-site-builder.sh  # Test runner
```

## 🚀 Quick Start

### Prerequisites

- Debian or RedHat-based Linux distribution
- Python 3.7+
- Docker (if using containerized components)
- Root or sudo access

### Installation

#### Option 1: Direct Installation via pip (Recommended)

```bash
pip install git+https://github.com/bdobrica/Server-Tools.git@main#subdirectory=site-builder
```

After installation, the `site-builder` command will be available in your environment:

```bash
site-builder --help
```

#### Option 2: Manual Installation from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bdobrica/Server-Tools.git
   cd Server-Tools
   ```

2. **Install Python dependencies:**
   ```bash
   cd site-builder
   pip install -r requirements.txt
   ```

3. **Run the configuration tool:**
   ```bash
   python -m site-builder --help
   ```

### Basic Usage

```bash
# Generate configurations for discovered websites
site-builder

# Specify custom paths
site-builder \
    --web-path /var/www \
    --nginx-config-path /etc/nginx/sites-available \
    --docker-compose-path /opt/docker/docker-compose.yml

# Use Docker for Nginx and database
site-builder \
    --nginx-mode docker \
    --database-mode docker

# Force SSL certificate renewal
site-builder --renew-crts
```

**Note**: If you installed from source, use `python -m site-builder` instead of `site-builder` in all commands above.

## ⚙️ Configuration Options

### Deployment Modes

| Component | Mode | Description |
|-----------|------|-------------|
| **Nginx** | `native` | System-installed Nginx (default) |
|           | `docker` | Nginx in Docker container |
| **Database** | `native` | System-installed MariaDB (default) |
|              | `docker` | MariaDB in Docker container |
|              | `none` | No database configuration |

### SSL Certificate Management

- **Automatic Generation**: Self-signed certificates for container communication
- **Certificate Authority**: Internal CA for signing certificates
- **Auto-Renewal**: Certificates auto-renew before expiration
- **Customizable Details**: Country, state, organization settings

### Network Configuration

- **IP Range**: Configurable container network (default: 192.168.100.x)
- **SSL Communication**: Encrypted proxy-to-container traffic
- **Unix Sockets**: Database access via shared socket

## 🧪 Testing Environment

The `test/` directory provides a complete chroot-based testing environment:

### Quick Test Setup

```bash
cd test/

# Create lightweight test environment
sudo ./setup-simple-chroot.sh

# Test the configuration
sudo ./chroot-run-site-builder.sh --help
sudo ./chroot-run-site-builder.sh status

# Clean up when done
sudo ./cleanup-chroot.sh
```

### Test Features

- **Isolated Environment**: No impact on host system
- **Pre-configured Services**: Nginx, MariaDB, Python ready to use
- **Realistic Testing**: Full stack testing capabilities
- **Easy Cleanup**: Safe environment removal

## 🐳 Docker Images

### Available Images

1. **lighttpd-php8**: Lightweight web server with PHP 8
   - Based on Alpine Linux
   - Optimized for performance
   - SSL certificate support

2. **nginx-php8**: Nginx with PHP-FPM 8
   - Full-featured web server
   - Advanced configuration options
   - SSL termination capable

### Building Images

```bash
cd site-builder/site_builder/resources/lighttpd-php8
docker build -t lighttpd-php8 .

cd ../nginx-php8
docker build -t nginx-php8 .
```

## 📋 Command Line Options

### Essential Options

```bash
--web-path PATH              # Web root directory (default: /mnt/www/)
--nginx-config-path PATH     # Nginx sites-available path
--docker-compose-path PATH   # Docker compose file location
--nginx-mode MODE           # nginx deployment: native|docker
--database-mode MODE        # database: native|docker|none
```

### SSL Certificate Options

```bash
--root-ca-path PATH         # CA directory (default: /etc/site-builder/ssl)
--root-ca-password PASS     # CA password
--renew-keys               # Force private key renewal
--renew-csrs              # Force CSR renewal  
--renew-crts              # Force certificate renewal
--auto-renew-days N       # Auto-renew within N days (default: 30)
```

### Certificate Details

```bash
--country CODE            # Country code (default: RO)
--state STATE            # State/Province (default: Bucharest)
--organisation ORG       # Organization name
```

### Network Configuration

```bash
--ip-prefix PREFIX       # Container IP prefix (default: 192.168.100)
--ip-start NUMBER       # Starting IP suffix (default: 2)
```

## 🔧 Advanced Configuration

### Custom Templates

The tool uses Jinja2 templates for configuration generation:

- `nginx.conf.tpl`: Nginx virtual host template
- `docker-compose.yml.tpl`: Docker compose template
- `my.cnf.tpl`: MariaDB configuration template

### Site Discovery

The system automatically discovers websites by scanning the web root directory structure and generates appropriate configurations for each discovered site.

### SSL Certificate Workflow

1. **CA Generation**: Creates root Certificate Authority
2. **Key Generation**: Generates private keys for each site
3. **CSR Creation**: Creates Certificate Signing Requests
4. **Certificate Signing**: Signs certificates with internal CA
5. **Auto-Renewal**: Monitors and renews expiring certificates

## 🛠️ Development

### Code Structure

- **Core**: Site discovery, validation, factory patterns
- **Managers**: Specialized managers for Nginx, Docker, Database, SSL
- **Templates**: Jinja2-based configuration templates
- **CLI**: Command-line interface and argument parsing

## 📝 License

This project is open source. Please refer to the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📞 Support

For questions, issues, or contributions, please use the GitHub issue tracker or submit pull requests.

---

**Note**: This tool is designed for system administrators and developers familiar with web server deployment and Docker containerization. Ensure you understand the security implications of running web services before deploying in production environments.
