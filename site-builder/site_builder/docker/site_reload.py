"""Load renewed certificates in running site containers."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def reload_site_containers(sites):
    """Test and gracefully reload nginx for changed sites that are running.

    Unstarted containers will load the certificates at startup. Docker and nginx
    failures propagate so renewal cannot report success with stale certificates.
    """
    if not sites:
        return

    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        check=True, capture_output=True, text=True,
    )
    running = set(result.stdout.splitlines())
    for site in sites:
        container = f"site-{site['slug']}"
        if container not in running:
            logger.info("Skipping %s: container is not running", container)
            continue
        subprocess.run(["docker", "exec", container, "nginx", "-t"], check=True)
        subprocess.run(["docker", "exec", container, "nginx", "-s", "reload"], check=True)
        logger.info("Reloaded nginx in %s after certificate renewal", container)
