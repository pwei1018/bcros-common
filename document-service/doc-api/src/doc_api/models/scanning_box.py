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
from sqlalchemy import and_

from doc_api.exceptions import DatabaseException
from doc_api.models import utils as model_utils
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
            "pageCount": self.page_count if self.page_count else 0,
        }
        if self.opened_date:
            box["openedDate"] = model_utils.format_ts(self.opened_date)
        if self.closed_date:
            box["closedDate"] = model_utils.format_ts(self.closed_date)
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

    @classmethod
    def find_by_sequence_schedule(cls, sequence_num: int, schedule_num: int):
        """Return a scanning document box object by sequence number and schedule number."""
        boxes = None
        if sequence_num and schedule_num:
            try:
                boxes = (
                    db.session.query(ScanningBox)
                    .filter(
                        and_(ScanningBox.sequence_number == sequence_num, ScanningBox.schedule_number == schedule_num)
                    )
                    .order_by(ScanningBox.sequence_number, ScanningBox.schedule_number, ScanningBox.box_number)
                    .all()
                )
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("ScanningBox.find_by_sequence_schedule exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return boxes

    def save(self):
        """Store the Document Scanning information into the local cache."""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_all(cls):
        """Return a list of all author objects."""
        boxes = None
        try:
            boxes = (
                db.session.query(ScanningBox)
                .order_by(ScanningBox.sequence_number, ScanningBox.schedule_number, ScanningBox.box_number)
                .all()
            )
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error("ScanningBox.find_all exception: " + str(db_exception))
            raise DatabaseException(db_exception) from db_exception
        return boxes

    def update(self, box_json: dict):
        """Update an existing box object."""
        if box_json.get("pageCount"):
            self.page_count = box_json.get("pageCount")
        if box_json.get("openedDate"):
            self.opened_date = model_utils.ts_from_iso_date_noon(box_json.get("openedDate"))
        if box_json.get("closedDate"):
            self.closed_date = model_utils.ts_from_iso_date_noon(box_json.get("closedDate"))

    @staticmethod
    def create_from_json(box_json: dict):
        """Create a new box object."""
        box = ScanningBox()
        if box_json.get("sequenceNumber"):
            box.sequence_number = box_json.get("sequenceNumber")
        if box_json.get("scheduleNumber"):
            box.schedule_number = box_json.get("scheduleNumber")
        if box_json.get("boxNumber"):
            box.box_number = box_json.get("boxNumber")
        if box_json.get("pageCount"):
            box.page_count = box_json.get("pageCount")
        if box_json.get("openedDate"):
            box.opened_date = model_utils.ts_from_iso_date_noon(box_json.get("openedDate"))
        if box_json.get("closedDate"):
            box.closed_date = model_utils.ts_from_iso_date_noon(box_json.get("closedDate"))
        return box
