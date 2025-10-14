#!/bin/bash

# Simple Chroot Setup Script for Testing site-builder
# Creates a minimal Debian environment without Docker (to avoid complexity)

set -e

# Configuration
CHROOT_DIR="/opt/debian-simple-chroot"
DEBIAN_RELEASE="bookworm"
ARCH="amd64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

install_debootstrap() {
    log "Installing debootstrap if not present..."
    if ! command -v debootstrap &> /dev/null; then
        apt-get update
        apt-get install -y debootstrap
    fi
}

cleanup_old_chroot() {
    if [[ -d "$CHROOT_DIR" ]]; then
        warn "Chroot directory already exists. Cleaning up..."
        
        # Force unmount everything
        for mount in $(mount | grep "$CHROOT_DIR" | awk '{print $3}' | sort -r); do
            umount -f "$mount" 2>/dev/null || true
        done
        
        # Wait a moment for processes to exit
        sleep 2
        
        # Remove directory
        rm -rf "$CHROOT_DIR" || {
            warn "Could not remove $CHROOT_DIR completely. Some files may remain."
        }
    fi
}

create_chroot() {
    log "Creating simple Debian chroot environment at $CHROOT_DIR..."
    
    cleanup_old_chroot
    mkdir -p "$CHROOT_DIR"
    
    # Create minimal Debian system
    debootstrap --arch="$ARCH" "$DEBIAN_RELEASE" "$CHROOT_DIR" http://deb.debian.org/debian/
}

setup_chroot_mounts() {
    log "Setting up necessary mount points..."
    
    # Mount essential filesystems
    mount --bind /dev "$CHROOT_DIR/dev"
    mount -t devpts devpts "$CHROOT_DIR/dev/pts"
    mount -t proc proc "$CHROOT_DIR/proc"
    mount -t sysfs sysfs "$CHROOT_DIR/sys"
}

configure_chroot() {
    log "Configuring chroot environment..."
    
    # Copy DNS configuration
    cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf"
    
    # Set up sources.list
    cat > "$CHROOT_DIR/etc/apt/sources.list" << EOF
deb http://deb.debian.org/debian $DEBIAN_RELEASE main contrib non-free-firmware
deb http://deb.debian.org/debian-security/ $DEBIAN_RELEASE-security main contrib non-free-firmware
deb http://deb.debian.org/debian $DEBIAN_RELEASE-updates main contrib non-free-firmware
EOF

    # Configure locales to avoid warnings
    chroot "$CHROOT_DIR" /bin/bash -c "
        export DEBIAN_FRONTEND=noninteractive
        echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
        apt-get update
        apt-get install -y locales
        locale-gen
        echo 'LANG=en_US.UTF-8' > /etc/default/locale
    "

    # Install essential packages
    chroot "$CHROOT_DIR" /bin/bash -c "
        export DEBIAN_FRONTEND=noninteractive
        export LANG=en_US.UTF-8
        apt-get update
        apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            build-essential \
            git \
            vim \
            nano \
            sudo \
            curl \
            wget \
            nginx \
            mariadb-server \
            mariadb-client
    "
}

setup_site_builder_env() {
    log "Setting up site-builder environment..."
    
    # Create a user for testing
    chroot "$CHROOT_DIR" /bin/bash -c "
        useradd -m -s /bin/bash -G sudo testuser
        echo 'testuser:testpass' | chpasswd
        echo 'testuser ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
        chmod 666 /dev/null
    "
    
    # Copy site-builder to chroot
    mkdir -p "$CHROOT_DIR/home/testuser/site-builder"
    mount --rbind "$(dirname "$0")/../site-builder" "$CHROOT_DIR/home/testuser/site-builder"
    chown -R 1000:1000 "$CHROOT_DIR/home/testuser/site-builder"
    
    # Install Python dependencies for site-builder
    chroot "$CHROOT_DIR" /bin/bash -c "
        cd /home/testuser/site-builder
        python3 -m venv ../venv
        . ../venv/bin/activate
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt || true
    "
}

create_helper_scripts() {
    log "Creating helper scripts..."
    
    # Create enter-chroot script
    cat > "/usr/local/bin/enter-simple-chroot" << EOF
#!/bin/bash
CHROOT_DIR="$CHROOT_DIR"

if [[ \$EUID -ne 0 ]]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Create site-builder directory
mkdir -p "\$CHROOT_DIR/home/testuser/site-builder"

# Ensure mounts are active
mount --rbind $(dirname "$0")/../site-builder "\$CHROOT_DIR/home/testuser/site-builder" 2>/dev/null || true
mount --bind /dev "\$CHROOT_DIR/dev" 2>/dev/null || true
mount -t devpts devpts "\$CHROOT_DIR/dev/pts" 2>/dev/null || true
mount -t proc proc "\$CHROOT_DIR/proc" 2>/dev/null || true
mount -t sysfs sysfs "\$CHROOT_DIR/sys" 2>/dev/null || true

# Copy current resolv.conf
cp /etc/resolv.conf "\$CHROOT_DIR/etc/resolv.conf"
cp /etc/hosts "\$CHROOT_DIR/etc/hosts"
cp /etc/hostname "\$CHROOT_DIR/etc/hostname"

# Enter chroot as testuser
export LANG=en_US.UTF-8
chroot "\$CHROOT_DIR" /bin/bash -c "su - testuser"
EOF
    
    chmod +x "/usr/local/bin/enter-simple-chroot"
    
    # Create cleanup script
    cat > "/usr/local/bin/cleanup-simple-chroot" << EOF
#!/bin/bash
CHROOT_DIR="$CHROOT_DIR"

if [[ \$EUID -ne 0 ]]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

echo "Unmounting chroot filesystems..."
for mount in \$(mount | grep "\$CHROOT_DIR" | awk '{print \$3}' | sort -r); do
    umount -f "\$mount" 2>/dev/null || true
done

echo "Do you want to remove the chroot directory? (y/N)"
read -r response
if [[ "\$response" =~ ^[Yy]$ ]]; then
    rm -rf "\$CHROOT_DIR"
    echo "Chroot directory removed."
else
    echo "Chroot directory preserved at \$CHROOT_DIR"
fi
EOF
    
    chmod +x "/usr/local/bin/cleanup-simple-chroot"
}

main() {
    log "Setting up simple Debian chroot environment for site-builder testing..."
    
    check_root
    install_debootstrap
    create_chroot
    setup_chroot_mounts
    configure_chroot
    setup_site_builder_env
    create_helper_scripts
    
    log "Simple chroot environment setup complete!"
    echo
    echo -e "${GREEN}Usage:${NC}"
    echo "  • Enter chroot: sudo enter-simple-chroot"
    echo "  • Cleanup: sudo cleanup-simple-chroot"
    echo
    echo -e "${GREEN}In the chroot environment:${NC}"
    echo "  • User: testuser (password: testpass)"
    echo "  • Site-builder location: /home/testuser/site-builder (if copied)"
    echo "  • Start nginx: sudo systemctl start nginx"
    echo "  • Start mariadb: sudo systemctl start mariadb"
    echo "  • Test site-builder: cd /home/testuser/site-builder && python3 -m pytest"
    echo
    echo -e "${YELLOW}Note:${NC} This is a simple chroot without Docker support."
    echo "Use this for basic testing of your site-builder without container isolation."
}

main "$@"
