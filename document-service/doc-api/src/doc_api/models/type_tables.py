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
"""This module holds model definitions for the MHR type tables."""

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from doc_api.utils.base import BaseEnum

from .db import db


class RequestTypes(BaseEnum):
    """Render an Enum of the document service request types."""

    ADD = "ADD"
    GET = "GET"
    PENDING = "PENDING"
    REPLACE = "REPLACE"
    UPDATE = "UPDATE"


class DocumentClasses(BaseEnum):
    """Render an Enum of the document service document classes."""

    COOP = "COOP"
    CORP = "CORP"
    FIRM = "FIRM"
    LP_LLP = "LP_LLP"
    MHR = "MHR"
    NR = "NR"
    OTHER = "OTHER"
    PPR = "PPR"
    SOCIETY = "SOCIETY"
    XP = "XP"


class DocumentTypes(BaseEnum):
    """Render an Enum of the document service document types."""

    REG_101 = "REG_101"
    REG_102 = "REG_102"
    REG_103 = "REG_103"
    MHR_MISC = "MHR_MISC"
    ABAN = "ABAN"
    ADDI = "ADDI"
    AFFE = "AFFE"
    ATTA = "ATTA"
    BANK = "BANK"
    BCLC = "BCLC"
    CAU = "CAU"
    CAUC = "CAUC"
    CAUE = "CAUE"
    COMP = "COMP"
    COUR = "COUR"
    DEAT = "DEAT"
    DNCH = "DNCH"
    EXMN = "EXMN"
    EXNR = "EXNR"
    EXRE = "EXRE"
    EXRS = "EXRS"
    FORE = "FORE"
    FZE = "FZE"
    GENT = "GENT"
    LETA = "LETA"
    MAID = "MAID"
    MAIL = "MAIL"
    MARR = "MARR"
    NAMV = "NAMV"
    NCAN = "NCAN"
    NCON = "NCON"
    NPUB = "NPUB"
    NRED = "NRED"
    PDEC = "PDEC"
    PUBA = "PUBA"
    REBU = "REBU"
    REGC = "REGC"
    REIV = "REIV"
    REPV = "REPV"
    REST = "REST"
    STAT = "STAT"
    SZL = "SZL"
    TAXN = "TAXN"
    TAXS = "TAXS"
    THAW = "THAW"
    TRAN = "TRAN"
    VEST = "VEST"
    WHAL = "WHAL"
    WILL = "WILL"
    COOP_MISC = "COOP_MISC"
    CORP_MISC = "CORP_MISC"
    FIRM_MISC = "FIRM_MISC"
    LP_LLP_MISC = "LP_LLP_MISC"
    NR_MISC = "NR_MISC"
    PPR_MISC = "PPR_MISC"
    SOC_MISC = "SOC_MISC"
    XP_MISC = "XP_MISC"
    COFI = "COFI"
    DISS = "DISS"
    DISD = "DISD"
    ATTN = "ATTN"
    FRMA = "FRMA"
    AMLO = "AMLO"
    CNTA = "CNTA"
    CNTI = "CNTI"
    CNTO = "CNTO"
    COFF = "COFF"
    COSD = "COSD"
    AMLG = "AMLG"
    AMAL = "AMAL"
    RSRI = "RSRI"
    ASNU = "ASNU"
    LPRG = "LPRG"
    FILE = "FILE"
    CNVF = "CNVF"
    COPN = "COPN"
    MHSP = "MHSP"
    FNCH = "FNCH"
    CONS = "CONS"
    PPRS = "PPRS"
    PPRC = "PPRC"
    ADDR = "ADDR"
    ANNR = "ANNR"
    CORR = "CORR"
    DIRS = "DIRS"
    CORC = "CORC"
    SOCF = "SOCF"

    CERT = "CERT"
    LTR = "LTR"
    CLW = "CLW"
    BYLW = "BYLW"
    CNST = "CNST"
    CONT = "CONT"
    SYSR = "SYSR"
    ADMN = "ADMN"
    RSLN = "RSLN"
    AFDV = "AFDV"
    SUPP = "SUPP"
    MNOR = "MNOR"
    FINM = "FINM"
    APCO = "APCO"
    RPTP = "RPTP"
    DAT = "DAT"
    BYLT = "BYLT"
    CNVS = "CNVS"
    CRTO = "CRTO"
    MEM = "MEM"
    PRE = "PRE"
    REGO = "REGO"
    PLNA = "PLNA"
    REGN = "REGN"
    FINC = "FINC"
    BCGT = "BCGT"
    CHNM = "CHNM"
    OTP = "OTP"
    CORSP = "CORSP"
    PPR = "PPR"
    LHS = "LHS"
    RGS = "RGS"
    HSR = "HSR"
    RPL = "RPL"
    FINS = "FINS"


