import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("site-builder")


@lru_cache()
def get_default_runtime(app_type: str = "php") -> Dict[str, Any]:
    """Get the default runtime environment."""
    container_name = {
        "php": "nginx-php8",
        "python": "nginx-py312",
        "nodejs": "nginx-njs24",
    }.get(app_type, "nginx-php8")

    runtimes_path = Path(__file__).parent.parent.resolve() / "resources"
    logger.info(f"Using default runtime from {runtimes_path / container_name}")
    return {
        "name": container_name,
        "version": "latest",
        "context": runtimes_path / container_name,
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


def detect_default_runtime(subdomain_path: Path) -> Dict[str, Any]:
    """Detect the default runtime environment based on common files."""
    if (subdomain_path / "index.php").is_file():
        return get_default_runtime("php")
    elif (subdomain_path / "index.py").is_file():
        return get_default_runtime("python")
    elif (subdomain_path / "index.ts").is_file():
        return get_default_runtime("nodejs")
    else:
        logger.info(f"No specific runtime files found in {subdomain_path}, using PHP as default")
        return get_default_runtime("php")


def detect_runtime(subdomain_path: Path) -> Dict[str, Any]:
    """Detect the runtime environment for a given subdomain based on its files."""

    runtime_path = subdomain_path / ".runtime"
    if not runtime_path.is_dir():
        logger.info(f"No .runtime directory found in {subdomain_path}, using default runtime")
        return detect_default_runtime(subdomain_path)

    if not (runtime_path / "Dockerfile").is_file():
        logger.warning(f"No Dockerfile found in {runtime_path}, using default runtime")
        return detect_default_runtime(subdomain_path)

    runtime = {
        "name": f"{subdomain_path.name}",
        "version": get_runtime_version(runtime_path),
        "context": runtime_path,
    }

    return runtime
