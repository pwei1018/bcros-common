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
"""This module holds model data for registries application reports."""
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.sql import text

from doc_api.exceptions import DatabaseException
from doc_api.models import utils as model_utils
from doc_api.utils.logging import logger

from .db import db
from .type_tables import ProductCodes

QUERY_KEYS = """
select nextval('application_report_id_seq') AS report_id,
       get_service_report_id() AS service_report_id
"""
DEFAULT_NAME = "{entity_id}-{event_id}-{report_type}.pdf"


class ApplicationReport(db.Model):
    """This class maintains application report information."""

    __tablename__ = "application_reports"

    id = db.mapped_column("id", db.Integer, primary_key=True)
    document_service_id = db.mapped_column("document_service_id", db.String(20), nullable=False, unique=True)
    create_ts = db.mapped_column("create_ts", db.DateTime, nullable=False, index=True)
    entity_id = db.mapped_column("entity_id", db.String(20), nullable=False, index=True)
    event_id = db.mapped_column("event_id", db.Integer, nullable=False, index=True)
    report_type = db.mapped_column("report_type", db.String(30), nullable=False)
    filename = db.mapped_column("filename", db.String(1000), nullable=True)
    filing_date = db.mapped_column("filing_date", db.DateTime, nullable=True, index=True)
    doc_storage_url = db.mapped_column("doc_storage_url", db.String(1000), nullable=True)

    # parent keys
    product_code = db.mapped_column(
        "product_code",
        PG_ENUM(ProductCodes, name="productcode"),
        db.ForeignKey("product_codes.product_code"),
        nullable=True,
        index=True,
    )

    # Relationships - MhrRegistration
    prod_code = db.relationship(
        "ProductCode",
        foreign_keys=[product_code],
        back_populates="application_report",
        cascade="all, delete",
        uselist=False,
    )

    @property
    def json(self) -> dict:
        """Return the application report information as a json object."""
        report = {
            "identifier": self.document_service_id,
            "dateCreated": model_utils.format_ts(self.create_ts),
            "entityIdentifier": self.entity_id,
            "eventIdentifier": self.event_id,
            "reportType": self.report_type,
            "name": self.filename if self.filename else "",
            "url": self.doc_storage_url if self.doc_storage_url else "",
            "productCode": self.product_code if self.product_code else "",
        }
        if self.filing_date:
            report["datePublished"] = model_utils.format_ts(self.filing_date)
        return report

    def get_generated_values(self):
        """Get db generated identifiers that are required up front.

        Get application report id and document service report id.
        """
        query_text = QUERY_KEYS
        query = text(query_text)
        result = db.session.execute(query)
        row = result.first()
        self.id = int(row[0])
        self.document_service_id = str(row[1])

    def save(self):
        """Render an application report record to the local cache."""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as db_exception:  # noqa: B902; just logging
            logger.error("DB application report save exception: " + str(db_exception))
            raise DatabaseException(db_exception) from db_exception

    def update(self, request_json: dict):
        """Update the report Information from a patch request."""
        if not request_json:
            return
        if request_json.get("name"):
            self.filename = request_json.get("name")
        if request_json.get("reportType"):
            self.report_type = request_json.get("reportType")
        if request_json.get("datePublished"):
            if len(request_json.get("datePublished")) == 10:
                self.filing_date = model_utils.ts_from_iso_date_noon(request_json.get("datePublished"))
            else:
                self.filing_date = model_utils.ts_from_iso_format(request_json.get("datePublished"))

    def update_storage_url(self, doc_storage_url: str = None):
        """Update the report doc storage URL after the document is generated and stored."""
        self.doc_storage_url = doc_storage_url
        self.save()

    @classmethod
    def find_by_id(cls, report_id: int):
        """Return the application report metadata record matching the id."""
        report = None
        if report_id:
            report = db.session.query(ApplicationReport).filter(ApplicationReport.id == report_id).one_or_none()

        return report

    @classmethod
    def find_by_doc_service_id(cls, doc_service_id: str, product_code: str = None):
        """Return a application report object by document service ID."""
        report = None
        if doc_service_id:
            try:
                if product_code:
                    report = (
                        db.session.query(ApplicationReport)
                        .filter(
                            and_(
                                ApplicationReport.product_code == product_code.upper(),
                                ApplicationReport.document_service_id == doc_service_id,
                            )
                        )
                        .one_or_none()
                    )
                else:
                    report = (
                        db.session.query(ApplicationReport)
                        .filter(ApplicationReport.document_service_id == doc_service_id)
                        .one_or_none()
                    )
            except Exception as db_exception:  # noqa: B902; return nicer error
                logger.error("ApplicationReport.find_by_doc_service_id exception: " + str(db_exception))
                raise DatabaseException(db_exception) from db_exception
        return report

    @classmethod
    def find_by_entity_id(cls, entity_id: str, product_code: str = None) -> list:
        """Return the all report records that match the entity ID ordered by event ID."""
        if not entity_id:
            return None
        reports = None
        try:
            if product_code:
                reports = (
                    db.session.query(ApplicationReport)
                    .filter(
                        and_(
                            ApplicationReport.product_code == product_code.upper(),
                            ApplicationReport.entity_id == entity_id,
                        )
                    )
                    .order_by(ApplicationReport.event_id)
                    .all()
                )
            else:
                reports = (
                    db.session.query(ApplicationReport)
                    .filter(ApplicationReport.entity_id == entity_id)
                    .order_by(ApplicationReport.event_id)
                    .all()
                )
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error("ApplicationReport.find_by_entity_id exception: " + str(db_exception))
            raise DatabaseException(db_exception) from db_exception
        return reports

    @classmethod
    def find_by_entity_id_json(cls, entity_id: str, product_code: str = None) -> list[dict]:
        """Return the all report records that match the entity ID as JSON, ordered by event ID."""
        report_json = []
        reports = cls.find_by_entity_id(entity_id, product_code)
        if reports:
            for report in reports:
                report_json.append(report.json)
        return report_json

    @classmethod
    def find_by_event_id(cls, event_id: int, entity_id: str = None, product_code: str = None) -> list:
        """Return the all report records that match the event ID ordered by event ID."""
        if not event_id:
            return None
        reports = None
        try:
            if entity_id and product_code:
                reports = (
                    db.session.query(ApplicationReport)
                    .filter(
                        and_(
                            ApplicationReport.product_code == product_code.upper(),
                            ApplicationReport.entity_id == entity_id,
                            ApplicationReport.event_id == event_id,
                        )
                    )
                    .order_by(ApplicationReport.event_id)
                    .all()
                )
            else:
                reports = (
                    db.session.query(ApplicationReport)
                    .filter(ApplicationReport.event_id == event_id)
                    .order_by(ApplicationReport.event_id)
                    .all()
                )
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error("ApplicationReport.find_by_event_id exception: " + str(db_exception))
            raise DatabaseException(db_exception) from db_exception
        return reports

    @classmethod
    def find_by_event_id_json(cls, event_id: int, entity_id: str = None, product_code: str = None) -> list[dict]:
        """Return the all report records that match the event ID as JSON, ordered by event ID."""
        report_json = []
        reports = cls.find_by_event_id(event_id, entity_id, product_code)
        if reports:
            for report in reports:
                report_json.append(report.json)
        return report_json

    @staticmethod
    def create_from_json(request_json: dict):
        """Create a new application report object from a new save report request."""
        report = ApplicationReport(
            create_ts=model_utils.now_ts(),
            entity_id=request_json.get("entityIdentifier"),
            event_id=request_json.get("eventIdentifier"),
            report_type=request_json.get("reportType"),
        )
        if request_json.get("datePublished"):
            if len(request_json.get("datePublished")) == 10:
                report.filing_date = model_utils.ts_from_iso_date_noon(request_json.get("datePublished"))
            else:
                report.filing_date = model_utils.ts_from_iso_format(request_json.get("datePublished"))
        else:
            report.filing_date = report.create_ts
        if request_json.get("name"):
            report.filename = request_json.get("name")
        else:
            report.filename = DEFAULT_NAME.format(
                entity_id=report.entity_id, event_id=report.event_id, report_type=report.report_type.lower()
            )
        if request_json.get("productCode"):
            report.product_code = request_json.get("productCode")
        report.get_generated_values()
        return report
