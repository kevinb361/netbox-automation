"""Unit tests for config module.

Tests YAML loading, environment variable overrides, and validation.
Covers: UNIT-05 (YAML loading), UNIT-06 (env var overrides), UNIT-07 (validation).
"""

from pathlib import Path

import pytest

import netbox_auto.config as config_module
from netbox_auto.config import (
    Config,
    ConfigError,
    load_config,
)


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global config before each test to ensure isolation."""
    config_module._config = None
    yield
    config_module._config = None


# =============================================================================
# UNIT-05: Config loads from YAML file correctly
# =============================================================================


def test_load_config_reads_yaml_file(tmp_path: Path) -> None:
    """Given a valid YAML file with mikrotik section, load_config returns populated Config."""
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        """
mikrotik:
  host: 192.168.1.1
  username: admin
  password: secret123
  port: 8728
"""
    )

    config = load_config(config_yaml)

    assert config.mikrotik is not None
    assert config.mikrotik.host == "192.168.1.1"
    assert config.mikrotik.username == "admin"
    assert config.mikrotik.password == "secret123"
    assert config.mikrotik.port == 8728


def test_load_config_missing_file_raises_error(tmp_path: Path) -> None:
    """Given a non-existent config path, load_config raises ConfigError."""
    nonexistent = tmp_path / "nonexistent.yaml"

    with pytest.raises(ConfigError) as exc_info:
        load_config(nonexistent)

    assert "Configuration file not found" in str(exc_info.value)
    assert str(nonexistent) in str(exc_info.value)


def test_load_config_invalid_yaml_raises_error(tmp_path: Path) -> None:
    """Given malformed YAML content, load_config raises ConfigError."""
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        """
mikrotik:
  host: 192.168.1.1
  bad yaml here: [unclosed bracket
"""
    )

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_yaml)

    assert "Invalid YAML" in str(exc_info.value)


def test_load_config_empty_file_returns_defaults(tmp_path: Path) -> None:
    """Given an empty YAML file, load_config returns Config with default values."""
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("---\n")

    config = load_config(config_yaml)

    # Should return valid Config with defaults
    assert isinstance(config, Config)
    assert config.mikrotik is None
    assert config.proxmox is None
    assert config.netbox is None
    assert config.switches == []
    # Database and discovery have default factories
    assert config.database.path == "netbox-auto.db"
    assert config.discovery.include_ipv6 is False
