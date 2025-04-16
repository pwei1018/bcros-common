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
"""Resource helper utilities for processing requests."""
from http import HTTPStatus

from flask import current_app, jsonify, request

from doc_api.exceptions import ResourceErrorCodes
from doc_api.models import Document, DocumentRequest, DocumentScanning, User, db, search_utils
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypes, RequestTypes
from doc_api.services.abstract_storage_service import DocumentTypes as StorageDocTypes
from doc_api.services.document_storage.storage_service import GoogleStorageService
from doc_api.utils import request_validator
from doc_api.utils.logging import logger

from .request_info import RequestInfo

# Resource error messages
# Model business error messages in models.utils.py
ACCOUNT_REQUIRED = "{code}: Account-Id header required."
UNAUTHORIZED = "{code}: authorization failure submitting a request for {account_id}."
UNAUTHORIZED_HELPDESK = "{code}: BCOL helpdesk users are not authorized to create {reg_type} registrations."
ACCOUNT_ACCESS = (
    "{code}: the account ID {account_id} cannot access statement information for " + "mhr number {mhr_num}."
)
STAFF_SEARCH_BCOL_FAS = "{code}: provide either a BCOL Account Number or a Routing Slip Number but not both."
SBC_SEARCH_NO_PAYMENT = "{code}: provide either a BCOL Account Number or a Routing Slip Number."
DATABASE = "{code}: {context} database error for {account_id}."
NOT_FOUND = "{code}: no {item} found for {key}."
PATH_PARAM = "{code}: a {param_name} path parameter is required."
REPORT = ResourceErrorCodes.REPORT_ERR.value + ": error generating report. Detail: {detail}"
DEFAULT = "{code}: error processing request."
DUPLICATE_REGISTRATION_ERROR = "MH Registration {0} is already available to the account."
VAL_ERROR = "Document request data validation errors."  # Default validation error prefix
SAVE_ERROR_MESSAGE = "Account {0} create {1} statement db save failed: {2}"

# Known request parameters
PARAM_ACCOUNT_ID = "Account-Id"
PARAM_ACCEPT = "Accept"
PARAM_CONTENT_TYPE = "Content-Type"
PARAM_QUERY_START_DATE = "queryStartDate"
PARAM_QUERY_END_DATE = "queryEndDate"
PARAM_FROM_UI = "fromUI"
PARAM_DOC_SERVICE_ID = "documentServiceId"
PARAM_CONSUMER_DOC_ID = "consumerDocumentId"
PARAM_CONSUMER_FILENAME = "consumerFilename"
PARAM_CONSUMER_FILEDATE = "consumerFilingDate"
PARAM_CONSUMER_IDENTIFIER = "consumerIdentifier"
PARAM_CONSUMER_REFERENCE_ID = "consumerReferenceId"
PARAM_DESCRIPTION = "description"
PARAM_DOCUMENT_TYPE = "documentType"
PARAM_DOCUMENT_CLASS = "documentClass"
PARAM_PAGE_NUMBER = "pageNumber"

TO_STORAGE_TYPE = {
    DocumentClasses.MHR: StorageDocTypes.MHR,
    DocumentClasses.NR: StorageDocTypes.NR,
    DocumentClasses.PPR: StorageDocTypes.PPR,
    DocumentClasses.CORP: StorageDocTypes.BUSINESS,
    DocumentClasses.COOP: StorageDocTypes.BUSINESS,
    DocumentClasses.FIRM: StorageDocTypes.BUSINESS,
    DocumentClasses.LP_LLP: StorageDocTypes.BUSINESS,
    DocumentClasses.OTHER: StorageDocTypes.BUSINESS,
    DocumentClasses.SOCIETY: StorageDocTypes.BUSINESS,
    DocumentClasses.XP: StorageDocTypes.BUSINESS,
}
STORAGE_TYPE_DEFAULT = StorageDocTypes.BUSINESS
REMOVE_PREFIX = "DEL-"
CLASS_ENTITY_ID_PREFIX = {DocumentClasses.MHR.value: "MH"}


def serialize(errors):
    """Serialize errors."""
    error_message = []
    if errors:
        for error in errors:
            error_message.append("Schema validation: " + error.message + ".")
    return error_message


def get_account_id(req):
    """Get account ID from request headers."""
    return req.headers.get(PARAM_ACCOUNT_ID)


