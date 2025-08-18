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
"""Notification Attachment data model."""

from __future__ import annotations

import base64

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from notify_api.utils.util import download_file, to_camel

from .db import db


class AttachmentRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """This is the Request model for the Notification attachment."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    file_name: str = Field(alias="fileName")
    file_bytes: str | None = Field(default=None, alias="fileBytes")
    file_url: str | None = Field(default=None, alias="fileUrl")
    attach_order: str = Field(alias="attachOrder", coerce_numbers_to_str=True)

    @field_validator("file_name")
    @classmethod
    def not_empty(cls, v_field):
        """Valiate field is not empty."""
        if not v_field:
            raise ValueError("The file name must not empty.")
        return v_field

    @model_validator(mode="after")
    def must_contain_one(self):
        """Valiate field is not empty."""
        if not self.file_bytes and not self.file_url:
            raise ValueError("The file content must attach")
        return self


class Attachment(db.Model):
    """Immutable attachment record. Represents attachment."""

    __tablename__ = "attachment"

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(200), nullable=False)
    file_bytes = db.Column(db.LargeBinary, nullable=False)
    attach_order = db.Column(db.Integer, nullable=True)

    # parent keys
    content_id = db.Column(db.ForeignKey("content.id"), nullable=False)

    @property
    def json(self) -> dict:
        """Return a dict of this object, with keys in JSON format."""
        return {"id": self.id, "fileName": self.file_name, "attachOrder": self.attach_order}

    @classmethod
    def create_attachment(cls, attachment: AttachmentRequest, content_id: int):
        """Create notification attachment."""
        file_bytes = None

        if attachment.file_url:
            file_bytes = download_file(attachment.file_url)
        else:
            file_bytes = base64.b64decode(attachment.file_bytes)

        db_attachment = Attachment(
            content_id=content_id,
            file_name=attachment.file_name,
            file_bytes=file_bytes,
            attach_order=attachment.attach_order,
        )
        db.session.add(db_attachment)
        db.session.commit()
        db.session.refresh(db_attachment)

        return db_attachment

    def delete_attachment(self):
        """Delete notification attachment.."""
        db.session.delete(self)
        db.session.commit()
