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
"""This module holds unit note registration validation for rules not covered by the schema.

Validation includes verifying the data combination for various registration document types and timestamps.
"""
from datetime import datetime

from doc_api.models import DocumentScanning
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import DocumentClasses, DocumentTypeClass, DocumentTypes, RequestTypes
from doc_api.resources.request_info import RequestInfo
from doc_api.utils.logging import logger

VALIDATOR_ERROR = "Error performing new request extra validation. "
INVALID_DOC_TYPE = "Request invalid: unrecognized document type {doc_type}. "
MISSING_DOC_TYPE = "Request invalid: required request document type is missing. "
INVALID_DOC_CLASS = "Request invalid: unrecognized document class {doc_class}. "
MISSING_CONTENT_TYPE = "Request invalid: required request header Content-Type is missing. "
INVALID_CONTENT_TYPE = "Request invalid: unsupported request header Content-type {content_type}. "
MISSING_QUERY_PARAMS = "Request invalid: get documents is missing one of the required parameters. "
MISSING_DOC_CLASS = "Request invalid: required request document class is missing. "
MISSING_DATE_PARAM = "Request invalid: get documents require both query start date and query end date. "
INVALID_DOC_CLASS_TYPE = "Request invalid: document type {doc_type} does not belong to document class {doc_class}. "
INVALID_SCAN_DATE = "Request invalid: scan date format invalid {param_date}. "
INVALID_FILING_DATE = "Request invalid: filing date format invalid {param_date}. "
INVALID_START_DATE = "Request invalid: search start date format invalid {param_date}. "
INVALID_END_DATE = "Request invalid: search end date format invalid {param_date}. "
INVALID_START_END_DATE = "Request invalid: search end date {end_date} before start date {start_date}. "
MISSING_PATCH_PARAMS = "Request invalid: update document information nothing to change. "
MISSING_PAYLOAD = "Request invalid: add/replace document missing required payload. "
MISSING_SCAN_DATE = "Request invalid: missing required scanDateTime. "
MISSING_SCAN_PAYLOAD = "Request invalid: document scanning missing required payload or missing payload properties. "
MISSING_SCAN_DOCUMENT_ID = "Request invalid: missing required consumerDocumentId. "
INVALID_SCAN_EXISTS = "Request invalid: record already exists for class {doc_class} and ID {cons_doc_id}. "
INVALID_PAGE_COUNT = "The scan document page count must be greater than 0. "


def validate_request(info: RequestInfo) -> str:
    """Perform all extra data validation checks on a new request not covered by schema validation."""
    logger.info(f"Validating {info.request_type} account id={info.account_id} staff={info.staff}")
    error_msg: str = ""
    if not info.request_type or info.request_type not in (RequestTypes.GET, RequestTypes.UPDATE):
        if not info.document_type:
            error_msg += MISSING_DOC_TYPE
        elif info.document_type and info.document_type not in DocumentTypes:
            error_msg += INVALID_DOC_TYPE.format(doc_type=info.document_type)
    if info.document_class and info.document_class not in DocumentClasses:
        error_msg += INVALID_DOC_CLASS.format(doc_class=info.document_class)
    elif info.document_class and info.document_type:  # Verify document class - document type pair.
        error_msg += validate_class_type(info)
    if not info.document_class:
        error_msg += get_doc_class(info)
    if info.request_type and info.request_type == RequestTypes.ADD:
        if info.request_data and info.request_data.get("async"):
            return error_msg
        return validate_add(info, error_msg)
    if info.request_type and info.request_type == RequestTypes.GET:
        return validate_get(info, error_msg)
    if info.request_type and info.request_type == RequestTypes.UPDATE:
        return validate_patch(info, error_msg)
    if info.request_type and info.request_type == RequestTypes.REPLACE:
        return validate_put(info, error_msg)
    return error_msg


