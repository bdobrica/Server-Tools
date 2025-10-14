"""Site discovery utilities for site-builder."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from .runtime_management import detect_runtime

logger = logging.getLogger("site-builder")


def discover_sites(web_path: Path, verbose: bool = False) -> List[Dict[str, Any]]:
    """Discover sites from web directory structure."""
    domain_re = re.compile(r"^([a-z0-9-]+\.)+[a-z]{2,4}$")
    sites = []
    ip_suffix = 2

    for domain in web_path.glob("*"):
        if not domain.is_dir() or not domain_re.match(domain.name):
            continue

        for subdomain in domain.glob("*"):
            if not subdomain.is_dir() or not domain_re.match(subdomain.name):
                continue

            # Check if SSL certificates exist in the web directory
            ssl_cert_path = subdomain / ".cert"
            has_ssl = (ssl_cert_path / f"{subdomain.name}.key").is_file() and (
                ssl_cert_path / f"{subdomain.name}.crt"
            ).is_file()

            site = {
                "name": subdomain.name,
                "domain": domain.name,
                "slug": subdomain.name.replace(".", "-"),
                "web_root": subdomain.resolve().as_posix(),
                "use_ssl": has_ssl,
                "ip_suffix": ip_suffix,
                "runtime": detect_runtime(subdomain),
            }
            sites.append(site)

            if verbose:
                ssl_status = "SSL" if has_ssl else "NoSSL"
                logger.info("Found site: %s (%s) - %s", subdomain.name, domain.name, ssl_status)

            ip_suffix += 1

    # Sort sites by name for consistent ordering
    sites.sort(key=lambda x: x["name"])

    return sites
