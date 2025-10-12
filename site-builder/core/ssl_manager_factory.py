"""SSL manager factory for site-builder."""

from typing import Any

try:
    from ..ssl_certificate_manager import SSLCertificateManager
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from ssl_certificate_manager import SSLCertificateManager


def create_ssl_manager(args: Any, ca_password: str) -> SSLCertificateManager:
    """Create and configure SSL certificate manager."""
    root_ca_key = args.root_ca_path / "perseus_ca.key"
    root_ca_crt = args.root_ca_path / "perseus_ca.crt"

    return SSLCertificateManager(
        proxy_ssl_path=args.root_ca_path,
        root_ca_crt=root_ca_crt,
        root_ca_key=root_ca_key,
        root_ca_password=ca_password,
        country=args.country,
        state=args.state,
        organisation=args.organisation,
    )
