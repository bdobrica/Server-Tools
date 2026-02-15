# Server Tools - Web Server Configuration Package

A comprehensive bare-metal server configuration package for setting up isolated web hosting environments on Debian and RedHat-based distributions. This tool automates the deployment of web services using Docker containers with Nginx reverse proxy and MariaDB database backend.

## 🏗️ Architecture Overview

```
flowchart TB
    Internet[Internet]

    Nginx["Nginx Proxy<br/>(Native or Docker)<br/>- SSL/TLS<br/>- Load Balance"]

    PHP["PHP App<br/>Docker"]
    PY["Python<br/>App"]
    NODE["Node.js<br/>App<br/>(Auto-detected Containers)"]

    DB["Database<br/>(MariaDB or PostgreSQL)<br/>(Native or Docker)<br/>- Shared DB<br/>- Unix Socket"]

    Internet --> Nginx

    Nginx -->|"Self-signed SSL"| PHP
    Nginx -->|"Self-signed SSL"| PY
    Nginx -->|"Self-signed SSL"| NODE

    PHP --> DB
    PY --> DB
    NODE --> DB
```

## 📂 Directory Structure & App Detection

Site-builder automatically detects and configures different application types based on your directory structure and files. Applications are organized under `/mnt/www/` using the pattern `<domain>/<subdomain>`:

```
/mnt/www/
├── example.com/
|   ├── .cert/                  # Storage for example.com's SSL certificates
│   │   ├── www.example.com.crt # Server certificate for www.example.com
│   │   └── www.example.com.key # Private key for www.example.com
│   ├── example.com/            # Main website (www.example.com)
│   │   └── index.php           # PHP app (auto-detected)
│   ├── api.example.com/        # API subdomain (api.example.com)
│   │   ├── index.py            # Python app (auto-detected)
│   │   ├── requirements.txt    # Python dependencies
│   │   └── .venv/              # Virtual environment (persistent)
│   ├── app.example.com/        # Application subdomain (app.example.com)
│   │   ├── index.ts            # Node.js/TypeScript app (auto-detected)
│   │   ├── package.json        # Node.js dependencies
│   │   └── .node_modules/      # Dependencies (persistent)
│   └── any.example.com/        # Arbitrary application subdomain
│       └── .runtime/           # Custom runtime
│           └── Dockerfile      # Custom container definition
└── another-site.com/
    ├── .cert/                  # Storage for another-site.com's SSL certificates
    └── www.another-site.com/
        └── index.php           # Another PHP application
```

### 🔍 Automatic App Detection

Site-builder intelligently detects application types based on entry point files:

| **Entry File** | **Detected Runtime** | **Container** | **Description** |
|----------------|---------------------|---------------|-----------------|
| `index.php` | **PHP 8** | `nginx-php8` | Traditional PHP applications with Nginx + PHP-FPM |
| `index.py` | **Python 3.12** | `nginx-py312` | Python applications (FastAPI, Flask, Django) |
| `index.ts` | **Node.js 24** | `nginx-njs24` | TypeScript/Node.js applications with auto-compilation |

**Custom Runtimes**: Place a `Dockerfile` in the `.runtime/` directory to override automatic detection with your own container configuration.

### Key Features

- **� Smart Detection**: Automatically detects PHP, Python, and Node.js applications
- **�🔒 Security**: SSL/TLS encryption between proxy and containers using self-signed certificates
- **🏠 Isolation**: Each website runs in its own Docker container with persistent storage
- **⚖️ Load Balancing**: Nginx reverse proxy distributes traffic across applications
- **🗄️ Shared Database**: Common MariaDB instance accessible to all containers
- **🚀 Flexibility**: Native or containerized deployment for both proxy and database
- **🛠️ Custom Runtimes**: Support for custom Docker containers via `.runtime/` directories
- **📦 Dependency Management**: Persistent storage for Python `.venv` and Node.js `.node_modules`
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
│       │   ├── nginx-hdnd-php8/    # Nginx + PHP 8 + HTML/CSS/JS container
│       │   ├── nginx-njs24/        # Nginx + Node.js 24 container
│       │   ├── nginx-php8/         # Nginx + PHP 8 container
│       │   └── nginx-py312/        # Nginx + Python 3.12 container
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
- Python 3.8+
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
# Scan /mnt/www/ and auto-configure all detected applications
site-builder

# Specify custom web root path (default: /mnt/www/)
site-builder --web-path /var/www

# Use Docker for Nginx and database components
site-builder \
    --nginx-mode docker \
    --mysql-mode docker \
    --postgres-mode docker

# Force SSL certificate renewal for all sites
site-builder --renew-crts

# Custom configuration paths
site-builder \
    --web-path /mnt/www \
    --nginx-config-path /etc/nginx/sites-available \
    --docker-compose-path /opt/docker/docker-compose.yml
```

### Example: Setting Up a Multi-Language Environment

```bash
# 1. Create your directory structure
mkdir -p /mnt/www/example.com/{www,api,app}

