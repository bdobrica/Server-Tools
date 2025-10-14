"""Abstract base class for database management."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DatabaseManager(ABC):
    """Abstract base class for database service management."""

    def __init__(self, config_path: Path, template_vars: Dict[str, Any]):
        """
        Initialize Database manager.

        Args:
            config_path: Path where database configuration files will be stored
            template_vars: Template variables for configuration generation
        """
        self.config_path = config_path
        self.template_vars = template_vars
        self.config_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def setup(self) -> None:
        """Set up database service (install if needed, configure directories, etc.)."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the database service."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the database service."""
        pass

    @abstractmethod
    def restart(self) -> None:
        """Restart the database service."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if database service is running."""
        pass

    @abstractmethod
    def create_database(self, database_name: str) -> None:
        """Create a new database."""
        pass

    @abstractmethod
    def create_user(self, username: str, password: str, database_name: Optional[str] = None) -> None:
        """Create a new database user with optional database access."""
        pass

    @abstractmethod
    def grant_privileges(self, username: str, database_name: str, privileges: str = "ALL") -> None:
        """Grant privileges to a user on a database."""
        pass

    @abstractmethod
    def backup_database(self, database_name: str, backup_path: Path) -> None:
        """Backup a database to a file."""
        pass

    @abstractmethod
    def restore_database(self, database_name: str, backup_path: Path) -> None:
        """Restore a database from a backup file."""
        pass

    @abstractmethod
    def generate_config(self, config_generator) -> None:
        """Generate database configuration files."""
        pass

    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information."""
        pass
