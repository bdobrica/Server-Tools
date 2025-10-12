# Debian Chroot Environment for Site-Builder Testing

## Overview

This setup provides a isolated Debian chroot environment where you can test your site-builder application without interfering with your main OS packages. The environment includes Nginx, MariaDB, Python, and all necessary development tools.

## Files Created

### 1. `setup-simple-chroot.sh`
- Creates a Debian bookworm chroot environment at `/opt/debian-chroot-simple`
- Installs essential packages: nginx, mariadb-server, python3, build tools, etc.
- Sets up a test user account with sudo privileges
- Configures locale and basic environment

### 2. `chroot-run-site-builder.sh`
- Wrapper script to run site-builder within the chroot environment
- Automatically mounts necessary filesystems (/proc, /sys, /dev)
- Handles argument passing correctly to the site-builder
- Activates the Python virtual environment automatically

### 3. `cleanup-chroot.sh`
- Safely unmounts all filesystems from the chroot
- Provides option to completely remove the chroot environment

### 4. `run.py` (in site-builder/)
- Standalone runner for site-builder that works in chroot
- Fixes import issues with relative imports
- Provides all site-builder functionality

## Usage

### Initial Setup
```bash
# Create the chroot environment (run once)
sudo ./setup-simple-chroot.sh
```

### Running Site-Builder
```bash
# Show help
sudo ./chroot-run-site-builder.sh --help

# Check system status
sudo ./chroot-run-site-builder.sh status

# Create a new site
sudo ./chroot-run-site-builder.sh create mysite --domain mysite.local

# List existing sites
sudo ./chroot-run-site-builder.sh list

# Remove a site
sudo ./chroot-run-site-builder.sh remove mysite
```

### Manual Chroot Access
```bash
# Enter the chroot environment manually
sudo chroot /opt/debian-chroot-simple /bin/bash

# Or enter as the test user
sudo chroot /opt/debian-chroot-simple /bin/su - testuser
```

### Cleanup
```bash
# Unmount filesystems (keeps chroot for reuse)
sudo ./cleanup-chroot.sh

# Remove chroot entirely
sudo rm -rf /opt/debian-chroot-simple
```

## Environment Details

### Installed Packages
- **Web Server**: nginx
- **Database**: mariadb-server (MariaDB/MySQL)
- **Python**: python3.11 with pip, venv, dev tools
- **Development**: build-essential, git, curl, wget, vim
- **System**: sudo, openssh-client, ca-certificates

### Python Environment
- Virtual environment at `/opt/site-builder/venv`
- Installed packages:
  - mysql-connector-python
  - docker
  - requests
  - pyyaml
  - coloredlogs
  - jinja2
  - cryptography

### Directory Structure
```
/opt/debian-chroot-simple/
├── opt/site-builder/          # Your site-builder application
│   ├── venv/                  # Python virtual environment
│   └── run.py                 # Chroot-compatible runner
├── home/testuser/             # Test user home directory
└── [standard Debian filesystem]
```

## Benefits

1. **Isolation**: Complete separation from host OS packages
2. **Clean Testing**: Fresh environment for reproducible tests
3. **Safety**: No risk of breaking host system configuration
4. **Flexibility**: Easy to reset or recreate the environment
5. **Authenticity**: Real Debian environment, not containers

## Notes

- The chroot uses Debian bookworm (latest stable)
- Services (nginx, mariadb) are installed but may need configuration
- Docker is not included in the simple version to avoid complexity
- The environment persists between reboots
- You can safely test site-builder features without affecting your main system

## Troubleshooting

### If site-builder commands fail:
1. Check that all Python packages are installed in the venv
2. Verify the chroot environment is properly mounted
3. Ensure site-builder code is copied to `/opt/debian-chroot-simple/opt/site-builder`

### If filesystem errors occur:
1. Run `sudo ./cleanup-chroot.sh` to unmount filesystems
2. Check `/proc/mounts` for stuck mounts
3. Recreate the chroot if necessary

### Permission issues:
1. All chroot operations require sudo
2. Files in chroot are owned by root by default
3. Use the testuser account for non-privileged operations
