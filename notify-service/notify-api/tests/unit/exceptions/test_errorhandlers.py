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
"""Tests for ExceptionHandler.validation_handler()."""

from http import HTTPStatus
from types import SimpleNamespace

from notify_api.exceptions.errorhandlers import ExceptionHandler


def _make_error(body_params=None, query_params=None, path_params=None, form_params=None):
    """Build a stand-in for flask_pydantic.exceptions.ValidationError."""
    return SimpleNamespace(
        body_params=body_params,
        query_params=query_params,
        path_params=path_params,
        form_params=form_params,
    )


class TestValidationHandler:
    """Test suite for ExceptionHandler.validation_handler()."""

    def test_single_error_strips_value_error_prefix(self, app):
        """A single custom validator error should read cleanly, without pydantic's prefix."""
        error = _make_error(
            body_params=[
                {
                    "type": "value_error",
                    "loc": ("recipients",),
                    "msg": "Value error, Invalid recipient: -.",
                    "input": "-",
                    "ctx": {"error": {"type": "ValueError", "message": "Invalid recipient: -."}},
                    "url": "https://errors.pydantic.dev/2.13/v/value_error",
                }
            ]
        )

        with app.test_request_context("/api/v1/notify"):
            body, status, _headers = ExceptionHandler.validation_handler(error)

        assert status == HTTPStatus.BAD_REQUEST
        assert body["error"] == "Validation Error"
        assert body["message"] == "recipients: Invalid recipient: -."
        assert body["details"] == [{"field": "recipients", "message": "Invalid recipient: -."}]

    def test_multiple_errors_are_all_reported(self, app):
        """All invalid fields should be surfaced, not just the first one."""
        error = _make_error(
            body_params=[
                {"type": "value_error", "loc": ("recipients",), "msg": "Value error, Invalid recipient: -."},
                {"type": "value_error", "loc": ("content", 0, "subject"), "msg": "Value error, The email subject must not empty."},
            ]
        )

        with app.test_request_context("/api/v1/notify"):
            body, status, _headers = ExceptionHandler.validation_handler(error)

        assert status == HTTPStatus.BAD_REQUEST
        assert len(body["details"]) == 2  # noqa: PLR2004
        assert body["details"][0] == {"field": "recipients", "message": "Invalid recipient: -."}
        assert body["details"][1] == {
            "field": "content.0.subject",
            "message": "The email subject must not empty.",
        }
        assert "recipients: Invalid recipient: -." in body["message"]
        assert "content.0.subject: The email subject must not empty." in body["message"]

    def test_message_without_value_error_prefix_is_unchanged(self, app):
        """A non-custom pydantic message (no "Value error, " prefix) is passed through as-is."""
        error = _make_error(query_params=[{"type": "missing", "loc": ("page",), "msg": "Field required"}])

        with app.test_request_context("/api/v1/notify"):
            body, _status, _headers = ExceptionHandler.validation_handler(error)

        assert body["details"] == [{"field": "page", "message": "Field required"}]

    def test_falls_back_through_param_sources(self, app):
        """path_params and form_params are consulted when body/query are absent."""
        error = _make_error(path_params=[{"type": "value_error", "loc": ("id",), "msg": "Value error, Invalid id."}])

        with app.test_request_context("/api/v1/notify"):
            body, _status, _headers = ExceptionHandler.validation_handler(error)

        assert body["details"] == [{"field": "id", "message": "Invalid id."}]

    def test_no_error_details_returns_generic_message(self, app):
        """When flask_pydantic provides no details at all, fall back to a generic message."""
        error = _make_error()

        with app.test_request_context("/api/v1/notify"):
            body, status, _headers = ExceptionHandler.validation_handler(error)

        assert status == HTTPStatus.BAD_REQUEST
        assert body == {"error": "Validation Error", "message": "Validation Error"}
