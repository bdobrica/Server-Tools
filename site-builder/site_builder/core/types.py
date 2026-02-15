"""Type definitions for site-builder."""

from pathlib import Path
from typing import Protocol


class SiteBuilderArgs(Protocol):
    """Protocol defining the structure of CLI arguments.
    
    This protocol provides type safety and IDE support for the arguments
    object passed throughout the application.
    """
    
    # Path configuration
    root_ca_path: Path
    root_ca_password: str
    site_builder_config_path: Path
    web_path: Path
    nginx_config_path: Path
    nginx_enabled_path: Path
    docker_compose_path: Path
    template_path: Path
    mysql_config_path: Path
    postgres_config_path: Path
    
    # Network configuration
    ip_prefix: str
    
    # SSL Certificate configuration
    country: str
    state: str
    organisation: str
    renew_keys: bool
    renew_csrs: bool
    renew_crts: bool
    auto_renew_days: int
    
    # Mode configuration
    nginx_mode: str  # "native" or "docker"
    mysql_mode: str  # "native", "docker", or "none"
    postgres_mode: str  # "native", "docker", or "none"
    
    # Database passwords
    mysql_root_password: str
    postgres_root_password: str
