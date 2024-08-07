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
"""This module holds data for individual document requests."""

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from doc_api.exceptions import DatabaseException
from doc_api.models import utils as model_utils
from doc_api.utils.logging import logger

from .db import db
from .type_tables import RequestTypes


class DocumentRequest(db.Model):  # pylint: disable=too-many-instance-attributes
    """This class manages all of the document service document request auditing information."""

    __tablename__ = 'document_requests'

    id = db.mapped_column('id', db.Integer, db.Sequence('request_id_seq'), primary_key=True)
    request_ts = db.mapped_column('request_ts', db.DateTime, nullable=False, index=True)
    account_id = db.mapped_column('account_id', db.String(20), nullable=True, index=True)
    username = db.mapped_column('username', db.String(1000), nullable=True)
    request_data = db.mapped_column('request_data', db.JSON, nullable=True)
    status = db.mapped_column('status', db.Integer, nullable=True)
    status_message = db.mapped_column('status_message', db.String(4000), nullable=True)

    # parent keys
    request_type = db.mapped_column('request_type', PG_ENUM(RequestTypes, name='requesttype'),
                                    db.ForeignKey('request_types.request_type'), nullable=False)
    document_id = db.mapped_column('document_id', db.Integer, db.ForeignKey('documents.id'), nullable=False, index=True)

    # Relationships
    document = db.relationship('Document', foreign_keys=[document_id],
                               back_populates='doc_requests', cascade='all, delete', uselist=False)

    @property
    def json(self) -> dict:
        """Return the document request as a json object."""
        doc_request = {
            'createDateTime': model_utils.format_ts(self.request_ts),
            'requestType': self.request_type,
            'accountId': self.account_id,
            'documentId': self.document_id if self.document_id else 0,
            'status': self.status if self.status else 0,
            'statusMessage': self.status_message if self.status_message else ''
        }
        if self.request_data:
            doc_request['requestData'] = self.request_data
        return doc_request

    def save(self):
        """Store the Document request into the local cache."""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, pkey: int = None):
        """Return a document request object by primary key."""
        doc_request = None
        if pkey:
            try:
                doc_request = db.session.query(DocumentRequest).filter(DocumentRequest.id == pkey).one_or_none()
            except Exception as db_exception:   # noqa: B902; return nicer error
                logger.error('DocumentRequest.find_by_id exception: ' + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return doc_request
