# Copyright © 2026 Province of British Columbia
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
"""BC Notify callback data models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .db import db


class BCNotifyCallbackData(BaseModel):
    """Provider-specific data in a BC Notify callback event."""

    model_config = ConfigDict(populate_by_name=True)

    notify_id: str = Field(alias="notifyId")
    status: str
    status_display_name: str = Field(alias="statusDisplayName")
    channel: Literal["EMAIL", "SMS"]
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class BCNotifyCallbackRequest(BaseModel):
    """BC Notify notification status changed event."""

    model_config = ConfigDict(populate_by_name=True)

    event: str
    notification_id: str = Field(alias="notificationId")
    tenant_id: str = Field(alias="tenantId")
    data: BCNotifyCallbackData
    delivered_at: datetime = Field(alias="deliveredAt")


class BCNotifyCallback(db.Model):
    """Persisted BC Notify callback event."""

    __tablename__ = "bc_notify_callback"

    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String, nullable=False)
    notification_id = db.Column(db.String, nullable=False, index=True)
    tenant_id = db.Column(db.String, nullable=False)
    notify_id = db.Column(db.String, nullable=False, index=True)
    status = db.Column(db.String, nullable=False)
    status_display_name = db.Column(db.String, nullable=False)
    channel = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=False)

    @classmethod
    def save(cls, callback: BCNotifyCallbackRequest) -> None:
        """Persist a BC Notify callback event."""
        db_callback = cls(
            event=callback.event,
            notification_id=callback.notification_id,
            tenant_id=callback.tenant_id,
            notify_id=callback.data.notify_id,
            status=callback.data.status,
            status_display_name=callback.data.status_display_name,
            channel=callback.data.channel,
            created_at=callback.data.created_at,
            updated_at=callback.data.updated_at,
            delivered_at=callback.delivered_at,
        )

        try:
            db.session.add(db_callback)
            db.session.commit()
            db.session.refresh(db_callback)
        except Exception as error:  # pylint: disable=broad-except
            db.session.rollback()
            from structured_logging import StructuredLogging

            StructuredLogging.get_logger().warning(
                f"Failed to save BC Notify callback for notification {callback.notification_id}. Error: {error}"
            )
