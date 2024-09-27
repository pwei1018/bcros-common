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
"""This module holds data for the document scanning application schedules."""

from doc_api.exceptions import DatabaseException
from doc_api.utils.logging import logger

from .db import db


class ScanningSchedule(db.Model):
    """This class manages the document scanning application schedule information."""

    __tablename__ = "scanning_schedules"

    id = db.mapped_column("id", db.Integer, db.Sequence("scanning_schedule_id_seq"), primary_key=True)
    sequence_number = db.mapped_column("sequence_number", db.Integer, nullable=False)
    schedule_number = db.mapped_column("schedule_number", db.Integer, nullable=False)

    # parent keys

    # Relationships

    @property
    def json(self) -> dict:
        """Return the document scanning box information as a json object."""
        schedule = {"sequenceNumber": self.sequence_number, "scheduleNumber": self.schedule_number}
        return schedule

    @classmethod
    def find_by_id(cls, pkey: int = None):
        """Return a scanning document schedule object by primary key."""
        schedule = None
        if pkey:
            try:
                schedule = db.session.query(ScanningSchedule).filter(ScanningSchedule.id == pkey).one_or_none()
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("ScanningSchedule.find_by_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return schedule

    @classmethod
    def find_all(cls):
        """Return a list of all schedule objects."""
        schedule = None
        try:
            schedule = db.session.query(ScanningSchedule).order_by(ScanningSchedule.schedule_number).all()
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error("ScanningSchedule.find_all exception: " + str(db_exception))
            raise DatabaseException(db_exception) from db_exception
        return schedule

    def save(self):
        """Store the Document Scanning information into the local cache."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_from_json(schedule_json: dict):
        """Create a new scanning schedule object."""
        schedule = ScanningSchedule(
            sequence_number=schedule_json.get("sequenceNumber"), schedule_number=schedule_json.get("scheduleNumber")
        )
        return schedule
