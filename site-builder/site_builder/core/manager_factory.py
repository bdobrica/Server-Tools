"""Manager factories for site-builder."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from ..database import (
        MariaDBDockerManager,
        MariaDBNativeManager,
        PostgreSQLDockerManager,
        PostgreSQLNativeManager,
    )
    from ..nginx import NginxDockerManager, NginxNativeManager
except ImportError:
    # Fallback for direct execution
    import sys

    sys.path.append(str(Path(__file__).parent.parent))
    from database import (
        MariaDBDockerManager,
        MariaDBNativeManager,
        PostgreSQLDockerManager,
        PostgreSQLNativeManager,
    )
    from nginx import NginxDockerManager, NginxNativeManager


def create_nginx_manager(args: Any, template_vars: Dict[str, Any]) -> Union[NginxDockerManager, NginxNativeManager]:
    """Create and configure Nginx manager based on mode."""
    if args.nginx_mode == "docker":
        # Use the docker-compose directory as parent for nginx configs
        nginx_config_path = args.docker_compose_path.parent / "nginx"
        return NginxDockerManager(
            config_path=nginx_config_path, template_vars=template_vars, docker_compose_path=args.docker_compose_path
        )
    else:  # native mode
        return NginxNativeManager(
            config_path=args.root_ca_path,  # Not used for native, but required
            template_vars=template_vars,
            nginx_config_path=args.nginx_config_path,
            nginx_enabled_path=args.nginx_enabled_path,
        )


def _create_mysql_manager(
    args: Any, template_vars: Dict[str, Any]
) -> Optional[Union[MariaDBDockerManager, MariaDBNativeManager]]:
    """Create and configure MySQL manager based on mode."""
    if args.mysql_mode == "none":
        return None

    if args.mysql_mode == "docker":
        # Use the docker-compose directory as parent for database configs
        mysql_config_path = args.docker_compose_path.parent / "mysql"
        return MariaDBDockerManager(
            config_path=mysql_config_path,
            template_vars=template_vars,
            docker_compose_path=args.docker_compose_path,
            root_password=args.mysql_root_password,
        )
    elif args.mysql_mode == "native":
        mysql_config_path = args.site_builder_config_path / "mysql"
        return MariaDBNativeManager(
            config_path=mysql_config_path,  # For storing password file
            template_vars=template_vars,
            mysql_config_path=args.mysql_config_path,
            root_password=args.mysql_root_password,
        )

    return None


def _create_postgres_manager(
    args: Any, template_vars: Dict[str, Any]
) -> Optional[Union[PostgreSQLDockerManager, PostgreSQLNativeManager]]:
    """Create and configure PostgreSQL manager based on mode."""
    if args.postgres_mode == "none":
        return None

    if args.postgres_mode == "docker":
        # Use the docker-compose directory as parent for database configs
        postgres_config_path = args.docker_compose_path.parent / "postgres"
        return PostgreSQLDockerManager(
            config_path=postgres_config_path,
            template_vars=template_vars,
            docker_compose_path=args.docker_compose_path,
            root_password=args.postgres_root_password,
        )
    elif args.postgres_mode == "native":
        postgres_config_path = args.site_builder_config_path / "postgres"
        return PostgreSQLNativeManager(
            config_path=postgres_config_path,  # For storing password file
            template_vars=template_vars,
            postgres_config_path=args.postgres_config_path,
            root_password=args.postgres_root_password,
        )

    return None


def create_database_managers(
    args: Any, template_vars: Dict[str, Any]
) -> Dict[str, Union[MariaDBDockerManager, MariaDBNativeManager, PostgreSQLDockerManager, PostgreSQLNativeManager]]:
    """Create and configure Database manager based on mode and type."""
    managers = {}

    mysql_manager = _create_mysql_manager(args, template_vars)
    if mysql_manager:
        managers["mysql"] = mysql_manager

    postgres_manager = _create_postgres_manager(args, template_vars)
    if postgres_manager:
        managers["postgresql"] = postgres_manager

    return managers
