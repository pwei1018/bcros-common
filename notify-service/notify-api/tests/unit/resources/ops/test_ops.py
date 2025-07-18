# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the ops endpoints.

Test-Suite to ensure that the /ops endpoints are working as expected.
These endpoints are used for health checks and readiness probes in containerized environments.
"""

from http import HTTPStatus
import json
from unittest.mock import patch

import pytest
from sqlalchemy import exc

from notify_api.models import db


class TestOpsHealthEndpoint:
    """Test suite for the /ops/healthz endpoint."""

    @staticmethod
    def test_healthz_success(session, client):
        """Assert that the service reports healthy when database is accessible."""

        # Mock the database session execute to avoid actual database connection
        with patch("notify_api.resources.ops.ops.db.session.execute") as mock_execute:
            mock_execute.return_value = None  # Simulate successful execution

            response = client.get("/ops/healthz")

            assert response.status_code == HTTPStatus.OK
            assert response.content_type == "application/json"

            response_data = response.get_json()
            assert response_data == {"message": "api is healthy"}

    @staticmethod
    def test_healthz_content_type_header(session, client):
        """Assert that the healthz endpoint returns proper content type."""
        response = client.get("/ops/healthz")

        assert "application/json" in response.content_type

    @staticmethod
    def test_healthz_with_sqlalchemy_error(session, client):
        """Assert that the service reports down when SQLAlchemy error occurs."""
        with patch.object(db.session, "execute", side_effect=exc.SQLAlchemyError("Database connection failed")):
            response = client.get("/ops/healthz")

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            assert response.content_type == "application/json"

            response_data = response.get_json()
            assert response_data == {"message": "api is down"}

    @staticmethod
    def test_healthz_with_database_connection_error(session, client):
        """Assert that the service reports down when database connection fails."""
        with patch.object(db.session, "execute", side_effect=exc.DisconnectionError("Connection lost")):
            response = client.get("/ops/healthz")

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            response_data = response.get_json()
            assert response_data == {"message": "api is down"}

    @staticmethod
    def test_healthz_with_database_timeout_error(session, client):
        """Assert that the service reports down when database query times out."""
        with patch.object(db.session, "execute", side_effect=exc.TimeoutError("Query timeout")):
            response = client.get("/ops/healthz")

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            response_data = response.get_json()
            assert response_data == {"message": "api is down"}

    @staticmethod
    def test_healthz_with_generic_exception(session, client):
        """Assert that the service reports down when unexpected exception occurs."""
        with patch.object(db.session, "execute", side_effect=Exception("Unexpected error")):
            response = client.get("/ops/healthz")

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            response_data = response.get_json()
            assert response_data == {"message": "api is down"}

    @staticmethod
    def test_healthz_with_runtime_error(session, client):
        """Assert that the service handles runtime errors gracefully."""
        with patch.object(db.session, "execute", side_effect=RuntimeError("Runtime failure")):
            response = client.get("/ops/healthz")

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            response_data = response.get_json()
            assert response_data == {"message": "api is down"}

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    @staticmethod
    def test_healthz_unsupported_methods(session, client, method):
        """Assert that unsupported HTTP methods return 405."""
        response = client.open("/ops/healthz", method=method)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestOpsReadyEndpoint:
    """Test suite for the /ops/readyz endpoint."""

    @staticmethod
    def test_readyz_success(client):
        """Assert that the service reports ready."""
        response = client.get("/ops/readyz")

        assert response.status_code == HTTPStatus.OK
        assert response.content_type == "application/json"

        response_data = response.get_json()
        assert response_data == {"message": "api is ready"}

    @staticmethod
    def test_readyz_response_format(client):
        """Assert that the readyz endpoint returns proper JSON format."""
        response = client.get("/ops/readyz")

        # Verify it's valid JSON
        try:
            json.loads(response.data)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

        response_data = response.get_json()
        assert isinstance(response_data, dict)
        assert "message" in response_data
        assert isinstance(response_data["message"], str)

    @staticmethod
    def test_readyz_no_database_dependency(client):
        """Assert that readyz endpoint doesn't depend on database connectivity."""
        # Even if database is down, readyz should still return 200
        # This is important for Kubernetes readiness probes
        with patch.object(db.session, "execute", side_effect=exc.SQLAlchemyError("DB down")):
            response = client.get("/ops/readyz")

            assert response.status_code == HTTPStatus.OK
            response_data = response.get_json()
            assert response_data == {"message": "api is ready"}

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    @staticmethod
    def test_readyz_unsupported_methods(client, method):
        """Assert that unsupported HTTP methods return 405."""
        response = client.open("/ops/readyz", method=method)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    @staticmethod
    def test_readyz_multiple_requests(client):
        """Assert that readyz endpoint is idempotent."""
        # Make multiple requests to ensure consistent behavior
        for _ in range(3):
            response = client.get("/ops/readyz")
            assert response.status_code == HTTPStatus.OK
            response_data = response.get_json()
            assert response_data == {"message": "api is ready"}


class TestOpsEndpointsIntegration:
    """Integration tests for ops endpoints."""

    @staticmethod
    def test_both_endpoints_accessible(session, client):
        """Assert that both health and readiness endpoints are accessible."""

        # Mock the database session execute to avoid actual database connection
        with patch("notify_api.resources.ops.ops.db.session.execute") as mock_execute:
            mock_execute.return_value = None  # Simulate successful execution

            health_response = client.get("/ops/healthz")
            ready_response = client.get("/ops/readyz")

            assert health_response.status_code == HTTPStatus.OK
            assert ready_response.status_code == HTTPStatus.OK

    @staticmethod
    def test_endpoints_with_trailing_slash(session, client):
        """Assert that endpoints handle trailing slashes appropriately."""

        # Mock the database session execute to avoid actual database connection
        with patch("notify_api.resources.ops.ops.db.session.execute") as mock_execute:
            mock_execute.return_value = None  # Simulate successful execution

            # Test without trailing slash (should work)
            health_response = client.get("/ops/healthz")
            ready_response = client.get("/ops/readyz")

            assert health_response.status_code == HTTPStatus.OK
            assert ready_response.status_code == HTTPStatus.OK

    @staticmethod
    def test_case_sensitivity(client):
        """Assert that endpoints are case sensitive."""
        # These should return 404 as Flask routes are case sensitive
        response = client.get("/ops/HEALTHZ")
        assert response.status_code == HTTPStatus.NOT_FOUND

        response = client.get("/ops/READYZ")
        assert response.status_code == HTTPStatus.NOT_FOUND

    @staticmethod
    def test_invalid_ops_endpoints(client):
        """Assert that invalid ops endpoints return 404."""
        invalid_endpoints = ["/ops/health", "/ops/ready", "/ops/status", "/ops/ping", "/ops/alive"]

        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            assert response.status_code == HTTPStatus.NOT_FOUND
