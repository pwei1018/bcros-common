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
"""This module holds data for the document scanning application list of authors."""

from doc_api.exceptions import DatabaseException
from doc_api.utils.logging import logger

from .db import db


class ScanningAuthor(db.Model):
    """This class manages the document scanning application author information."""

    __tablename__ = "scanning_authors"

    id = db.mapped_column("id", db.Integer, db.Sequence("scanning_author_id_seq"), primary_key=True)
    last_name = db.mapped_column("last_name", db.String(50), nullable=False)
    first_name = db.mapped_column("first_name", db.String(50), nullable=False)
    job_title = db.mapped_column("job_title", db.String(150), nullable=True)
    email = db.mapped_column("email", db.String(250), nullable=True)
    phone_number = db.mapped_column("phone_number", db.String(20), nullable=True)

    # parent keys

    # Relationships

    @property
    def json(self) -> dict:
        """Return the author information as a json object."""
        author = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "jobTitle": self.job_title if self.job_title else "",
            "email": self.email if self.email else "",
            "phoneNumber": self.phone_number if self.phone_number else "",
        }
        return author

    @classmethod
    def find_by_id(cls, pkey: int = None):
        """Return an author object by primary key."""
        author = None
        if pkey:
            try:
                author = db.session.query(ScanningAuthor).filter(ScanningAuthor.id == pkey).one_or_none()
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("ScanningAuthor.find_by_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return author

    @classmethod
    def find_all(cls):
        """Return a list of all author objects."""
        authors = None
        try:
            authors = (
                db.session.query(ScanningAuthor).order_by(ScanningAuthor.last_name, ScanningAuthor.first_name).all()
            )
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error("ScanningAuthor.find_all exception: " + str(db_exception))
            raise DatabaseException(db_exception) from db_exception
        return authors

    def save(self):
        """Store the Document Scanning information into the local cache."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_from_json(author_json: dict):
        """Create a new author object."""
        author = ScanningAuthor(
            first_name=author_json.get("firstName"),
            last_name=author_json.get("lastName"),
        )
        if author_json.get("jobTitle"):
            author.job_title = author_json.get("jobTitle")
        if author_json.get("email"):
            author.email = author_json.get("email")
        if author_json.get("phoneNumber"):
            author.phone_number = author_json.get("phoneNumber")
        return author
