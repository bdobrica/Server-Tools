#!/usr/bin/env python3
"""
Test script to verify PostgreSQL configuration path detection.
This script tests the updated PostgreSQL managers to ensure they correctly
detect configuration paths in chroot environments.
"""

import sys
from pathlib import Path

# Add the site_builder module to the path
sys.path.insert(0, str(Path(__file__).parent / "site-builder"))

try:
    from site_builder.database.postgresql_native import PostgreSQLNativeManager
    from site_builder.database.postgresql_docker import PostgreSQLDockerManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


def test_postgres_config_detection():
    """Test PostgreSQL configuration path detection."""
    print("Testing PostgreSQL configuration path detection...")

    # Test native manager
    print("\n1. Testing PostgreSQL Native Manager:")
    try:
        native_manager = PostgreSQLNativeManager(config_path=Path("/tmp/test-postgres"), template_vars={})
        print(f"   Detected config path: {native_manager.postgres_config_path}")
        print(f"   Config file: {native_manager.config_file}")
        print(f"   HBA config: {native_manager.hba_config}")

        # Show connection info
        conn_info = native_manager.get_connection_info()
        print(f"   Connection info: {conn_info}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test docker manager
    print("\n2. Testing PostgreSQL Docker Manager:")
    try:
        docker_manager = PostgreSQLDockerManager(
            config_path=Path("/tmp/test-postgres-docker"),
            template_vars={},
            docker_compose_path=Path("/tmp/docker-compose.yml"),
        )
        print(f"   Container config path: {docker_manager.config_path}")
        print(f"   Host config path: {docker_manager.postgres_host_config_path}")
        print(f"   Config file: {docker_manager.config_file}")

        # Show connection info
        conn_info = docker_manager.get_connection_info()
        print(f"   Connection info: {conn_info}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test path detection manually
    print("\n3. Manual Path Detection Test:")
    test_paths = [
        Path("/etc/postgresql"),
        Path("/etc/postgresql/15/main"),
        Path("/etc/postgresql/14/main"),
        Path("/etc/postgresql/13/main"),
        Path("/var/lib/pgsql/data"),
        Path("/usr/local/pgsql/data"),
    ]

    for path in test_paths:
        exists = "✓" if path.exists() else "✗"
        print(f"   {exists} {path}")

        if path.exists() and path.name == "main":
            config_file = path / "postgresql.conf"
            conf_exists = "✓" if config_file.exists() else "✗"
            print(f"     {conf_exists} {config_file}")


if __name__ == "__main__":
    test_postgres_config_detection()
