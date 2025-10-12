#!/bin/bash

# Cleanup script for the simple chroot environment
# Usage: sudo ./cleanup-chroot.sh

CHROOT_PATH="/opt/debian-chroot-simple"

echo "Cleaning up chroot environment..."

# Unmount filesystems in reverse order
if mountpoint -q "$CHROOT_PATH/dev/pts"; then
    echo "Unmounting $CHROOT_PATH/dev/pts"
    umount "$CHROOT_PATH/dev/pts"
fi

if mountpoint -q "$CHROOT_PATH/dev"; then
    echo "Unmounting $CHROOT_PATH/dev"
    umount "$CHROOT_PATH/dev"
fi

if mountpoint -q "$CHROOT_PATH/sys"; then
    echo "Unmounting $CHROOT_PATH/sys"
    umount "$CHROOT_PATH/sys"
fi

if mountpoint -q "$CHROOT_PATH/proc"; then
    echo "Unmounting $CHROOT_PATH/proc"
    umount "$CHROOT_PATH/proc"
fi

if mountpoint -q "$CHROOT_PATH/tmp"; then
    echo "Unmounting $CHROOT_PATH/tmp"
    umount "$CHROOT_PATH/tmp"
fi

if mountpoint -q "$CHROOT_PATH/opt/site-builder"; then
    echo "Unmounting $CHROOT_PATH/opt/site-builder"
    umount "$CHROOT_PATH/opt/site-builder"
fi

if mountpoint -q "$CHROOT_PATH/home/testuser/site-builder"; then
    echo "Unmounting $CHROOT_PATH/home/testuser/site-builder"
    umount "$CHROOT_PATH/home/testuser/site-builder"
fi

echo "Chroot cleanup complete!"
echo "To remove the chroot entirely, run: sudo rm -rf $CHROOT_PATH"
