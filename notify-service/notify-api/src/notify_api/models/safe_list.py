# Copyright © 2019 Province of British Columbia
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
"""Safe List data model."""

from __future__ import annotations

from pydantic import BaseModel

from .db import db


class SafeListRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Notification model for request."""

    email: list[str] | None = None


class SafeList(db.Model):
    """Immutable Safe List record."""

    __tablename__ = "safe_list"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(2000), nullable=False)

    @property
    def json(self) -> dict:
        """Return a dict of this object, with keys in JSON format."""
        return {"id": self.id, "email": self.email}

    @classmethod
    def add_email(cls, email: str):
        """Add email to list."""
        db_email = SafeList(email=email)

        try:
            db.session.add(db_email)
            db.session.commit()
            db.session.refresh(db_email)
        except Exception:  # pylint: disable=broad-except
            db.session.rollback()

        return db_email

    @classmethod
    def is_in_safe_list(cls, email: str) -> bool:
        """Is email in safe list."""
        is_safe = False
        safe_email = cls.query.filter_by(email=email).all()
        if safe_email:
            is_safe = True

        return is_safe

    @classmethod
    def find_by_email(cls, email: str) -> SafeList:
        """return safe list."""
        return (cls.query.filter_by(email=email).all())[0]

    @classmethod
    def find_all(cls) -> list[SafeList]:
        """Return all of the safe emails."""
        return cls.query.all()

    def delete_email(self):
        """delete email from safe list."""
        db.session.delete(self)
        db.session.commit()