def is_pdf(req):
    """Check if request headers Accept is application/pdf."""
    accept = req.headers.get("Accept")
    return accept and accept.upper() == "APPLICATION/PDF"


def get_apikey(req):
    """Get gateway api key from request headers or parameter."""
    key = req.headers.get("x-apikey")
    if not key:
        key = request.args.get("x-apikey")
    return key


def valid_api_key(req) -> bool:
    """Verify the callback request api key is valid."""
    key = get_apikey(req)
    if not key:
        return False
    apikey = current_app.config.get("SUBSCRIPTION_API_KEY")
    if not apikey:
        return False
    return key == apikey


def account_required_response():
    """Build account required error response."""
    message = ACCOUNT_REQUIRED.format(code=ResourceErrorCodes.ACCOUNT_REQUIRED_ERR.value)
    return jsonify({"message": message}), HTTPStatus.BAD_REQUEST


def error_response(status_code, message):
    """Build generic error response."""
    return jsonify({"message": message}), status_code


def bad_request_response(message):
    """Build generic bad request response."""
    return jsonify({"message": message}), HTTPStatus.BAD_REQUEST


def validation_error_response(errors, cause, additional_msg: str = None):
    """Build a schema validation error response."""
    message = ResourceErrorCodes.VALIDATION_ERR + ": " + cause
    details = serialize(errors)
    if additional_msg:
        details.append("Additional validation: " + additional_msg)
    return jsonify({"message": message, "detail": details}), HTTPStatus.BAD_REQUEST


def extra_validation_error_response(additional_msg: str = None):
    """Build a schema validation error response."""
    message = ResourceErrorCodes.VALIDATION_ERR.value + ": " + VAL_ERROR
    details = "Additional validation: "
    if additional_msg:
        details += additional_msg
    return jsonify({"message": message, "detail": details}), HTTPStatus.BAD_REQUEST


def db_exception_response(exception, account_id: str, context: str):
    """Build a database error response."""
    message = DATABASE.format(code=ResourceErrorCodes.DATABASE_ERR.value, context=context, account_id=account_id)
    logger.error(message)
    return jsonify({"message": message, "detail": str(exception)}), HTTPStatus.INTERNAL_SERVER_ERROR


def report_exception_response(exception, detail: str):
    """Build a report request error response."""
    message = REPORT.format(detail=detail)
    logger.error(message)
    return jsonify({"message": message, "detail": str(exception)}), HTTPStatus.INTERNAL_SERVER_ERROR


def business_exception_response(exception):
    """Build business exception error response."""
    logger.error(str(exception))
    return jsonify({"message": exception.error}), exception.status_code


def default_exception_response(exception):
    """Build default 500 exception error response."""
    logger.error(str(exception))
    message = DEFAULT.format(code=ResourceErrorCodes.DEFAULT_ERR.value)
    return jsonify({"message": message, "detail": str(exception)}), HTTPStatus.INTERNAL_SERVER_ERROR


def service_exception_response(message):
    """Build 500 exception error response."""
    return jsonify({"message": message}), HTTPStatus.INTERNAL_SERVER_ERROR


def not_found_error_response(item, key):
    """Build a not found error response."""
    message = NOT_FOUND.format(code=ResourceErrorCodes.NOT_FOUND_ERR.value, item=item, key=key)
    logger.info(str(HTTPStatus.NOT_FOUND.value) + ": " + message)
    return jsonify({"message": message}), HTTPStatus.NOT_FOUND


def duplicate_error_response(message):
    """Build a duplicate request error response."""
    err_msg = ResourceErrorCodes.DUPLICATE_ERR + ": " + message
    logger.info(str(HTTPStatus.CONFLICT.value) + ": " + message)
    return jsonify({"message": err_msg}), HTTPStatus.CONFLICT


def unauthorized_error_response(account_id):
    """Build an unauthorized error response."""
    message = UNAUTHORIZED.format(code=ResourceErrorCodes.UNAUTHORIZED_ERR.value, account_id=account_id)
    logger.info(str(HTTPStatus.UNAUTHORIZED.value) + ": " + message)
    return jsonify({"message": message}), HTTPStatus.UNAUTHORIZED


def path_param_error_response(param_name):
    """Build a bad request param missing error response."""
    message = PATH_PARAM.format(code=ResourceErrorCodes.PATH_PARAM_ERR.value, param_name=param_name)
    logger.info(str(HTTPStatus.BAD_REQUEST.value) + ": " + message)
    return jsonify({"message": message}), HTTPStatus.BAD_REQUEST


