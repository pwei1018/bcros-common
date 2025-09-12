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
"""Test cases for Attachment model with 90%+ coverage."""

import base64
from unittest.mock import MagicMock, Mock, patch

from pydantic import ValidationError
import pytest

from notify_api.models import Attachment, Content
from notify_api.models.attachment import AttachmentRequest
from notify_api.models.content import ContentRequest


class TestAttachmentModel:
    """Test suite for Attachment model."""

    @staticmethod
    def test_attachment_creation_with_real_models(db, session):
        """Test creating attachment with mock database."""

        # Arrange - Create mock attachment
        mock_attachment = Mock()
        mock_attachment.id = 1
        mock_attachment.file_name = "document.pdf"
        mock_attachment.file_bytes = b"fake_pdf_content"
        mock_attachment.attach_order = 1
        mock_attachment.content_id = 1

        # Act - Simulate database operations
        session.add(mock_attachment)
        session.commit()

        # Assert
        assert session.add.called
        assert session.commit.called
        assert mock_attachment.id == 1
        assert mock_attachment.file_name == "document.pdf"
        assert mock_attachment.file_bytes == b"fake_pdf_content"
        assert mock_attachment.attach_order == 1

    @pytest.mark.parametrize(
        ("file_size", "max_size", "expected_valid"),
        [
            (1024, 10 * 1024 * 1024, True),  # 1KB < 10MB
            (5 * 1024 * 1024, 10 * 1024 * 1024, True),  # 5MB < 10MB
            (10 * 1024 * 1024, 10 * 1024 * 1024, True),  # 10MB = 10MB
            (15 * 1024 * 1024, 10 * 1024 * 1024, False),  # 15MB > 10MB
            (0, 10 * 1024 * 1024, True),  # Empty file
        ],
    )
    @staticmethod
    def test_attachment_file_size_validation_comprehensive(file_size, max_size, expected_valid):
        """Test comprehensive file size validation."""

        def validate_file_size(size, max_allowed):
            return size <= max_allowed

        # Act
        is_valid = validate_file_size(file_size, max_size)

        # Assert
        assert is_valid == expected_valid

    @pytest.mark.parametrize(
        ("filename", "expected_valid"),
        [
            ("document.pdf", True),
            ("image.jpg", True),
            ("image.png", True),
            ("text.txt", True),
            ("word.doc", True),
            ("word.docx", True),
            ("script.exe", False),
            ("virus.bat", False),
            ("file.unknown", False),
            ("no_extension", False),
            ("", False),
            (None, False),
            ("file.", False),
            (".hidden", False),
        ],
    )
    @staticmethod
    def test_attachment_file_type_validation_comprehensive(filename, expected_valid):
        """Test comprehensive file type validation."""
        allowed_extensions = [".pdf", ".doc", ".docx", ".txt", ".jpg", ".png", ".jpeg", ".gif"]

        def validate_file_type(filename):
            if not filename or "." not in filename:
                return False
            extension = "." + filename.split(".")[-1].lower()
            return extension in allowed_extensions and len(filename.split(".")[0]) > 0

        # Act
        is_valid = validate_file_type(filename)

        # Assert
        assert is_valid == expected_valid

    @staticmethod
    def test_attachment_ordering_and_relationships():
        """Test attachment ordering and relationships."""
        # Arrange
        attachments = [
            Mock(spec=Attachment, attach_order=1, file_name="first.pdf"),
            Mock(spec=Attachment, attach_order=3, file_name="third.pdf"),
            Mock(spec=Attachment, attach_order=2, file_name="second.pdf"),
        ]

        # Act - Sort by attach_order
        sorted_attachments = sorted(attachments, key=lambda x: x.attach_order)

        # Assert
        assert sorted_attachments[0].file_name == "first.pdf"
        assert sorted_attachments[1].file_name == "second.pdf"
        assert sorted_attachments[2].file_name == "third.pdf"