class RequestType(db.Model):  # pylint: disable=too-few-public-methods
    """This class defines the model for the request_types table."""

    __tablename__ = "request_types"

    request_type = db.mapped_column("request_type", PG_ENUM(RequestTypes, name="requesttype"), primary_key=True)
    request_type_desc = db.mapped_column("request_type_desc", db.String(100), nullable=False)

    # Relationships -

    @classmethod
    def find_all(cls):
        """Return all the type records."""
        return db.session.query(RequestType).all()


class DocumentClass(db.Model):  # pylint: disable=too-few-public-methods
    """This class defines the model for the document classes table."""

    __tablename__ = "document_classes"

    document_class = db.mapped_column(
        "document_class", PG_ENUM(DocumentClasses, name="documentclass"), primary_key=True
    )
    document_class_desc = db.mapped_column("document_class_desc", db.String(100), nullable=False)
    #  Added to support scanning app
    active = db.mapped_column("active", db.Boolean, nullable=True)
    scanning_owner_type = db.mapped_column("scanning_owner_type", db.String(20), nullable=True)
    schedule_number = db.mapped_column("schedule_number", db.Boolean, nullable=True)

    # Relationships
    doc_type = db.relationship("DocumentType", back_populates="doc_class")

    @property
    def scanning_json(self) -> dict:
        """Return the document class as a scanning json object."""
        doc_type = {
            "ownerType": self.scanning_owner_type if self.scanning_owner_type else "",
            "documentClass": self.document_class,
            "documentClassDescription": self.document_class_desc,
            "active": bool(self.active) if self.active is not None else True,
            "scheduleNumber": self.schedule_number if self.schedule_number else 0,
        }
        return doc_type

    @classmethod
    def find_all_scanning(cls):
        """Return all the type records for the scanning application."""
        return db.session.query(DocumentClass).order_by(DocumentClass.scanning_owner_type).all()

    @classmethod
    def find_all(cls):
        """Return all the type records."""
        return db.session.query(DocumentClass).all()

    @classmethod
    def find_by_doc_class(cls, doc_class: str):
        """Return a specific record by type."""
        if not doc_class or doc_class not in DocumentClasses:
            return None
        return db.session.query(DocumentClass).filter(DocumentClass.document_class == doc_class).one_or_none()


class DocumentType(db.Model):  # pylint: disable=too-few-public-methods
    """This class defines the model for the document types table."""

    __tablename__ = "document_types"

    document_type = db.mapped_column("document_type", PG_ENUM(DocumentTypes, name="documenttype"), primary_key=True)
    document_class = db.mapped_column(
        "document_class",
        PG_ENUM(DocumentClasses, name="documentclass"),
        db.ForeignKey("document_classes.document_class"),
        nullable=False,
    )
    document_type_desc = db.mapped_column("document_type_desc", db.String(100), nullable=False)
    product = db.mapped_column("product", db.String(20), nullable=False)
    doc_id_required = db.mapped_column("doc_id_required", db.Boolean, nullable=False)
    #  Added to support scanning app
    active = db.mapped_column("active", db.Boolean, nullable=True)
    application_id = db.mapped_column("application_id", db.String(20), nullable=True)

    # Relationships
    doc_class = db.relationship(
        "DocumentClass", foreign_keys=[document_class], back_populates="doc_type", cascade="all, delete", uselist=False
    )
    document = db.relationship("Document", back_populates="doc_type")

    @property
    def scanning_json(self) -> dict:
        """Return the document type as a json object."""
        doc_type = {
            "documentType": self.document_type,
            "documentTypeDescription": self.document_type_desc,
            "active": bool(self.active) if self.active is not None else True,
            "applicationId": self.application_id if self.application_id else "",
        }
        return doc_type

    @classmethod
    def find_all_scanning(cls):
        """Return all the type records for the scanning application."""
        return db.session.query(DocumentType).order_by(DocumentType.document_type).all()

    @classmethod
    def find_all(cls):
        """Return all the type records."""
        return db.session.query(DocumentType).all()

    @classmethod
    def find_by_doc_type(cls, doc_type: str):
        """Return a specific record by type."""
        if not doc_type or doc_type not in DocumentTypes:
            return None
        return db.session.query(DocumentType).filter(DocumentType.document_type == doc_type).one_or_none()

    @classmethod
    def find_by_doc_class(cls, doc_class: str):
        """Return all types that belong to the class."""
        if not doc_class or doc_class not in DocumentClasses:
            return None
        return db.session.query(DocumentType).filter(DocumentType.document_class == doc_class).all()
