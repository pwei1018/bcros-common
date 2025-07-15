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
"""API public endpoints for requests to maintain application documents uploaded by clients."""

from http import HTTPStatus

from flask import Blueprint, g, jsonify, request

from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models import ApplicationReport, Document
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes, RequestTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.resources.v1.pdf_conversions import get_filename, validate_content_type
from doc_api.services.authz import is_staff
from doc_api.services.document_storage.storage_service import GoogleStorageService
from doc_api.services.pdf_convert import MediaTypes, PdfConvert
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger
from doc_api.utils.pdf_clean import clean_pdf

POST_REQUEST_PATH = "/application-documents"
PATCH_REQUEST_PATH = "/application-documents/{doc_service_id}"
GET_REQUEST_PATH = "/application-documents/{doc_service_id}"
CONTENT_JSON = {"Content-Type": "application/json"}
CONTENT_PDF = {"Content-Type": "application/pdf"}
DOCUMENT_TYPE = DocumentTypes.APP_FILE.value
DOCUMENT_CLASS = DocumentClasses.OTHER.value
STORAGE_TYPE = resource_utils.get_doc_storage_type(DocumentClasses.OTHER.value)
PARAM_FILENAME = "name"
PARAM_FILEDATE = "datePublished"

bp = Blueprint("APP_DOCUMENTS1", __name__, url_prefix="/application-documents")  # pylint: disable=invalid-name


@bp.route("", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_documents():
    """Save a new client uploaded application document."""
    account_id = ""
    try:
        account_id: str = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        req_path: str = POST_REQUEST_PATH
        info: RequestInfo = RequestInfo(RequestTypes.ADD, req_path, DOCUMENT_TYPE, STORAGE_TYPE)
        info = resource_utils.get_request_info(request, info, is_staff(jwt))
        info.document_class = DOCUMENT_CLASS
        info.consumer_filename = request.args.get(PARAM_FILENAME, "")
        info.consumer_filedate = request.args.get(PARAM_FILEDATE, "")
        payload = request.get_data()
        if payload:
            info.has_payload = True
        logger.info(f"Starting new save application document request {req_path}, account={account_id}")
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        cleaned_data, status, headers = convert_clean(info, payload)
        if status != HTTPStatus.OK:
            return cleaned_data, status, headers
        response_json = resource_utils.save_add_app(info, g.jwt_oidc_token_info, cleaned_data)
        return jsonify(response_json), HTTPStatus.CREATED, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(
            db_exception, account_id, "POST save new app document id=" + account_id
        )
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def update_document_info(doc_service_id: str):
    """Update application document info (excluding the document) that is associated with the document service ID."""
    try:
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        req_path: str = PATCH_REQUEST_PATH.format(doc_service_id=doc_service_id)
        logger.info(f"Starting update application document record request {req_path}, account={account_id}")
        info: RequestInfo = RequestInfo(RequestTypes.UPDATE, req_path, DOCUMENT_TYPE, STORAGE_TYPE)
        info = resource_utils.update_request_info_app(request, info, doc_service_id, DOCUMENT_CLASS, is_staff(jwt))
        logger.debug(f"update_document_info payload={info.request_data}")
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        document: Document = Document.find_by_doc_service_id(doc_service_id)
        if not document:
            logger.warning(f"No app document found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("PATCH application document information", doc_service_id)
        response_json = resource_utils.save_update_app(info, document, g.jwt_oidc_token_info)
        return jsonify(response_json), HTTPStatus.OK, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH application document information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_individual_document(doc_service_id: str):
    """Get document information including a url that is associated with the document service ID."""
    try:
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        req_path: str = GET_REQUEST_PATH.format(doc_service_id=doc_service_id)
        logger.info(f"Starting get_individual_document record request {req_path}, account={account_id}")
        request_json: dict = {"isGet": True}
        extra_validation_msg = resource_utils.validate_report_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        doc: Document = Document.find_by_doc_service_id(doc_service_id)
        if not doc:
            logger.info(f"No document record found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("GET application document information", doc_service_id)
        if resource_utils.is_pdf(request):
            logger.info(f"Request {req_path} for PDF data.")
            report_data = get_document_data(doc)
            return report_data, HTTPStatus.OK, CONTENT_PDF
        response_json = get_document_link(doc)
        return jsonify(response_json), HTTPStatus.OK, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET app document information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


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


def save_to_doc_storage(app_report: ApplicationReport, raw_data) -> str:
    """Save request binary data to document storage. Return a download link"""
    storage_type: str = resource_utils.TO_PRODUCT_STORAGE_TYPE.get(app_report.product_code)
    if not storage_type:
        storage_type = resource_utils.STORAGE_TYPE_DEFAULT.value
    content_type = model_utils.CONTENT_TYPE_PDF
    logger.info(f"Save to storage type={storage_type}, content type={content_type}")
    storage_name: str = model_utils.get_report_storage_name(app_report)
    doc_link = GoogleStorageService.save_document_link(storage_name, raw_data, storage_type, 2, content_type)
    logger.info(f"Save doc to storage {storage_name} successful: link= {doc_link}")
    app_report.doc_storage_url = storage_name
    return doc_link


def get_document_link(doc: Document) -> dict:
    """Generate the document download URL link for the app document."""
    doc_json: dict = doc.app_json
    storage_name: str = doc.doc_storage_url
    if storage_name:
        logger.info(f"getting link for type={STORAGE_TYPE} name={storage_name}...")
        doc_link = GoogleStorageService.get_document_link(storage_name, STORAGE_TYPE, 2)
        doc_json["url"] = doc_link
    return doc_json


def get_document_data(doc: Document):
    """Retrieve the document itselfs as binary data."""
    storage_name: str = doc.doc_storage_url
    doc_data = None
    if storage_name:
        logger.info(f"getting report data for type={STORAGE_TYPE} name={storage_name}...")
        doc_data = GoogleStorageService.get_document(storage_name, STORAGE_TYPE)
        logger.info(f"Retrieved {storage_name} document data length={len(doc_data)}.")
    return doc_data
