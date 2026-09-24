# Copyright © 2021 Province of British Columbia
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
"""Notification Content data model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from notify_api.utils.util import config_limit, to_camel

from .attachment import Attachment, AttachmentRequest
from .db import db

# Default guardrails (overridable via app config / env vars, see Config.NOTIFY_MAX_*).
DEFAULT_MAX_BODY_LENGTH = 1_000_000
DEFAULT_MAX_ATTACHMENTS = 10
# Matches the `subject` column width (String(2000)) so oversized input is rejected
# with a clean 400 instead of failing at the database layer.
MAX_SUBJECT_LENGTH = 2000


class ContentRequest(BaseModel):
    """Entity Request model for the Notification content."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, coerce_numbers_to_str=True)

    subject: str = Field(alias="subject")
    body: str = Field(alias="body")
    attachments: list[AttachmentRequest] | None = None

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v_field):
        """Valiate field is not empty."""
        if not v_field:
            raise ValueError("The email subject must not empty.")
        if len(v_field) > MAX_SUBJECT_LENGTH:
            raise ValueError(f"The email subject must not exceed {MAX_SUBJECT_LENGTH} characters.")
        return v_field

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v_field):
        """Valiate field is not empty."""
        if not v_field:
            raise ValueError("The email body must not empty.")
        max_body_length = config_limit("NOTIFY_MAX_BODY_LENGTH", DEFAULT_MAX_BODY_LENGTH)
        if len(v_field) > max_body_length:
            raise ValueError(f"The email body must not exceed {max_body_length} characters.")
        return v_field

    @field_validator("attachments")
    @classmethod
    def attachments_within_limit(cls, v_field):
        """Validate the number of attachments does not exceed the configured maximum."""
        if v_field:
            max_attachments = config_limit("NOTIFY_MAX_ATTACHMENTS", DEFAULT_MAX_ATTACHMENTS)
            if len(v_field) > max_attachments:
                raise ValueError(
                    f"Too many attachments: {len(v_field)} provided, maximum is {max_attachments}."
                )
        return v_field


class Content(db.Model):
    """Immutable Content record. Represents Content."""

    __tablename__ = "content"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(2000), nullable=False)
    body = db.Column(db.Text, nullable=False)

    # parent keys
    notification_id = db.Column(db.ForeignKey("notification.id"), nullable=False)

    # relationships
    attachments = db.relationship("Attachment", order_by="Attachment.attach_order")

    @property
    def json(self):
        """Return a dict of this object, with keys in JSON format."""
        content_json = {"id": self.id, "subject": self.subject}

        if self.attachments:
            attachment_list = [attachment.json for attachment in self.attachments]

            content_json["attachments"] = attachment_list

        return content_json

    @classmethod
    def create_content(cls, content: ContentRequest, notification_id: int, commit: bool = True):
        """Create notification content.

        Args:
            content: The content request data.
            notification_id: The parent notification row id.
            commit: When True (default), commits immediately. Pass False to
                only flush the content and its attachments within a
                caller-managed transaction (e.g. so they can be committed
                atomically alongside the parent notification row).
        """
        db_content = Content(subject=content.subject, body=content.body, notification_id=notification_id)
        db.session.add(db_content)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        db.session.refresh(db_content)

        if content.attachments:
            for attachment in content.attachments:
                # save email attachment
                Attachment.create_attachment(attachment=attachment, content_id=db_content.id, commit=commit)
        return db_content

    def update_content(self):
        """Update content."""
        db.session.add(self)
        db.session.flush()
        db.session.commit()
        return self

    def delete_content(self, commit: bool = True):
        """Delete notification content.

        Args:
            commit: When True (default), commits immediately. Pass False to
                only flush the delete within a caller-managed transaction
                (e.g. so it can be committed atomically alongside other
                related changes).
        """
        if self.attachments:
            for attachment in self.attachments:
                # delete email attachment
                attachment.delete_attachment(commit=commit)

        db.session.delete(self)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
