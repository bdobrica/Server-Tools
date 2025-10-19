#!/usr/bin/env python3
"""
Simple test to verify PostgreSQL path detection logic works correctly.
"""

import tempfile
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


def create_mock_postgres_structure():
    """Create a mock PostgreSQL directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create mock PostgreSQL structure: /etc/postgresql/15/main/
        pg_base = temp_path / "etc" / "postgresql"
        pg_version_dir = pg_base / "15" / "main"
        pg_version_dir.mkdir(parents=True)

        # Create mock postgresql.conf
        config_file = pg_version_dir / "postgresql.conf"
        config_file.write_text("# Mock PostgreSQL configuration\n")

        print(f"Created mock structure at: {temp_path}")
        print(f"PostgreSQL config at: {config_file}")

        # Test the managers with mock structure
        test_managers_with_mock_structure(temp_path)


def test_managers_with_mock_structure(base_path):
    """Test managers with a mock PostgreSQL structure."""
    # Patch the _find_postgres_config_path method to look in our test directory
    pg_base = base_path / "etc" / "postgresql"

    print("\nTesting with mock PostgreSQL structure:")

    # Test native manager
    try:
        native_manager = PostgreSQLNativeManager(
            config_path=base_path / "tmp" / "test-postgres",
            template_vars={},
            postgres_config_path=pg_base / "15" / "main",  # Explicitly set for test
        )
        print(f"✓ Native manager config path: {native_manager.postgres_config_path}")
        print(f"  Config file: {native_manager.config_file}")

        conn_info = native_manager.get_connection_info()
        print(f"  Config path in connection info: {conn_info['config_path']}")

    except Exception as e:
        print(f"✗ Native manager error: {e}")

    # Test docker manager
    try:
        docker_manager = PostgreSQLDockerManager(
            config_path=base_path / "tmp" / "test-postgres-docker",
            template_vars={},
            docker_compose_path=base_path / "docker-compose.yml",
            postgres_host_config_path=pg_base / "15" / "main",  # Explicitly set for test
        )
        print(f"✓ Docker manager host config path: {docker_manager.postgres_host_config_path}")
        print(f"  Container config file: {docker_manager.config_file}")

        conn_info = docker_manager.get_connection_info()
        print(f"  Host config path in connection info: {conn_info['host_config_path']}")

    except Exception as e:
        print(f"✗ Docker manager error: {e}")


if __name__ == "__main__":
    create_mock_postgres_structure()
