# Copyright © 2022 Province of British Columbia
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
"""Test suite for EmailSMTP service provider with comprehensive coverage."""

import smtplib
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest
from notify_api.models import (
    Attachment,
    Content,
    Notification,
    NotificationSendResponse,
    NotificationSendResponses,
)

from notify_delivery.services.providers.email_smtp import EmailSMTP


class TestEmailSMTPServiceProvider(unittest.TestCase):
    """Comprehensive test suite for EmailSMTP service provider."""

    # Test constants
    SMTP_PORT = 587
    EXPECTED_MULTIPLE_RECIPIENTS = 3
    EXPECTED_WHITESPACE_RECIPIENTS = 2

    def setUp(self):
        """Set up test fixtures."""
        self.mock_content = Content(
            subject="Test Subject", body="<html><body>Test email body</body></html>", attachments=[]
        )

        self.mock_notification = Notification(
            id=1,
            recipients="test@example.com",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        # Standard mock config
        self.mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": self.SMTP_PORT,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }

    def _create_mock_app(self, config_override=None):
        """Helper to create properly configured mock app."""
        config = {**self.mock_config, **(config_override or {})}
        mock_app = Mock()
        mock_app.config.get.side_effect = lambda key, default=None: config.get(key, default)
        return mock_app

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_email_smtp_initialization(self, mock_current_app):
        """Test EmailSMTP class initialization."""
        mock_current_app.config.get.side_effect = lambda key: self.mock_config.get(key)

        email_smtp = EmailSMTP(self.mock_notification)

        assert email_smtp.mail_server == "smtp.example.com"
        assert email_smtp.mail_port == self.SMTP_PORT
        assert email_smtp.mail_from_id == "sender@example.com"
        assert email_smtp.notification == self.mock_notification

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_production_environment(self, mock_current_app, mock_smtp_class):
        """Test email sending in production environment."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        mock_server.sendmail.return_value = None

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 1
        assert result.recipients[0].recipient == "test@example.com"
        mock_smtp_class.assert_called_once_with(host="smtp.example.com", port=self.SMTP_PORT)

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_development_environment(self, mock_current_app, mock_smtp_class):
        """Test email sending in development environment with subject suffix."""
        dev_config = {**self.mock_config, "DEPLOYMENT_ENV": "development"}
        mock_current_app.config.get.side_effect = lambda key, default=None: dev_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)
        email_smtp.send()

        # Verify the subject includes environment suffix
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "Test Subject - from DEVELOPMENT environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_multiple_recipients(self, mock_current_app, mock_smtp_class):
        """Test email sending to multiple recipients."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        multi_recipient_notification = Notification(
            id=1,
            recipients="test1@example.com,test2@example.com,test3@example.com",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        mock_server.sendmail.return_value = None

        email_smtp = EmailSMTP(multi_recipient_notification)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == self.EXPECTED_MULTIPLE_RECIPIENTS
        assert mock_server.sendmail.call_count == self.EXPECTED_MULTIPLE_RECIPIENTS

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_with_attachments(self, mock_current_app, mock_smtp_class):
        """Test email sending with file attachments."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        attachment = Attachment(file_name="test_document.pdf", file_bytes=b"fake pdf content")
        content_with_attachments = Content(
            subject="Test Subject", body="<html><body>Test email body</body></html>", attachments=[attachment]
        )
        notification_with_attachments = Notification(
            id=1,
            recipients="test@example.com",
            content=[content_with_attachments],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(notification_with_attachments)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        # Verify attachment was included in the message
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "test_document.pdf" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_unicode_attachment_filename(self, mock_current_app, mock_smtp_class):
        """Test email sending with unicode characters in attachment filename."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        attachment = Attachment(file_name="tëst_dócümént_ñäme.pdf", file_bytes=b"fake pdf content")
        content_with_attachments = Content(
            subject="Test Subject", body="<html><body>Test email body</body></html>", attachments=[attachment]
        )
        notification_with_attachments = Notification(
            id=1,
            recipients="test@example.com",
            content=[content_with_attachments],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(notification_with_attachments)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        # Verify unicode filename was normalized
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        # Should contain ASCII-safe version of filename
        assert "test_document_name.pdf" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    @patch("notify_delivery.services.providers.email_smtp.logger")
    def test_send_email_smtp_connection_error(self, mock_logger, mock_current_app, mock_smtp_class):
        """Test handling of SMTP connection errors."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 0  # No successful sends
        mock_logger.error.assert_called_with("Error connecting to SMTP server: Connection failed")

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    @patch("notify_delivery.services.providers.email_smtp.logger")
    def test_send_email_individual_recipient_error(self, mock_logger, mock_current_app, mock_smtp_class):
        """Test handling of individual recipient send errors."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        multi_recipient_notification = Notification(
            id=1,
            recipients="good@example.com,bad@example.com",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        def sendmail_side_effect(from_addr, to_addrs, msg):
            if "bad@example.com" in to_addrs:
                raise Exception("Invalid recipient")

        mock_server.sendmail.side_effect = sendmail_side_effect

        email_smtp = EmailSMTP(multi_recipient_notification)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 1  # Only successful send
        assert result.recipients[0].recipient == "good@example.com"
        mock_logger.error.assert_called_with("Error sending email to bad@example.com: Invalid recipient")

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_empty_deployment_env(self, mock_current_app, mock_smtp_class):
        """Test email sending with empty deployment environment."""
        empty_env_config = {**self.mock_config, "DEPLOYMENT_ENV": ""}
        mock_current_app.config.get.side_effect = lambda key, default=None: empty_env_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)
        email_smtp.send()

        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "Test Subject - from UNKNOWN environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_missing_deployment_env(self, mock_current_app, mock_smtp_class):
        """Test email sending with missing deployment environment config."""
        config_without_env = {k: v for k, v in self.mock_config.items() if k != "DEPLOYMENT_ENV"}
        mock_current_app.config.get.side_effect = lambda key, default=None: config_without_env.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)
        email_smtp.send()

        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "Test Subject - from UNKNOWN environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_no_content_error(self, mock_current_app):
        """Test email sending with notification having no content."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        notification_no_content = Notification(
            id=1,
            recipients="test@example.com",
            content=[],  # Empty content
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        email_smtp = EmailSMTP(notification_no_content)

        # Test that send() returns None when no content
        result = email_smtp.send()
        assert result is None

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_staging_environment(self, mock_current_app, mock_smtp_class):
        """Test email sending in staging environment."""
        staging_config = {**self.mock_config, "DEPLOYMENT_ENV": "staging"}
        mock_current_app.config.get.side_effect = lambda key, default=None: staging_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)
        email_smtp.send()

        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "Test Subject - from STAGING environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_message_structure(self, mock_current_app, mock_smtp_class):
        """Test that email message structure is correctly formatted."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)
        email_smtp.send()

        # Verify message structure
        call_args = mock_server.sendmail.call_args
        from_addr = call_args[0][0]
        to_addrs = call_args[0][1]
        message_str = call_args[0][2]

        assert from_addr == "sender@example.com"
        assert to_addrs == ["test@example.com"]
        assert "From: sender@example.com" in message_str
        assert "To: test@example.com" in message_str
        assert "Subject: Test Subject" in message_str
        assert "Content-Type: text/html" in message_str

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_invalid_content_structure(self, mock_current_app):
        """Test sending with invalid content structure."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        # Create content without required attributes
        invalid_content = MagicMock()
        invalid_content.subject = "Test Subject"
        # Don't set body attribute to simulate missing body
        if hasattr(invalid_content, "body"):
            delattr(invalid_content, "body")

        email_smtp = EmailSMTP(self.mock_notification)
        # Temporarily replace content with invalid content
        original_content = email_smtp.notification.content
        email_smtp.notification.content = [invalid_content]

        result = email_smtp.send()

        # Restore original content
        email_smtp.notification.content = original_content

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 0

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_with_whitespace_recipients(self, mock_current_app, mock_smtp_class):
        """Test email sending with recipients containing whitespace."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        notification_with_spaces = Notification(
            id=1,
            recipients=" test1@example.com , test2@example.com , ",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        mock_server.sendmail.return_value = None

        email_smtp = EmailSMTP(notification_with_spaces)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == self.EXPECTED_WHITESPACE_RECIPIENTS  # Should handle whitespace correctly
        assert mock_server.sendmail.call_count == self.EXPECTED_WHITESPACE_RECIPIENTS

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    @patch("notify_delivery.services.providers.email_smtp.logger")
    def test_send_general_exception_handling(self, mock_logger, mock_current_app, mock_smtp_class):
        """Test general exception handling during SMTP connection."""
        mock_current_app.config.get.side_effect = lambda key, default=None: self.mock_config.get(key, default)

        mock_smtp_class.side_effect = Exception("Unexpected error")

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp.send()

        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 0
        mock_logger.error.assert_called_with(
            "An unexpected error occurred when connecting to SMTP server: Unexpected error"
        )

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_prepare_subject_production(self, mock_current_app):
        """Test subject preparation in production environment."""
        production_config = {**self.mock_config, "DEPLOYMENT_ENV": "production"}
        mock_current_app.config.get.side_effect = lambda key, default=None: production_config.get(key, default)

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp._prepare_subject("Test Subject")

        assert result == "Test Subject"

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_prepare_subject_development(self, mock_current_app):
        """Test subject preparation in development environment."""
        dev_config = {**self.mock_config, "DEPLOYMENT_ENV": "development"}
        mock_current_app.config.get.side_effect = lambda key, default=None: dev_config.get(key, default)

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp._prepare_subject("Test Subject")

        assert result == "Test Subject - from DEVELOPMENT environment"

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_prepare_subject_unknown_env(self, mock_current_app):
        """Test subject preparation with unknown environment."""
        config_without_env = {k: v for k, v in self.mock_config.items() if k != "DEPLOYMENT_ENV"}
        mock_current_app.config.get.side_effect = lambda key, default=None: config_without_env.get(key, default)

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp._prepare_subject("Test Subject")

        assert result == "Test Subject - from UNKNOWN environment"

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_prepare_subject_empty_env(self, mock_current_app):
        """Test subject preparation with empty deployment environment."""
        empty_env_config = {**self.mock_config, "DEPLOYMENT_ENV": ""}
        mock_current_app.config.get.side_effect = lambda key, default=None: empty_env_config.get(key, default)

        email_smtp = EmailSMTP(self.mock_notification)
        result = email_smtp._prepare_subject("Test Subject")

        assert result == "Test Subject - from UNKNOWN environment"
