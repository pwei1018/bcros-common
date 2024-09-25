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
"""This module holds data for the document scanning application scanner parameters."""

from doc_api.exceptions import DatabaseException
from doc_api.utils.logging import logger

from .db import db


class ScanningParameter(db.Model):
    """This class manages the document scanning application scanner parameters."""

    __tablename__ = "scanning_parameters"

    id = db.mapped_column("id", db.Integer, db.Sequence("scanning_parameter_id_seq"), primary_key=True)
    use_document_feeder = db.mapped_column("use_document_feeder", db.Boolean, nullable=True)
    show_twain_ui = db.mapped_column("show_twain_ui", db.Boolean, nullable=True)
    show_twain_progress = db.mapped_column("show_twain_progress", db.Boolean, nullable=True)
    use_full_duplex = db.mapped_column("use_full_duplex", db.Boolean, nullable=True)
    use_low_resolution = db.mapped_column("use_low_resolution", db.Boolean, nullable=True)
    max_pages_in_box = db.mapped_column("max_pages_in_box", db.Integer, nullable=True)

    # parent keys

    # Relationships

    @property
    def json(self) -> dict:
        """Return the document scanning box information as a json object."""
        parameters = {
            "useDocumentFeeder": self.use_document_feeder if self.use_document_feeder else False,
            "showTwainUi": self.show_twain_ui if self.show_twain_ui else False,
            "showTwainProgress": self.show_twain_progress if self.show_twain_progress else False,
            "useFullDuplex": self.use_full_duplex if self.use_full_duplex else False,
            "useLowResolution": self.use_low_resolution if self.use_low_resolution else False,
            "maxPagesInBox": self.max_pages_in_box if self.max_pages_in_box else 0,
        }
        return parameters

    @classmethod
    def find_by_id(cls, pkey: int = None):
        """Return a scanning parameters object by primary key."""
        parameters = None
        if pkey:
            try:
                parameters = db.session.query(ScanningParameter).filter(ScanningParameter.id == pkey).one_or_none()
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("ScanningParameter.find_by_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return parameters

    def save(self):
        """Store the Document Scanning information into the local cache."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_from_json(param_json: dict):
        """Create a new scanning parameters object."""
        parameters = ScanningParameter(max_pages_in_box=param_json.get("maxPagesInBox", 0))
        return parameters
