import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("site-builder")


@lru_cache()
def get_default_runtime() -> Dict[str, Any]:
    """Get the default runtime environment."""
    runtimes_path = Path(__file__).parent.parent.resolve() / "resources"
    logger.info(f"Using default runtime from {runtimes_path / 'nginx-php8'}")
    return {
        "name": "nginx-php8",
        "version": "latest",
        "context": runtimes_path / "nginx-php8",
    }


def get_runtime_version(runtime_path: Path) -> str:
    """Get the version of the runtime from its Dockerfile."""
    dockerfile_path = runtime_path / "Dockerfile"
    if not dockerfile_path.is_file():
        raise FileNotFoundError(f"Dockerfile not found in runtime path: {runtime_path}")

    with dockerfile_path.open("r") as df:
        for line in df:
            if line.startswith("ENV RUNTIME_VERSION="):
                return line.strip().split("=")[1]
    logger.warning(f"RUNTIME_VERSION not found in Dockerfile at: {dockerfile_path}")
    return "latest"


def detect_runtime(subdomain_path: Path) -> Dict[str, Any]:
    """Detect the runtime environment for a given subdomain based on its files."""

    runtime_path = subdomain_path / ".runtime"
    if not runtime_path.is_dir():
        logger.info(f"No .runtime directory found in {subdomain_path}, using default runtime")
        return get_default_runtime()

    if not (runtime_path / "Dockerfile").is_file():
        logger.warning(f"No Dockerfile found in {runtime_path}, using default runtime")
        return get_default_runtime()

    runtime = {
        "name": f"{subdomain_path.name}",
        "version": get_runtime_version(runtime_path),
        "context": runtime_path,
    }

    return runtime
