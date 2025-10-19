"""Docker-based PostgreSQL service management."""

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


class PostgreSQLDockerManager(DatabaseManager):
    """PostgreSQL service management using Docker containers."""

    def __init__(
        self,
        config_path: Path,
        template_vars: Dict[str, Any],
        docker_compose_path: Path,
        postgres_host_config_path: Optional[Path] = None,
        root_password: Optional[str] = None,
    ):
        """
        Initialize Docker-based PostgreSQL manager.

        Args:
            config_path: Path where PostgreSQL configuration files will be stored (/etc/site-builder/postgres)
            template_vars: Template variables for configuration generation
            docker_compose_path: Path to docker-compose.yml file
            postgres_host_config_path: Path to host PostgreSQL config (for mapping into container)
            root_password: PostgreSQL root password (generated if not provided)
        """
        super().__init__(config_path, template_vars)
        self.docker_compose_path = docker_compose_path
        self.postgres_host_config_path = postgres_host_config_path or self._find_postgres_config_path()
        self.root_password = root_password or self._generate_password()
        self.config_file = config_path / "postgresql.conf"
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

    def _find_postgres_config_path(self) -> Path:
        """Find the PostgreSQL configuration directory on the host system."""
        # Common PostgreSQL configuration paths
        base_paths = [
            Path("/etc/postgresql"),
            Path("/var/lib/pgsql/data"),  # CentOS/RHEL
            Path("/usr/local/pgsql/data"),  # Source installations
        ]

        for base_path in base_paths:
            if base_path.exists():
                # For Debian/Ubuntu: /etc/postgresql/<version>/main/
                if base_path == Path("/etc/postgresql"):
                    # Find the version directory
                    version_dirs = [d for d in base_path.iterdir() if d.is_dir()]
                    if version_dirs:
                        # Sort to get the latest version
                        version_dirs.sort(reverse=True)
                        main_dir = version_dirs[0] / "main"
                        if main_dir.exists():
                            return main_dir

                # For other paths, check if postgresql.conf exists
                config_file = base_path / "postgresql.conf"
                if config_file.exists():
                    return base_path

        # Default fallback - will be created if it doesn't exist
        return Path("/etc/postgresql/15/main")  # Default to PostgreSQL 15

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
        """Set up Docker-based PostgreSQL service."""
        if not self._is_docker_installed():
            logger.info("Docker not found, installing...")
            docker_manager = DockerManager()
            docker_manager.setup()

        # Generate default configuration if it doesn't exist
        if not self.config_file.exists():
            # Try to copy from host system if available
            host_config = self.postgres_host_config_path / "postgresql.conf"
            if host_config.exists():
                import shutil

                shutil.copy2(host_config, self.config_file)
                logger.info("Copied PostgreSQL configuration from host: %s", host_config)
            else:
                logger.warning("PostgreSQL configuration file not found: %s", self.config_file)

        logger.info("Docker-based PostgreSQL manager setup complete")

    def start(self) -> None:
        """Start the PostgreSQL Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "up", "-d", "postgres"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("PostgreSQL Docker service started")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to start PostgreSQL Docker service: %s", e)
            raise

    def stop(self) -> None:
        """Stop the PostgreSQL Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "stop", "postgres"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("PostgreSQL Docker service stopped")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to stop PostgreSQL Docker service: %s", e)
            raise

    def restart(self) -> None:
        """Restart the PostgreSQL Docker service."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "restart", "postgres"],
                check=True,
                cwd=self.docker_compose_path.parent,
            )
            logger.info("PostgreSQL Docker service restarted")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restart PostgreSQL Docker service: %s", e)
            raise

    def is_running(self) -> bool:
        """Check if PostgreSQL Docker service is running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_path), "ps", "-q", "postgres"],
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
                "postgres",
                "psql",
                "-U",
                "postgres",
                "-c",
                (
                    f"CREATE DATABASE \"{database_name}\" WITH ENCODING='UTF8' "
                    f"LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';"
                ),
            ]

            # Set password environment variable
            env = {"PGPASSWORD": self.root_password}
            subprocess.run(cmd, check=True, cwd=self.docker_compose_path.parent, env=env)
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
                "postgres",
                "psql",
                "-U",
                "postgres",
                "-c",
                f"CREATE USER \"{username}\" WITH PASSWORD '{password}';",
            ]

            # Set password environment variable
            env = {"PGPASSWORD": self.root_password}
            subprocess.run(cmd, check=True, cwd=self.docker_compose_path.parent, env=env)

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
                "postgres",
                "psql",
                "-U",
                "postgres",
                "-c",
                f'GRANT {privileges} PRIVILEGES ON DATABASE "{database_name}" TO "{username}";',
            ]

            # Set password environment variable
            env = {"PGPASSWORD": self.root_password}
            subprocess.run(cmd, check=True, cwd=self.docker_compose_path.parent, env=env)
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
                "postgres",
                "pg_dump",
                "-U",
                "postgres",
                "--no-password",
                "--format=custom",
                "--blobs",
                database_name,
            ]

            # Set password environment variable
            env = {"PGPASSWORD": self.root_password}
            with backup_path.open("wb") as f:
                subprocess.run(cmd, stdout=f, check=True, cwd=self.docker_compose_path.parent, env=env)

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
                "postgres",
                "pg_restore",
                "-U",
                "postgres",
                "--no-password",
                "--dbname",
                database_name,
                "--clean",
                "--if-exists",
            ]

            # Set password environment variable
            env = {"PGPASSWORD": self.root_password}
            with backup_path.open("rb") as f:
                subprocess.run(cmd, stdin=f, check=True, cwd=self.docker_compose_path.parent, env=env)

            logger.info("Restored database %s from %s", database_name, backup_path)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restore database %s: %s", database_name, e)
            raise

    def generate_config(self, config_generator: ConfigGenerator) -> None:
        """Generate PostgreSQL configuration files."""
        config_content = config_generator.render_postgresql_config(self.template_vars)

        # Write to both container config path and host config path (if different)
        with self.config_file.open("w") as fp:
            fp.write(config_content)
        logger.info("Generated PostgreSQL configuration at %s", self.config_file)

        # Also write to host config path if it's different and accessible
        if self.postgres_host_config_path != self.config_file.parent:
            host_config_file = self.postgres_host_config_path / "postgresql.conf"
            try:
                host_config_file.parent.mkdir(parents=True, exist_ok=True)
                with host_config_file.open("w") as fp:
                    fp.write(config_content)
                logger.info("Generated PostgreSQL host configuration at %s", host_config_file)
            except (PermissionError, OSError) as e:
                logger.warning("Could not write to host config path %s: %s", host_config_file, e)

    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information."""
        return {
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": self.root_password,
            "type": "docker",
            "config_path": str(self.config_path),
            "config_file": str(self.config_file),
            "host_config_path": str(self.postgres_host_config_path),
        }
