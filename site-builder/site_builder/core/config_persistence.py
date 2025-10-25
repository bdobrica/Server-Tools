"""Configuration persistence functionality for site-builder."""

import argparse
import configparser
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("site-builder")


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from config.ini file."""
    from .. import get_template_path
    
    config_file = config_path / "config.ini"
    config = configparser.ConfigParser()

    if config_file.exists():
        config.read(config_file)
        logger.info(f"Loaded configuration from {config_file}")
    else:
        logger.info(f"No configuration file found at {config_file}, using defaults")

    # Convert config to dictionary with proper type conversion
    config_dict = {}

    # SSL Certificate Authority configuration
    ssl_section = "ssl_certificate_authority"
    if config.has_section(ssl_section):
        section = config[ssl_section]
        config_dict.update(
            {
                "root_ca_path": Path(section.get("root_ca_path", "/etc/site-builder/ssl")),
                "root_ca_password": section.get("root_ca_password"),
            }
        )

    # Paths configuration
    paths_section = "paths"
    if config.has_section(paths_section):
        section = config[paths_section]
        config_dict.update(
            {
                "site_builder_config_path": Path(section.get("site_builder_config_path", "/etc/site-builder/")),
                "web_path": Path(section.get("web_path", "/mnt/www/")),
                "nginx_config_path": Path(section.get("nginx_config_path", "/etc/nginx/sites-available")),
                "nginx_enabled_path": Path(section.get("nginx_enabled_path", "/etc/nginx/sites-enabled")),
                "docker_compose_path": Path(
                    section.get("docker_compose_path", "/etc/site-builder/docker/docker-compose.yml")
                ),
                "template_path": Path(section.get("template_path", str(get_template_path()))),
            }
        )

    # Network configuration
    network_section = "network"
    if config.has_section(network_section):
        section = config[network_section]
        config_dict.update(
            {
                "ip_prefix": section.get("ip_prefix", "192.168.100"),
                "ip_start": section.getint("ip_start", 2),
            }
        )

    # SSL Certificate renewal flags
    ssl_renewal_section = "ssl_renewal"
    if config.has_section(ssl_renewal_section):
        section = config[ssl_renewal_section]
        config_dict.update(
            {
                "renew_keys": section.getboolean("renew_keys", False),
                "renew_csrs": section.getboolean("renew_csrs", False),
                "renew_crts": section.getboolean("renew_crts", False),
                "auto_renew_days": section.getint("auto_renew_days", 30),
            }
        )

    # SSL Certificate details
    ssl_details_section = "ssl_details"
    if config.has_section(ssl_details_section):
        section = config[ssl_details_section]
        config_dict.update(
            {
                "country": section.get("country", "RO"),
                "state": section.get("state", "Bucharest"),
                "organisation": section.get("organisation", "Perseus Reverse Proxy"),
            }
        )

    # Nginx deployment options
    nginx_section = "nginx"
    if config.has_section(nginx_section):
        section = config[nginx_section]
        config_dict.update(
            {
                "nginx_mode": section.get("nginx_mode", "native"),
            }
        )

    # Database deployment options
    database_section = "database"
    if config.has_section(database_section):
        section = config[database_section]
        config_dict.update(
            {
                "mysql_mode": section.get("mysql_mode", "native"),
                "mysql_config_path": Path(section.get("mysql_config_path", "/etc/mysql")),
                "mysql_root_password": section.get("mysql_root_password"),
                "postgres_mode": section.get("postgres_mode", "native"),
                "postgres_config_path": (
                    Path(postgres_path) if (postgres_path := section.get("postgres_config_path")) else None
                ),
                "postgres_root_password": section.get("postgres_root_password"),
                "database_root_password": section.get("database_root_password"),
            }
        )

    # Service management options
    service_section = "service_management"
    if config.has_section(service_section):
        section = config[service_section]
        config_dict.update(
            {
                "skip_service_restart": section.getboolean("skip_service_restart", False),
            }
        )

    # Output options
    output_section = "output"
    if config.has_section(output_section):
        section = config[output_section]
        config_dict.update(
            {
                "verbose": section.getboolean("verbose", False),
            }
        )

    return config_dict


def save_config(config_path: Path, args: argparse.Namespace) -> None:
    """Save configuration to config.ini file."""
    config_file = config_path / "config.ini"
    config = configparser.ConfigParser()

    # SSL Certificate Authority configuration
    config.add_section("ssl_certificate_authority")
    config["ssl_certificate_authority"]["root_ca_path"] = str(args.root_ca_path)
    if args.root_ca_password:
        config["ssl_certificate_authority"]["root_ca_password"] = args.root_ca_password

    # Paths configuration
    config.add_section("paths")
    config["paths"]["site_builder_config_path"] = str(args.site_builder_config_path)
    config["paths"]["web_path"] = str(args.web_path)
    config["paths"]["nginx_config_path"] = str(args.nginx_config_path)
    config["paths"]["nginx_enabled_path"] = str(args.nginx_enabled_path)
    config["paths"]["docker_compose_path"] = str(args.docker_compose_path)
    config["paths"]["template_path"] = str(args.template_path)

    # Network configuration
    config.add_section("network")
    config["network"]["ip_prefix"] = args.ip_prefix
    config["network"]["ip_start"] = str(args.ip_start)

    # SSL Certificate renewal flags
    config.add_section("ssl_renewal")
    config["ssl_renewal"]["renew_keys"] = str(args.renew_keys)
    config["ssl_renewal"]["renew_csrs"] = str(args.renew_csrs)
    config["ssl_renewal"]["renew_crts"] = str(args.renew_crts)
    config["ssl_renewal"]["auto_renew_days"] = str(args.auto_renew_days)

    # SSL Certificate details
    config.add_section("ssl_details")
    config["ssl_details"]["country"] = args.country
    config["ssl_details"]["state"] = args.state
    config["ssl_details"]["organisation"] = args.organisation

    # Nginx deployment options
    config.add_section("nginx")
    config["nginx"]["nginx_mode"] = args.nginx_mode

    # Database deployment options
    config.add_section("database")
    config["database"]["mysql_mode"] = args.mysql_mode
    config["database"]["mysql_config_path"] = str(args.mysql_config_path)
    if args.mysql_root_password:
        config["database"]["mysql_root_password"] = args.mysql_root_password
    config["database"]["postgres_mode"] = args.postgres_mode
    if args.postgres_config_path:
        config["database"]["postgres_config_path"] = str(args.postgres_config_path)
    if args.postgres_root_password:
        config["database"]["postgres_root_password"] = args.postgres_root_password
    if args.database_root_password:
        config["database"]["database_root_password"] = args.database_root_password

    # Service management options
    config.add_section("service_management")
    config["service_management"]["skip_service_restart"] = str(args.skip_service_restart)

    # Output options
    config.add_section("output")
    config["output"]["verbose"] = str(args.verbose)

    # Ensure config directory exists
    config_path.mkdir(parents=True, exist_ok=True)

    # Write configuration file
    try:
        with config_file.open("w") as f:
            config.write(f)
        logger.info(f"Saved configuration to {config_file}")
    except Exception as e:
        logger.error(f"Failed to save configuration to {config_file}: {e}")
