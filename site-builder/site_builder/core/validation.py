"""Validation utilities for site-builder."""

import logging
import secrets
import sys
from typing import Any

logger = logging.getLogger("site-builder")


def validate_paths(args: Any) -> None:
    """Validate required paths exist."""
    if not args.root_ca_path.exists():
        try:
            args.root_ca_path.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logger.error("Failed to create Root CA path: %s", err)
            sys.exit(1)

    if not args.web_path.exists():
        try:
            args.web_path.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logger.error("Failed to create Web path: %s", err)
            sys.exit(1)

    if not args.template_path.exists():
        try:
            args.template_path.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logger.error("Failed to create Template path: %s", err)
            sys.exit(1)

    # Ensure nginx directories exist
    try:
        args.nginx_config_path.mkdir(parents=True, exist_ok=True)
        args.nginx_enabled_path.mkdir(parents=True, exist_ok=True)
    except Exception as err:
        logger.error("Failed to create nginx directories: %s", err)
        sys.exit(1)

    # Ensure docker compose directory exists
    args.docker_compose_path.parent.mkdir(parents=True, exist_ok=True)


def get_ca_password(args: Any) -> str:
    """Get CA password from argument or file."""
    if args.root_ca_password:
        return args.root_ca_password

    password_file = args.root_ca_path / "password.txt"
    if password_file.exists():
        with password_file.open("r") as fp:
            return fp.read().strip()

    logger.warning("No CA password provided and password.txt not found")
    password = secrets.token_urlsafe(16)
    try:
        with password_file.open("w") as fp:
            fp.write(password)
        logger.info(f"Generated new CA password and saved to {password_file}")
        return password
    except Exception as err:
        logger.error(f"Failed to write CA password to {password_file}: {err}")
        sys.exit(1)
