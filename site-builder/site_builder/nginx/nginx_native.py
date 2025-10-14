"""Native Nginx service management."""

import logging
import shutil
import subprocess
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..pkgs import PKGsManager
from .nginx_manager import NginxManager


class NginxNativeManager(NginxManager):
    """Native Nginx service management using system installation."""

    def __init__(
        self, config_path: Path, template_vars: Dict[str, Any], nginx_config_path: Path, nginx_enabled_path: Path
    ):
        """
        Initialize native Nginx manager.

        Args:
            config_path: Path where nginx configuration files will be stored
            template_vars: Template variables for configuration generation
            nginx_config_path: Path to nginx sites-available directory
            nginx_enabled_path: Path to nginx sites-enabled directory
        """
        super().__init__(config_path, template_vars)
        self.nginx_config_path = nginx_config_path
        self.nginx_enabled_path = nginx_enabled_path

        # Create nginx directories
        self.nginx_config_path.mkdir(parents=True, exist_ok=True)
        self.nginx_enabled_path.mkdir(parents=True, exist_ok=True)

    @cached_property
    def logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        return logger

    def _is_installed(self) -> bool:
        """Check if nginx is installed on the system."""
        return shutil.which("nginx") is not None

    def _install(self) -> None:
        """Install nginx using the system's package manager."""
        self.logger.info("Installing nginx...")
        pkgs_manager = PKGsManager()
        pkgs_manager.install(["nginx"])

        # Enable nginx service
        try:
            subprocess.run(["systemctl", "enable", "nginx"], check=True)
        except subprocess.CalledProcessError:
            self.logger.warning("Could not enable nginx service via systemctl")

        self.logger.info("Nginx installed successfully")

    def setup(self) -> None:
        """Set up native Nginx service."""
        if not self._is_installed():
            self._install()

        self.logger.info("Native Nginx manager setup complete")

    def start(self) -> None:
        """Start the native Nginx service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "start", "nginx"], check=True)
            self.logger.info("Nginx service started via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "nginx", "start"], check=True)
                self.logger.info("Nginx service started via service command")
            except subprocess.CalledProcessError as e:
                self.logger.error("Failed to start Nginx service: %s", e)
                raise

    def stop(self) -> None:
        """Stop the native Nginx service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "stop", "nginx"], check=True)
            self.logger.info("Nginx service stopped via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "nginx", "stop"], check=True)
                self.logger.info("Nginx service stopped via service command")
            except subprocess.CalledProcessError as e:
                self.logger.error("Failed to stop Nginx service: %s", e)
                raise

    def reload(self) -> None:
        """Reload Nginx configuration without downtime using SIGHUP."""
        try:
            # First, test configuration
            subprocess.run(["nginx", "-t"], check=True)

            # Try systemctl reload first
            try:
                subprocess.run(["systemctl", "reload", "nginx"], check=True)
                self.logger.info("Nginx configuration reloaded via systemctl")
                return
            except subprocess.CalledProcessError:
                pass

            # Fallback to service command
            try:
                subprocess.run(["service", "nginx", "reload"], check=True)
                self.logger.info("Nginx configuration reloaded via service command")
                return
            except subprocess.CalledProcessError:
                pass

            # Fallback to SIGHUP signal
            nginx_pid = self._get_nginx_master_pid()
            if nginx_pid:
                subprocess.run(["kill", "-HUP", str(nginx_pid)], check=True)
                self.logger.info("Nginx configuration reloaded via SIGHUP signal")
            else:
                raise RuntimeError("Could not find nginx master process")

        except subprocess.CalledProcessError as e:
            self.logger.error("Failed to reload Nginx configuration: %s", e)
            raise

    def is_running(self) -> bool:
        """Check if native Nginx service is running."""
        try:
            # Try systemctl first
            result = subprocess.run(["systemctl", "is-active", "nginx"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip() == "active":
                return True
        except subprocess.CalledProcessError:
            pass

        # Fallback to checking process
        return self._get_nginx_master_pid() is not None

    def generate_site_config(self, site: Dict[str, Any], config_generator) -> None:
        """Generate configuration for a single site."""
        site_config_path = self.nginx_config_path / site["name"]
        with site_config_path.open("w") as fp:
            site_template_vars = self.template_vars.copy()
            site_template_vars.update(site)
            config = config_generator.render_nginx_config(site, site_template_vars)
            fp.write(config)

        self.logger.info("Generated nginx config for %s", site["name"])

    def generate_main_config(self, sites: List[Dict[str, Any]], config_generator) -> None:
        """Generate main Nginx configuration (no additional main config needed for native)."""
        # For native nginx, individual site configs are sufficient
        # The main nginx.conf is managed by the system
        pass

    def enable_site(self, site_name: str) -> None:
        """Enable a site configuration by creating a symlink."""
        available_path = self.nginx_config_path / site_name
        enabled_path = self.nginx_enabled_path / site_name

        if not available_path.exists():
            self.logger.error("Site configuration not found: %s", available_path)
            return

        if enabled_path.exists():
            enabled_path.unlink()

        enabled_path.symlink_to(available_path)
        self.logger.info("Enabled site: %s", site_name)

    def disable_site(self, site_name: str) -> None:
        """Disable a site configuration by removing the symlink."""
        enabled_path = self.nginx_enabled_path / site_name
        if enabled_path.exists():
            enabled_path.unlink()
            self.logger.info("Disabled site: %s", site_name)

    def cleanup_sites(self) -> None:
        """Clean up existing site configurations."""
        for site_enabled in self.nginx_enabled_path.glob("*"):
            if site_enabled.is_symlink():
                site_enabled.unlink()
        self.logger.info("Cleaned up existing site configurations")

    def _get_nginx_master_pid(self) -> Optional[int]:
        """Get the PID of the nginx master process."""
        try:
            # Use ps command to find nginx master process
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True)

            for line in result.stdout.split("\n"):
                if "nginx: master process" in line:
                    # Extract PID (second column in ps aux output)
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1])
        except (subprocess.CalledProcessError, ValueError, IndexError):
            pass
        return None