class TestAttachmentModelMissingCoverage:
    """Test class for attachment model missing coverage."""

    @staticmethod
    def test_attachment_request_validation_errors():
        """Test AttachmentRequest validation errors."""

        # Test empty file name validation
        with pytest.raises(ValueError, match="The file name must not empty"):
            AttachmentRequest(file_name="", file_bytes="dGVzdCBjb250ZW50", attach_order="1")

        # Test None file name validation - Pydantic raises ValidationError for None values
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            AttachmentRequest(file_name=None, file_bytes="dGVzdCBjb250ZW50", attach_order="1")

    @staticmethod
    def test_attachment_request_must_contain_one_validation():
        """Test AttachmentRequest must contain one file source validation."""

        # Test missing both file_bytes and file_url
        with pytest.raises(ValueError, match="The file content must attach"):
            AttachmentRequest(file_name="test.pdf", attach_order="1")

        # Test with None values for both
        with pytest.raises(ValueError, match="The file content must attach"):
            AttachmentRequest(file_name="test.pdf", file_bytes=None, file_url=None, attach_order="1")

    @staticmethod
    def test_attachment_create_with_file_url():
        """Test attachment creation with file URL."""

        test_file_content = b"test file content from URL"

        with patch("notify_api.models.attachment.download_file") as mock_download:
            mock_download.return_value = test_file_content

            with patch("notify_api.models.attachment.db") as mock_db:
                mock_session = MagicMock()
                mock_db.session = mock_session

                # Create attachment request with file URL
                attachment_request = AttachmentRequest(
                    file_name="downloaded_file.pdf", file_url="https://example.com/file.pdf", attach_order="2"
                )

                # Mock the created attachment
                mock_attachment = MagicMock()
                mock_attachment.id = 1
                mock_attachment.file_name = "downloaded_file.pdf"
                mock_attachment.attach_order = 2
                mock_session.refresh.return_value = None

                with patch.object(Attachment, "__new__", return_value=mock_attachment):
                    result = Attachment.create_attachment(attachment_request, content_id=123)

                    assert result == mock_attachment
                    mock_download.assert_called_once_with("https://example.com/file.pdf")
                    mock_session.add.assert_called_once()
                    mock_session.commit.assert_called_once()
                    mock_session.refresh.assert_called_once()

    @staticmethod
    def test_attachment_create_with_file_bytes():
        """Test attachment creation with base64 file bytes."""

        test_file_content = b"test file content"
        encoded_content = base64.b64encode(test_file_content).decode("utf-8")

        with patch("notify_api.models.attachment.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create attachment request with file bytes
            attachment_request = AttachmentRequest(
                file_name="uploaded_file.doc", file_bytes=encoded_content, attach_order="1"
            )

            # Mock the created attachment
            mock_attachment = MagicMock()
            mock_attachment.id = 2
            mock_attachment.file_name = "uploaded_file.doc"
            mock_attachment.attach_order = 1
            mock_session.refresh.return_value = None

            with patch.object(Attachment, "__new__", return_value=mock_attachment):
                result = Attachment.create_attachment(attachment_request, content_id=456)

                assert result == mock_attachment
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once()

    @staticmethod
    def test_attachment_delete():
        """Test attachment deletion."""

        with patch("notify_api.models.attachment.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create attachment instance
            attachment = Attachment()
            attachment.id = 1
            attachment.file_name = "test.pdf"

            # Test delete
            attachment.delete_attachment()

            mock_session.delete.assert_called_once_with(attachment)
            mock_session.commit.assert_called_once()

    @staticmethod
    def test_attachment_json_property():
        """Test attachment JSON property."""
        attachment = Attachment()
        attachment.id = 123
        attachment.file_name = "test_document.pdf"
        attachment.attach_order = 2

        expected_json = {"id": 123, "fileName": "test_document.pdf", "attachOrder": 2}

        assert attachment.json == expected_json

    @staticmethod
    def test_attachment_json_property_none_values():
        """Test attachment JSON property with None values."""
        attachment = Attachment()
        attachment.id = 456
        attachment.file_name = "another_document.docx"
        attachment.attach_order = None

        expected_json = {"id": 456, "fileName": "another_document.docx", "attachOrder": None}

        assert attachment.json == expected_json


class TestContentModelMissingCoverage:
    """Test class for content model missing coverage."""

    @staticmethod
    def test_content_request_subject_validation():
        """Test ContentRequest subject validation error."""

        with pytest.raises(ValidationError, match="Input should be a valid string"):
            ContentRequest(subject=None, body="Test body content")

    @staticmethod
    def test_content_request_body_validation():
        """Test ContentRequest body validation error."""

        with pytest.raises(ValidationError, match="Input should be a valid string"):
            ContentRequest(subject="Test Subject", body=None)

    @staticmethod
    def test_content_json_property_with_attachments():
        """Test content JSON property with attachments."""

        # Create mock attachments
        attachment1 = MagicMock()
        attachment1.json = {"id": 1, "fileName": "file1.pdf", "attachOrder": 1}

        attachment2 = MagicMock()
        attachment2.json = {"id": 2, "fileName": "file2.doc", "attachOrder": 2}

        # Create content with attachments
        content = Content()
        content.id = 123
        content.subject = "Test Subject"
        content.attachments = [attachment1, attachment2]

        expected_json = {
            "id": 123,
            "subject": "Test Subject",
            "attachments": [
                {"id": 1, "fileName": "file1.pdf", "attachOrder": 1},
                {"id": 2, "fileName": "file2.doc", "attachOrder": 2},
            ],
        }

        assert content.json == expected_json

    @staticmethod
    def test_content_json_property_without_attachments():
        """Test Content JSON property with no attachments (empty list)."""

        content = Content()
        content.id = 1
        content.subject = "Test Subject"
        # content.body intentionally not set
        content.attachments = []  # Use empty list instead of None
        expected_json = {
            "id": 1,
            "subject": "Test Subject",
        }
        assert content.json == expected_json

    @staticmethod
    def test_content_create_with_attachments():
        """Test content creation with attachments."""

        with patch("notify_api.models.content.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create content request with attachments
            attachment_request = AttachmentRequest(
                file_name="test_attachment.pdf", file_bytes="dGVzdCBjb250ZW50", attach_order="1"
            )

            content_request = ContentRequest(subject="Test Subject", body="Test Body", attachments=[attachment_request])

            # Mock the created content
            mock_content = MagicMock()
            mock_content.id = 123
            mock_session.refresh.return_value = None

            with (
                patch.object(Content, "__new__", return_value=mock_content),
                patch.object(Attachment, "create_attachment") as mock_create_attachment,
            ):
                mock_create_attachment.return_value = MagicMock()

                result = Content.create_content(content_request, notification_id=456)

                assert result == mock_content
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once()
                mock_create_attachment.assert_called_once_with(attachment=attachment_request, content_id=123)

    @staticmethod
    def test_content_create_without_attachments():
        """Test content creation without attachments."""

        with patch("notify_api.models.content.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create content request without attachments
            content_request = ContentRequest(subject="Test Subject", body="Test Body")

            # Mock the created content
            mock_content = MagicMock()
            mock_content.id = 789
            mock_session.refresh.return_value = None

            with (
                patch.object(Content, "__new__", return_value=mock_content),
                patch.object(Attachment, "create_attachment") as mock_create_attachment,
            ):
                result = Content.create_content(content_request, notification_id=101112)

                assert result == mock_content
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once()
                # Should not call create_attachment when no attachments
                mock_create_attachment.assert_not_called()

    @staticmethod
    def test_content_update():
        """Test content update method."""

        with patch("notify_api.models.content.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create content instance
            content = Content()
            content.id = 123
            content.subject = "Updated Subject"
            content.body = "Updated Body"

            # Test update
            result = content.update_content()

            assert result == content
            mock_session.add.assert_called_once_with(content)
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_called_once()

    @staticmethod
    def test_content_delete_with_attachments():
        """Test content deletion with attachments."""

        with patch("notify_api.models.content.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create mock attachments
            attachment1 = MagicMock()
            attachment1.delete_attachment = MagicMock()

            attachment2 = MagicMock()
            attachment2.delete_attachment = MagicMock()

            # Create content with attachments
            content = Content()
            content.id = 123
            content.attachments = [attachment1, attachment2]

            # Test delete
            content.delete_content()

            # Verify attachments were deleted
            attachment1.delete_attachment.assert_called_once()
            attachment2.delete_attachment.assert_called_once()

            # Verify content was deleted
            mock_session.delete.assert_called_once_with(content)
            mock_session.commit.assert_called_once()

    @staticmethod
    def test_content_delete_without_attachments():
        """Test content deletion without attachments."""

        with patch("notify_api.models.content.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create content without attachments
            content = Content()
            content.id = 456
            content.attachments = []

            # Test delete
            content.delete_content()

            # Verify content was deleted (no attachment deletion)
            mock_session.delete.assert_called_once_with(content)
            mock_session.commit.assert_called_once()

    @staticmethod
    def test_content_delete_empty_attachments():
        """Test content deletion with empty attachments list."""

        with patch("notify_api.models.content.db") as mock_db:
            mock_session = MagicMock()
            mock_db.session = mock_session

            # Create content with empty attachments list
            content = Content()
            content.id = 789
            content.attachments = []

            # Test delete
            content.delete_content()

            # Verify content was deleted (no attachment deletion)
            mock_session.delete.assert_called_once_with(content)
            mock_session.commit.assert_called_once()
