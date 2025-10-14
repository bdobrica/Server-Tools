"""Docker-based MariaDB service management."""

import logging
import secrets
import string
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from ..config_generator import ConfigGenerator
from ..docker import DockerManager
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MariaDBDockerManager(DatabaseManager):
    """MariaDB service management using Docker containers."""

    def __init__(
        self,
        config_path: Path,
        template_vars: Dict[str, Any],
        docker_compose_path: Path,
        root_password: Optional[str] = None,
    ):
        """
        Initialize Docker-based MariaDB manager.

        Args:
            config_path: Path where MariaDB configuration files will be stored (/etc/site-builder/mysql)
            template_vars: Template variables for configuration generation
            docker_compose_path: Path to docker-compose.yml file
            root_password: MariaDB root password (generated if not provided)
        """
        super().__init__(config_path, template_vars)
        self.docker_compose_path = docker_compose_path
        self.root_password = root_password or self._generate_password()
        self.config_file = config_path / "my.cnf"
        self.data_path = config_path / "data"
        self.logs_path = config_path / "logs"

        # Create necessary directories
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Store root password securely
        self._store_root_password()

    def _generate_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _store_root_password(self) -> None:
        """Store the root password in a secure file."""
        password_file = self.config_path / "root_password.txt"
        if not password_file.exists():
            with password_file.open("w") as f:
                f.write(self.root_password)
            password_file.chmod(0o600)  # Read/write for owner only

    def _is_docker_installed(self) -> bool:
        """Check if Docker is installed on the system."""
        docker_manager = DockerManager()
        return docker_manager._has_docker and docker_manager._has_docker_compose

    def setup(self) -> None:
        """Set up Docker-based MariaDB service."""
        if not self._is_docker_installed():
            logger.info("Docker not found, installing...")
            docker_manager = DockerManager()
            docker_manager.setup()

        # Generate default configuration if it doesn't exist
        if not self.config_file.exists():
            raise FileNotFoundError(f"MariaDB configuration file not found: {self.config_file}")

        logger.info("Docker-based MariaDB manager setup complete")

    def start(self) -> None:
        """Start the MariaDB Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "up", "-d", "mariadb"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("MariaDB Docker service started")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to start MariaDB Docker service: %s", e)
            raise

    def stop(self) -> None:
        """Stop the MariaDB Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "stop", "mariadb"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("MariaDB Docker service stopped")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to stop MariaDB Docker service: %s", e)
            raise

    def restart(self) -> None:
        """Restart the MariaDB Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "restart", "mariadb"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("MariaDB Docker service restarted")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restart MariaDB Docker service: %s", e)
            raise

    def is_running(self) -> bool:
        """Check if MariaDB Docker service is running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "ps", "-q", "mariadb"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def create_database(self, database_name: str) -> None:
        """Create a new database."""
        try:
            cmd = [
                "docker",
                "compose",
                "-f",
                str(self.docker_compose_path),
                "exec",
                "-T",
                "mariadb",
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                "-e",
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            ]
            subprocess.run(cmd, check=True, cwd=self.docker_compose_path.parent)
            logger.info("Created database: %s", database_name)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create database %s: %s", database_name, e)
            raise

    def create_user(self, username: str, password: str, database_name: Optional[str] = None) -> None:
        """Create a new database user with optional database access."""
        try:
            # Create user
            cmd = [
                "docker",
                "compose",
                "-f",
                str(self.docker_compose_path),
                "exec",
                "-T",
                "mariadb",
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                "-e",
                f"CREATE USER IF NOT EXISTS '{username}'@'%' IDENTIFIED BY '{password}';",
            ]
            subprocess.run(cmd, check=True, cwd=self.docker_compose_path.parent)

            # Grant privileges if database specified
            if database_name:
                self.grant_privileges(username, database_name)

            logger.info("Created user: %s", username)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create user %s: %s", username, e)
            raise

    def grant_privileges(self, username: str, database_name: str, privileges: str = "ALL") -> None:
        """Grant privileges to a user on a database."""
        try:
            cmd = [
                "docker",
                "compose",
                "-f",
                str(self.docker_compose_path),
                "exec",
                "-T",
                "mariadb",
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                "-e",
                f"GRANT {privileges} PRIVILEGES ON `{database_name}`.* TO '{username}'@'%'; FLUSH PRIVILEGES;",
            ]
            subprocess.run(cmd, check=True, cwd=self.docker_compose_path.parent)
            logger.info("Granted %s privileges on %s to %s", privileges, database_name, username)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to grant privileges: %s", e)
            raise

    def backup_database(self, database_name: str, backup_path: Path) -> None:
        """Backup a database to a file."""
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "docker",
                "compose",
                "-f",
                str(self.docker_compose_path),
                "exec",
                "-T",
                "mariadb",
                "mysqldump",
                "-uroot",
                f"-p{self.root_password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                database_name,
            ]

            with backup_path.open("w") as f:
                subprocess.run(cmd, stdout=f, check=True, cwd=self.docker_compose_path.parent)

            logger.info("Backed up database %s to %s", database_name, backup_path)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to backup database %s: %s", database_name, e)
            raise

    def restore_database(self, database_name: str, backup_path: Path) -> None:
        """Restore a database from a backup file."""
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Create database if it doesn't exist
            self.create_database(database_name)

            cmd = [
                "docker",
                "compose",
                "-f",
                str(self.docker_compose_path),
                "exec",
                "-T",
                "mariadb",
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                database_name,
            ]

            with backup_path.open("r") as f:
                subprocess.run(cmd, stdin=f, check=True, cwd=self.docker_compose_path.parent)

            logger.info("Restored database %s from %s", database_name, backup_path)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restore database %s: %s", database_name, e)
            raise

    def generate_config(self, config_generator: ConfigGenerator) -> None:
        """Generate MariaDB configuration files."""
        config_content = config_generator.render_mariadb_config(self.template_vars)
        with self.config_file.open("w") as fp:
            fp.write(config_content)
        logger.info("Generated MariaDB configuration at %s", self.config_file)

    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information."""
        return {
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": self.root_password,
            "socket": "/var/run/mysqld/mysqld.sock",
            "type": "docker",
        }