def validate_scanning(request_json: dict, is_new: bool = True) -> str:
    """Perform all extra data validation checks on a new doc scanning request not covered by schema validation."""
    logger.info(f"Validating new document scanning request new={is_new}...")
    error_msg: str = ""
    if not request_json:

        return MISSING_SCAN_PAYLOAD
    elif (
        not request_json.get("accessionNumber")
        and not request_json.get("batchId")
        and not request_json.get("author")
        and "pageCount" not in request_json
    ):
        if "scanDateTime" not in request_json and "scanDate" not in request_json:
            return MISSING_SCAN_PAYLOAD
    try:
        doc_class = request_json.get("documentClass")
        cons_doc_id = request_json.get("consumerDocumentId")
        if not doc_class:
            error_msg += MISSING_DOC_CLASS
        elif doc_class not in DocumentClasses:
            error_msg += INVALID_DOC_CLASS.format(doc_class=doc_class)
        if not cons_doc_id:
            error_msg += MISSING_SCAN_DOCUMENT_ID
        if "pageCount" in request_json and int(request_json.get("pageCount")) < 1:
            error_msg += INVALID_PAGE_COUNT
        if is_new:
            scan_doc: DocumentScanning = DocumentScanning.find_by_document_id(cons_doc_id, doc_class)
            if scan_doc:
                error_msg += INVALID_SCAN_EXISTS.format(doc_class=doc_class, cons_doc_id=cons_doc_id)
        error_msg += validate_scandate(request_json)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_scanning exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_add(info: RequestInfo, error_msg: str) -> str:
    """Validate the add request."""
    try:
        if not info.content_type:
            error_msg += MISSING_CONTENT_TYPE
        elif not model_utils.TO_FILE_TYPE.get(info.content_type):
            error_msg += INVALID_CONTENT_TYPE.format(content_type=info.content_type)
        error_msg += validate_filingdate(info)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_add exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_get(info: RequestInfo, error_msg: str) -> str:
    """Validate the get request."""
    try:
        if not info.request_path or not info.request_path.endswith("*"):
            if not info.document_class:
                error_msg += MISSING_DOC_CLASS
            if (
                not info.consumer_doc_id
                and not info.consumer_identifier
                and not info.document_service_id
                and not info.query_start_date
                and not info.query_end_date
            ):
                error_msg += MISSING_QUERY_PARAMS
        error_msg += validate_search_dates(info)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_get exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_patch(info: RequestInfo, error_msg: str) -> str:
    """Validate the patch request."""
    try:
        if info.request_data and info.request_data.get("removed"):
            return error_msg
        if (
            not info.consumer_filedate
            and not info.consumer_identifier
            and not info.consumer_filename
            and not info.consumer_doc_id
            and not info.description
        ):
            error_msg += MISSING_PATCH_PARAMS
        error_msg += validate_filingdate(info)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_patch exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_put(info: RequestInfo, error_msg: str) -> str:
    """Validate the put request."""
    try:
        if not info.content_type:
            error_msg += MISSING_CONTENT_TYPE
        elif not model_utils.TO_FILE_TYPE.get(info.content_type):
            error_msg += INVALID_CONTENT_TYPE.format(content_type=info.content_type)
        if not info.has_payload:
            error_msg += MISSING_PAYLOAD
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_put exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_class_type(info: RequestInfo) -> str:
    """Validate the document class matches the document type."""
    error_msg: str = ""
    if not info.document_class or not info.document_type:
        return error_msg
    doc_types = DocumentTypeClass.find_by_doc_type(info.document_type)
    if doc_types:
        valid_class: bool = False
        for type_class in doc_types:
            if type_class.document_class == info.document_class:
                valid_class = True
                break
        if not valid_class:
            error_msg = INVALID_DOC_CLASS_TYPE.format(doc_type=info.document_type, doc_class=info.document_class)
    return error_msg


def get_doc_class(info: RequestInfo) -> str:
    """Get the document class for the document type if the mapping is 1 to 1."""
    error_msg: str = ""
    if info.document_class or not info.document_type:
        return error_msg
    # doc class is optional for GET (Searches)
    optional: bool = (
        info.request_type
        and info.request_type == RequestTypes.GET
        and info.request_path
        and info.request_path.endswith("*")
    )
    try:
        doc_classes = DocumentTypeClass.find_by_doc_type(info.document_type)
        if doc_classes and len(doc_classes) == 1:
            info.document_class = doc_classes[0].document_class
        elif not optional:
            error_msg += MISSING_DOC_CLASS
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_class_type exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_scandate(request_json: dict) -> str:
    """Check that the optional scan date is in a valid date format."""
    error_msg: str = ""
    scan_date = request_json.get("scanDateTime")
    if not scan_date and request_json.get("scanDate"):
        scan_date = request_json.get("scanDate")
    else:
        return error_msg
    try:
        test_date = model_utils.ts_from_iso_date_noon(scan_date)
        if test_date:
            return error_msg
        error_msg = INVALID_SCAN_DATE.format(param_date=scan_date)
    except Exception:  # noqa: B902; eat all errors
        error_msg = INVALID_SCAN_DATE.format(param_date=scan_date)
    return error_msg


def validate_filingdate(info: RequestInfo) -> str:
    """Check that the optional filing date is in a valid date format."""
    error_msg: str = ""
    if not info.consumer_filedate:
        return error_msg
    try:
        test_date = model_utils.ts_from_iso_date_noon(info.consumer_filedate)
        if test_date:
            return error_msg
        error_msg = INVALID_FILING_DATE.format(param_date=info.consumer_filedate)
    except Exception:  # noqa: B902; eat all errors
        error_msg = INVALID_FILING_DATE.format(param_date=info.consumer_filedate)
    return error_msg


def validate_search_dates(info: RequestInfo) -> str:
    """Check that the search query dates are in a valid date format and date range."""
    error_msg: str = ""
    if not info.query_start_date and not info.query_end_date:
        return error_msg
    start_date: datetime = None
    end_date: datetime = None
    if (not info.query_end_date and info.query_start_date) or (info.query_end_date and not info.query_start_date):
        error_msg += MISSING_DATE_PARAM
    if info.query_start_date:
        try:
            start_date = model_utils.ts_from_iso_date_start(info.query_start_date)
            if not start_date:
                error_msg += INVALID_START_DATE.format(param_date=info.query_start_date)
        except Exception:  # noqa: B902; eat all errors
            error_msg += INVALID_START_DATE.format(param_date=info.query_start_date)

    if info.query_end_date:
        try:
            end_date = model_utils.ts_from_iso_date_start(info.query_end_date)
            if not end_date:
                error_msg += INVALID_END_DATE.format(param_date=info.query_end_date)
        except Exception:  # noqa: B902; eat all errors
            error_msg += INVALID_END_DATE.format(param_date=info.query_end_date)
    if end_date and start_date and end_date < start_date:
        error_msg += INVALID_START_END_DATE.format(end_date=info.query_end_date, start_date=info.query_start_date)
    return error_msg
