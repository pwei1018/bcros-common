"""Comprehensive tests for NotifyService - covering core functionality and advanced scenarios."""

import base64
import unittest.mock
from unittest.mock import Mock, patch

from notify_api.models import Notification, NotificationRequest
from notify_api.models.attachment import AttachmentRequest
from notify_api.models.content import ContentRequest
from notify_api.services.notify_service import NotifyService


class TestNotifyServiceProviderSelection:
    """Test suite for provider selection logic."""

    @staticmethod
    def test_get_provider_strr_request():
        """Test provider selection for STRR requests."""
        provider = NotifyService.get_provider("STRR", "Any content")
        assert provider == Notification.NotificationProvider.HOUSING

    @staticmethod
    def test_get_provider_strr_request_lowercase():
        """Test provider selection for STRR requests (lowercase)."""
        provider = NotifyService.get_provider("strr", "Any content")
        assert provider == Notification.NotificationProvider.HOUSING

    @staticmethod
    def test_get_provider_html_content():
        """Test provider selection for HTML content."""
        provider = NotifyService.get_provider("other", "<html><body>HTML content</body></html>")
        assert provider == Notification.NotificationProvider.SMTP

    @staticmethod
    def test_get_provider_html_tags_in_content():
        """Test provider selection for content with HTML tags."""
        provider = NotifyService.get_provider("other", "<p>Paragraph content</p>")
        assert provider == Notification.NotificationProvider.SMTP

    @staticmethod
    def test_get_provider_default_gc_notify():
        """Test default provider selection for plain text."""
        provider = NotifyService.get_provider("other", "Plain text content")
        assert provider == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    def test_get_provider_empty_content():
        """Test provider selection with empty content."""
        provider = NotifyService.get_provider("other", "")
        assert provider == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    def test_get_provider_invalid_request_by():
        """Test provider selection with invalid request_by."""
        provider = NotifyService.get_provider("", "content")
        assert provider == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    def test_get_provider_non_string_request_by():
        """Test provider selection with non-string request_by."""
        provider = NotifyService.get_provider(None, "content")
        assert provider == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    def test_get_provider_large_attachments():
        """Test provider selection with large attachments."""

        # Create a large attachment (over 6MB)
        large_content = b"a" * (7 * 1024 * 1024)  # 7MB of data
        encoded_content = base64.b64encode(large_content).decode("utf-8")

        attachment = AttachmentRequest(file_name="large_file.pdf", file_bytes=encoded_content, attach_order="1")

        content = ContentRequest(subject="Test Subject", body="Test Body", attachments=[attachment])

        notification_request = NotificationRequest(
            recipients="+12345678901", request_by="test_service", content=content
        )

        provider = NotifyService.get_provider("test_service", "Plain text", notification_request)
        assert provider == Notification.NotificationProvider.SMTP

    @staticmethod
    def test_get_provider_small_attachments():
        """Test provider selection with small attachments."""

        # Create a small attachment (under 6MB)
        small_content = b"small content"
        encoded_content = base64.b64encode(small_content).decode("utf-8")

        attachment = AttachmentRequest(file_name="small_file.pdf", file_bytes=encoded_content, attach_order="1")

        content = ContentRequest(subject="Test Subject", body="Test Body", attachments=[attachment])

        notification_request = NotificationRequest(
            recipients="+12345678901", request_by="test_service", content=content
        )

        provider = NotifyService.get_provider("test_service", "Plain text", notification_request)
        assert provider == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    def test_get_provider_no_attachments():
        """Test provider selection with no attachments."""

        content = ContentRequest(subject="Test Subject", body="Test Body")

        notification_request = NotificationRequest(
            recipients="+12345678901", request_by="test_service", content=content
        )

        provider = NotifyService.get_provider("test_service", "Plain text", notification_request)
        assert provider == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    def test_get_provider_multiple_attachments_exceeding_limit():
        """Test provider selection with multiple attachments exceeding 6MB total."""

        # Create multiple attachments that together exceed 6MB
        content_4mb = b"a" * (4 * 1024 * 1024)  # 4MB
        content_3mb = b"b" * (3 * 1024 * 1024)  # 3MB (total = 7MB)

        attachment1 = AttachmentRequest(
            file_name="file1.pdf", file_bytes=base64.b64encode(content_4mb).decode("utf-8"), attach_order="1"
        )

        attachment2 = AttachmentRequest(
            file_name="file2.pdf", file_bytes=base64.b64encode(content_3mb).decode("utf-8"), attach_order="2"
        )

        content = ContentRequest(subject="Test Subject", body="Test Body", attachments=[attachment1, attachment2])

        notification_request = NotificationRequest(
            recipients="+12345678901", request_by="test_service", content=content
        )

        provider = NotifyService.get_provider("test_service", "Plain text", notification_request)
        assert provider == Notification.NotificationProvider.SMTP

    @staticmethod
    def test_get_provider_attachment_calculation_error():
        """Test provider selection when attachment size calculation fails."""

        # Mock the _calculate_attachment_size method to raise an exception
        with unittest.mock.patch.object(
            NotifyService, "_calculate_attachment_size", side_effect=Exception("Base64 decode error")
        ):
            # Create valid attachment (the mock will make it fail)
            attachment = AttachmentRequest(
                file_name="test_file.pdf",
                file_bytes="dGVzdCBjb250ZW50",  # Valid base64 for "test content"
                attach_order="1",
            )

            content = ContentRequest(subject="Test Subject", body="Test Body", attachments=[attachment])

            notification_request = NotificationRequest(
                recipients="+12345678901", request_by="test_service", content=content
            )

            # Should default to SMTP when calculation fails (safer approach)
            provider = NotifyService.get_provider("test_service", "Plain text", notification_request)
            assert provider == Notification.NotificationProvider.SMTP

    @staticmethod
    def test_contains_html_parsing_error():
        """Test HTML detection with parsing error."""
        service = NotifyService()

        with patch("notify_api.services.notify_service.BeautifulSoup", side_effect=Exception("Parse error")):
            result = service._contains_html("<invalid>html")
            assert result is False

    @staticmethod
    def test_notify_service_init():
        """Test NotifyService initialization."""
        service = NotifyService()
        assert service is not None
        assert isinstance(service, NotifyService)

    @staticmethod
    def test_create_cloud_event():
        """Test cloud event creation."""
        provider = "test_provider"
        notification_data = {"test": "data"}

        cloud_event = NotifyService._create_cloud_event(provider, notification_data)

        assert cloud_event.source == "notify-api"
        assert cloud_event.type == f"bc.registry.notify.{provider}"
        assert cloud_event.data == notification_data

    @staticmethod
    def test_update_notification_status():
        """Test notification status update."""
        mock_notification = Mock()
        provider = "test_provider"
        status = "test_status"

        NotifyService._update_notification_status(mock_notification, provider, status)

        assert mock_notification.status_code == status
        assert mock_notification.provider_code == provider
        assert mock_notification.sent_date is not None
        mock_notification.update_notification.assert_called_once()


