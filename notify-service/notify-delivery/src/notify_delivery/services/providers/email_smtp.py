# Copyright © 2022 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This provides send email through SMTP."""

import re
import smtplib
import unicodedata
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app
from notify_api.models import (
    Content,
    Notification,
    NotificationSendResponse,
    NotificationSendResponses,
)
from structured_logging import StructuredLogging

logger = StructuredLogging.get_logger()


class EmailSMTP:
    """Send emails via SMTP."""

    def __init__(self, notification: Notification) -> None:
        """Construct object."""
        config = current_app.config
        self.mail_server = config.get("MAIL_SERVER")
        self.mail_port = config.get("MAIL_PORT")
        self.mail_from_id = config.get("MAIL_FROM_ID")
        self.notification = notification

    def _prepare_subject(self, subject: str) -> str:
        """Prepare email subject with environment prefix if needed."""
        deployment_env = current_app.config.get("DEPLOYMENT_ENV")

        if deployment_env is None:
            # When deployment env is not configured, treat as unknown rather than production
            env_name = "UNKNOWN"
            return f"{subject} - from {env_name} environment"

        deployment_env = deployment_env.lower()
        if deployment_env == "production":
            return subject
        else:
            env_name = deployment_env.upper() if deployment_env else "UNKNOWN"
            return f"{subject} - from {env_name} environment"

    def _prepare_message(self, content: Content) -> MIMEMultipart:
        """Prepare the email message with content and attachments."""
        encoding = "utf-8"
        message = MIMEMultipart()

        subject = self._prepare_subject(content.subject)
        message["Subject"] = subject
        message["From"] = self.mail_from_id
        message["To"] = self.notification.recipients
        message.attach(MIMEText(content.body, "html", encoding))

        if content.attachments:
            for attachment in content.attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.file_bytes)
                encode_base64(part)

                filename = unicodedata.normalize("NFKD", attachment.file_name)
                filename = re.sub(r"[\s]+", " ", filename).strip().encode("ascii", "ignore").decode("ascii")

                part.add_header("Content-Disposition", "attachment; filename=" + filename)
                message.attach(part)

        return message

    def send(self) -> NotificationSendResponses:
        """Send message."""
        # Validate notification content exists and is not empty
        if not self.notification.content:
            logger.error("No message content available for notification")
            return None
            return NotificationSendResponses(recipients=[])

        content = self.notification.content[0]

        # Additional content validation
        if not all(hasattr(content, attr) for attr in ["subject", "body"]):
            logger.error("Invalid message content structure - missing subject or body")
            return NotificationSendResponses(recipients=[])

        message = self._prepare_message(content)
        response_list: list[NotificationSendResponse] = []
        recipients = [r.strip() for r in self.notification.recipients.split(",") if r.strip()]

        try:
            with smtplib.SMTP(host=self.mail_server, port=self.mail_port) as server:
                for recipient in recipients:
                    try:
                        server.sendmail(message["From"], [recipient], message.as_string())
                        sent_response = NotificationSendResponse(response_id=None, recipient=recipient)
                        response_list.append(sent_response)
                    except Exception as e:
                        logger.error(f"Error sending email to {recipient}: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"Error connecting to SMTP server: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred when connecting to SMTP server: {e}")

        return NotificationSendResponses(recipients=response_list)