def unprocessable_error_response(description):
    """Build an unprocessable entity error response."""
    message = f"The {description} request could not be processed (no change/results)."
    logger.info(str(HTTPStatus.UNPROCESSABLE_ENTITY.value) + ": " + message)
    return jsonify({"message": message}), HTTPStatus.UNPROCESSABLE_ENTITY


def validate_request(info: RequestInfo) -> str:
    """Perform non-schema extra validation on a new requests."""
    return request_validator.validate_request(info)


def validate_report_request(request_json: dict, is_create: bool) -> str:
    """Perform non-schema extra validation on a new requests."""
    return request_validator.validate_report_request(request_json, is_create)


def validate_scanning_request(request_json: dict, is_new: bool = True) -> str:
    """Perform non-schema extra validation on a new document scanning requests."""
    return request_validator.validate_scanning(request_json, is_new)


def get_request_info(req: request, info: RequestInfo, staff: bool = False) -> RequestInfo:
    """Extract header and query parameters from the request."""
    info.from_ui = req.args.get(PARAM_FROM_UI, False)
    info.account_id = req.headers.get(PARAM_ACCOUNT_ID)
    info.accept = req.headers.get(PARAM_ACCEPT)
    info.content_type = req.headers.get(PARAM_CONTENT_TYPE)
    info.document_service_id = req.args.get(PARAM_DOC_SERVICE_ID)
    info.consumer_doc_id = req.args.get(PARAM_CONSUMER_DOC_ID)
    info.consumer_filename = req.args.get(PARAM_CONSUMER_FILENAME)
    info.consumer_filedate = req.args.get(PARAM_CONSUMER_FILEDATE)
    info.consumer_identifier = req.args.get(PARAM_CONSUMER_IDENTIFIER)
    info.consumer_reference_id = req.args.get(PARAM_CONSUMER_REFERENCE_ID)
    info.query_start_date = req.args.get(PARAM_QUERY_START_DATE)
    info.query_end_date = req.args.get(PARAM_QUERY_END_DATE)
    info.description = req.args.get(PARAM_DESCRIPTION)
    info.staff = staff
    if info.content_type:
        info.content_type = info.content_type.lower()
    if not info.document_type and req.args.get(PARAM_DOCUMENT_TYPE):
        info.document_type = req.args.get(PARAM_DOCUMENT_TYPE)
    if req.args.get(PARAM_PAGE_NUMBER):
        info.page_number = req.args.get(PARAM_PAGE_NUMBER)
    if req.args.get(PARAM_DOCUMENT_CLASS):
        info.document_class = req.args.get(PARAM_DOCUMENT_CLASS)
    return info


def update_request_info(
    req: request, info: RequestInfo, doc_service_id: str, doc_class: str, staff: bool = False
) -> RequestInfo:
    """Extract header and from the request and update parameters from the request payload."""
    info.from_ui = req.args.get(PARAM_FROM_UI, False)
    info.account_id = req.headers.get(PARAM_ACCOUNT_ID)
    info.document_service_id = doc_service_id
    info.document_class = doc_class
    request_json = req.get_json(silent=True)
    if request_json:
        info.consumer_doc_id = request_json.get(PARAM_CONSUMER_DOC_ID)
        info.consumer_filename = request_json.get(PARAM_CONSUMER_FILENAME)
        info.consumer_filedate = request_json.get(PARAM_CONSUMER_FILEDATE)
        if not info.consumer_filedate and request_json.get("consumerFilingDateTime"):
            info.consumer_filedate = request_json.get("consumerFilingDateTime")
        info.consumer_identifier = request_json.get(PARAM_CONSUMER_IDENTIFIER)
        info.consumer_reference_id = request_json.get(PARAM_CONSUMER_REFERENCE_ID)
        info.description = request_json.get(PARAM_DESCRIPTION)
        info.request_data = request_json
    info.staff = staff
    info.content_type = req.headers.get(PARAM_CONTENT_TYPE)
    if info.content_type:
        info.content_type = info.content_type.lower()
    if info.request_type == RequestTypes.REPLACE and req.args.get(PARAM_CONSUMER_FILENAME):
        info.consumer_filename = req.args.get(PARAM_CONSUMER_FILENAME)
    if info.request_type == RequestTypes.REPLACE and request.get_data():
        info.has_payload = True
    return info


