"""Docker-based Nginx service management."""

import logging
import subprocess
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List

from ..docker import DockerManager
from .nginx_manager import NginxManager


class NginxDockerManager(NginxManager):
    """Nginx service management using Docker containers."""

    def __init__(self, config_path: Path, template_vars: Dict[str, Any], docker_compose_path: Path):
        """
        Initialize Docker-based Nginx manager.

        Args:
            config_path: Path where nginx configuration files will be stored (/etc/site-builder/nginx)
            template_vars: Template variables for configuration generation
            docker_compose_path: Path to docker-compose.yml file
        """
        super().__init__(config_path, template_vars)
        self.docker_compose_path = docker_compose_path
        self.sites_available_path = config_path / "sites-available"
        self.sites_enabled_path = config_path / "sites-enabled"

        # Create nginx-specific directories
        self.sites_available_path.mkdir(parents=True, exist_ok=True)
        self.sites_enabled_path.mkdir(parents=True, exist_ok=True)

    @cached_property
    def logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        return logger

    def _is_docker_installed(self) -> bool:
        """Check if Docker is installed on the system."""
        docker_manager = DockerManager()
        return docker_manager._has_docker and docker_manager._has_docker_compose

    def setup(self) -> None:
        """Set up Docker-based Nginx service."""
        if not self._is_docker_installed():
            self.logger.info("Docker not found, installing...")
            docker_manager = DockerManager()
            docker_manager.setup()

        self.logger.info("Docker-based Nginx manager setup complete")

    def start(self) -> None:
        """Start the Nginx Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "up", "-d", "nginx"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            self.logger.info("Nginx Docker service started")
        except subprocess.CalledProcessError as e:
            self.logger.error("Failed to start Nginx Docker service: %s", e)
            raise

    def stop(self) -> None:
        """Stop the Nginx Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "stop", "nginx"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            self.logger.info("Nginx Docker service stopped")
        except subprocess.CalledProcessError as e:
            self.logger.error("Failed to stop Nginx Docker service: %s", e)
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
                self.logger.error("Nginx container not found")
                return

            # Send SIGHUP to nginx master process
            subprocess.run(["docker", "exec", container_id, "nginx", "-s", "reload"], check=True)
            self.logger.info("Nginx configuration reloaded successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error("Failed to reload Nginx configuration: %s", e)
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

        self.logger.info("Generated nginx config for %s", site["name"])

    def generate_main_config(self, sites: List[Dict[str, Any]], config_generator) -> None:
        """Generate main Nginx configuration and update docker-compose.yml."""
        # Update docker-compose.yml to include nginx service
        pass

    def enable_site(self, site_name: str) -> None:
        """Enable a site configuration by creating a symlink."""
        available_path = self.sites_available_path / site_name
        enabled_path = self.sites_enabled_path / site_name

        if not available_path.exists():
            self.logger.error("Site configuration not found: %s", available_path)
            return

        if enabled_path.exists():
            enabled_path.unlink()

        enabled_path.symlink_to(available_path)
        self.logger.info("Enabled site: %s", site_name)

    def disable_site(self, site_name: str) -> None:
        """Disable a site configuration by removing the symlink."""
        enabled_path = self.sites_enabled_path / site_name
        if enabled_path.exists():
            enabled_path.unlink()
            self.logger.info("Disabled site: %s", site_name)

    def cleanup_sites(self) -> None:
        """Clean up existing site configurations."""
        for site_enabled in self.sites_enabled_path.glob("*"):
            if site_enabled.is_symlink():
                site_enabled.unlink()
        self.logger.info("Cleaned up existing site configurations")
