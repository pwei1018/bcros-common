"""Comprehensive tests for Callback model."""

from datetime import datetime
from unittest.mock import patch

import pytest

from notify_api.models.callback import Callback, CallbackRequest


class TestCallbackRequest:
    """Test CallbackRequest model."""

    @staticmethod
    def test_callback_request_creation_with_all_fields():
        """Test creating CallbackRequest with all fields."""
        # Arrange
        callback_data = {
            "id": "123",
            "reference": "ref-456",
            "to": "test@example.com",
            "status": "delivered",
            "status_description": "Message delivered successfully",
            "provider_response": "OK",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:05:00Z",
            "completed_at": "2024-01-01T10:10:00Z",
            "sent_at": "2024-01-01T10:08:00Z",
            "notification_type": "email",
        }

        # Act
        callback = CallbackRequest(**callback_data)

        # Assert
        assert callback.id == "123"
        assert callback.reference == "ref-456"
        assert callback.to == "test@example.com"
        assert callback.status == "delivered"
        assert callback.status_description == "Message delivered successfully"
        assert callback.provider_response == "OK"
        assert callback.created_at == "2024-01-01T10:00:00Z"
        assert callback.updated_at == "2024-01-01T10:05:00Z"
        assert callback.completed_at == "2024-01-01T10:10:00Z"
        assert callback.sent_at == "2024-01-01T10:08:00Z"
        assert callback.notification_type == "email"

    @staticmethod
    def test_callback_request_creation_with_minimal_fields():
        """Test creating CallbackRequest with minimal fields."""
        # Act
        callback = CallbackRequest()

        # Assert
        assert callback.id is None
        assert callback.reference is None
        assert callback.to is None
        assert callback.status is None
        assert callback.status_description is None
        assert callback.provider_response is None
        assert callback.created_at is None
        assert callback.updated_at is None
        assert callback.completed_at is None
        assert callback.sent_at is None
        assert callback.notification_type is None

    @staticmethod
    def test_callback_request_with_partial_data():
        """Test creating CallbackRequest with partial data."""
        # Arrange
        partial_data = {"id": "789", "to": "partial@example.com", "status": "pending"}

        # Act
        callback = CallbackRequest(**partial_data)

        # Assert
        assert callback.id == "789"
        assert callback.to == "partial@example.com"
        assert callback.status == "pending"
        assert callback.reference is None
        assert callback.status_description is None