def remove_quotes(text: str) -> str:
    """Remove single and double quotation marks from request parameters."""
    if text:
        text = text.replace("'", "''")
        text = text.replace('"', '""')
    return text


def save_to_doc_storage(document: Document, info: RequestInfo, raw_data) -> str:
    """Save request binary data to document storage. Return a download link"""
    storage_type: str = info.document_storage_type
    content_type = info.content_type
    logger.info(f"Save to storage type={storage_type}, content type={content_type}")
    storage_name: str = model_utils.get_doc_storage_name(document, content_type)
    doc_link = GoogleStorageService.save_document_link(storage_name, raw_data, storage_type, 2, content_type)
    logger.info(f"Save doc to storage {storage_name} successful: link= {doc_link}")
    document.doc_storage_url = storage_name
    return doc_link


def delete_from_doc_storage(document: Document, info: RequestInfo) -> str:
    """Delete document record document from storage."""
    storage_type: str = info.document_storage_type
    storage_name: str = document.doc_storage_url
    logger.info(f"Delete from storage type={storage_type}, name={storage_name}")
    GoogleStorageService.delete_document(storage_name, storage_type)
    logger.info(f"Delete doc from storage successful for {storage_name}")


def build_doc_request(info: RequestInfo, user: User, doc_id: int) -> DocumentRequest:
    """Build a document request for audit tracking from ther request properties."""
    doc_request: DocumentRequest = DocumentRequest(
        request_ts=model_utils.now_ts(),
        account_id=info.account_id,
        username=user.username if user else "",
        request_type=info.request_type,
        status=HTTPStatus.OK,
        document_id=doc_id,
    )
    doc_request.request_data = info.json
    return doc_request


def save_add(info: RequestInfo, token, raw_data) -> dict:
    """Save request binary data to document storage. Return a download link"""
    request_json = info.json
    logger.info(f"save_add starting raw data size={len(raw_data)}, getting user from token...")
    user: User = User.get_or_create_user_by_jwt(token, info.account_id)
    logger.info("save_add building Document model...")
    document: Document = Document.create_from_json(request_json, info.document_type)
    doc_link: str = None
    if raw_data:
        logger.info("save_add saving file data to doc storage...")
        doc_link = save_to_doc_storage(document, info, raw_data)
    else:
        logger.info("save_add no payload file to save to doc storage...")
        info.request_type = RequestTypes.PENDING.value
    logger.info("save_add building doc request model and saving...")
    doc_request: DocumentRequest = build_doc_request(info, user, document.id)
    db.session.add(document)
    db.session.add(doc_request)
    db.session.commit()
    doc_json = document.json
    if doc_link:
        doc_json["documentURL"] = doc_link
    logger.info("save_add completed...")
    return doc_json


def save_remove(info: RequestInfo, document: Document, token) -> dict:
    """Mark a document record as removed from subsequent searches."""
    logger.info(f"save_remove starting for doc service id={document.document_service_id}, getting user from token...")
    user: User = User.get_or_create_user_by_jwt(token, info.account_id)
    info.request_type = RequestTypes.DELETE.value
    doc_class: str = DocumentClasses.DELETED.value
    doc_type: str = DocumentTypes.DELETED.value
    cons_doc_id: str = REMOVE_PREFIX + document.consumer_document_id
    doc_scan: DocumentScanning = None
    if len(document.consumer_document_id) < 10:
        doc_scan = DocumentScanning.find_by_document_id(document.consumer_document_id, document.document_class)
    if doc_scan:
        logger.info("save_remove found existing scanning record to update")
        doc_scan.consumer_document_id = cons_doc_id
        doc_scan.document_class = doc_class
    document.document_class = doc_class
    document.document_type = doc_type
    document.consumer_document_id = cons_doc_id
    document.document_service_id = REMOVE_PREFIX + document.document_service_id
    if document.consumer_identifier:
        document.consumer_identifier = REMOVE_PREFIX + document.consumer_identifier
    logger.info("save_remove saving updated document model and document_request...")
    doc_request: DocumentRequest = build_doc_request(info, user, document.id)
    db.session.add(document)
    if doc_scan:
        db.session.add(doc_scan)
    db.session.add(doc_request)
    db.session.commit()
    doc_json = document.json
    logger.info(f"save_remove completed document updated to {doc_json}")
    return {}


