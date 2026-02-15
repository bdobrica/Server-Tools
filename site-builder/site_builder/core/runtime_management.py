import logging
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger("site-builder")


class RuntimeInfo(NamedTuple):
    """Immutable runtime information container."""
    name: str
    version: str
    context: Path
    port: int | None = None  # Custom port from EXPOSE directive


@lru_cache()
def get_default_runtime(app_type: str = "php") -> RuntimeInfo:
    """Get the default runtime environment."""
    container_name = {
        "php": "nginx-php8",
        "python": "nginx-py312",
        "nodejs": "nginx-njs24",
    }.get(app_type, "nginx-php8")

    runtimes_path = Path(__file__).parent.parent.resolve() / "resources"
    logger.info("Using default runtime from %s", runtimes_path / container_name)
    return RuntimeInfo(
        name=container_name,
        version="latest",
        context=runtimes_path / container_name,
    )


def get_runtime_version(runtime_path: Path) -> str:
    """Get the version of the runtime from its Dockerfile."""
    dockerfile_path = runtime_path / "Dockerfile"
    if not dockerfile_path.is_file():
        raise FileNotFoundError(f"Dockerfile not found in runtime path: {runtime_path}")

    with dockerfile_path.open("r") as df:
        for line in df:
            if line.startswith("ENV RUNTIME_VERSION="):
                return line.strip().split("=")[1]
    logger.warning("RUNTIME_VERSION not found in Dockerfile at: %s", dockerfile_path)
    return "latest"


def get_exposed_ports(runtime_path: Path) -> list[int]:
    """Extract EXPOSE ports from a Dockerfile.
    
    Args:
        runtime_path: Path to the runtime directory containing Dockerfile
        
    Returns:
        List of exposed port numbers, empty list if none found
    """
    dockerfile_path = runtime_path / "Dockerfile"
    if not dockerfile_path.is_file():
        return []
    
    exposed_ports = []
    with dockerfile_path.open("r") as df:
        for line in df:
            line = line.strip()
            if line.startswith("EXPOSE"):
                # Handle EXPOSE directive: EXPOSE 8080 or EXPOSE 8080/tcp
                parts = line.split()
                for part in parts[1:]:  # Skip "EXPOSE" keyword
                    # Remove protocol suffix if present (e.g., "8080/tcp" -> "8080")
                    port_str = part.split("/")[0]
                    try:
                        port = int(port_str)
                        exposed_ports.append(port)
                    except ValueError:
                        logger.warning("Invalid port in EXPOSE directive: %s", part)
    
    if exposed_ports:
        logger.info("Found exposed ports in %s: %s", dockerfile_path, exposed_ports)
    
    return exposed_ports


def detect_default_runtime(subdomain_path: Path) -> RuntimeInfo:
    """Detect the default runtime environment based on common files."""
    if (subdomain_path / "index.php").is_file():
        return get_default_runtime("php")
    elif (subdomain_path / "index.py").is_file():
        return get_default_runtime("python")
    elif (subdomain_path / "index.ts").is_file():
        return get_default_runtime("nodejs")
    else:
        logger.info("No specific runtime files found in %s, using PHP as default", subdomain_path)
        return get_default_runtime("php")


def detect_runtime(subdomain_path: Path) -> RuntimeInfo:
    """Detect the runtime environment for a given subdomain based on its files."""

    runtime_path = subdomain_path / ".runtime"
    if not runtime_path.is_dir():
        logger.info("No .runtime directory found in %s, using default runtime", subdomain_path)
        return detect_default_runtime(subdomain_path)

    if not (runtime_path / "Dockerfile").is_file():
        logger.warning("No Dockerfile found in %s, using default runtime", runtime_path)
        return detect_default_runtime(subdomain_path)

    # Extract exposed ports from custom Dockerfile
    exposed_ports = get_exposed_ports(runtime_path)
    custom_port = exposed_ports[0] if exposed_ports else None
    
    if custom_port:
        logger.info("Using custom port %d for %s", custom_port, subdomain_path.name)

    return RuntimeInfo(
        name=f"{subdomain_path.name}",
        version=get_runtime_version(runtime_path),
        context=runtime_path,
        port=custom_port,
    )
