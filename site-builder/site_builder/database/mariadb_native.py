"""Native MariaDB service management."""

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


class MariaDBNativeManager(DatabaseManager):
    """Native MariaDB service management using system installation."""

    def __init__(
        self,
        config_path: Path,
        template_vars: Dict[str, Any],
        mysql_config_path: Path,
        root_password: Optional[str] = None,
    ):
        """
        Initialize native MariaDB manager.

        Args:
            config_path: Path where MariaDB configuration files will be stored
            template_vars: Template variables for configuration generation
            mysql_config_path: Path to MySQL configuration directory (/etc/mysql)
            root_password: MariaDB root password (generated if not provided)
        """
        super().__init__(config_path, template_vars)
        self.mysql_config_path = mysql_config_path
        self.root_password = root_password or self._generate_password()
        self.config_file = mysql_config_path / "my.cnf"
        self.debian_config = mysql_config_path / "debian.cnf"

        # Create mysql configuration directory
        self.mysql_config_path.mkdir(parents=True, exist_ok=True)

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

    def _is_installed(self) -> bool:
        """Check if MariaDB is installed on the system."""
        return shutil.which("mysql") is not None and shutil.which("mysqld") is not None

    def _install(self) -> None:
        """Install MariaDB using the system's package manager."""
        logger.info("Installing MariaDB...")
        pkgs_manager = PKGsManager()
        pkgs_manager.install(["mariadb-server", "mariadb-client"])

        # Enable and start service
        try:
            subprocess.run(["systemctl", "enable", "mariadb"], check=True)
            subprocess.run(["systemctl", "start", "mariadb"], check=True)
        except subprocess.CalledProcessError:
            logger.warning("Could not enable MariaDB service via systemctl")

        # Secure installation
        self._secure_installation()

        logger.info("MariaDB installed successfully")

    def _secure_installation(self) -> None:
        """Run mysql_secure_installation equivalent commands."""
        try:
            # Set root password and remove anonymous users, test database, etc.
            commands = [
                f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{self.root_password}';",
                "DELETE FROM mysql.user WHERE User='';",
                "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');",
                "DROP DATABASE IF EXISTS test;",
                "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';",
                "FLUSH PRIVILEGES;",
            ]

            for command in commands:
                subprocess.run(["mysql", "-e", command], check=True)

            logger.info("MariaDB secured successfully")
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to secure MariaDB installation: %s", e)

    def setup(self) -> None:
        """Set up native MariaDB service."""
        if not self._is_installed():
            self._install()

        # Generate default configuration if it doesn't exist
        if not self.config_file.exists():
            raise FileNotFoundError(f"MariaDB configuration file not found: {self.config_file}")

        logger.info("Native MariaDB manager setup complete")

    def start(self) -> None:
        """Start the native MariaDB service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "start", "mariadb"], check=True)
            logger.info("MariaDB service started via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "mysql", "start"], check=True)
                logger.info("MariaDB service started via service command")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to start MariaDB service: %s", e)
                raise

    def stop(self) -> None:
        """Stop the native MariaDB service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "stop", "mariadb"], check=True)
            logger.info("MariaDB service stopped via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "mysql", "stop"], check=True)
                logger.info("MariaDB service stopped via service command")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to stop MariaDB service: %s", e)
                raise

    def restart(self) -> None:
        """Restart the native MariaDB service."""
        try:
            # Try systemctl first
            subprocess.run(["systemctl", "restart", "mariadb"], check=True)
            logger.info("MariaDB service restarted via systemctl")
        except subprocess.CalledProcessError:
            try:
                # Fallback to service command
                subprocess.run(["service", "mysql", "restart"], check=True)
                logger.info("MariaDB service restarted via service command")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to restart MariaDB service: %s", e)
                raise

    def is_running(self) -> bool:
        """Check if native MariaDB service is running."""
        try:
            # Try systemctl first
            result = subprocess.run(["systemctl", "is-active", "mariadb"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip() == "active":
                return True
        except subprocess.CalledProcessError:
            pass

        # Fallback to checking mysql process
        try:
            result = subprocess.run(
                ["mysqladmin", "-uroot", f"-p{self.root_password}", "ping"], capture_output=True, text=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def create_database(self, database_name: str) -> None:
        """Create a new database."""
        try:
            cmd = [
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                "-e",
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            ]
            subprocess.run(cmd, check=True)
            logger.info("Created database: %s", database_name)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create database %s: %s", database_name, e)
            raise

    def create_user(self, username: str, password: str, database_name: Optional[str] = None) -> None:
        """Create a new database user with optional database access."""
        try:
            # Create user
            cmd = [
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                "-e",
                f"CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{password}';",
            ]
            subprocess.run(cmd, check=True)

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
                "mysql",
                "-uroot",
                f"-p{self.root_password}",
                "-e",
                f"GRANT {privileges} PRIVILEGES ON `{database_name}`.* TO '{username}'@'localhost'; "
                f"FLUSH PRIVILEGES;",
            ]
            subprocess.run(cmd, check=True)
            logger.info("Granted %s privileges on %s to %s", privileges, database_name, username)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to grant privileges: %s", e)
            raise

    def backup_database(self, database_name: str, backup_path: Path) -> None:
        """Backup a database to a file."""
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "mysqldump",
                "-uroot",
                f"-p{self.root_password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                database_name,
            ]

            with backup_path.open("w") as f:
                subprocess.run(cmd, stdout=f, check=True)

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

            cmd = ["mysql", "-uroot", f"-p{self.root_password}", database_name]

            with backup_path.open("r") as f:
                subprocess.run(cmd, stdin=f, check=True)

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
            "type": "native",
        }