def save_update(info: RequestInfo, document: Document, token) -> dict:
    """Save updated document information including optional document scanning. Return the updated information."""
    logger.info("save_update starting, getting user from token...")
    user: User = User.get_or_create_user_by_jwt(token, info.account_id)
    if info.request_data and info.request_data.get("removed"):
        return save_remove(info, document, token)
    doc_scan: DocumentScanning = None
    update_doc_id: str = info.request_data.get("consumerDocumentId") if info.request_data else None
    update_doc_class: str = document.document_class
    # Conditionally update scanning information
    if info.request_data and request_validator.is_scanning_modified(info):
        scan_json = info.request_data.get("scanningInformation")
        doc_scan = DocumentScanning.find_by_document_id(document.consumer_document_id, document.document_class)
        if not doc_scan and update_doc_id and update_doc_class:
            doc_scan = DocumentScanning.find_by_document_id(update_doc_id, update_doc_class)
        if doc_scan:
            logger.info("save_update found existing scanning record to update")
            doc_scan.update(scan_json, update_doc_id, update_doc_class)
        # Only allow scanning info updates from the UI: not new scanning info records.
        # else:
        #    logger.info("save_update no existing scanning record to update: creating one.")
        #    if not update_doc_id:
        #        update_doc_id = document.consumer_document_id
        #    if not update_doc_class:
        #        update_doc_class = document.document_class
        #    doc_scan = DocumentScanning.create_from_json(scan_json, update_doc_id, update_doc_class)
    doc_request: DocumentRequest = build_doc_request(info, user, document.id)
    if request_validator.is_document_modified(info):
        document.update(info.request_data)
        db.session.add(document)
        logger.info("save_update saving updated document model...")
    if doc_scan:
        db.session.add(doc_scan)
        logger.info("save_update saving updated document_scanning model...")
    db.session.add(doc_request)
    logger.info("save_update saving document_request...")
    db.session.commit()
    doc_json = document.json
    if doc_json.get("documentURL"):
        del doc_json["documentURL"]
    logger.info("save_update completed...")
    return doc_json


def save_replace(info: RequestInfo, document: Document, token, raw_data) -> dict:
    """Save request binary data to document storage, adding or replacing the existing document. Return a link"""
    logger.info(f"save_replace starting raw data size={len(raw_data)}, getting user from token...")
    service_id: str = document.document_service_id
    user: User = User.get_or_create_user_by_jwt(token, info.account_id)
    if info.consumer_filename:
        document.consumer_filename = info.consumer_filename
    if document.doc_storage_url:
        logger.info(f"save_replace ID {service_id} replacing existing doc storage file {document.doc_storage_url}...")
    else:
        logger.info(f"save_replace adding new file for doc service id {service_id}...")
    doc_link = save_to_doc_storage(document, info, raw_data)
    logger.info("save_replace building doc request model and saving...")
    doc_request: DocumentRequest = build_doc_request(info, user, document.id)
    db.session.add(document)
    db.session.add(doc_request)
    db.session.commit()
    doc_json = document.json
    if doc_link:
        doc_json["documentURL"] = doc_link
    logger.info("save_replace completed...")
    return doc_json


def save_delete(info: RequestInfo, document: Document, token) -> dict:
    """Save request binary data to document storage, adding or replacing the existing document. Return a link"""
    logger.info("save_delete starting, getting user from token...")
    service_id: str = document.document_service_id
    user: User = User.get_or_create_user_by_jwt(token, info.account_id)
    logger.info(f"save_delete service ID {service_id} deleting existing doc storage file {document.doc_storage_url}...")
    delete_from_doc_storage(document, info)
    document.doc_storage_url = None
    logger.info("save_delete building doc request model and saving...")
    doc_request: DocumentRequest = build_doc_request(info, user, document.id)
    db.session.add(document)
    db.session.add(doc_request)
    db.session.commit()
    doc_json = document.json
    logger.info("save_delete completed...")
    return doc_json


def save_callback_create_rec(info: RequestInfo) -> dict:
    """Save request document record information."""
    request_json = info.json
    logger.info("save_callback_create_rec starting, building Document model...")
    document: Document = Document.create_from_json(request_json, info.document_type)
    info.request_type = RequestTypes.PENDING.value
    logger.info("save_callback_create_rec building doc request model...")
    doc_request: DocumentRequest = build_doc_request(info, None, document.id)
    db.session.add(document)
    db.session.add(doc_request)
    db.session.commit()
    doc_json = document.json
    logger.info("save_callback_create_rec completed...")
    return doc_json


