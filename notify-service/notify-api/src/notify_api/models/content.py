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

from notify_api.utils.util import to_camel

from .attachment import Attachment, AttachmentRequest
from .db import db


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
        return v_field

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v_field):
        """Valiate field is not empty."""
        if not v_field:
            raise ValueError("The email body must not empty.")
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
    def create_content(cls, content: ContentRequest, notification_id: int):
        """Create notification content."""
        db_content = Content(subject=content.subject, body=content.body, notification_id=notification_id)
        db.session.add(db_content)
        db.session.commit()
        db.session.refresh(db_content)

        if content.attachments:
            for attachment in content.attachments:
                # save email attachment
                Attachment.create_attachment(attachment=attachment, content_id=db_content.id)
        return db_content

    def update_content(self):
        """Update content."""
        db.session.add(self)
        db.session.flush()
        db.session.commit()
        return self

    def delete_content(self):
        """Delete notification content."""
        if self.attachments:
            for attachment in self.attachments:
                # delete email attachment
                attachment.delete_attachment()

        db.session.delete(self)
        db.session.commit()
