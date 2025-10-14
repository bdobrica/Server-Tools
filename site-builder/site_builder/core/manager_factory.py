"""Manager factories for site-builder."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from ..database import MariaDBDockerManager, MariaDBNativeManager
    from ..nginx import NginxDockerManager, NginxNativeManager
except ImportError:
    # Fallback for direct execution
    import sys

    sys.path.append(str(Path(__file__).parent.parent))
    from database import MariaDBDockerManager, MariaDBNativeManager
    from nginx import NginxDockerManager, NginxNativeManager


def create_nginx_manager(args: Any, template_vars: Dict[str, Any]) -> Union[NginxDockerManager, NginxNativeManager]:
    """Create and configure Nginx manager based on mode."""
    if args.nginx_mode == "docker":
        nginx_config_path = Path("/etc/site-builder/nginx")
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


def create_database_manager(
    args: Any, template_vars: Dict[str, Any]
) -> Optional[Union[MariaDBDockerManager, MariaDBNativeManager]]:
    """Create and configure Database manager based on mode."""
    if args.database_mode == "docker":
        mysql_config_path = Path("/etc/site-builder/mysql")
        return MariaDBDockerManager(
            config_path=mysql_config_path,
            template_vars=template_vars,
            docker_compose_path=args.docker_compose_path,
            root_password=args.database_root_password,
        )
    elif args.database_mode == "native":
        return MariaDBNativeManager(
            config_path=args.root_ca_path,  # For storing password file
            template_vars=template_vars,
            mysql_config_path=args.mysql_config_path,
            root_password=args.database_root_password,
        )
    return None
