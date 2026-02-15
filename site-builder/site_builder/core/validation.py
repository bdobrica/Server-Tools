"""Validation utilities for site-builder."""

import logging
import re
import secrets
import sys
from typing import Any

logger = logging.getLogger("site-builder")


# Allowed SQL privileges (whitelist)
ALLOWED_PRIVILEGES = {
    "ALL",
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "DROP",
    "ALTER",
    "INDEX",
    "GRANT",
    "REFERENCES",
    "CREATE VIEW",
    "SHOW VIEW",
    "CREATE ROUTINE",
    "ALTER ROUTINE",
    "EXECUTE",
    "TRIGGER",
}


def validate_database_name(name: str) -> str:
    """
    Validate database name to prevent SQL injection.
    
    Allows only alphanumeric characters, underscores, and hyphens.
    Max length 64 characters (MySQL/PostgreSQL limit).
    
    Args:
        name: Database name to validate
        
    Returns:
        The validated name
        
    Raises:
        ValueError: If name contains invalid characters
    """
    if not name:
        raise ValueError("Database name cannot be empty")
    
    if len(name) > 64:
        raise ValueError(f"Database name too long (max 64 characters): {name}")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError(f"Invalid database name (only alphanumeric, underscore, hyphen allowed): {name}")
    
    return name


def validate_username(username: str) -> str:
    """
    Validate database username to prevent SQL injection.
    
    Allows only alphanumeric characters, underscores, and hyphens.
    Max length 32 characters (MySQL limit, PostgreSQL is 63).
    
    Args:
        username: Username to validate
        
    Returns:
        The validated username
        
    Raises:
        ValueError: If username contains invalid characters
    """
    if not username:
        raise ValueError("Username cannot be empty")
    
    if len(username) > 32:
        raise ValueError(f"Username too long (max 32 characters): {username}")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValueError(f"Invalid username (only alphanumeric, underscore, hyphen allowed): {username}")
    
    return username


def validate_privileges(privileges: str) -> str:
    """
    Validate SQL privileges against whitelist to prevent SQL injection.
    
    Args:
        privileges: Privilege string (e.g., "ALL", "SELECT", "SELECT, INSERT")
        
    Returns:
        The validated privileges string
        
    Raises:
        ValueError: If privileges contain invalid values
    """
    if not privileges:
        raise ValueError("Privileges cannot be empty")
    
    # Handle multiple comma-separated privileges
    priv_list = [p.strip().upper() for p in privileges.split(',')]
    
    for priv in priv_list:
        if priv not in ALLOWED_PRIVILEGES:
            raise ValueError(f"Invalid privilege '{priv}'. Allowed: {', '.join(sorted(ALLOWED_PRIVILEGES))}")
    
    return ', '.join(priv_list)


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
        # Set restrictive permissions (read/write for owner only)
        password_file.chmod(0o600)
        logger.info("Generated new CA password and saved to %s", password_file)
        return password
    except Exception as err:
        logger.error("Failed to write CA password to %s: %s", password_file, err)
        sys.exit(1)
