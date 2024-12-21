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
"""This module holds data for individual legacy document scanning record information."""

from sqlalchemy import UniqueConstraint, and_
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.sql import text

from doc_api.exceptions import DatabaseException
from doc_api.models import utils as model_utils
from doc_api.utils.logging import logger

from .db import db
from .type_tables import DocumentClasses

MAX_BATCH_ID_QUERY = "select max(cast(batch_id as integer)) from document_scanning where accession_number = :query_val"


class DocumentScanning(db.Model):
    """This class manages all of the document service legacy document scanning information."""

    __tablename__ = "document_scanning"

    id = db.mapped_column("id", db.Integer, db.Sequence("doc_scanning_id_seq"), primary_key=True)
    consumer_document_id = db.mapped_column("consumer_document_id", db.String(20), nullable=False, index=True)
    create_ts = db.mapped_column("create_ts", db.DateTime, nullable=True, index=True)
    scan_date = db.mapped_column("scan_date", db.DateTime, nullable=True, index=True)
    accession_number = db.mapped_column("accession_number", db.String(20), nullable=True)
    batch_id = db.mapped_column("batch_id", db.String(20), nullable=True)
    author = db.mapped_column("author", db.String(1000), nullable=True)
    page_count = db.mapped_column("page_count", db.Integer, nullable=True)

    # parent keys
    document_class = db.mapped_column(
        "document_class",
        PG_ENUM(DocumentClasses, name="documentclass"),
        db.ForeignKey("document_classes.document_class"),
        nullable=False,
        index=True,
    )

    __table_args__ = (UniqueConstraint("consumer_document_id", "document_class", name="scanning_cons_id_class_uc"),)

    # Relationships

    @property
    def json(self) -> dict:
        """Return the document scanning information as a json object."""
        scan_info = {
            "consumerDocumentId": self.consumer_document_id,
            "createDateTime": model_utils.format_ts(self.create_ts),
            "documentClass": self.document_class,
            "accessionNumber": self.accession_number if self.accession_number else "",
            "batchId": self.batch_id if self.batch_id else "",
            "author": self.author if self.author else "",
        }
        if self.scan_date:
            scan_info["scanDateTime"] = model_utils.format_ts(self.scan_date)
        if self.page_count and self.page_count > 0:
            scan_info["pageCount"] = self.page_count
        return scan_info

    @classmethod
    def find_by_id(cls, pkey: int = None):
        """Return a document object by primary key."""
        doc_scan = None
        if pkey:
            try:
                doc_scan = db.session.query(DocumentScanning).filter(DocumentScanning.id == pkey).one_or_none()
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("DocumentScanning.find_by_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return doc_scan

    @classmethod
    def find_by_document_id(cls, doc_id: str, doc_class: str):
        """Return a document scanning record by consumer document id and document class."""
        doc_scan = None
        if doc_id:
            try:
                doc_scan = (
                    db.session.query(DocumentScanning)
                    .filter(
                        and_(
                            DocumentScanning.consumer_document_id == doc_id,
                            DocumentScanning.document_class == doc_class,
                        )
                    )
                    .one_or_none()
                )
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("DocumentScanning.find_by_document_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return doc_scan

    def save(self):
        """Store the Document Scanning information into the local cache."""
        db.session.add(self)
        db.session.commit()

    def update(self, scan_json: dict, consumer_doc_id: str = None, doc_class: str = None):
        """Update the Document Scanning Information."""
        if scan_json.get("scanDateTime"):
            self.scan_date = model_utils.ts_from_iso_date_noon(scan_json.get("scanDateTime"))
        if scan_json.get("accessionNumber"):
            self.accession_number = scan_json.get("accessionNumber")
        if scan_json.get("batchId"):
            self.batch_id = scan_json.get("batchId")
        if scan_json.get("pageCount"):
            self.page_count = scan_json.get("pageCount")
        if scan_json.get("author"):
            self.author = scan_json.get("author")
        if consumer_doc_id:
            self.consumer_document_id = consumer_doc_id
        if doc_class:
            self.document_class = doc_class

    @staticmethod
    def create_from_json(scan_json: dict, consumer_doc_id: str, doc_class: str):
        """Create a new document object from a new save document request."""
        doc_scan = DocumentScanning(
            create_ts=model_utils.now_ts(),
            consumer_document_id=consumer_doc_id,
            document_class=doc_class,
        )
        if scan_json.get("scanDateTime"):
            doc_scan.scan_date = model_utils.ts_from_iso_date_noon(scan_json.get("scanDateTime"))
        elif scan_json.get("scanDate"):
            doc_scan.scan_date = model_utils.ts_from_iso_date_noon(scan_json.get("scanDate"))
        if scan_json.get("accessionNumber"):
            doc_scan.accession_number = scan_json.get("accessionNumber")
        if scan_json.get("batchId"):
            doc_scan.batch_id = scan_json.get("batchId")
        if scan_json.get("pageCount"):
            doc_scan.page_count = scan_json.get("pageCount")
        if scan_json.get("author"):
            doc_scan.author = scan_json.get("author")
        return doc_scan

    @staticmethod
    def get_max_batch_id(accession_number: str) -> int:
        """Get the current highest batch id for an accession_number. The default is 0."""
        batch_id: int = 0
        if not accession_number:
            return batch_id
        try:
            query = text(MAX_BATCH_ID_QUERY)
            result = db.session.execute(query, {"query_val": accession_number})
            row = result.first()
            if row and row[0]:
                batch_id = int(row[0])
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error("get_max_batch_id exception: " + str(db_exception))
        return batch_id