# 2. Create application entry points
echo '<?php phpinfo(); ?>' > /mnt/www/example.com/www/index.php
echo 'from fastapi import FastAPI; app = FastAPI()' > /mnt/www/example.com/api/index.py  
echo 'import express from "express"; const app = express()' > /mnt/www/example.com/app/index.ts

# 3. Run site-builder to auto-configure everything
site-builder

# Result: Three containers automatically configured:
# - www.example.com → nginx-php8 (detected PHP)
# - api.example.com → nginx-py312 (detected Python) 
# - app.example.com → nginx-njs24 (detected TypeScript)
```

**Note**: If you installed from source, use `python -m site-builder` instead of `site-builder` in all commands above.

## ⚙️ Configuration Options

### Deployment Modes

| Component | Mode | Description |
|-----------|------|-------------|
| **Nginx** | `native` | System-installed Nginx (default) |
|           | `docker` | Nginx in Docker container |
| **MariaDB** | `native` | System-installed MariaDB (default) |
|             | `docker` | MariaDB in Docker container |
|             | `none` | No MariaDB configuration |
| **PostgreSQL** | `native` | System-installed PostgreSQL |
|                | `docker` | PostgreSQL in Docker container |
|                | `none` | No PostgreSQL configuration (default) |

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

## 🐳 Docker Images & Runtime Environments

### Available Runtime Images

#### 1. **nginx-php8** - PHP Applications
- **Base**: Alpine Linux with Nginx + PHP-FPM 8.3
- **Use Cases**: WordPress, Laravel, Symfony, custom PHP applications
- **Features**: SSL termination, optimized PHP configuration
- **Auto-detected by**: `index.php` presence

#### 2. **nginx-py312** - Python Applications  
- **Base**: Python 3.12 slim with Nginx reverse proxy
- **Use Cases**: FastAPI, Flask, Django applications
- **Features**: Virtual environment support, automatic dependency installation
- **Persistent Storage**: `.venv/` directory for Python packages
- **Auto-detected by**: `index.py` presence

#### 3. **nginx-njs24** - Node.js/TypeScript Applications
- **Base**: Node.js 24 Alpine with Nginx reverse proxy
- **Use Cases**: Express.js, NestJS, React SSR, custom Node.js applications
- **Features**: TypeScript compilation, npm dependency management
- **Persistent Storage**: `.node_modules/` directory for Node.js packages
- **Auto-detected by**: `index.ts` presence

#### 4. **lighttpd-php8** - Lightweight PHP Applications
- **Base**: Alpine Linux with Lighttpd + PHP-FPM 8.3
- **Use Cases**: Simple PHP sites, lightweight applications
- **Features**: Minimal footprint, SSL support

### Building Images

```bash
# PHP Runtime (Nginx + PHP-FPM)
cd site-builder/site_builder/resources/nginx-php8
docker build -t nginx-php8 .

# Python Runtime (Nginx + Python 3.12)
cd ../nginx-py312  
docker build -t nginx-py312 .

# Node.js Runtime (Nginx + Node.js 24)
cd ../nginx-njs24
docker build -t nginx-njs24 .

# Lightweight PHP Runtime
cd ../lighttpd-php8
docker build -t lighttpd-php8 .
```

## 📋 Command Line Options

### Essential Options

```bash
--web-path PATH              # Web root directory (default: /mnt/www/)
--nginx-config-path PATH     # Nginx sites-available path
--docker-compose-path PATH   # Docker compose file location
--nginx-mode MODE           # nginx deployment: native|docker
--mysql-mode MODE           # MySQL/MariaDB: native|docker|none
--postgres-mode MODE        # PostgreSQL: native|docker|none
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
- `postgresql.conf.tpl`: PostgreSQL configuration template

### Site Discovery & Runtime Detection

The system automatically discovers websites by scanning the `/mnt/www/` directory structure and intelligently detects the appropriate runtime environment:

1. **Directory Scanning**: Discovers sites using `<domain>/<subdomain>` pattern
2. **Runtime Detection**: Analyzes entry files (`index.php`, `index.py`, `index.ts`) to determine app type
3. **Custom Runtime Support**: Checks for `.runtime/Dockerfile` for custom container definitions
4. **SSL Certificate Management**: Automatically generates certificates in `.cert/` directories
5. **Dependency Persistence**: Maintains persistent storage for language-specific dependencies

**Detection Priority**:
1. Custom `.runtime/Dockerfile` (highest priority)
2. `index.ts` → Node.js 24 with TypeScript compilation
3. `index.py` → Python 3.12 with FastAPI/Flask support  
4. `index.php` → PHP 8 with Nginx + PHP-FPM (default fallback)

### SSL Certificate Workflow

1. **CA Generation**: Creates root Certificate Authority
2. **Key Generation**: Generates private keys for each site
3. **CSR Creation**: Creates Certificate Signing Requests
4. **Certificate Signing**: Signs certificates with internal CA
5. **Auto-Renewal**: Monitors and renews expiring certificates
6. **Certificate Placement**: Stores certificates in site-specific `.cert/` directories:
   - `<subdomain>.crt` - Server certificate
   - `<subdomain>.key` - Private key  

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
