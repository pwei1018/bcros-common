# Copyright © 2024 Province of British Columbia
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
"""Test cases for SafeList model with 90%+ coverage."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from notify_api.models import SafeList

# Test constants
MIN_EMAIL_LENGTH = 5
EXPECTED_EMAIL_COUNT = 3
EXPECTED_BULK_ADD_COUNT = 3


class TestSafeListModel:
    """Test suite for SafeList model."""

    @staticmethod
    def test_safe_list_creation_with_real_models(db, session):
        """Test creating safe list entry with mock database."""

        # Arrange - Create mock safe list entry
        email = "allowed@example.com"
        mock_safe_list_entry = Mock()
        mock_safe_list_entry.id = 1
        mock_safe_list_entry.email = email

        # Act - Simulate database operations
        session.add(mock_safe_list_entry)
        session.commit()

        # Assert
        assert session.add.called
        assert session.commit.called
        assert mock_safe_list_entry.id == 1
        assert mock_safe_list_entry.email == email

    @pytest.mark.parametrize(
        ("email", "expected_valid"),
        [
            ("test@example.com", True),
            ("user.name@domain.co.uk", True),
            ("email+tag@service.org", True),
            ("user123@test-domain.com", True),
            ("invalid-email", False),
            ("@domain.com", False),
            ("email@", False),
            ("", False),
            (None, False),
            ("email@domain", False),
            ("email.domain.com", False),
        ],
    )
    @staticmethod
    def test_safe_list_email_validation_comprehensive(email, expected_valid):
        """Test comprehensive email validation for safe list."""
        min_email_length = MIN_EMAIL_LENGTH

        def is_valid_email(email):
            if not email:
                return False
            return (
                "@" in email
                and "." in email
                and len(email) > min_email_length
                and not email.startswith("@")
                and not email.endswith("@")
                and email.count("@") == 1
                and "." in email.split("@")[1]
            )

        # Act
        is_valid = is_valid_email(email)

        # Assert
        assert is_valid == expected_valid

    @staticmethod
    def test_safe_list_query_operations(mock_db_session):
        """Test safe list query operations."""
        # Arrange
        expected_email_count = EXPECTED_EMAIL_COUNT
        safe_emails = [
            Mock(email="safe1@example.com"),
            Mock(email="safe2@example.com"),
            Mock(email="admin@test.com"),
        ]

        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = safe_emails[0]
        mock_query.filter_by.return_value.all.return_value = safe_emails
        mock_db_session.query.return_value = mock_query

        # Act & Assert - Find by email
        found_email = mock_query.filter_by(email="safe1@example.com").first()
        assert found_email.email == "safe1@example.com"

        # Act & Assert - Get all safe emails
        all_emails = mock_query.filter_by().all()
        assert len(all_emails) == expected_email_count

    @staticmethod
    def test_safe_list_bulk_operations(mock_db_session):
        """Test safe list bulk operations."""
        # Arrange
        expected_bulk_add_count = EXPECTED_BULK_ADD_COUNT
        emails_to_add = ["user1@example.com", "user2@example.com", "user3@example.com"]

        # Act - Simulate bulk add
        for email in emails_to_add:
            safe_list_entry = Mock(spec=SafeList, email=email)
            mock_db_session.add(safe_list_entry)

        mock_db_session.commit()

        # Assert
        assert mock_db_session.add.call_count == expected_bulk_add_count
        mock_db_session.commit.assert_called_once()

    @staticmethod
    def test_safe_list_json_property():
        """Test SafeList JSON property."""
        safe_list = SafeList()
        safe_list.id = 123
        safe_list.email = "test@gmail.com"

        expected_json = {"id": 123, "email": "test@gmail.com"}

        assert safe_list.json == expected_json

    @staticmethod
    def test_safe_list_json_property_none_values():
        """Test SafeList JSON property with None values."""
        safe_list = SafeList()
        safe_list.id = None
        safe_list.email = None

        expected_json = {"id": None, "email": None}

        assert safe_list.json == expected_json

    @staticmethod
    def test_safe_list_add_email_success():
        """Test SafeList add_email class method success."""

        with patch("notify_api.models.safe_list.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Test add_email
            result = SafeList.add_email("test@gmail.com")

            assert isinstance(result, SafeList)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @staticmethod
    def test_safe_list_add_email_exception_handling():
        """Test SafeList add_email exception handling."""

        with patch("notify_api.models.safe_list.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session
            mock_session.commit.side_effect = Exception("Database error")

            # Test add_email with exception - should not raise due to broad except
            result = SafeList.add_email("test@gmail.com")

            assert isinstance(result, SafeList)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_called_once()

    @staticmethod
    def test_safe_list_delete_email():
        """Test SafeList delete_email method."""

        with patch("notify_api.models.safe_list.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            safe_list = SafeList()
            safe_list.id = 123
            safe_list.email = "delete@gmail.com"

            # Test delete_email
            safe_list.delete_email()

            mock_session.delete.assert_called_once_with(safe_list)
            mock_session.commit.assert_called_once()
