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
"""API endpoints for requests to maintain business documents."""

from http import HTTPStatus

from flask import Blueprint, g, jsonify, request

from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models import Document
from doc_api.models.type_tables import DocumentClasses, DocumentTypeClass, FilingTypeDocument, RequestTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.resources.v1.pdf_conversions import get_filename, validate_content_type
from doc_api.services.authz import is_document_authorized, is_staff
from doc_api.services.pdf_convert import MediaTypes, PdfConvert
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger
from doc_api.utils.pdf_clean import clean_pdf
from doc_api.utils.request_validator import checksum_valid

POST_REQUEST_PATH = "/documents/{doc_class}/{doc_type}"
CHANGE_REQUEST_PATH = "/documents/{doc_service_id}"
VERIFY_REQUEST_PATH = "/documents/verify{consumer_doc_id}"
PARAM_CONSUMER_FILINGTYPE = "consumerFilingType"

bp = Blueprint("DOCUMENTS1", __name__, url_prefix="/documents")  # pylint: disable=invalid-name


@bp.route("/<string:doc_class>/<string:doc_type>", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_documents(doc_class: str, doc_type: str):
    """Save a new document."""
    account_id = ""
    try:
        req_path: str = POST_REQUEST_PATH.format(doc_class=doc_class, doc_type=doc_type)
        info: RequestInfo = RequestInfo(
            RequestTypes.ADD, req_path, doc_type, resource_utils.get_doc_storage_type(doc_class)
        )
        info = resource_utils.get_request_info(request, info, is_staff(jwt))
        info.document_class = doc_class
        logger.info(f"Starting new create document request {req_path}, account={info.account_id}")
        if doc_class == DocumentClasses.CORP.value and request.args.get(PARAM_CONSUMER_FILINGTYPE):
            filing_type: str = request.args.get(PARAM_CONSUMER_FILINGTYPE)
            filing_doc: FilingTypeDocument = FilingTypeDocument.find_by_filing_type(filing_type)
            if filing_doc:
                info.document_type = filing_doc.document_type
                logger.info(f"Setting doc type={info.document_type} mapped from filing type {filing_type}.")
        if not info.account_id:
            return resource_utils.account_required_response()
        account_id = info.account_id
        if not is_document_authorized(jwt):
            logger.error("User not authorized for this endpoint: currently requests are staff/system only.")
            return resource_utils.unauthorized_error_response(account_id)
        # Additional validation not covered by the schema.
        extra_validation_msg = validate_new_doc_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        cleaned_data, status, headers = convert_clean(info, request.get_data())
        if status != HTTPStatus.OK:
            return cleaned_data, status, headers
        response_json = resource_utils.save_add(info, g.jwt_oidc_token_info, cleaned_data)
        return jsonify(response_json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "POST create document id=" + account_id)
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def update_document_info(doc_service_id: str):
    """Update document information excluding the document (use PUT) that is associated with the document service ID."""
    try:
        req_path: str = CHANGE_REQUEST_PATH.format(doc_service_id=doc_service_id)
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        logger.info(f"Starting update document record request {req_path}, account={account_id}")
        if not is_document_authorized(jwt):
            logger.error("User not authorized for this endpoint: currently requests are staff/system only.")
            return resource_utils.unauthorized_error_response(account_id)
        document: Document = Document.find_by_doc_service_id(doc_service_id)
        if not document:
            logger.warning(f"No document found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("PATCH document information", doc_service_id)
        doc_class: str = document.document_class
        info: RequestInfo = RequestInfo(
            RequestTypes.UPDATE, req_path, document.document_type, resource_utils.get_doc_storage_type(doc_class)
        )
        info = resource_utils.update_request_info(request, info, doc_service_id, doc_class, is_staff(jwt))
        req_data = info.request_data
        req_data["existingDocument"] = document.json  # Add to validate changes
        info.request_data = req_data
        logger.info(info.request_data)
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        response_json = resource_utils.save_update(info, document, g.jwt_oidc_token_info)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH document information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["PUT", "OPTIONS"])
@jwt.requires_auth
def replace_document(doc_service_id: str):
    """Add or replace the document that is associated with the document service ID."""
    try:
        req_path: str = CHANGE_REQUEST_PATH.format(doc_service_id=doc_service_id)
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        logger.info(f"Starting add/replace document request {req_path}, account={account_id}")
        if not is_document_authorized(jwt):
            logger.error("User not authorized for this endpoint: currently requests are staff/system only.")
            return resource_utils.unauthorized_error_response(account_id)
        document: Document = Document.find_by_doc_service_id(doc_service_id)
        if not document:
            logger.warning(f"No document found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("PUT document", doc_service_id)
        doc_class: str = document.document_class
        info: RequestInfo = RequestInfo(
            RequestTypes.REPLACE, req_path, document.document_type, resource_utils.get_doc_storage_type(doc_class)
        )
        info = resource_utils.update_request_info(request, info, doc_service_id, doc_class, is_staff(jwt))
        # Additional validation not covered by the schema.
        extra_validation_msg = validate_new_doc_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        cleaned_data, status, headers = convert_clean(info, request.get_data())
        if status != HTTPStatus.OK:
            return cleaned_data, status, headers
        response_json = resource_utils.save_replace(info, document, g.jwt_oidc_token_info, cleaned_data)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PUT document")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["DELETE", "OPTIONS"])
@jwt.requires_auth
def delete_document(doc_service_id: str):
    """Permanently delete from document storage a previously uploaded associated with the document service ID."""
    try:
        req_path: str = CHANGE_REQUEST_PATH.format(doc_service_id=doc_service_id)
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        logger.info(f"Starting delete document request {req_path}, account={account_id}")
        if not is_document_authorized(jwt):
            logger.error("User not authorized for this endpoint: currently requests are staff/system only.")
            return resource_utils.unauthorized_error_response(account_id)
        document: Document = Document.find_by_doc_service_id(doc_service_id)
        if not document:
            logger.warning(f"No document found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("PUT document", doc_service_id)
        if not document.doc_storage_url:
            msg: str = f"Delete document no document in storage for document service id={doc_service_id}."
            logger.info(msg)
            return resource_utils.bad_request_response(msg)
        doc_class: str = document.document_class
        info: RequestInfo = RequestInfo(
            RequestTypes.DELETE, req_path, document.document_type, resource_utils.get_doc_storage_type(doc_class)
        )
        info = resource_utils.update_request_info(request, info, doc_service_id, doc_class, is_staff(jwt))
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        response_json = resource_utils.save_delete(info, document, g.jwt_oidc_token_info)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PUT document")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/verify/<string:consumer_doc_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def verify_document_id(consumer_doc_id: str):
    """Verify that a document record exists by getting information by consumer document ID."""
    try:
        req_path: str = VERIFY_REQUEST_PATH.format(consumer_doc_id=consumer_doc_id)
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        logger.info(f"Starting verify document consumer ID request {req_path}, account={account_id}")
        if not is_document_authorized(jwt):
            logger.error("User not authorized for this endpoint: currently requests are staff/system only.")
            return resource_utils.unauthorized_error_response(account_id)
        documents = Document.find_by_document_id(consumer_doc_id)
        if not documents:
            logger.info(f"No documents found for document consumer id={consumer_doc_id}.")
            if not checksum_valid(consumer_doc_id):
                return resource_utils.bad_request_response(f"Document ID check digit failed for {consumer_doc_id}.")
            return resource_utils.not_found_error_response("GET documents by document ID", consumer_doc_id)
        response_json = []
        for document in documents:
            doc_json = document.json
            if doc_json.get("documentURL"):
                doc_json["documentExists"] = True
                del doc_json["documentURL"]
            else:
                doc_json["documentExists"] = False
            response_json.append(doc_json)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PUT document")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/document-types", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_doc_types():
    """Get the complete set of active document types sorted by class then type."""
    try:
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        logger.info(f"Starting get document types, account={account_id}")
        if not is_document_authorized(jwt):
            logger.error("User not authorized for this endpoint: currently requests are staff/system only.")
            return resource_utils.unauthorized_error_response(account_id)
        response_json = DocumentTypeClass.find_all_json()
        if not response_json:
            return resource_utils.not_found_error_response("get document types information", account_id)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET document types info")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


def validate_new_doc_request(info: RequestInfo) -> str:
    """Validate a request that includes saving a new document."""
    extra_validation_msg = resource_utils.validate_request(info)
    extra_validation_msg += validate_content_type(info.content_type)
    return extra_validation_msg


def convert_clean(info: RequestInfo, in_data: bytes):
    """Convert non-pdf document file data to pdf, clean the pdf data."""
    if not in_data:
        return in_data, HTTPStatus.OK, None
    if info.content_type == MediaTypes.CONTENT_TYPE_PDF:
        cleaned_data = clean_pdf(in_data)
        return cleaned_data, HTTPStatus.OK, None
    filename = get_filename(info.account_id, info.content_type)
    pdf_converter: PdfConvert = PdfConvert(in_data, filename, info.content_type)
    pdf_data, status, headers = pdf_converter.convert()
    if status != HTTPStatus.OK:
        return pdf_data, status, headers
    logger.info(f"Pdf convert successful for file={filename}, data length={len(pdf_data)}, starting pdf clean.")
    cleaned_pdf = clean_pdf(pdf_data)
    return cleaned_pdf, status, headers
