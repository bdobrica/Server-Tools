import argparse
import logging
from pathlib import Path

import coloredlogs

from . import get_template_path
from .config_generator import ConfigGenerator
from .core import (
    create_database_managers,
    create_nginx_manager,
    create_ssl_manager,
    discover_sites,
    get_ca_password,
    load_config,
    save_config,
    validate_paths,
)

logging.basicConfig(level=logging.INFO)
coloredlogs.install(level=logging.INFO)
logger = logging.getLogger("site-builder")


def parse_arguments():
    """Parse command line arguments."""
    # Load saved configuration first to use as defaults
    # We need to parse --site-builder-config-path first to know where to look for config
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument(
        "--site-builder-config-path",
        type=Path,
        default=Path("/etc/site-builder/"),
        help="Path to site-builder configuration directory (default: /etc/site-builder/)",
    )
    pre_args, _ = pre_parser.parse_known_args()

    # Load saved configuration
    saved_config = load_config(pre_args.site_builder_config_path)

    parser = argparse.ArgumentParser(description="Generate Nginx and Docker configurations for web services")

    # SSL Certificate Authority configuration
    parser.add_argument(
        "--root-ca-path",
        type=Path,
        default=saved_config.get("root_ca_path", Path("/etc/site-builder/ssl")),
        help="Path to root CA directory (default: /etc/site-builder/ssl)",
    )
    parser.add_argument(
        "--root-ca-password",
        type=str,
        default=saved_config.get("root_ca_password"),
        help="Root CA password (if not provided, will read from password.txt)",
    )

    # Paths configuration
    parser.add_argument(
        "--site-builder-config-path",
        type=Path,
        default=saved_config.get("site_builder_config_path", Path("/etc/site-builder/")),
        help="Path to site-builder configuration directory (default: /etc/site-builder/)",
    )
    parser.add_argument(
        "--web-path",
        type=Path,
        default=saved_config.get("web_path", Path("/mnt/www/")),
        help="Path to web root directory (default: /mnt/www/)",
    )
    parser.add_argument(
        "--nginx-config-path",
        type=Path,
        default=saved_config.get("nginx_config_path", Path("/etc/nginx/sites-available")),
        help="Nginx sites-available path (default: /etc/nginx/sites-available)",
    )
    parser.add_argument(
        "--nginx-enabled-path",
        type=Path,
        default=saved_config.get("nginx_enabled_path", Path("/etc/nginx/sites-enabled")),
        help="Nginx sites-enabled path (default: /etc/nginx/sites-enabled)",
    )
    parser.add_argument(
        "--docker-compose-path",
        type=Path,
        default=saved_config.get("docker_compose_path", Path("/etc/site-builder/docker/docker-compose.yml")),
        help="Docker compose file path (default: /etc/site-builder/docker/docker-compose.yml)",
    )
    parser.add_argument(
        "--template-path",
        type=Path,
        default=saved_config.get("template_path", get_template_path()),
        help=f"Path to Jinja2 templates (default: {get_template_path()})",
    )

    # Network configuration
    parser.add_argument(
        "--ip-prefix",
        type=str,
        default=saved_config.get("ip_prefix", "192.168.100"),
        help="IP prefix for containers (default: 192.168.100)",
    )
    parser.add_argument(
        "--ip-start",
        type=int,
        default=saved_config.get("ip_start", 2),
        help="Starting IP suffix for containers (default: 2)",
    )

    # SSL Certificate renewal flags
    parser.add_argument(
        "--renew-keys",
        action="store_true",
        default=saved_config.get("renew_keys", False),
        help="Force renewal of SSL private keys",
    )
    parser.add_argument(
        "--renew-csrs",
        action="store_true",
        default=saved_config.get("renew_csrs", False),
        help="Force renewal of certificate signing requests",
    )
    parser.add_argument(
        "--renew-crts",
        action="store_true",
        default=saved_config.get("renew_crts", False),
        help="Force renewal of SSL certificates",
    )
    parser.add_argument(
        "--auto-renew-days",
        type=int,
        default=saved_config.get("auto_renew_days", 30),
        help="Auto-renew certificates expiring within N days (default: 30)",
    )

    # SSL Certificate details
    parser.add_argument(
        "--country",
        type=str,
        default=saved_config.get("country", "RO"),
        help="Country code for SSL certificates (default: RO)",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=saved_config.get("state", "Bucharest"),
        help="State/Province for SSL certificates (default: Bucharest)",
    )
    parser.add_argument(
        "--organisation",
        type=str,
        default=saved_config.get("organisation", "Perseus Reverse Proxy"),
        help="Organisation for SSL certificates (default: Perseus Reverse Proxy)",
    )

    # Nginx deployment options
    parser.add_argument(
        "--nginx-mode",
        type=str,
        choices=["docker", "native"],
        default=saved_config.get("nginx_mode", "native"),
        help="Nginx deployment mode: docker or native (default: native)",
    )

    # Database deployment options
    parser.add_argument(
        "--mysql-mode",
        type=str,
        choices=["docker", "native", "none"],
        default=saved_config.get("mysql_mode", "native"),
        help="MySQL deployment mode: docker, native, or none (default: native)",
    )
    parser.add_argument(
        "--mysql-config-path",
        type=Path,
        default=saved_config.get("mysql_config_path", Path("/etc/mysql")),
        help="MySQL configuration path (default: /etc/mysql)",
    )
    parser.add_argument(
        "--mysql-root-password",
        type=str,
        default=saved_config.get("mysql_root_password"),
        help="MySQL root password (generated if not provided)",
    )
    parser.add_argument(
        "--postgres-mode",
        type=str,
        choices=["docker", "native", "none"],
        default=saved_config.get("postgres_mode", "native"),
        help="PostgreSQL deployment mode: docker, native, or none (default: native)",
    )
    parser.add_argument(
        "--postgres-config-path",
        type=Path,
        default=saved_config.get("postgres_config_path"),
        help="PostgreSQL configuration path (auto-detected if not provided, typically /etc/postgresql/<version>/main/)",
    )
    parser.add_argument(
        "--postgres-root-password",
        type=str,
        default=saved_config.get("postgres_root_password"),
        help="PostgreSQL root password (generated if not provided)",
    )
    parser.add_argument(
        "--database-root-password",
        type=str,
        default=saved_config.get("database_root_password"),
        help="Database root password (generated if not provided)",
    )

    # Service management options
    parser.add_argument(
        "--skip-service-restart",
        action="store_true",
        default=saved_config.get("skip_service_restart", False),
        help="Skip restarting services after configuration",
    )

    # Output options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=saved_config.get("verbose", False),
        help="Enable verbose output",
    )

    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()

    # Save configuration for future runs
    save_config(args.site_builder_config_path, args)

    validate_paths(args)

    # Get CA password
    ca_password = get_ca_password(args)

    # Initialize SSL certificate manager
    ssl_manager = create_ssl_manager(args, ca_password)

    # Initialize configuration generator
    config_generator = ConfigGenerator(args.template_path)

    # Template variables
    root_ca_crt = args.root_ca_path / "perseus_ca.crt"
    template_vars = {
        "IP_PREFIX": args.ip_prefix,
        "PROXY_SSL_PATH": args.root_ca_path.resolve().as_posix(),
        "ROOT_CA_CRT": root_ca_crt.resolve().as_posix(),
        "MYSQL_MODE": args.mysql_mode,
        "MYSQL_ROOT_PASSWORD": args.mysql_root_password or "generated_password_placeholder",
        "ENABLE_MYSQL_DATABASE": True if args.mysql_mode == "docker" else False,
        "POSTGRES_MODE": args.postgres_mode,
        "POSTGRES_ROOT_PASSWORD": args.postgres_root_password or "generated_password_placeholder",
        "ENABLE_POSTGRES_DATABASE": True if args.postgres_mode == "docker" else False,
        "ENABLE_PROXY": True if args.nginx_mode == "docker" else False,
    }

    # Initialize managers using factory functions
    nginx_manager = create_nginx_manager(args, template_vars)
    database_managers = create_database_managers(args, template_vars)

    # Setup services (install if needed)
    nginx_manager.setup()
    for db_type, db_manager in database_managers.items():
        db_manager.setup()
        # Update template vars with actual database password
        template_vars[f"{db_type.upper()}_ROOT_PASSWORD"] = db_manager.root_password

    # Clean up existing nginx enabled sites
    nginx_manager.cleanup_sites()

    # Discover sites
    sites = discover_sites(args.web_path, args.verbose)

    if not sites:
        logger.warning("No sites found to configure")
        return

    # Generate SSL certificates for each site
    for site in sites:
        ssl_manager.generate_certificates(
            domain=site["domain"],
            subdomain=site["name"],
            renew_keys=args.renew_keys,
            renew_csrs=args.renew_csrs,
            renew_crts=args.renew_crts,
            auto_renew_days=args.auto_renew_days,
        )

    # Generate site configurations
    for site in sites:
        logger.info("Configuring site: %s (TLS: %s)", site["name"], site["use_ssl"])
        nginx_manager.generate_site_config(site, config_generator)
        nginx_manager.enable_site(site["name"])

        if args.verbose:
            logger.info("Generated nginx config for %s", site["name"])

    # Generate docker-compose.yaml
    docker_compose_config = config_generator.render_docker_compose(sites, template_vars)
    try:
        args.docker_compose_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory for docker-compose file: {e}")
        return

    try:
        with args.docker_compose_path.open("w") as fp:
            fp.write(docker_compose_config)
        logger.info("Updated docker-compose.yml with nginx service")
    except Exception as e:
        logger.error(f"Failed to write docker-compose file: {e}")
        return

    # Generate main configuration (docker-compose for docker mode)
    nginx_manager.generate_main_config(sites, config_generator)

    # Generate database configuration
    for database_manager in database_managers.values():
        database_manager.generate_config(config_generator)

    # Start services and reload configuration
    for database_manager in database_managers.values():
        if database_manager and not database_manager.is_running():
            database_manager.start()

    if not nginx_manager.is_running():
        nginx_manager.start()
    elif not args.skip_service_restart:
        nginx_manager.reload()

    # Log configuration summary
    database_modes = []
    if args.mysql_mode != "none":
        database_modes.append(f"mysql:{args.mysql_mode}")
    if args.postgres_mode != "none":
        database_modes.append(f"postgres:{args.postgres_mode}")

    database_str = ",".join(database_modes) if database_modes else "none"

    logger.info(
        "Successfully configured %d sites using nginx:%s database:%s",
        len(sites),
        args.nginx_mode,
        database_str,
    )


if __name__ == "__main__":
    main()
