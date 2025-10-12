#!/bin/bash

# Simple wrapper to run site-builder in chroot environment
# Usage: sudo ./chroot-run-site-builder.sh [site-builder arguments]

CHROOT_PATH="/opt/debian-chroot-simple"
SITE_BUILDER_PATH="/opt/site-builder"

# Check if chroot exists
if [ ! -d "$CHROOT_PATH" ]; then
    echo "Error: Chroot environment not found at $CHROOT_PATH"
    echo "Please run setup-simple-chroot.sh first"
    exit 1
fi

# Mount necessary filesystems for chroot if not already mounted
if ! mountpoint -q "$CHROOT_PATH/proc"; then
    mount -t proc proc "$CHROOT_PATH/proc"
fi

if ! mountpoint -q "$CHROOT_PATH/sys"; then
    mount -t sysfs sysfs "$CHROOT_PATH/sys"
fi

if ! mountpoint -q "$CHROOT_PATH/dev"; then
    mount --bind /dev "$CHROOT_PATH/dev"
fi

if ! mountpoint -q "$SITE_BUILDER_PATH"; then
    mount --rbind "$(dirname "$0")/../site-builder" "$SITE_BUILDER_PATH"
fi

# Create a temporary script with the command to run
TEMP_SCRIPT="/tmp/chroot_run_$$"
cat > "$TEMP_SCRIPT" << EOF
#!/bin/bash
cd $SITE_BUILDER_PATH
source venv/bin/activate
python run.py "\$@"
EOF

chmod +x "$TEMP_SCRIPT"
cp "$TEMP_SCRIPT" "$CHROOT_PATH/tmp/"

# Run site-builder in chroot
chroot "$CHROOT_PATH" "/tmp/$(basename "$TEMP_SCRIPT")" "$@"

# Cleanup
rm -f "$TEMP_SCRIPT" "$CHROOT_PATH/tmp/$(basename "$TEMP_SCRIPT")"

# Note: We keep mounts active for subsequent uses
# To cleanup mounts, run: sudo ./cleanup-chroot.sh
