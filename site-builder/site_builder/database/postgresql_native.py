"""Native PostgreSQL service management."""

import logging
import secrets
import shutil
import string
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from ..config_generator import ConfigGenerator
from ..pkgs import PKGsManager
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PostgreSQLNativeManager(DatabaseManager):
    """Native PostgreSQL service management using system installation."""

    def __init__(
        self,
        config_path: Path,
        template_vars: Dict[str, Any],
        postgres_config_path: Optional[Path] = None,
        root_password: Optional[str] = None,
    ):
        """
        Initialize native PostgreSQL manager.

        Args:
            config_path: Path where PostgreSQL configuration files will be stored
            template_vars: Template variables for configuration generation
            postgres_config_path: Path to PostgreSQL configuration directory (auto-detected if not provided)
            root_password: PostgreSQL root password (generated if not provided)
        """
        super().__init__(config_path, template_vars)
        self.postgres_config_path = postgres_config_path or self._find_postgres_config_path()
        self.root_password = root_password or self._generate_password()
        self.config_file = self.postgres_config_path / "postgresql.conf"
        self.hba_config = self.postgres_config_path / "pg_hba.conf"

        # Create postgres configuration directory
        self.postgres_config_path.mkdir(parents=True, exist_ok=True)

        # Store root password securely
        self._store_root_password()

    def _generate_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _find_postgres_config_path(self) -> Path:
        """Find the PostgreSQL configuration directory."""
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

    def _is_installed(self) -> bool:
        """Check if PostgreSQL is installed on the system."""
        return shutil.which("psql") is not None and shutil.which("postgres") is not None

    def _install(self) -> None:
        """Install PostgreSQL using the system's package manager."""
        logger.info("Installing PostgreSQL...")
        pkgs_manager = PKGsManager()
        pkgs_manager.install(["postgresql", "postgresql-contrib"])

        # Enable and start service
        try:
            subprocess.run(["systemctl", "enable", "postgresql"], check=True)
            subprocess.run(["systemctl", "start", "postgresql"], check=True)
        except subprocess.CalledProcessError:
            logger.warning("Could not enable PostgreSQL service via systemctl")

        # Set postgres user password
        self._set_postgres_password()

        logger.info("PostgreSQL installed successfully")

    def _set_postgres_password(self) -> None:
        """Set the postgres user password."""
        try:
            # Set password for postgres user
            cmd = [
                "sudo",
                "-u",
                "postgres",
                "psql",
                "-c",
                f"ALTER USER postgres PASSWORD '{self.root_password}';",
            ]
            subprocess.run(cmd, check=True)

            logger.info("PostgreSQL postgres user password set successfully")
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to set PostgreSQL postgres user password: %s", e)

    def setup(self) -> None:
        """Set up native PostgreSQL service."""
        if not self._is_installed():
            self._install()

        # Generate default configuration if it doesn't exist
        if not self.config_file.exists():
            # Try to copy from system default if available
            system_config = Path("/usr/share/postgresql") / "postgresql.conf.sample"
            if system_config.exists():
                import shutil

                shutil.copy2(system_config, self.config_file)
                logger.info("Copied default PostgreSQL configuration from %s", system_config)
            else:
                logger.warning("PostgreSQL configuration file not found: %s", self.config_file)

        logger.info("Native PostgreSQL manager setup complete")

    def start(self) -> None:
        """Start the native PostgreSQL service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "start", "postgresql"], check=True)
            logger.info("PostgreSQL service started via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "postgresql", "start"], check=True)
                logger.info("PostgreSQL service started via service command")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to start PostgreSQL service: %s", e)
                raise

    def stop(self) -> None:
        """Stop the native PostgreSQL service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "stop", "postgresql"], check=True)
            logger.info("PostgreSQL service stopped via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "postgresql", "stop"], check=True)
                logger.info("PostgreSQL service stopped via service command")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to stop PostgreSQL service: %s", e)
                raise

    def restart(self) -> None:
        """Restart the native PostgreSQL service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "restart", "postgresql"], check=True)
            logger.info("PostgreSQL service restarted via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "postgresql", "restart"], check=True)
                logger.info("PostgreSQL service restarted via service command")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to restart PostgreSQL service: %s", e)
                raise

    def is_running(self) -> bool:
        """Check if native PostgreSQL service is running."""
        try:
            # Try systemctl first
            result = subprocess.run(["systemctl", "is-active", "postgresql"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip() == "active":
                return True
        except subprocess.CalledProcessError:
            pass

        # Fallback to checking postgres process
        try:
            env = {"PGPASSWORD": self.root_password}
            result = subprocess.run(
                ["psql", "-U", "postgres", "-c", "SELECT 1"], capture_output=True, text=True, env=env
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def create_database(self, database_name: str) -> None:
        """Create a new database."""
        try:
            env = {"PGPASSWORD": self.root_password}
            cmd = [
                "psql",
                "-U",
                "postgres",
                "-c",
                (
                    f"CREATE DATABASE \"{database_name}\" WITH ENCODING='UTF8' "
                    f"LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';"
                ),
            ]
            subprocess.run(cmd, check=True, env=env)
            logger.info("Created database: %s", database_name)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create database %s: %s", database_name, e)
            raise

    def create_user(self, username: str, password: str, database_name: Optional[str] = None) -> None:
        """Create a new database user with optional database access."""
        try:
            # Create user
            env = {"PGPASSWORD": self.root_password}
            cmd = [
                "psql",
                "-U",
                "postgres",
                "-c",
                f"CREATE USER \"{username}\" WITH PASSWORD '{password}';",
            ]
            subprocess.run(cmd, check=True, env=env)

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
            env = {"PGPASSWORD": self.root_password}
            cmd = [
                "psql",
                "-U",
                "postgres",
                "-c",
                f'GRANT {privileges} PRIVILEGES ON DATABASE "{database_name}" TO "{username}";',
            ]
            subprocess.run(cmd, check=True, env=env)
            logger.info("Granted %s privileges on %s to %s", privileges, database_name, username)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to grant privileges: %s", e)
            raise

    def backup_database(self, database_name: str, backup_path: Path) -> None:
        """Backup a database to a file."""
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            env = {"PGPASSWORD": self.root_password}
            cmd = [
                "pg_dump",
                "-U",
                "postgres",
                "--no-password",
                "--format=custom",
                "--blobs",
                database_name,
            ]

            with backup_path.open("wb") as f:
                subprocess.run(cmd, stdout=f, check=True, env=env)

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

            env = {"PGPASSWORD": self.root_password}
            cmd = [
                "pg_restore",
                "-U",
                "postgres",
                "--no-password",
                "--dbname",
                database_name,
                "--clean",
                "--if-exists",
            ]

            with backup_path.open("rb") as f:
                subprocess.run(cmd, stdin=f, check=True, env=env)

            logger.info("Restored database %s from %s", database_name, backup_path)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restore database %s: %s", database_name, e)
            raise

    def generate_config(self, config_generator: ConfigGenerator) -> None:
        """Generate PostgreSQL configuration files."""
        config_content = config_generator.render_postgresql_config(self.template_vars)
        with self.config_file.open("w") as fp:
            fp.write(config_content)
        logger.info("Generated PostgreSQL configuration at %s", self.config_file)

    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information."""
        return {
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": self.root_password,
            "type": "native",
            "config_path": str(self.postgres_config_path),
            "config_file": str(self.config_file),
        }
