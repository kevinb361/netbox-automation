"""Configuration module for netbox-auto.

Provides Pydantic models for configuration with YAML loading
and environment variable override support.

Env var format: NETBOX_AUTO_{SECTION}__{FIELD}
Example: NETBOX_AUTO_MIKROTIK__PASSWORD overrides mikrotik.password
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MikroTikConfig(BaseModel):
    """MikroTik router connection configuration."""

    host: str = Field(description="MikroTik router hostname or IP")
    username: str = Field(description="API username")
    password: str = Field(default="", description="API password")
    port: int = Field(default=8728, description="API port (default 8728)")


class SwitchConfig(BaseModel):
    """MikroTik switch connection configuration for MAC table queries."""

    host: str = Field(description="Switch hostname or IP")
    username: str = Field(description="API username")
    password: str = Field(default="", description="API password")
    port: int = Field(default=8728, description="API port (default 8728)")
    name: str = Field(description="Friendly name for the switch (used in switch_port field)")


class ProxmoxConfig(BaseModel):
    """Proxmox API connection configuration."""

    host: str = Field(description="Proxmox hostname or IP")
    username: str = Field(description="API username (e.g., user@pam)")
    password: str = Field(default="", description="API password or token")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class NetBoxConfig(BaseModel):
    """NetBox API connection configuration."""

    url: str = Field(description="NetBox API URL (e.g., https://netbox.example.com)")
    token: str = Field(description="API token")


class UnboundHostConfig(BaseModel):
    """Configuration for a single Unbound DNS server."""

    host: str = Field(description="SSH hostname or IP")
    user: str = Field(description="SSH username")
    config_path: str = Field(
        default="/etc/unbound/local.d/local.conf",
        description="Path to Unbound local records config",
    )


class UnboundConfig(BaseModel):
    """Unbound DNS configuration for all managed servers."""

    hosts: list[UnboundHostConfig] = Field(
        default_factory=list, description="List of Unbound servers to update"
    )


class ScannerConfig(BaseModel):
    """Network scanner configuration for ARP-based host discovery."""

    subnets: list[str] = Field(
        description="List of subnets to scan (CIDR notation, e.g., '192.168.1.0/24')"
    )
    timeout: float = Field(default=2.0, description="ARP response timeout in seconds")


class DatabaseConfig(BaseModel):
    """Local database configuration."""

    path: str = Field(default="netbox-auto.db", description="Path to SQLite database file")


class Config(BaseSettings):
    """Main configuration for netbox-auto.

    Loads from YAML file with environment variable override support.
    Env vars use format: NETBOX_AUTO_{SECTION}__{FIELD}
    """

    model_config = SettingsConfigDict(
        env_prefix="NETBOX_AUTO_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    mikrotik: MikroTikConfig | None = Field(
        default=None, description="MikroTik router configuration"
    )
    switches: list[SwitchConfig] = Field(
        default_factory=list, description="MikroTik switches to query for MAC tables"
    )
    proxmox: ProxmoxConfig | None = Field(
        default=None, description="Proxmox API configuration (optional)"
    )
    scanner: ScannerConfig | None = Field(
        default=None, description="Network scanner configuration"
    )
    netbox: NetBoxConfig | None = Field(default=None, description="NetBox API configuration")
    unbound: UnboundConfig = Field(
        default_factory=UnboundConfig, description="Unbound DNS configuration"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="Local database configuration"
    )


# Global cached config instance
_config: Config | None = None


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _get_env_overrides() -> dict[str, Any]:
    """Extract config overrides from environment variables.

    Looks for NETBOX_AUTO_* env vars and converts them to nested dict.
    NETBOX_AUTO_MIKROTIK__PASSWORD=secret -> {"mikrotik": {"password": "secret"}}
    """
    prefix = "NETBOX_AUTO_"
    overrides: dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        # Remove prefix and split by delimiter
        parts = key[len(prefix) :].lower().split("__")

        # Build nested dict
        current = overrides
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    return overrides


def load_config(path: Path | None = None) -> Config:
    """Load configuration from YAML file with environment variable overrides.

    Args:
        path: Path to config file. Defaults to ./config.yaml

    Returns:
        Validated Config instance.

    Raises:
        ConfigError: If file not found or validation fails.
    """
    global _config

    config_path = path or Path("config.yaml")

    if not config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {config_path}\n"
            f"Create a config file by copying config.example.yaml:\n"
            f"  cp config.example.yaml config.yaml\n"
            f"Then edit with your credentials."
        )

    try:
        with open(config_path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}") from e

    # Apply environment variable overrides
    env_overrides = _get_env_overrides()
    if env_overrides:
        data = _deep_merge(data, env_overrides)

    try:
        _config = Config(**data)
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}") from e

    return _config


def get_config() -> Config:
    """Get the loaded configuration.

    Returns:
        The cached Config instance.

    Raises:
        ConfigError: If config has not been loaded yet.
    """
    if _config is None:
        raise ConfigError(
            "Configuration not loaded. Call load_config() first or ensure "
            "the CLI was started with a valid config file."
        )
    return _config
