"""Abstract base class for Nginx management."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class NginxManager(ABC):
    """Abstract base class for Nginx service management."""

    def __init__(self, config_path: Path, template_vars: Dict[str, Any]):
        """
        Initialize Nginx manager.

        Args:
            config_path: Path where nginx configuration files will be stored
            template_vars: Template variables for configuration generation
        """
        self.config_path = config_path
        self.template_vars = template_vars
        self.config_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def setup(self) -> None:
        """Set up Nginx service (install if needed, configure directories, etc.)."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the Nginx service."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the Nginx service."""
        pass

    @abstractmethod
    def reload(self) -> None:
        """Reload Nginx configuration without downtime using SIGHUP."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if Nginx service is running."""
        pass

    @abstractmethod
    def generate_site_config(self, site: Dict[str, Any], config_generator) -> None:
        """Generate configuration for a single site."""
        pass

    @abstractmethod
    def generate_main_config(self, sites: List[Dict[str, Any]], config_generator) -> None:
        """Generate main Nginx configuration."""
        pass

    @abstractmethod
    def enable_site(self, site_name: str) -> None:
        """Enable a site configuration."""
        pass

    @abstractmethod
    def disable_site(self, site_name: str) -> None:
        """Disable a site configuration."""
        pass

    @abstractmethod
    def cleanup_sites(self) -> None:
        """Clean up existing site configurations."""
        pass