class TestCallback:
    """Test Callback database model."""

    @pytest.fixture
    @staticmethod
    def sample_callback_request():
        """Sample CallbackRequest for testing."""
        return CallbackRequest(
            id="test-123",
            reference="ref-456",
            to="test@example.com",
            status="delivered",
            status_description="Successfully delivered",
            provider_response="200 OK",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:05:00Z",
            completed_at="2024-01-01T10:10:00Z",
            sent_at="2024-01-01T10:08:00Z",
            notification_type="email",
        )

    @staticmethod
    def test_callback_model_creation(sample_callback_request):
        """Test creating Callback database model."""
        # Act
        callback = Callback(
            notify_id=sample_callback_request.id,
            reference=sample_callback_request.reference,
            to=sample_callback_request.to,
            status=sample_callback_request.status,
            status_description=sample_callback_request.status_description,
            provider_response=sample_callback_request.provider_response,
            created_at=sample_callback_request.created_at,
            updated_at=sample_callback_request.updated_at,
            completed_at=sample_callback_request.completed_at,
            sent_at=sample_callback_request.sent_at,
            notification_type=sample_callback_request.notification_type,
        )

        # Assert
        assert callback.notify_id == "test-123"
        assert callback.reference == "ref-456"
        assert callback.to == "test@example.com"
        assert callback.status == "delivered"
        assert callback.status_description == "Successfully delivered"
        assert callback.provider_response == "200 OK"
        assert callback.created_at == "2024-01-01T10:00:00Z"
        assert callback.updated_at == "2024-01-01T10:05:00Z"
        assert callback.completed_at == "2024-01-01T10:10:00Z"
        assert callback.sent_at == "2024-01-01T10:08:00Z"
        assert callback.notification_type == "email"

    @staticmethod
    def test_callback_json_property():
        """Test Callback json property."""
        # Arrange
        test_date = datetime(2024, 1, 1, 10, 0, 0)
        callback = Callback(
            id=1,
            notify_id="notify-123",
            to="json@example.com",
            status="delivered",
            status_description="Message delivered",
            provider_response="OK",
            created_at=test_date,
            completed_at=test_date,
            sent_at=test_date,
            notification_type="email",
        )

        # Act
        json_data = callback.json

        # Assert
        expected_json = {
            "notify_id": 1,  # This uses callback.id, not notify_id
            "to": "json@example.com",
            "status": "delivered",
            "status_description": "Message delivered",
            "provider_response": "OK",
            "created_at": test_date,
            "completed_at": test_date,
            "sent_at": test_date,
            "notification_type": "email",
        }

        assert json_data == expected_json
        assert isinstance(json_data, dict)

    @staticmethod
    def test_callback_json_property_with_none_values():
        """Test Callback json property with None values."""
        # Arrange
        callback = Callback(id=2)

        # Act
        json_data = callback.json

        # Assert
        expected_json = {
            "notify_id": 2,
            "to": None,
            "status": None,
            "status_description": None,
            "provider_response": None,
            "created_at": None,
            "completed_at": None,
            "sent_at": None,
            "notification_type": None,
        }

        assert json_data == expected_json

    @staticmethod
    def test_callback_save_success(sample_callback_request):
        """Test successful Callback.save operation."""
        with patch("notify_api.models.callback.db.session") as mock_session:
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None

            # Act
            Callback.save(sample_callback_request)

            # Assert
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

            # Verify the callback object was created with correct data
            add_call_args = mock_session.add.call_args[0][0]
            assert isinstance(add_call_args, Callback)
            assert add_call_args.notify_id == "test-123"
            assert add_call_args.reference == "ref-456"
            assert add_call_args.to == "test@example.com"
            assert add_call_args.status == "delivered"

    @staticmethod
    def test_callback_save_with_exception(sample_callback_request):
        """Test Callback.save with database exception."""
        with patch("notify_api.models.callback.db.session") as mock_session:
            mock_session.add.return_value = None
            mock_session.commit.side_effect = Exception("Database error")
            mock_session.rollback.return_value = None

            # Act
            Callback.save(sample_callback_request)

            # Assert
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_called_once()
            # refresh should not be called due to exception
            mock_session.refresh.assert_not_called()

    @staticmethod
    def test_callback_save_with_minimal_request():
        """Test Callback.save with minimal callback request."""
        minimal_request = CallbackRequest(id="minimal-123", status="pending")

        with patch("notify_api.models.callback.db.session") as mock_session:
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None

            # Act
            Callback.save(minimal_request)

            # Assert
            mock_session.add.assert_called_once()
            add_call_args = mock_session.add.call_args[0][0]
            assert isinstance(add_call_args, Callback)
            assert add_call_args.notify_id == "minimal-123"
            assert add_call_args.status == "pending"
            assert add_call_args.to is None
            assert add_call_args.reference is None

    @staticmethod
    def test_callback_save_creates_correct_db_object(sample_callback_request):
        """Test that Callback.save creates database object with correct field mapping."""
        with patch("notify_api.models.callback.db.session") as mock_session:
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None

            # Act
            Callback.save(sample_callback_request)

            # Assert
            db_callback = mock_session.add.call_args[0][0]

            # Verify field mapping from CallbackRequest to Callback
            assert db_callback.notify_id == sample_callback_request.id
            assert db_callback.reference == sample_callback_request.reference
            assert db_callback.to == sample_callback_request.to
            assert db_callback.status == sample_callback_request.status
            assert db_callback.status_description == sample_callback_request.status_description
            assert db_callback.provider_response == sample_callback_request.provider_response
            assert db_callback.created_at == sample_callback_request.created_at
            assert db_callback.updated_at == sample_callback_request.updated_at
            assert db_callback.completed_at == sample_callback_request.completed_at
            assert db_callback.sent_at == sample_callback_request.sent_at
            assert db_callback.notification_type == sample_callback_request.notification_type

    @staticmethod
    def test_callback_save_with_none_values():
        """Test Callback.save handles None values correctly."""
        callback_with_nones = CallbackRequest(
            id=None,
            reference=None,
            to=None,
            status=None,
            status_description=None,
            provider_response=None,
            created_at=None,
            updated_at=None,
            completed_at=None,
            sent_at=None,
            notification_type=None,
        )

        with patch("notify_api.models.callback.db.session") as mock_session:
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None

            # Act
            Callback.save(callback_with_nones)

            # Assert
            mock_session.add.assert_called_once()
            db_callback = mock_session.add.call_args[0][0]

            # All fields should be None
            assert db_callback.notify_id is None
            assert db_callback.reference is None
            assert db_callback.to is None
            assert db_callback.status is None
            assert db_callback.status_description is None
            assert db_callback.provider_response is None
            assert db_callback.created_at is None
            assert db_callback.updated_at is None
            assert db_callback.completed_at is None
            assert db_callback.sent_at is None
            assert db_callback.notification_type is None

    @staticmethod
    def test_callback_table_name():
        """Test that Callback model has correct table name."""
        assert Callback.__tablename__ == "gc_notify_callback"

    @staticmethod
    def test_callback_model_inheritance():
        """Test that Callback inherits from db.Model."""
        # This test ensures the model is properly configured for SQLAlchemy
        callback = Callback()
        assert hasattr(callback, "query")  # SQLAlchemy model should have query attribute
        assert hasattr(callback, "__tablename__")
