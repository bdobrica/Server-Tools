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

    return RuntimeInfo(
        name=f"{subdomain_path.name}",
        version=get_runtime_version(runtime_path),
        context=runtime_path,
    )
