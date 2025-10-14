__version__ = "1.0.0"

from pathlib import Path


def get_docker_resource_path(image_name: str) -> Path:
    """Get the path to a docker image resource directory.

    Args:
        image_name: Name of the docker image (e.g., 'lighttpd-php8', 'nginx-php8')

    Returns:
        Path to the docker image resource directory
    """
    # Use direct path approach for better compatibility
    resources_dir = Path(__file__).parent / "resources"
    return resources_dir / image_name


def get_template_path() -> Path:
    """Get the path to the templates directory.

    Returns:
        Path to the templates directory
    """
    # Use direct path approach for better compatibility
    return Path(__file__).parent / "templates"