class TestNotifyServiceQueueOperations:
    """Test suite for queue operations and notification processing."""

    @staticmethod
    def test_get_delivery_topic_gc_notify(app):
        """Test delivery topic retrieval for GC Notify provider."""
        with app.app_context():
            app.config["DELIVERY_GCNOTIFY_TOPIC"] = "test-gc-notify-topic"

            topic = NotifyService._get_delivery_topic(Notification.NotificationProvider.GC_NOTIFY)

            assert topic == "test-gc-notify-topic"

    @staticmethod
    def test_get_delivery_topic_smtp(app):
        """Test delivery topic retrieval for SMTP provider."""
        with app.app_context():
            app.config["DELIVERY_SMTP_TOPIC"] = "test-smtp-topic"

            topic = NotifyService._get_delivery_topic(Notification.NotificationProvider.SMTP)

            assert topic == "test-smtp-topic"

    @staticmethod
    def test_get_delivery_topic_housing(app):
        """Test delivery topic retrieval for Housing provider."""
        with app.app_context():
            app.config["DELIVERY_GCNOTIFY_HOUSING_TOPIC"] = "test-housing-topic"

            topic = NotifyService._get_delivery_topic(Notification.NotificationProvider.HOUSING)

            assert topic == "test-housing-topic"

    @staticmethod
    def test_get_delivery_topic_none_found(app):
        """Test delivery topic retrieval when no topic configured."""
        with app.app_context():
            app.config["DELIVERY_GCNOTIFY_TOPIC"] = None
            topic = NotifyService._get_delivery_topic(Notification.NotificationProvider.GC_NOTIFY)

            assert topic is None

    @staticmethod
    def test_filter_safe_recipients_production(app):
        """Test recipient filtering in production environment."""
        with app.app_context():
            app.config["DEVELOPMENT"] = False

            recipients = "test1@example.com, test2@example.com, test3@example.com"
            result = NotifyService._filter_safe_recipients(recipients)

            assert result == ["test1@example.com", "test2@example.com", "test3@example.com"]

    @staticmethod
    @patch("notify_api.services.notify_service.SafeList")
    def test_filter_safe_recipients_development_with_safe_list(mock_safe_list, app):
        """Test recipient filtering in development with safe list."""
        with app.app_context():
            app.config["DEVELOPMENT"] = True
            mock_safe_list.find_all.return_value = [
                Mock(email="test1@example.com"),
                Mock(email="test3@example.com"),
            ]

            recipients = "test1@example.com, test2@example.com, test3@example.com"
            result = NotifyService._filter_safe_recipients(recipients)

            assert result == ["test1@example.com", "test3@example.com"]

    @staticmethod
    @patch("notify_api.services.notify_service.SafeList")
    def test_filter_safe_recipients_development_no_safe_recipients(mock_safe_list, app):
        """Test recipient filtering in development with no safe recipients."""
        with app.app_context():
            app.config["DEVELOPMENT"] = True
            mock_safe_list.is_in_safe_list.return_value = False
            recipients = "test1@example.com, test2@example.com"
            result = NotifyService._filter_safe_recipients(recipients)

            assert result == []

    @staticmethod
    def test_queue_publish_success(app):
        """Test successful queue publishing."""
        with app.app_context():
            # Setup app config
            app.config["DEVELOPMENT"] = False
            app.config["DELIVERY_GCNOTIFY_TOPIC"] = "test-topic"

            # Create test request
            mock_request = Mock()
            mock_request.request_by = "test-service"
            mock_request.content.body = "Plain text content"
            mock_request.recipients = "test@example.com"
            mock_request.content.subject = "Test Subject"
            mock_request.model_dump_json.return_value = '{"test": "data"}'

            service = NotifyService()

            # Mock the external dependencies
            with (
                patch.object(service, "get_provider", return_value="GC_NOTIFY"),
                patch.object(service, "_filter_safe_recipients", return_value=["test@example.com"]),
                patch.object(NotifyService, "_get_delivery_topic", return_value="test-topic"),
                patch.object(
                    NotifyService,
                    "_process_single_recipient",
                    return_value=Mock(
                        recipients="test@example.com", status_code=Notification.NotificationStatus.QUEUED
                    ),
                ),
            ):
                result = service.queue_publish(mock_request)

            assert result.recipients == "test@example.com"
            assert result.status_code == Notification.NotificationStatus.QUEUED

    @staticmethod
    def test_queue_publish_no_safe_recipients(app):
        """Test queue publishing with no safe recipients."""
        with app.app_context():
            app.config["DEVELOPMENT"] = False

            mock_request = Mock()
            mock_request.request_by = "test-service"
            mock_request.content.body = "Plain text content"
            mock_request.recipients = ""  # Empty recipients

            service = NotifyService()

            # Mock to return empty list for safe recipients
            with (
                patch.object(service, "get_provider", return_value="GC_NOTIFY"),
                patch.object(NotifyService, "_filter_safe_recipients", return_value=[]),
            ):
                result = service.queue_publish(mock_request)

            assert result.recipients is None
            assert result.status_code == Notification.NotificationStatus.FAILURE

    @staticmethod
    def test_queue_publish_no_delivery_topic(app):
        """Test queue publishing with no delivery topic."""
        with app.app_context():
            app.config["DEVELOPMENT"] = False
            app.config["DELIVERY_GCNOTIFY_TOPIC"] = None  # No topic configured

            mock_request = Mock()
            mock_request.request_by = "test-service"
            mock_request.content.body = "Plain text content"
            mock_request.recipients = "test@example.com"

            service = NotifyService()

            with patch.object(service, "get_provider", return_value="GC_NOTIFY"):
                result = service.queue_publish(mock_request)

            assert result.recipients == "test@example.com"
            assert result.status_code == Notification.NotificationStatus.FAILURE

    @staticmethod
    def test_queue_publish_exception(app):
        """Test queue publishing with exception."""
        with app.app_context():
            mock_request = Mock()
            mock_request.request_by = "test-service"
            mock_request.content.body = "Plain text content"
            mock_request.recipients = "test@example.com"

            service = NotifyService()

            with patch.object(service, "get_provider", side_effect=Exception("Config error")):
                result = service.queue_publish(mock_request)

            assert result.recipients == "test@example.com"
            assert result.status_code == Notification.NotificationStatus.FAILURE

    @staticmethod
    @patch("notify_api.services.notify_service.queue")
    @patch("notify_api.services.notify_service.GcpQueue")
    @patch("notify_api.services.notify_service.Notification")
    def test_process_single_recipient_success(mock_notification_class, mock_gcp_queue, mock_queue):
        """Test successful single recipient processing."""
        # Setup mocks
        mock_notification = Mock()
        mock_notification.id = "test-notification-id"
        mock_notification_class.create_notification.return_value = mock_notification
        mock_queued_status = Mock()
        mock_queued_status.name = "QUEUED"
        mock_notification_class.NotificationStatus.QUEUED = mock_queued_status

        mock_gcp_queue.to_queue_message.return_value = "test-queue-message"
        mock_queue.publish.return_value = "test-future"

        mock_request = Mock()
        mock_request.content.subject = "Test Subject"

        notification_data = {"test": "data"}

        with (
            patch.object(NotifyService, "_create_cloud_event") as mock_create_event,
            patch.object(NotifyService, "_update_notification_status") as mock_update_status,
        ):
            mock_create_event.return_value = Mock()

            result = NotifyService._process_single_recipient(
                "test@example.com", mock_request, "GC_NOTIFY", "test-topic", notification_data
            )

        assert result == mock_notification
        mock_notification_class.create_notification.assert_called_once_with(
            mock_request, "test@example.com", "GC_NOTIFY"
        )
        mock_update_status.assert_called_once()
        # Verify cached response is set for safe access after session expiry
        assert result._cached_response["id"] == "test-notification-id"
        assert result._cached_response["recipients"] == "test@example.com"

    @staticmethod
    @patch("notify_api.services.notify_service.queue")
    @patch("notify_api.services.notify_service.Notification")
    def test_process_single_recipient_exception(mock_notification_class, mock_queue):
        """Test single recipient processing with exception."""
        mock_notification_class.create_notification.side_effect = Exception("Database error")

        mock_request = Mock()
        notification_data = {"test": "data"}

        result = NotifyService._process_single_recipient(
            "test@example.com", mock_request, "GC_NOTIFY", "test-topic", notification_data
        )

        assert result is None

    @staticmethod
    @patch("notify_api.services.notify_service.Notification")
    def test_queue_republish_no_notifications(mock_notification_class):
        """Test queue republish with no notifications found."""
        mock_notification_class.find_resend_notifications.return_value = []

        # Should not raise any exception
        NotifyService.queue_republish()

    @staticmethod
    @patch("notify_api.services.notify_service.Notification")
    def test_queue_republish_with_notifications(mock_notification_class):
        """Test queue republish with notifications found."""
        mock_notification1 = Mock()
        mock_notification1.id = "notification-1"
        mock_notification2 = Mock()
        mock_notification2.id = "notification-2"

        mock_notification_class.find_resend_notifications.return_value = [mock_notification1, mock_notification2]

        with patch.object(NotifyService, "_republish_single_notification") as mock_republish:
            mock_republish.side_effect = [True, False]  # First succeeds, second fails

            NotifyService.queue_republish()

        expected_calls = 2
        assert mock_republish.call_count == expected_calls

    @staticmethod
    @patch("notify_api.services.notify_service.Notification")
    def test_queue_republish_exception(mock_notification_class):
        """Test queue republish with exception."""
        mock_notification_class.find_resend_notifications.side_effect = Exception("Database error")

        # Should not raise any exception
        NotifyService.queue_republish()

    @staticmethod
    @patch("notify_api.services.notify_service.queue")
    @patch("notify_api.services.notify_service.GcpQueue")
    def test_republish_single_notification_success(mock_gcp_queue, mock_queue):
        """Test successful single notification republish."""
        mock_notification = Mock()
        mock_notification.id = "test-notification-id"
        mock_notification.provider_code = "GC_NOTIFY"
        mock_notification.recipients = "test@example.com"

        mock_gcp_queue.to_queue_message.return_value = "test-queue-message"
        mock_queue.publish.return_value = "test-future"

        with (
            patch.object(NotifyService, "_get_delivery_topic", return_value="test-topic") as mock_get_topic,
            patch.object(NotifyService, "_create_cloud_event") as mock_create_event,
            patch.object(NotifyService, "_update_notification_status") as mock_update_status,
        ):
            mock_create_event.return_value = Mock()

            result = NotifyService._republish_single_notification(mock_notification)

        assert result is True
        mock_get_topic.assert_called_once_with("GC_NOTIFY")
        mock_update_status.assert_called_once()

    @staticmethod
    @patch("notify_api.services.notify_service.queue")
    def test_republish_single_notification_no_topic(mock_queue):
        """Test single notification republish with no delivery topic."""
        mock_notification = Mock()
        mock_notification.id = "test-notification-id"
        mock_notification.provider_code = "GC_NOTIFY"

        with patch.object(NotifyService, "_get_delivery_topic", return_value=None):
            result = NotifyService._republish_single_notification(mock_notification)

        assert result is False

    @staticmethod
    @patch("notify_api.services.notify_service.queue")
    def test_republish_single_notification_exception(mock_queue):
        """Test single notification republish with exception."""
        mock_notification = Mock()
        mock_notification.id = "test-notification-id"
        mock_notification.provider_code = "GC_NOTIFY"

        with patch.object(NotifyService, "_get_delivery_topic", side_effect=Exception("Error")):
            result = NotifyService._republish_single_notification(mock_notification)

        assert result is False

    @staticmethod
    def test_contains_html_with_various_tags():
        """Test HTML detection with various HTML tags."""
        service = NotifyService()

        # Test with different HTML structures
        assert service._contains_html("<div>content</div>") is True
        assert service._contains_html("<p>paragraph</p>") is True
        assert service._contains_html("<br>") is True
        assert service._contains_html("<span>text</span>") is True
        assert service._contains_html("plain text") is False
        assert service._contains_html("") is False
        assert service._contains_html("<invalid tag") is False

    @staticmethod
    def test_filter_safe_recipients_edge_cases(app):
        """Test recipient filtering with edge cases."""
        with app.app_context():
            app.config["DEVELOPMENT"] = False

            # Test with empty recipients
            result = NotifyService._filter_safe_recipients("")
            assert result == [""]

            # Test with whitespace
            result = NotifyService._filter_safe_recipients("  test@example.com  ,  test2@example.com  ")
            assert result == ["test@example.com", "test2@example.com"]

            # Test with single recipient
            result = NotifyService._filter_safe_recipients("single@example.com")
            assert result == ["single@example.com"]

    @staticmethod
    def test_queue_publish_empty_recipient_filtering(app):
        """Test queue publish with empty recipients after filtering."""
        with app.app_context():
            app.config["DEVELOPMENT"] = False
            app.config["DELIVERY_GCNOTIFY_TOPIC"] = "test-topic"

            mock_request = Mock()
            mock_request.request_by = "test-service"
            mock_request.content.body = "Plain text content"
            mock_request.recipients = "  ,  ,  "  # Only whitespace

            service = NotifyService()

            # Mock to return empty list after filtering whitespace
            with (
                patch.object(service, "get_provider", return_value="GC_NOTIFY"),
                patch.object(service, "_filter_safe_recipients", return_value=[]),
            ):
                result = service.queue_publish(mock_request)

            assert result.status_code == Notification.NotificationStatus.FAILURE

    @staticmethod
    def test_get_provider_edge_cases():
        """Test provider selection with edge cases."""
        # Test with various request_by formats - STRR must be exact match, not substring
        assert NotifyService.get_provider("STRR", "content") == Notification.NotificationProvider.HOUSING
        assert NotifyService.get_provider("strr", "content") == Notification.NotificationProvider.HOUSING
        # These should NOT match housing since they're not exact STRR
        assert NotifyService.get_provider("STRR_SOMETHING", "content") == Notification.NotificationProvider.GC_NOTIFY
        assert NotifyService.get_provider("strr_test", "content") == Notification.NotificationProvider.GC_NOTIFY
        assert NotifyService.get_provider(123, "content") == Notification.NotificationProvider.GC_NOTIFY
        assert NotifyService.get_provider([], "content") == Notification.NotificationProvider.GC_NOTIFY

        # Test with HTML content edge cases
        assert (
            NotifyService.get_provider("test", "Text with angle chars but not HTML")
            == Notification.NotificationProvider.GC_NOTIFY
        )
        # HTML comments are not detected as HTML by BeautifulSoup.find() so they go to GC_NOTIFY
        assert NotifyService.get_provider("test", "<!-- comment -->") == Notification.NotificationProvider.GC_NOTIFY
        assert (
            NotifyService.get_provider("test", "<script>alert('test')</script>")
            == Notification.NotificationProvider.SMTP
        )
