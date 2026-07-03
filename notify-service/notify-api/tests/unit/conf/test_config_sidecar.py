"""Tests for Cloud SQL Proxy sidecar database URI configuration."""

import json
import os
import subprocess
import sys

import pytest


def _resolve_uris(env_overrides: dict[str, str]) -> dict[str, str]:
    """Import the config in a clean subprocess and return the resolved URIs.

    A subprocess is used so module-level (import-time) config evaluation picks up
    the provided environment without mutating the shared module cache used by the
    session-scoped ``app`` fixture.
    """
    script = (
        "import json;"
        "from notify_api.config import Config, MigrationConfig;"
        "print(json.dumps({"
        "'config_sidecar': Config.CLOUD_SQL_PROXY_SIDECAR,"
        "'config_uri': Config.SQLALCHEMY_DATABASE_URI,"
        "'migration_sidecar': MigrationConfig.CLOUD_SQL_PROXY_SIDECAR,"
        "'migration_uri': MigrationConfig.SQLALCHEMY_DATABASE_URI,"
        "}))"
    )

    base_env = {
        "PATH": os.environ.get("PATH", ""),
        # IAM username intentionally contains an "@" to verify URL-encoding.
        "NOTIFY_DATABASE_USERNAME": "sa-api@c4hnrd-dev.iam",
        "NOTIFY_DATABASE_NAME": "notifydb",
        "NOTIFY_DATABASE_PORT": "5432",
    }
    base_env.update(env_overrides)

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        env=base_env,
    )
    return json.loads(result.stdout.strip())


@pytest.mark.parametrize("flag_value", ["true", "yes", "1", "on", "TRUE", "Yes", " on "])
def test_sidecar_enabled_uses_local_psycopg_uri(flag_value):
    """When the sidecar flag is on (any truthy form), configs target 127.0.0.1 via psycopg.

    The IAM username's "@" must be URL-encoded to "%40" so the single host "@"
    separator stays unambiguous.
    """
    uris = _resolve_uris({"CLOUD_SQL_PROXY_SIDECAR": flag_value})

    expected = "postgresql+psycopg://sa-api%40c4hnrd-dev.iam@127.0.0.1:5432/notifydb"

    assert uris["config_sidecar"] is True
    assert uris["config_uri"] == expected
    assert uris["migration_sidecar"] is True
    assert uris["migration_uri"] == expected


def test_sidecar_enabled_ignores_instance_connection_name():
    """Sidecar mode takes precedence over the Cloud SQL connector branch."""
    uris = _resolve_uris({
        "CLOUD_SQL_PROXY_SIDECAR": "true",
        "NOTIFY_DATABASE_INSTANCE_CONNECTION_NAME": "project:region:instance",
    })

    expected = "postgresql+psycopg://sa-api%40c4hnrd-dev.iam@127.0.0.1:5432/notifydb"

    assert uris["config_uri"] == expected
    assert uris["migration_uri"] == expected


def test_sidecar_disabled_uses_pg8000_connector_uri():
    """Without the sidecar flag, the connector (pg8000) branch is used."""
    uris = _resolve_uris({
        "CLOUD_SQL_PROXY_SIDECAR": "false",
        "NOTIFY_DATABASE_INSTANCE_CONNECTION_NAME": "project:region:instance",
    })

    assert uris["config_sidecar"] is False
    assert uris["config_uri"] == "postgresql+pg8000://"
    assert uris["migration_sidecar"] is False
    assert uris["migration_uri"] == "postgresql+pg8000://"


@pytest.mark.parametrize("flag_value", ["false", "no", "0", "off", "", "maybe"])
def test_sidecar_non_truthy_values_disable_sidecar(flag_value):
    """Non-truthy flag values keep the connector (pg8000) branch active."""
    uris = _resolve_uris({
        "CLOUD_SQL_PROXY_SIDECAR": flag_value,
        "NOTIFY_DATABASE_INSTANCE_CONNECTION_NAME": "project:region:instance",
    })

    assert uris["config_sidecar"] is False
    assert uris["config_uri"] == "postgresql+pg8000://"
    assert uris["migration_sidecar"] is False
    assert uris["migration_uri"] == "postgresql+pg8000://"
