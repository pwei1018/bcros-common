"""Comprehensive tests for the base utility classes."""

from enum import auto
from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch
from urllib.error import URLError

from flask import Flask
import pytest

from notify_api.config import Config, ProductionConfig, UnitTestingConfig
from notify_api.exceptions.errorhandlers import ExceptionHandler
from notify_api.resources.constants import EndpointVersionPath
from notify_api.resources.meta.meta import info
from notify_api.resources.version_endpoint import VersionEndpoint
from notify_api.utils.base import BaseEnum
from notify_api.utils.util import download_file, to_camel


class SampleBaseEnum(BaseEnum):
    """Test enum using BaseEnum."""

    VALUE_ONE = "value_one"
    VALUE_TWO = "value_two"
    UPPER_CASE = "upper_case"


class TestBaseUtilities:
    """Comprehensive test suite for base utility classes and functions."""

    # BaseMeta tests
    @staticmethod
    def test_contains_valid_value():
        """Test that __contains__ returns True for valid enum values."""
        assert "value_one" in SampleBaseEnum
        assert "value_two" in SampleBaseEnum
        assert "upper_case" in SampleBaseEnum

    @staticmethod
    def test_contains_invalid_value():
        """Test that __contains__ returns False for invalid enum values."""
        test_number = 123
        assert "invalid_value" not in SampleBaseEnum
        assert "VALUE_ONE" not in SampleBaseEnum  # Case sensitive
        assert "" not in SampleBaseEnum
        assert None not in SampleBaseEnum
        assert test_number not in SampleBaseEnum

    @staticmethod
    def test_contains_enum_member():
        """Test that __contains__ works with enum members."""
        assert SampleBaseEnum.VALUE_ONE in SampleBaseEnum
        assert SampleBaseEnum.VALUE_TWO in SampleBaseEnum

    @staticmethod
    def test_contains_edge_cases():
        """Test __contains__ with edge cases."""
        # Test with different types
        assert 0 not in SampleBaseEnum
        assert [] not in SampleBaseEnum
        assert {} not in SampleBaseEnum
        assert False not in SampleBaseEnum

    # BaseEnum functionality tests
    @staticmethod
    def test_str_representation():
        """Test that __str__ returns the string value."""
        assert str(SampleBaseEnum.VALUE_ONE) == "value_one"
        assert str(SampleBaseEnum.VALUE_TWO) == "value_two"
        assert str(SampleBaseEnum.UPPER_CASE) == "upper_case"

    @staticmethod
    def test_enum_value_access():
        """Test accessing enum values."""
        assert SampleBaseEnum.VALUE_ONE.value == "value_one"
        assert SampleBaseEnum.VALUE_TWO.value == "value_two"
        assert SampleBaseEnum.UPPER_CASE.value == "upper_case"

    @staticmethod
    def test_get_enum_by_value_valid():
        """Test get_enum_by_value with valid values."""
        assert SampleBaseEnum.get_enum_by_value("value_one") == SampleBaseEnum.VALUE_ONE
        assert SampleBaseEnum.get_enum_by_value("value_two") == SampleBaseEnum.VALUE_TWO
        assert SampleBaseEnum.get_enum_by_value("upper_case") == SampleBaseEnum.UPPER_CASE

    @staticmethod
    def test_get_enum_by_value_invalid():
        """Test get_enum_by_value with invalid values."""
        assert SampleBaseEnum.get_enum_by_value("invalid_value") is None
        assert SampleBaseEnum.get_enum_by_value("VALUE_ONE") is None  # Case sensitive
        assert SampleBaseEnum.get_enum_by_value("") is None
        assert SampleBaseEnum.get_enum_by_value(None) is None

    @staticmethod
    def test_get_enum_by_value_edge_cases():
        """Test get_enum_by_value with edge cases."""
        test_number = 123
        assert SampleBaseEnum.get_enum_by_value(test_number) is None
        assert SampleBaseEnum.get_enum_by_value([]) is None
        assert SampleBaseEnum.get_enum_by_value({}) is None
        assert SampleBaseEnum.get_enum_by_value(False) is None

    @staticmethod
    def test_enum_iteration():
        """Test that enum can be iterated."""
        values = list(SampleBaseEnum)
        expected_count = 3
        assert len(values) == expected_count
        assert SampleBaseEnum.VALUE_ONE in values
        assert SampleBaseEnum.VALUE_TWO in values
        assert SampleBaseEnum.UPPER_CASE in values

    @staticmethod
    def test_enum_equality():
        """Test enum equality comparisons."""
        assert SampleBaseEnum.VALUE_ONE == SampleBaseEnum.VALUE_ONE
        assert SampleBaseEnum.VALUE_ONE != SampleBaseEnum.VALUE_TWO
        assert SampleBaseEnum.VALUE_ONE == "value_one"
        assert SampleBaseEnum.VALUE_ONE != "value_two"

    @staticmethod
    def test_enum_membership():
        """Test enum membership using 'in' operator."""
        assert SampleBaseEnum.VALUE_ONE in SampleBaseEnum
        assert SampleBaseEnum.VALUE_TWO in SampleBaseEnum
        assert SampleBaseEnum.UPPER_CASE in SampleBaseEnum

    @staticmethod
    def test_generate_next_value_functionality():
        """Test the _generate_next_value_ static method functionality."""

        class TestEnum(BaseEnum):
            TEST_NAME = auto()  # Auto-generated
            ANOTHER_TEST = auto()  # Auto-generated
            lowercase = auto()  # Auto-generated

        # Verify the auto-generation works as expected
        assert str(TestEnum.TEST_NAME) == "test_name"
        assert str(TestEnum.ANOTHER_TEST) == "another_test"
        assert str(TestEnum.lowercase) == "lowercase"

    @staticmethod
    def test_string_inheritance():
        """Test that BaseEnum inherits from str."""
        assert isinstance(SampleBaseEnum.VALUE_ONE, str)
        assert isinstance(SampleBaseEnum.VALUE_TWO, str)

        # Test string operations
        assert SampleBaseEnum.VALUE_ONE.upper() == "VALUE_ONE"
        assert SampleBaseEnum.VALUE_ONE.startswith("value")
        assert "one" in SampleBaseEnum.VALUE_ONE

    @staticmethod
    def test_enum_type_checking():
        """Test type checking and isinstance behavior."""
        assert isinstance(SampleBaseEnum.VALUE_ONE, SampleBaseEnum)
        assert isinstance(SampleBaseEnum.VALUE_ONE, str)
        assert isinstance(SampleBaseEnum.VALUE_ONE, SampleBaseEnum)

    @staticmethod
    def test_enum_comparison_with_strings():
        """Test comparison operations with strings."""
        assert SampleBaseEnum.VALUE_ONE == "value_one"
        assert SampleBaseEnum.VALUE_ONE != "value_two"
        assert SampleBaseEnum.VALUE_ONE < "value_two"  # String comparison
        assert SampleBaseEnum.VALUE_TWO > "value_one"

    @staticmethod
    def test_enum_hashing():
        """Test that enum values can be used as dictionary keys."""
        test_dict = {SampleBaseEnum.VALUE_ONE: "first", SampleBaseEnum.VALUE_TWO: "second"}

        assert test_dict[SampleBaseEnum.VALUE_ONE] == "first"
        assert test_dict[SampleBaseEnum.VALUE_TWO] == "second"

        # Test with string keys too
        string_dict = {"value_one": "first", "value_two": "second"}

        assert string_dict[SampleBaseEnum.VALUE_ONE] == "first"
        assert string_dict[SampleBaseEnum.VALUE_TWO] == "second"

    # Inheritance and integration tests
    @staticmethod
    def test_multiple_enum_classes():
        """Test that multiple enum classes work independently."""

        class AnotherEnum(BaseEnum):
            """Another test enum."""

            ANOTHER_VALUE = "another_value"

        assert SampleBaseEnum.VALUE_ONE != AnotherEnum.ANOTHER_VALUE
        assert "value_one" in SampleBaseEnum
        assert "another_value" in AnotherEnum
        assert "value_one" not in AnotherEnum
        assert "another_value" not in SampleBaseEnum

    @staticmethod
    def test_enum_with_complex_values():
        """Test enum with more complex scenarios."""

        class ComplexEnum(BaseEnum):
            SIMPLE = "simple"
            WITH_UNDERSCORE = "with_underscore"
            WITH_NUMBERS_123 = "with_numbers_123"
            SPECIAL_CHARS = "special-chars"

        assert ComplexEnum.SIMPLE == "simple"
        assert ComplexEnum.WITH_UNDERSCORE == "with_underscore"
        assert ComplexEnum.WITH_NUMBERS_123 == "with_numbers_123"
        assert ComplexEnum.SPECIAL_CHARS == "special-chars"

        assert "simple" in ComplexEnum
        assert "with_underscore" in ComplexEnum
        assert "with_numbers_123" in ComplexEnum
        assert "special-chars" in ComplexEnum

    @staticmethod
    def test_enum_edge_case_values():
        """Test enum with edge case values."""

        class EdgeCaseEnum(BaseEnum):
            EMPTY_STRING = ""
            SINGLE_CHAR = "a"
            LONG_VALUE = "a_very_long_enum_value_with_many_words_and_underscores"

        assert not EdgeCaseEnum.EMPTY_STRING
        assert EdgeCaseEnum.SINGLE_CHAR == "a"
        assert EdgeCaseEnum.LONG_VALUE == "a_very_long_enum_value_with_many_words_and_underscores"

        assert "" in EdgeCaseEnum
        assert "a" in EdgeCaseEnum
        assert "a_very_long_enum_value_with_many_words_and_underscores" in EdgeCaseEnum

    @staticmethod
    def test_enum_case_sensitivity():
        """Test that enum values are case sensitive."""

        class CaseSensitiveEnum(BaseEnum):
            lower_case = "lower_case"
            UPPER_CASE = "UPPER_CASE"
            Mixed_Case = "Mixed_Case"

        assert "lower_case" in CaseSensitiveEnum
        assert "UPPER_CASE" in CaseSensitiveEnum
        assert "Mixed_Case" in CaseSensitiveEnum

        assert "LOWER_CASE" not in CaseSensitiveEnum
        assert "upper_case" not in CaseSensitiveEnum
        assert "mixed_case" not in CaseSensitiveEnum

    @staticmethod
    def test_enum_duplicate_value_handling():
        """Test handling of enums with duplicate values."""

        class DuplicateEnum(BaseEnum):
            FIRST = "same_value"
            SECOND = "same_value"  # Duplicate value

        # Both should work, but they're aliases
        assert DuplicateEnum.FIRST == "same_value"
        assert DuplicateEnum.SECOND == "same_value"
        assert DuplicateEnum.FIRST is DuplicateEnum.SECOND  # They are the same object

        found_enum = DuplicateEnum.get_enum_by_value("same_value")
        assert found_enum == DuplicateEnum.FIRST
        assert found_enum == DuplicateEnum.SECOND

    @staticmethod
    def test_enum_with_none_value():
        """Test enum behavior with explicit string 'None' as a value."""

        class NoneEnum(BaseEnum):
            NONE_VALUE = "None"  # Explicit string instead of None
            STRING_VALUE = "string_value"

        # Test that explicit string values work
        assert NoneEnum.NONE_VALUE == "None"
        assert NoneEnum.STRING_VALUE == "string_value"

        # Test membership
        assert "None" in NoneEnum
        assert "string_value" in NoneEnum
        assert "none" not in NoneEnum  # Case sensitive

    @staticmethod
    def test_get_enum_by_value_comprehensive():
        """Comprehensive test of get_enum_by_value method."""

        class ComprehensiveEnum(BaseEnum):
            ALPHA = "alpha"
            BETA = "beta"
            GAMMA = "gamma"

        # Valid cases
        assert ComprehensiveEnum.get_enum_by_value("alpha") == ComprehensiveEnum.ALPHA
        assert ComprehensiveEnum.get_enum_by_value("beta") == ComprehensiveEnum.BETA
        assert ComprehensiveEnum.get_enum_by_value("gamma") == ComprehensiveEnum.GAMMA

        # Invalid cases
        assert ComprehensiveEnum.get_enum_by_value("delta") is None
        assert ComprehensiveEnum.get_enum_by_value("ALPHA") is None
        assert ComprehensiveEnum.get_enum_by_value("") is None
        assert ComprehensiveEnum.get_enum_by_value(None) is None
        assert ComprehensiveEnum.get_enum_by_value(123) is None
        assert ComprehensiveEnum.get_enum_by_value([]) is None
        assert ComprehensiveEnum.get_enum_by_value({}) is None

    # Utility function tests
    @staticmethod
    def test_download_file_success():
        """Test download_file function success."""
        test_url = "https://example.com/test.pdf"
        test_content = b"test file content"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = test_content
            mock_response.__enter__ = lambda _: mock_response  # noqa: ARG005
            mock_response.__exit__ = lambda *_: None  # noqa: ARG005
            mock_urlopen.return_value = mock_response

            result = download_file(test_url)

            assert result == test_content
            mock_urlopen.assert_called_once_with(test_url)
            mock_response.read.assert_called_once()

    @staticmethod
    def test_download_file_http_error():
        """Test download_file function with HTTP error."""
        test_url = "https://example.com/notfound.pdf"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = URLError("HTTP Error 404: Not Found")

            with pytest.raises(URLError, match="HTTP Error 404: Not Found"):
                download_file(test_url)

            mock_urlopen.assert_called_once_with(test_url)

    @staticmethod
    def test_download_file_timeout_error():
        """Test download_file function with timeout error."""
        test_url = "https://example.com/slow.pdf"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = URLError("timeout")

            with pytest.raises(URLError, match="timeout"):
                download_file(test_url)

            mock_urlopen.assert_called_once_with(test_url)

    @staticmethod
    def test_to_camel_function_usage():
        """Test to_camel function usage."""
        # Test snake_case to camelCase conversion
        assert to_camel("snake_case") == "snakeCase"
        assert to_camel("test_field_name") == "testFieldName"
        assert to_camel("single") == "single"
        assert to_camel("already_camelcase") == "alreadyCamelcase"

        # Test with underscores at start/end
        assert to_camel("_private_field") == "_private_field"
        assert to_camel("field_name_") == "fieldName"

    # Config tests
    @staticmethod
    def test_config_database_url_construction():
        """Test database URL construction in config."""

        # Test that the config class variables are accessible
        # Since Config class variables are evaluated at import time,
        # we test that the attribute exists and is a string
        config = Config()

        # Test that SQLALCHEMY_DATABASE_URI is accessible and is a string
        assert hasattr(config, "SQLALCHEMY_DATABASE_URI")
        assert isinstance(config.SQLALCHEMY_DATABASE_URI, str)
        assert "postgresql+pg8000" in config.SQLALCHEMY_DATABASE_URI

    @staticmethod
    def test_config_testing_environment():
        """Test config in testing environment."""
        config = UnitTestingConfig()

        # Test testing-specific configurations
        assert config.TESTING is True
        assert "postgresql+pg8000" in config.SQLALCHEMY_DATABASE_URI

    @staticmethod
    def test_config_production_settings():
        """Test config production settings."""
        config = ProductionConfig()

        assert config.DEBUG is False
        # Test that SQLALCHEMY_DATABASE_URI exists and contains the expected driver
        assert hasattr(config, "SQLALCHEMY_DATABASE_URI")
        assert isinstance(config.SQLALCHEMY_DATABASE_URI, str)
        assert "postgresql+pg8000" in config.SQLALCHEMY_DATABASE_URI
        assert config.DEVELOPMENT is False

    # Error handler tests
    @staticmethod
    def test_error_handler_business_exception():
        """Test error handler for business exceptions."""
        app = Flask(__name__)
        exception_handler = ExceptionHandler(app)

        # Test that exception handler is properly initialized
        assert exception_handler.app == app

    @staticmethod
    def test_error_handler_validation_error(app):
        """Test error handler for validation errors."""
        # Mock a validation error
        mock_error = Mock()
        mock_error.body_params = None
        mock_error.query_params = [{"msg": "field required"}]
        mock_error.path_params = None

        handler = ExceptionHandler()

        with app.app_context():
            response, status_code, headers = handler.validation_handler(mock_error)

        assert status_code == HTTPStatus.BAD_REQUEST
        assert "error" in response
        assert response["error"] == "field required"

    @staticmethod
    def test_error_handler_default_exception_handler(app):
        """Test default exception handler."""

        handler = ExceptionHandler()

        # Test with Exception
        test_exception = Exception("Test error message")

        with app.test_request_context():
            response, status_code, headers = handler.std_handler(test_exception)

        assert status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "message" in response
        assert response["message"] == "Internal server error"

    @staticmethod
    def test_error_handler_business_exception_handler(app):
        """Test business exception handler."""
        handler = ExceptionHandler()
        business_error = ValueError("Business logic error")

        with app.test_request_context():
            response, status_code, headers = handler.std_handler(business_error)

        assert status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "message" in response
        assert response["message"] == "Internal server error"

    # Version endpoint tests
    @staticmethod
    def test_version_endpoint_ops_healthz():
        """Test version endpoint initialization."""
        # Create a version endpoint instance
        version_endpoint = VersionEndpoint("test", EndpointVersionPath.API_V1, [])

        assert version_endpoint.version_bp is not None
        assert version_endpoint.version_bp.name == "test"

    @staticmethod
    def test_version_endpoint_ops_readyz():
        """Test version endpoint with app initialization."""
        # Create a mock Flask app
        mock_app = Mock()
        mock_app.register_blueprint = Mock()

        # Create a version endpoint instance and initialize it
        version_endpoint = VersionEndpoint("test", EndpointVersionPath.API_V1, [])
        version_endpoint.init_app(mock_app)

        assert version_endpoint.app == mock_app
        mock_app.register_blueprint.assert_called_once_with(version_endpoint.version_bp)

    @staticmethod
    def test_version_endpoint_initialization():
        """Test version endpoint blueprint initialization with exception."""
        # Test initialization without Flask app
        version_endpoint = VersionEndpoint("test", EndpointVersionPath.API_V1, [])

        # Test exception when trying to initialize with None app
        with pytest.raises(Exception, match="Cannot initialize without a Flask App"):
            version_endpoint.init_app(None)

    @staticmethod
    def test_meta_endpoint_info(app):
        """Test meta endpoint info method."""
        with app.app_context():
            response = info()

            assert response is not None
            # Response should contain API information
            response_data = response.get_json()
            assert "API" in response_data
            assert "FrameWork" in response_data
            assert "notify_api" in response_data["API"]
