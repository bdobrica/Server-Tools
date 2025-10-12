"""Module to manage system package installation and repository management."""

import logging
import shutil
import subprocess
from functools import cached_property
from typing import Optional


class PKGsManager:
    def __init__(self):
        pass

    @cached_property
    def logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        return logger

    @cached_property
    def is_debian_based(self) -> bool:
        return shutil.which("apt-get") is not None

    @cached_property
    def is_redhat_based(self) -> bool:
        return shutil.which("dnf") is not None

    def _update_package_list(self) -> None:
        if self.is_debian_based:
            subprocess.run(["apt-get", "update"], check=True)
        elif self.is_redhat_based:
            subprocess.run(["dnf", "makecache"], check=True)
        else:
            raise EnvironmentError("Unsupported package manager. Please update packages manually.")

    def _install_packages(self, packages: list) -> None:
        if self.is_debian_based:
            subprocess.run(["apt-get", "install", "-y"] + packages, check=True)
        elif self.is_redhat_based:
            subprocess.run(["dnf", "install", "-y"] + packages, check=True)
        else:
            raise EnvironmentError("Unsupported package manager. Please install packages manually.")

    def install(self, packages: list) -> None:
        """Install the given list of packages using the system's package manager."""
        self.logger.info("Updating package list...")
        self._update_package_list()
        self.logger.info("Installing packages: %s", ", ".join(packages))
        self._install_packages(packages)
        self.logger.info("Package installation complete")

    def add_repository(self, repo_url_or_line: str, repo_name: Optional[str] = None) -> None:
        """Add a repository to the system's package manager.

        Args:
            repo_url_or_line: For RedHat systems, this should be a .repo URL.
                             For Debian systems, this should be the complete repository line.
            repo_name: Optional repository name (used for Debian systems as filename).
        """
        if self.is_debian_based:
            self._add_apt_repository(repo_url_or_line, repo_name)
        elif self.is_redhat_based:
            self._add_dnf_repository(repo_url_or_line)
        else:
            raise EnvironmentError("Unsupported package manager for repository management.")

    def _add_apt_repository(self, repo_line: str, repo_name: Optional[str] = None) -> None:
        """Add an APT repository on Debian-based systems."""
        if not repo_name:
            repo_name = "custom"

        sources_list_path = f"/etc/apt/sources.list.d/{repo_name}.list"
        self.logger.info("Adding APT repository to %s", sources_list_path)

        subprocess.run(["tee", sources_list_path], input=repo_line, text=True, check=True, stdout=subprocess.DEVNULL)

    def _add_dnf_repository(self, repo_url: str) -> None:
        """Add a DNF repository on RedHat-based systems."""
        self.logger.info("Adding DNF repository: %s", repo_url)
        subprocess.run(["dnf", "config-manager", "--add-repo", repo_url], check=True)

    def setup_apt_gpg_key(self, gpg_key_content: bytes, key_path: str) -> None:
        """Set up a GPG key for APT repositories on Debian-based systems."""
        if not self.is_debian_based:
            raise EnvironmentError("GPG key setup is only supported on Debian-based systems")

        # Create keyring directory if it doesn't exist
        subprocess.run(["install", "-m", "0755", "-d", "/etc/apt/keyrings"], check=True)

        # Write the GPG key
        with open(key_path, "wb") as f:
            f.write(gpg_key_content)

        # Set proper permissions
        subprocess.run(["chmod", "a+r", key_path], check=True)

        self.logger.info("GPG key installed at %s", key_path)
