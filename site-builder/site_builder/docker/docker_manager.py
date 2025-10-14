"""Module to manage Docker installation and setup."""

import logging
import shutil
import subprocess
from functools import cached_property

import requests

from ..pkgs import PKGsManager


class DockerManager:
    @cached_property
    def logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        return logger

    @cached_property
    def _has_docker(self) -> bool:
        return shutil.which("docker") is not None

    @cached_property
    def _has_docker_compose(self) -> bool:
        # Check for both standalone docker-compose and docker compose plugin
        return shutil.which("docker") is not None and self._has_compose_plugin()

    def _has_compose_plugin(self) -> bool:
        """Check if docker compose plugin is available."""
        try:
            result = subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def setup(self) -> None:
        """Set up Docker environment if not already set up."""
        if self._has_docker and self._has_docker_compose:
            self.logger.info("Docker and Docker Compose are already installed")
            return None

        pkgs_manager = PKGsManager()

        if pkgs_manager.is_debian_based:
            self._setup_debian(pkgs_manager)
        elif pkgs_manager.is_redhat_based:
            self._setup_redhat(pkgs_manager)
        else:
            raise EnvironmentError("Unsupported operating system. Please install Docker manually.")

    def _setup_debian(self, pkgs_manager: PKGsManager) -> None:
        """Set up Docker on Debian-based systems."""
        self.logger.info("Installing Docker using official Debian repository...")

        # Install prerequisites
        pkgs_manager.install(["ca-certificates", "curl"])

        # Download and set up Docker's GPG key
        response = requests.get("https://download.docker.com/linux/debian/gpg", timeout=10)
        response.raise_for_status()
        self.logger.info("Downloaded Docker GPG key")

        gpg_key_path = "/etc/apt/keyrings/docker.asc"
        pkgs_manager.setup_apt_gpg_key(response.content, gpg_key_path)

        # Add Docker repository to sources
        # Get architecture and version codename
        arch_result = subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True, check=True)
        architecture = arch_result.stdout.strip()

        # Get version codename from os-release
        with open("/etc/os-release", "r") as f:
            os_release_content = f.read()

        version_codename = None
        for line in os_release_content.split("\n"):
            if line.startswith("VERSION_CODENAME="):
                version_codename = line.split("=")[1].strip('"')
                break

        if not version_codename:
            raise EnvironmentError("Could not determine Debian version codename")

        # Create the repository line
        repo_line = (
            f"deb [arch={architecture} signed-by={gpg_key_path}] "
            f"https://download.docker.com/linux/debian {version_codename} stable"
        )

        # Add Docker repository
        pkgs_manager.add_repository(repo_line, "docker")

        # Update package list and install Docker packages
        pkgs_manager._update_package_list()
        pkgs_manager.install(
            ["docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"]
        )

        # Enable and start Docker service
        subprocess.run(["systemctl", "enable", "docker"], check=True)
        subprocess.run(["systemctl", "start", "docker"], check=True)

        self.logger.info("Docker installed and started successfully")

    def _setup_redhat(self, pkgs_manager: PKGsManager) -> None:
        """Set up Docker on RedHat-based systems (CentOS, RHEL, Fedora)."""
        self.logger.info("Installing Docker using official RedHat repository...")

        # Install DNF plugins core (required for adding repositories)
        pkgs_manager.install(["dnf-plugins-core"])

        # Add Docker's official repository
        docker_repo_url = "https://download.docker.com/linux/centos/docker-ce.repo"
        pkgs_manager.add_repository(docker_repo_url)

        # Install Docker packages
        pkgs_manager.install(
            ["docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"]
        )

        # Enable and start Docker service
        subprocess.run(["systemctl", "enable", "docker"], check=True)
        subprocess.run(["systemctl", "start", "docker"], check=True)

        self.logger.info("Docker installed and started successfully")
