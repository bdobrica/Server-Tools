# Site-Builder Testing Environment

This directory contains scripts and documentation for setting up isolated testing environments for the site-builder application. The scripts create Debian chroot environments that allow you to test nginx configurations, database operations, and SSL certificates without affecting your host system.

## 📁 Files Overview

### Main Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup-simple-chroot.sh` | **Recommended** - Creates lightweight chroot | `sudo ./setup-simple-chroot.sh` |
| `setup-chroot.sh` | Full-featured chroot with Docker | `sudo ./setup-chroot.sh` |
| `chroot-run-site-builder.sh` | Run site-builder in chroot | `sudo ./chroot-run-site-builder.sh [args]` |
| `cleanup-chroot.sh` | Clean up chroot environment | `sudo ./cleanup-chroot.sh` |

### Documentation

| File | Description |
|------|-------------|
| `CHROOT_SETUP.md` | Detailed documentation and usage guide |
| `README.md` | This file - quick start guide |

## 🚀 Quick Start

### 1. Create Test Environment
```bash
cd test/
sudo ./setup-simple-chroot.sh
```

This creates a Debian chroot at `/opt/debian-chroot-simple` with:
- ✅ Nginx web server
- ✅ MariaDB database
- ✅ Python 3.11 + pip
- ✅ Development tools
- ✅ Site-builder dependencies

### 2. Test Site-Builder
```bash
# Show available commands
sudo ./chroot-run-site-builder.sh --help

# Check system status
sudo ./chroot-run-site-builder.sh status

# Create a test site
sudo ./chroot-run-site-builder.sh create mysite --domain mysite.local
```

### 3. Manual Access (Optional)
```bash
# Enter chroot environment manually
sudo chroot /opt/debian-chroot-simple /bin/bash

# Or as test user
sudo chroot /opt/debian-chroot-simple /bin/su - testuser
```

### 4. Cleanup When Done
```bash
# Unmount filesystems (keeps chroot for reuse)
sudo ./cleanup-chroot.sh

# Or remove everything
sudo rm -rf /opt/debian-chroot-simple
```

## 📋 Script Details

### `setup-simple-chroot.sh` ⭐ **Recommended**
- **Purpose**: Creates a lightweight, stable chroot environment
- **What it installs**: Nginx, MariaDB, Python, essential tools
- **Pros**: Fast, reliable, fewer dependencies
- **Cons**: No Docker support
- **Best for**: General site-builder testing

### `setup-chroot.sh` 
- **Purpose**: Full-featured chroot with Docker support
- **What it installs**: Everything in simple + Docker
- **Pros**: Complete environment, supports all features
- **Cons**: More complex, potential mount issues
- **Best for**: Advanced testing requiring Docker

### `chroot-run-site-builder.sh`
- **Purpose**: Wrapper to run site-builder commands in chroot
- **Features**:
  - Auto-mounts necessary filesystems
  - Activates Python virtual environment
  - Handles argument passing correctly
  - Preserves mounts for subsequent runs

### `cleanup-chroot.sh`
- **Purpose**: Safe cleanup of chroot environments
- **Features**:
  - Unmounts all filesystems in correct order
  - Option to remove chroot entirely
  - Prevents filesystem corruption

## 🔧 Environment Details

### Chroot Location
- **Simple**: `/opt/debian-chroot-simple`
- **Full**: `/opt/debian-chroot`

### Pre-installed Software
```
Operating System: Debian bookworm (stable)
Web Server:       nginx
Database:         mariadb-server
Python:           3.11 + pip + venv
Development:      build-essential, git, vim, curl
System:           sudo, openssh-client, ca-certificates
```

### Python Dependencies (in venv)
```
mysql-connector-python  # Database connectivity
docker                  # Container management
requests               # HTTP client
pyyaml                 # Configuration files
coloredlogs            # Enhanced logging
jinja2                 # Template engine
cryptography           # SSL/TLS operations
```

### Test User Account
- **Username**: `testuser`
- **Password**: `testpass`
- **Privileges**: sudo access
- **Home**: `/home/testuser`

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Permission denied" errors
```bash
# Make sure scripts are executable
chmod +x *.sh

# Run with sudo
sudo ./setup-simple-chroot.sh
```

#### 2. "No such file or directory" for chroot
```bash
# Check if chroot was created successfully
ls -la /opt/debian-chroot-simple

# If missing, run setup again
sudo ./setup-simple-chroot.sh
```

#### 3. Mount point errors
```bash
# Clean up existing mounts
sudo ./cleanup-chroot.sh

# Check for stuck mounts
cat /proc/mounts | grep chroot

# Force unmount if needed
sudo umount -l /opt/debian-chroot-simple/proc
```

#### 4. Python import errors in chroot
```bash
# Check if dependencies are installed
sudo chroot /opt/debian-chroot-simple /bin/bash -c "
    cd /opt/site-builder && 
    source venv/bin/activate && 
    pip list
"

# Reinstall if needed
sudo chroot /opt/debian-chroot-simple /bin/bash -c "
    cd /opt/site-builder && 
    source venv/bin/activate && 
    pip install mysql-connector-python docker requests pyyaml coloredlogs jinja2 cryptography
"
```

### Recovery Steps

If something goes wrong:

1. **Clean up mounts**:
   ```bash
   sudo ./cleanup-chroot.sh
   ```

2. **Remove broken chroot**:
   ```bash
   sudo rm -rf /opt/debian-chroot-simple
   ```

3. **Start fresh**:
   ```bash
   sudo ./setup-simple-chroot.sh
   ```

## 🎯 Use Cases

### Development Testing
```bash
# Test new site creation
sudo ./chroot-run-site-builder.sh create devsite --php --database --ssl

# Test configuration generation
sudo ./chroot-run-site-builder.sh config --nginx --mysql
```

### Regression Testing
```bash
# Run in clean environment
sudo ./setup-simple-chroot.sh
sudo ./chroot-run-site-builder.sh status
sudo ./chroot-run-site-builder.sh list
```

### Feature Development
```bash
# Manual access for debugging
sudo chroot /opt/debian-chroot-simple /bin/bash
cd /opt/site-builder
source venv/bin/activate
python run.py --help
```

## 📚 Additional Resources

- **Detailed Documentation**: See `CHROOT_SETUP.md` for comprehensive setup guide
- **Site-Builder Source**: Located at `../site-builder/`
- **Chroot Documentation**: `man chroot` for system details

## ⚠️ Important Notes

1. **Root Required**: All chroot operations require sudo/root privileges
2. **Filesystem Safety**: Always use cleanup script before removing chroot
3. **Host Isolation**: Changes in chroot don't affect host system
4. **Persistent Data**: Chroot persists between reboots until removed
5. **Resource Usage**: Chroot shares host kernel but has separate userspace

## 🔄 Workflow Example

Complete testing workflow:

```bash
# 1. Setup
cd test/
sudo ./setup-simple-chroot.sh

# 2. Test
sudo ./chroot-run-site-builder.sh status
sudo ./chroot-run-site-builder.sh create testsite

# 3. Debug (if needed)
sudo chroot /opt/debian-chroot-simple /bin/bash

# 4. Cleanup
sudo ./cleanup-chroot.sh
```

---

**Need help?** Check `CHROOT_SETUP.md` for detailed documentation or create an issue in the repository.