def save_callback_update_rec(info: RequestInfo, document: Document) -> dict:
    """Save updated document record information."""
    logger.info("save_callback_update_rec starting, updating Document model...")
    document.update(info.request_data)
    info.request_type = RequestTypes.UPDATE.value
    logger.info("save_callback_update_rec building doc request model...")
    doc_request: DocumentRequest = build_doc_request(info, None, document.id)
    db.session.add(document)
    db.session.add(doc_request)
    db.session.commit()
    doc_json = document.json
    logger.info("save_callback_update_rec completed...")
    return doc_json


def get_doc_links(info: RequestInfo, results: list) -> list:
    """Generate document links for the documents in the list"""
    if not results:
        return results
    for result in results:
        storage_name = result.get("documentURL")
        storage_type = info.document_storage_type
        if storage_name:
            logger.info(f"getting link for type={storage_type} name={storage_name}...")
            doc_link = GoogleStorageService.get_document_link(storage_name, storage_type, 2)
            result["documentURL"] = doc_link
    return results


def get_docs(info: RequestInfo) -> list:
    """Get document information by query parameters. If not querying by date range get a doc link."""
    results = []
    query_results = []
    if info.document_service_id:
        logger.info(f"get_docs class {info.document_class} query by service id {info.document_service_id}")
        result = Document.find_by_doc_service_id(info.document_service_id)
        if result and result.doc_type and result.document_class == info.document_class:
            results.append(result.json)
    elif info.consumer_doc_id:
        logger.info(f"get_docs class {info.document_class} query by document id {info.consumer_doc_id}")
        query_results = Document.find_by_document_id(info.consumer_doc_id)
        if query_results:
            for result in query_results:
                # logger.info(f'Checking doc class {result.document_class} with {info.document_class}')
                if result.doc_type and result.document_class == info.document_class:
                    results.append(result.json)
    elif info.consumer_identifier and not (info.query_start_date or info.query_end_date):
        logger.info(f"get_docs class {info.document_class} query by consumer id {info.consumer_identifier}")
        if info.document_type:
            logger.info(f"Filtering on doc_type={info.document_type}")
        query_results = Document.find_by_consumer_id(info.consumer_identifier, info.document_type)
        if query_results:
            for result in query_results:
                if result.doc_type and result.document_class == info.document_class:
                    results.append(result.json)
    elif info.query_start_date and info.query_end_date:
        return search_utils.get_docs_by_date_range(
            info.document_class,
            info.query_start_date,
            info.query_end_date,
            info.document_type,
            info.consumer_identifier,
        )
    logger.info("get docs completed...")
    return get_doc_links(info, results)


def get_doc_storage_type(doc_class: str) -> str:
    """Get the document storage type that maps to the document class."""
    if doc_class and TO_STORAGE_TYPE.get(doc_class):
        return TO_STORAGE_TYPE.get(doc_class)
    return STORAGE_TYPE_DEFAULT


def get_callback_request_info(request_json: dict, info: RequestInfo) -> RequestInfo:
    """Extract Build the request information from the request payload."""
    if request_json:
        info.account_id = request_json.get("accountId")
        if info.account_id:
            info.account_id += "_SYSTEM"
        else:
            info.account_id = "SYSTEM"
        info.document_type = request_json.get(PARAM_DOCUMENT_TYPE)
        info.document_class = request_json.get(PARAM_DOCUMENT_CLASS)
        info.consumer_doc_id = request_json.get(PARAM_CONSUMER_DOC_ID)
        info.consumer_identifier = request_json.get(PARAM_CONSUMER_IDENTIFIER)
        info.consumer_filedate = request_json.get(PARAM_CONSUMER_FILEDATE)
        info.consumer_reference_id = request_json.get(PARAM_CONSUMER_REFERENCE_ID)
        info.has_payload = False
        info.staff = False
        info.document_storage_type = get_doc_storage_type(info.document_class)
        if info.consumer_identifier:
            info.consumer_identifier = info.consumer_identifier.strip().upper()
        if info.document_class and info.consumer_identifier and CLASS_ENTITY_ID_PREFIX.get(info.document_class):
            id_prefix: str = CLASS_ENTITY_ID_PREFIX.get(info.document_class)
            if not info.consumer_identifier.startswith(id_prefix):
                info.consumer_identifier = id_prefix + info.consumer_identifier
                request_json["consumerIdentifier"] = info.consumer_identifier
        info.request_data = request_json
        info.request_data["async"] = True
    return info
