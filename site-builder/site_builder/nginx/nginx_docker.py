"""Docker-based Nginx service management."""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..docker import DockerManager
from .nginx_manager import NginxManager

logger = logging.getLogger(__name__)


class NginxDockerManager(NginxManager):
    """Nginx service management using Docker containers."""

    # Shared Docker manager instance
    _shared_docker_manager: Optional[DockerManager] = None

    def __init__(
        self,
        config_path: Path,
        template_vars: Dict[str, Any],
        docker_compose_path: Path,
        docker_manager: Optional[DockerManager] = None,
    ):
        """
        Initialize Docker-based Nginx manager.

        Args:
            config_path: Path where nginx configuration files will be stored (/etc/site-builder/nginx)
            template_vars: Template variables for configuration generation
            docker_compose_path: Path to docker-compose.yml file
            docker_manager: Optional shared DockerManager instance (created if not provided)
        """
        super().__init__(config_path, template_vars)
        self.docker_compose_path = docker_compose_path
        self.sites_available_path = config_path / "sites-available"
        self.sites_enabled_path = config_path / "sites-enabled"

        # Use provided docker_manager or create/reuse shared instance
        if docker_manager is not None:
            self.docker_manager = docker_manager
        elif NginxDockerManager._shared_docker_manager is None:
            NginxDockerManager._shared_docker_manager = DockerManager()
            self.docker_manager = NginxDockerManager._shared_docker_manager
        else:
            self.docker_manager = NginxDockerManager._shared_docker_manager

        # Create nginx-specific directories
        self.sites_available_path.mkdir(parents=True, exist_ok=True)
        self.sites_enabled_path.mkdir(parents=True, exist_ok=True)

    def _is_docker_installed(self) -> bool:
        """Check if Docker is installed on the system."""
        return self.docker_manager._has_docker and self.docker_manager._has_docker_compose

    def setup(self) -> None:
        """Set up Docker-based Nginx service."""
        if not self._is_docker_installed():
            logger.info("Docker not found, installing...")
            self.docker_manager.setup()

        logger.info("Docker-based Nginx manager setup complete")

    def start(self) -> None:
        """Start the Nginx Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "up", "-d", "nginx"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("Nginx Docker service started")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to start Nginx Docker service: %s", e)
            raise

    def stop(self) -> None:
        """Stop the Nginx Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "stop", "nginx"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("Nginx Docker service stopped")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to stop Nginx Docker service: %s", e)
            raise

    def reload(self) -> None:
        """Reload Nginx configuration without downtime using SIGHUP."""
        try:
            # Get the nginx container ID
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "ps", "-q", "nginx"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.docker_compose_path.parent,
            )

            container_id = result.stdout.strip()
            if not container_id:
                logger.error("Nginx container not found")
                return

            # Send SIGHUP to nginx master process
            subprocess.run(["docker", "exec", container_id, "nginx", "-s", "reload"], check=True)
            logger.info("Nginx configuration reloaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to reload Nginx configuration: %s", e)
            raise

    def is_running(self) -> bool:
        """Check if Nginx Docker service is running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "ps", "-q", "nginx"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def generate_site_config(self, site: Dict[str, Any], config_generator) -> None:
        """Generate configuration for a single site."""
        site_config_path = self.sites_available_path / site["name"]
        with site_config_path.open("w") as fp:
            site_template_vars = self.template_vars.copy()
            site_template_vars.update(site)
            config = config_generator.render_nginx_config(site, site_template_vars)
            fp.write(config)

        logger.info("Generated nginx config for %s", site["name"])

    def generate_main_config(self, sites: List[Dict[str, Any]], config_generator) -> None:
        """Generate main Nginx configuration and update docker-compose.yml.
        
        Note: For Docker-based Nginx, the docker-compose.yml generation is centralized
        in __main__.py along with all other docker services to ensure proper service
        dependencies and network configuration. This method is intentionally a no-op
        as the Docker service configuration is handled during the main orchestration.
        
        Individual site configurations are still managed via generate_site_config().
        """
        pass

    def enable_site(self, site_name: str) -> None:
        """Enable a site configuration by creating a symlink."""
        available_path = self.sites_available_path / site_name
        enabled_path = self.sites_enabled_path / site_name

        if not available_path.exists():
            logger.error("Site configuration not found: %s", available_path)
            return

        if enabled_path.exists():
            enabled_path.unlink()

        enabled_path.symlink_to(available_path)
        logger.info("Enabled site: %s", site_name)

    def disable_site(self, site_name: str) -> None:
        """Disable a site configuration by removing the symlink."""
        enabled_path = self.sites_enabled_path / site_name
        if enabled_path.exists():
            enabled_path.unlink()
            logger.info("Disabled site: %s", site_name)

    def cleanup_sites(self) -> None:
        """Clean up existing site configurations."""
        for site_enabled in self.sites_enabled_path.glob("*"):
            if site_enabled.is_symlink():
                site_enabled.unlink()
        logger.info("Cleaned up existing site configurations")
