# PostgreSQL Configuration Path Updates

## Summary

Updated both PostgreSQL managers (`postgresql_docker.py` and `postgresql_native.py`) to correctly handle the PostgreSQL configuration directory structure used in Debian/Ubuntu systems, particularly in chroot environments.

## Key Changes

### 1. Automatic Path Detection

Both managers now automatically detect the correct PostgreSQL configuration path:

- **Debian/Ubuntu**: `/etc/postgresql/<version>/main/`
- **CentOS/RHEL**: `/var/lib/pgsql/data`
- **Source installations**: `/usr/local/pgsql/data`
- **Fallback**: `/etc/postgresql/15/main/`

### 2. Updated Constructor Parameters

#### PostgreSQL Native Manager
```python
def __init__(
    self,
    config_path: Path,
    template_vars: Dict[str, Any],
    postgres_config_path: Optional[Path] = None,  # Now optional, auto-detected if None
    root_password: Optional[str] = None,
)
```

#### PostgreSQL Docker Manager
```python  
def __init__(
    self,
    config_path: Path,
    template_vars: Dict[str, Any],
    docker_compose_path: Path,
    postgres_host_config_path: Optional[Path] = None,  # New optional parameter
    root_password: Optional[str] = None,
)
```

### 3. Enhanced Configuration Generation

- **Native Manager**: Automatically finds the correct system PostgreSQL configuration directory
- **Docker Manager**: Can map host PostgreSQL configurations into containers
- Both managers now copy from existing system configurations when available

### 4. Improved Error Handling

- Graceful fallback when system configurations are not found
- Better permission handling for configuration file access
- Warning messages when expected configurations are missing

### 5. Enhanced Connection Information

Both managers now return additional metadata in `get_connection_info()`:

```python
{
    "host": "localhost",
    "port": 5432,
    "username": "postgres", 
    "password": "...",
    "type": "native|docker",
    "config_path": "/path/to/config",
    "config_file": "/path/to/postgresql.conf",
    # Docker manager also includes:
    "host_config_path": "/etc/postgresql/15/main"
}
```

### 6. Command Line Interface Updates

Updated the `--postgres-config-path` argument:
- Now optional (defaults to `None` for auto-detection)
- Updated help text to reflect the typical path structure

## Compatibility

- **Backward Compatible**: Existing code that explicitly passes configuration paths will continue to work
- **Chroot Friendly**: Automatically detects PostgreSQL configurations in chroot environments
- **Multi-Distribution**: Supports various Linux distributions and PostgreSQL installation methods

## Testing

The changes have been tested with:
- Mock PostgreSQL directory structures
- Permission handling scenarios  
- Path detection logic across different system configurations

## Files Modified

1. `/site-builder/site_builder/database/postgresql_native.py`
2. `/site-builder/site_builder/database/postgresql_docker.py` 
3. `/site-builder/site_builder/__main__.py` (command line argument defaults)

The changes ensure that PostgreSQL configuration files are correctly located in chroot environments created by `setup-simple-chroot.sh` while maintaining compatibility with standard system installations.
