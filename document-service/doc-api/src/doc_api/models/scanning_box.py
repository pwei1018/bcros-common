# Copyright © 2019 Province of British Columbia
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
"""This module holds data for the document scanning application physical storage boxes."""

from doc_api.exceptions import DatabaseException
from doc_api.utils.logging import logger

from .db import db


class ScanningBox(db.Model):
    """This class manages the document scanning application storage box information."""

    __tablename__ = "scanning_boxes"

    id = db.mapped_column("id", db.Integer, db.Sequence("scanning_box_id_seq"), primary_key=True)
    sequence_number = db.mapped_column("sequence_number", db.Integer, nullable=False)
    schedule_number = db.mapped_column("schedule_number", db.Integer, nullable=False)
    box_number = db.mapped_column("box_number", db.Integer, nullable=False)
    opened_date = db.mapped_column("opened_date", db.DateTime, nullable=True)
    closed_date = db.mapped_column("closed_date", db.DateTime, nullable=True)
    page_count = db.mapped_column("page_count", db.Integer, nullable=True)

    # parent keys

    # Relationships

    @property
    def json(self) -> dict:
        """Return the document scanning box information as a json object."""
        box = {
            "boxId": self.id,
            "boxNumber": self.box_number,
            "sequenceNumber": self.sequence_number,
            "scheduleNumber": self.schedule_number,
        }
        return box

    @classmethod
    def find_by_id(cls, pkey: int = None):
        """Return a scanning document box object by primary key."""
        box = None
        if pkey:
            try:
                box = db.session.query(ScanningBox).filter(ScanningBox.id == pkey).one_or_none()
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("ScanningBox.find_by_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return box

    def save(self):
        """Store the Document Scanning information into the local cache."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_from_json(box_json: dict):
        """Create a new box object."""
        box = ScanningBox(
            sequence_number=box_json.get("sequenceNumber"),
            schedule_number=box_json.get("scheduleNumber"),
            box_number=box_json.get("box_number"),
        )
        return box
