"""Rebuild site runtimes and recreate their containers."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def rebuild_site_containers(sites, compose_path):
    """Build every site successfully before replacing any running containers.

    Explicit service names and --no-deps keep database and proxy containers out
    of the recreation. Failures propagate to prevent a false success report.
    """
    if not sites:
        return

    services = [f"web-{site['slug']}" for site in sites]
    compose = ["docker", "compose", "-f", str(compose_path.resolve())]
    logger.info("Rebuilding site runtimes for %d sites", len(services))
    subprocess.run(compose + ["build", "--pull", "--no-cache"] + services, check=True)
    subprocess.run(
        compose + ["up", "-d", "--no-deps", "--force-recreate"] + services,
        check=True,
    )
    logger.info("Recreated %d site containers", len(services))
