#!/bin/bash

# Debian Chroot Environment Setup Script
# Creates a minimal Debian environment for testing site-builder

set -e

# Configuration
CHROOT_DIR="/opt/debian-chroot"
DEBIAN_RELEASE="bookworm"  # Latest stable Debian
ARCH="amd64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

create_chroot() {
    log "Creating Debian chroot environment at $CHROOT_DIR..."
    
    if [[ -d "$CHROOT_DIR" ]]; then
        warn "Chroot directory already exists. Remove it? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            log "Unmounting existing chroot filesystems..."
            # Unmount all chroot mount points in reverse order
            umount "$CHROOT_DIR/tmp" 2>/dev/null || true
            umount "$CHROOT_DIR/sys" 2>/dev/null || true
            umount "$CHROOT_DIR/proc" 2>/dev/null || true
            umount "$CHROOT_DIR/dev/pts" 2>/dev/null || true
            umount "$CHROOT_DIR/dev" 2>/dev/null || true
            
            log "Removing existing chroot directory..."
            rm -rf "$CHROOT_DIR"
        else
            error "Aborting. Please remove $CHROOT_DIR manually if you want to recreate it."
        fi
    fi
    
    mkdir -p "$CHROOT_DIR"
    
    # Create minimal Debian system
    debootstrap --arch="$ARCH" "$DEBIAN_RELEASE" "$CHROOT_DIR" http://deb.debian.org/debian/
}

setup_chroot_mounts() {
    log "Setting up necessary mount points..."
    
    # Mount essential filesystems
    mount --bind /dev "$CHROOT_DIR/dev"
    mount -t devpts devpts "$CHROOT_DIR/dev/pts"
    mount --bind /proc "$CHROOT_DIR/proc"
    mount --bind /sys "$CHROOT_DIR/sys"
    mount --bind /tmp "$CHROOT_DIR/tmp"
}

configure_chroot() {
    log "Configuring chroot environment..."
    
    # Copy DNS configuration
    cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf"
    cp /etc/hosts "$CHROOT_DIR/etc/hosts"
    cp /etc/hostname "$CHROOT_DIR/etc/hostname"
    
    # Set up sources.list with all necessary repositories
    cat > "$CHROOT_DIR/etc/apt/sources.list" << EOF
deb http://deb.debian.org/debian $DEBIAN_RELEASE main contrib non-free-firmware
deb-src http://deb.debian.org/debian $DEBIAN_RELEASE main contrib non-free-firmware

deb http://deb.debian.org/debian-security/ $DEBIAN_RELEASE-security main contrib non-free-firmware
deb-src http://deb.debian.org/debian-security/ $DEBIAN_RELEASE-security main contrib non-free-firmware

deb http://deb.debian.org/debian $DEBIAN_RELEASE-updates main contrib non-free-firmware
deb-src http://deb.debian.org/debian $DEBIAN_RELEASE-updates main contrib non-free-firmware
EOF

    # Install essential packages in chroot
    chroot "$CHROOT_DIR" /bin/bash -c "
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release \
            wget \
            software-properties-common \
            python3 \
            python3-pip \
            python3-venv \
            build-essential \
            git \
            vim \
            nano \
            sudo \
            systemd
    "
}

install_docker() {
    log "Installing Docker in chroot..."
    
    chroot "$CHROOT_DIR" /bin/bash -c "
        export DEBIAN_FRONTEND=noninteractive
        
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Add Docker repository
        echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable' | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    "
}

install_nginx() {
    log "Installing Nginx in chroot..."
    
    chroot "$CHROOT_DIR" /bin/bash -c "
        apt-get update
        apt-get install -y nginx nginx-extras
    "
}

install_mysql() {
    log "Installing MariaDB (MySQL) in chroot..."
    
    chroot "$CHROOT_DIR" /bin/bash -c "
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y mariadb-server mariadb-client
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
    mount --rbind "/var/run/docker.sock" "$CHROOT_DIR/var/run/docker.sock" || (
        warn "Docker socket not found or cannot be mounted. Continuing without Docker support."
    )
    mount --rbind "$(dirname "$0")/../site-builder" "$CHROOT_DIR/home/testuser/site-builder"
    chown -R 1000:1000 "$CHROOT_DIR/home/testuser/site-builder"
    
    # Install Python dependencies
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
    cat > "$CHROOT_DIR/enter-chroot.sh" << 'EOF'
#!/bin/bash
# Helper script to enter chroot (run from host)
CHROOT_DIR="/opt/debian-chroot"

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Ensure mounts are active
mount --bind /dev "$CHROOT_DIR/dev" 2>/dev/null || true
mount -t devpts devpts "$CHROOT_DIR/dev/pts" 2>/dev/null || true
mount --bind /proc "$CHROOT_DIR/proc" 2>/dev/null || true
mount --bind /sys "$CHROOT_DIR/sys" 2>/dev/null || true
mount --bind /tmp "$CHROOT_DIR/tmp" 2>/dev/null || true

# Enter chroot as testuser
chroot "$CHROOT_DIR" /bin/bash -c "su - testuser"
EOF
    
    chmod +x "$CHROOT_DIR/enter-chroot.sh"
    cp "$CHROOT_DIR/enter-chroot.sh" /usr/local/bin/enter-chroot
    
    # Create cleanup script
    cat > "/usr/local/bin/cleanup-chroot" << EOF
#!/bin/bash
# Cleanup script to unmount and optionally remove chroot

CHROOT_DIR="$CHROOT_DIR"

if [[ \$EUID -ne 0 ]]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

echo "Unmounting chroot filesystems..."
umount "\$CHROOT_DIR/tmp" 2>/dev/null || true
umount "\$CHROOT_DIR/sys" 2>/dev/null || true
umount "\$CHROOT_DIR/proc" 2>/dev/null || true
umount "\$CHROOT_DIR/dev/pts" 2>/dev/null || true
umount "\$CHROOT_DIR/dev" 2>/dev/null || true

echo "Do you want to remove the chroot directory? (y/N)"
read -r response
if [[ "\$response" =~ ^[Yy]$ ]]; then
    rm -rf "\$CHROOT_DIR"
    echo "Chroot directory removed."
else
    echo "Chroot directory preserved at \$CHROOT_DIR"
fi
EOF
    
    chmod +x /usr/local/bin/cleanup-chroot
}

main() {
    log "Setting up Debian chroot environment for site-builder testing..."
    
    check_root
    install_debootstrap
    create_chroot
    setup_chroot_mounts
    configure_chroot
    install_docker
    install_nginx
    install_mysql
    setup_site_builder_env
    create_helper_scripts
    
    log "Chroot environment setup complete!"
    echo
    echo -e "${GREEN}Usage:${NC}"
    echo "  • Enter chroot: sudo enter-chroot"
    echo "  • Cleanup: sudo cleanup-chroot"
    echo
    echo -e "${GREEN}In the chroot environment:${NC}"
    echo "  • User: testuser (password: testpass)"
    echo "  • Site-builder location: /home/testuser/site-builder"
    echo "  • Start services: sudo systemctl start nginx mariadb docker"
    echo "  • Test site-builder: cd /home/testuser/site-builder && python3 -m pytest"
    echo
    echo -e "${YELLOW}Note:${NC} Docker daemon needs to be started manually in chroot:"
    echo "  sudo dockerd --data-root=/var/lib/docker &"
}

main "$@"
