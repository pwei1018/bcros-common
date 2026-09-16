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
"""API endpoints for callback requests to maintain document records."""
import json
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models import Document
from doc_api.models.type_tables import DocumentClasses, DocumentTypes, FilingTypeDocument, RequestTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.utils.logging import logger

POST_REC_REQUEST_PATH = "/callbacks/document-records"
PATCH_REC_REQUEST_PATH = "/callbacks/update/document-records"
POST_LEGACY_SCAN_REQUEST_PATH = "/callbacks/legacy-scan-files"
LEGACY_SCAN_DOC_TYPE = DocumentTypes.PRE.value
LEGACY_SCAN_DOC_CLASS = DocumentClasses.CORP.value
LEGACY_SCAN_DOC_AUTHOR = "BCMail+"
LEGACY_SCAN_FILENAME: str = "{name}-legacy-scan-{size}MB.pdf"
LEGACY_SCAN_REFERENCE_ID = "0"

bp = Blueprint("CALLBACKS1", __name__, url_prefix="/callbacks")  # pylint: disable=invalid-name


@bp.route("/document-records", methods=["POST", "OPTIONS"])
def post_document_records():
    """Save a new callback document record with no binary document data."""
    account_id = ""
    try:
        req_path: str = POST_REC_REQUEST_PATH
        info: RequestInfo = RequestInfo(RequestTypes.ADD, req_path, None, None)
        request_json = json.loads(request.get_data().decode("utf-8"))
        # CORP class requests map filing type to doc type if available.
        logger.info(f"{req_path} payload= {request_json}")
        if request_json.get("data"):
            logger.info(f"{req_path} payload wrapped: using data.")
            request_json = request_json.get("data")
        if request_json.get("documentClass", "") == DocumentClasses.CORP.value and not request_json.get("documentType"):
            doc_type: str = DocumentTypes.FILE.value  # default
            filing_type: str = request_json.get("consumerFilingType", "")
            if filing_type:
                filing_doc: FilingTypeDocument = FilingTypeDocument.find_by_filing_type(filing_type)
                if filing_doc:
                    doc_type = filing_doc.document_type
            logger.info(f"Setting request doc type={doc_type} mapped from filing type {filing_type}.")
            request_json["documentType"] = doc_type
        info = resource_utils.get_callback_request_info(request_json, info)
        account_id = info.account_id
        logger.info(f"Starting new callback create document record request {req_path}, account={info.account_id}")
        # Authenticate with request api key
        if not resource_utils.valid_api_key(request):
            return resource_utils.unauthorized_error_response("Create record callback missing api key")
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            logger.info(f"{req_path} validation errors: {extra_validation_msg}")
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        docs = Document.find_by_document_id(request_json.get("consumerDocumentId"))
        if docs:  # For this scenario the document ID should always only have 1 document.
            response_json = resource_utils.save_callback_update_rec(info, docs[0])
            return jsonify(response_json), HTTPStatus.OK
        else:
            response_json = resource_utils.save_callback_create_rec(info)
            return jsonify(response_json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(
            db_exception, account_id, f"POST create callback document record id={account_id}"
        )
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/update/document-records", methods=["POST", "OPTIONS"])
def update_document_records():
    """Update document record information for an existing document."""
    doc_service_id: str = ""
    account_id: str = ""
    try:
        req_path: str = PATCH_REC_REQUEST_PATH
        info: RequestInfo = RequestInfo(RequestTypes.UPDATE, req_path, None, None)
        request_json = json.loads(request.get_data().decode("utf-8"))
        if request_json.get("data"):
            logger.info(f"{req_path} payload wrapped: using data.")
            request_json = request_json.get("data")
        request_json = build_update_json(request_json)
        info = resource_utils.get_callback_request_info(request_json, info)
        account_id = info.account_id
        doc_service_id = request_json.get(resource_utils.PARAM_DOC_SERVICE_ID)
        logger.info(f"Starting new callback update document record request payload={request_json}")
        # Authenticate with request subscription api key
        if not resource_utils.valid_api_key(request):
            return resource_utils.unauthorized_error_response("Update record callback missing api key")
        if not doc_service_id:
            logger.error(f"{req_path} missing payload DRS ID fileKey or documentServiceId.")
            # No point retrying with this payload
            return resource_utils.bad_request_response(f"{req_path} missing DRS ID fileKey or documentServiceId.")

        document: Document = Document.find_by_doc_service_id(doc_service_id)
        if not document:
            logger.error(f"{req_path} no record found for DRS ID={doc_service_id}")
            # No point retrying with this payload
            return resource_utils.not_found_error_response("PATCH document information", doc_service_id)

        response_json = resource_utils.save_callback_update_rec(info, document)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(
            db_exception, account_id, f"POST update callback document record id={doc_service_id}"
        )
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/legacy-scan-files", methods=["POST", "OPTIONS"])
def post_legacy_scan_files():
    """
    Subscription to receive notification and process a new legacy scanned document.
    """
    account_id = "legacy_scan"
    request_json: dict = {}
    try:
        req_path: str = POST_LEGACY_SCAN_REQUEST_PATH
        info: RequestInfo = RequestInfo(RequestTypes.ADD, req_path, None, None)
        request_json = json.loads(request.get_data().decode("utf-8"))
        logger.info(f"{req_path} payload= {request_json}")
        if request_json.get("data"):
            logger.info(f"{req_path} payload wrapped: using data.")
            request_json = request_json.get("data")
        # Authenticate with request api key
        if not resource_utils.valid_api_key(request):
            return resource_utils.unauthorized_error_response("Create legacy scan callback missing api key")
        doc_json = build_legacy_scan_json(request_json)
        info = resource_utils.get_callback_request_info(doc_json, info)
        info.account_id = account_id
        resource_utils.save_callback_legacy_add(info)
        return jsonify({}), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        logger.error(f"POST create legacy scan file DatabaseException with payload {request_json}")
        return resource_utils.db_exception_response(
            db_exception, account_id, f"POST create legacy scan file document record id={account_id}"
        )
    except BusinessException as exception:
        logger.error(f"POST create legacy scan file BusinessException with payload {request_json}")
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        logger.error(f"POST create legacy scan file default Exception with payload {request_json}")
        return resource_utils.default_exception_response(default_exception)


def build_update_json(request_json: dict) -> dict:
    """Build the DRS record update json from the callback payload."""
    if not request_json.get(resource_utils.PARAM_DOC_SERVICE_ID) and request_json.get("fileKey"):
        filekey: str = str(request_json.get("fileKey"))
        if filekey.find("-") > 0:
            tokens = filekey.split("-")
            request_json[resource_utils.PARAM_DOC_SERVICE_ID] = tokens[1]
        else:
            request_json[resource_utils.PARAM_DOC_SERVICE_ID] = filekey
    if not request_json.get(resource_utils.PARAM_CONSUMER_FILEDATE) and request_json.get("filingDate"):
        request_json[resource_utils.PARAM_CONSUMER_FILEDATE] = request_json.get("filingDate")
    if not request_json.get(resource_utils.PARAM_CONSUMER_IDENTIFIER) and request_json.get("businessIdentifier"):
        request_json[resource_utils.PARAM_CONSUMER_IDENTIFIER] = request_json.get("businessIdentifier")
    if not request_json.get(resource_utils.PARAM_CONSUMER_REFERENCE_ID) and request_json.get("filingId"):
        request_json[resource_utils.PARAM_CONSUMER_REFERENCE_ID] = str(request_json.get("filingId"))
    return request_json


def build_legacy_scan_json(request_json: dict) -> dict:
    """Build a basic document record dictionary from the legacy scanned file information."""
    fname: str = str(request_json.get("name")).removesuffix(".pdf")
    size: int = int(request_json.get("size")) // 1024000
    # Filename is "{entity_type} {entity_number}" for example "BC 0204750"
    tokens = fname.split(" ")
    entity_type: str = tokens[0]
    entity_number: str = tokens[1]
    identifier: str = entity_type + entity_number if not entity_number.startswith(entity_type) else entity_number
    if size == 0:
        size = 1
    # Filing date is unknown, for these docs using the creation date is misleading.
    doc_json: dict = {
        "documentType": LEGACY_SCAN_DOC_TYPE,
        "documentClass": LEGACY_SCAN_DOC_CLASS,
        "consumerFilename": LEGACY_SCAN_FILENAME.format(name=identifier, size=size),
        "consumerIdentifier": identifier,
        "author": LEGACY_SCAN_DOC_AUTHOR,
        "consumerReferenceId": LEGACY_SCAN_REFERENCE_ID,
        "legacyScanInfo": request_json,
    }
    # Map entity type to DRS document class if not default CORP.
    if resource_utils.TO_LEGACY_SCAN_CLASS.get(entity_type):
        doc_json["documentClass"] = resource_utils.TO_LEGACY_SCAN_CLASS.get(entity_type)
    return doc_json
