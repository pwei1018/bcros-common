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
from doc_api.models.type_tables import (
    DocumentClasses,
    DocumentType,
    DocumentTypeClass,
    DocumentTypes,
    ProductCodes,
    RequestTypes,
)
from doc_api.resources.request_info import RequestInfo
from doc_api.services.pdf_convert import MediaTypes
from doc_api.utils.logging import logger

REPORT_TYPE_MIN: int = 3
REPORT_TYPE_MAX: int = 30
ENTITY_ID_MIN: int = 4
ENTITY_ID_MAX: int = 20
FILENAME_MIN: int = 5
FILENAME_MAX: int = 1000
VALIDATOR_ERROR = "Error performing new request extra validation. "
INVALID_DOC_TYPE = "Request invalid: unrecognized document type {doc_type}. "
INACTIVE_DOC_TYPE = "Request invalid: document type {doc_type} is not active. "
MISSING_DOC_TYPE = "Request invalid: required request document type is missing. "
INVALID_DOC_CLASS = "Request invalid: unrecognized document class {doc_class}. "
INACTIVE_DOC_CLASS_TYPE = "Request invalid: document class {doc_class} type {doc_type} combination is not active. "
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
INVALID_REFERENCE_ID = "The consumerReferenceId value cannot be greater than 50 characters in length. "
INVALID_REPORT_TYPE = "Report type {report_type} is required and must be between 3 and 30 characters in length. "
INVALID_ENTITY_ID = "Entity identifier {entity_id} is required and must be between 4 and 20 characters in length. "
INVALID_EVENT_ID = "Event identifier {event_id} is invalid: it must be an integer > 0. "
INVALID_FILENAME = "File name {filename} is invalid: it must be between 5 and 1000 characters in length. "
INVALID_REPORT_UPDATE = "PATCH update report record payload no properties found to update (see the API spec). "
INVALID_DOC_CLASS_UPDATE = "Request invalid: document class may not be updated. "
MISSING_EXISTING_SCAN = "Request invalid: no document scanning information exists to update. "
INVALID_PRODUCT_CODE = "Request invalid: unknown product code {product_code}. "
MISSING_PAYLOAD_APP = "Request invalid: add application document missing required payload. "
INVALID_FILING_DATE_APP = "Request invalid: datePublished format invalid {param_date}. "


def validate_request(info: RequestInfo) -> str:
    """Perform all extra data validation checks on a new request not covered by schema validation."""
    logger.info(f"Validating {info.request_type} account id={info.account_id} staff={info.staff}")
    error_msg: str = ""
    if not info.request_type or info.request_type not in (RequestTypes.GET, RequestTypes.UPDATE):
        error_msg += validate_doc_type(info)
    if info.document_class and info.document_class not in DocumentClasses:
        error_msg += INVALID_DOC_CLASS.format(doc_class=info.document_class)
    elif info.document_class and info.document_type:  # Verify document class - document type pair.
        error_msg += validate_class_type(info)
    if not info.document_class:
        error_msg += get_doc_class(info)
    if info.request_type and info.request_type == RequestTypes.ADD:
        if info.document_type and info.document_type == DocumentTypes.APP_FILE.value:
            return validate_add_app(info, error_msg)
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


def validate_report_request(request_json: dict, is_create: bool) -> str:
    """Perform all extra data validation checks on a new report request not covered by schema validation."""
    logger.info(f"Validating new report request for entity {request_json.get('entityIdentifier')}")
    error_msg: str = ""
    try:
        if request_json.get("productCode") and request_json.get("productCode") not in ProductCodes:
            error_msg += INVALID_PRODUCT_CODE.format(product_code=request_json.get("productCode"))
        if request_json.get("isGet"):
            return error_msg
        if not is_create and not request_json:
            logger.info("PATCH with no payload: request invalid.")
            return INVALID_REPORT_UPDATE
        error_msg += validate_report_filingdate(request_json)
        report_type: str = request_json.get("reportType")
        if not report_type and is_create:
            error_msg += INVALID_REPORT_TYPE.format(report_type="(missing)")
        elif report_type and (len(report_type) < REPORT_TYPE_MIN or len(report_type) > REPORT_TYPE_MAX):
            error_msg += INVALID_REPORT_TYPE.format(report_type=report_type)
        filename: str = request_json.get("name")
        if filename and (len(filename) < FILENAME_MIN or len(filename) > FILENAME_MAX):
            error_msg += INVALID_FILENAME.format(filename=filename)
        if is_create:
            entity_id: str = request_json.get("entityIdentifier")
            if not entity_id or len(entity_id) < ENTITY_ID_MIN or len(entity_id) > ENTITY_ID_MAX:
                error_msg += INVALID_ENTITY_ID.format(entity_id=entity_id)
            error_msg += validate_report_event_id(request_json)
        elif not report_type and not filename and not request_json.get("datePublished"):
            error_msg += INVALID_REPORT_UPDATE
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_report_request exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_add(info: RequestInfo, error_msg: str) -> str:
    """Validate the add request."""
    try:
        if not info.content_type:
            error_msg += MISSING_CONTENT_TYPE
        elif info.content_type not in MediaTypes:
            error_msg += INVALID_CONTENT_TYPE.format(content_type=info.content_type)
        error_msg += validate_filingdate(info)
        error_msg += validate_reference_id(info)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_add exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_add_app(info: RequestInfo, error_msg: str) -> str:
    """Validate the add application document request."""
    try:
        if not info.content_type:
            error_msg += MISSING_CONTENT_TYPE
        elif info.content_type not in MediaTypes:
            error_msg += INVALID_CONTENT_TYPE.format(content_type=info.content_type)
        if not info.has_payload:
            error_msg += MISSING_PAYLOAD_APP
        filename = info.consumer_filename
        if filename and (len(filename) < FILENAME_MIN or len(filename) > FILENAME_MAX):
            error_msg += INVALID_FILENAME.format(filename=filename)
        if info.consumer_filedate:
            try:
                test_date = model_utils.ts_from_iso_date_noon(info.consumer_filedate)
                if not test_date:
                    error_msg = INVALID_FILING_DATE_APP.format(param_date=info.consumer_filedate)
            except Exception:  # noqa: B902; eat all errors
                error_msg = INVALID_FILING_DATE_APP.format(param_date=info.consumer_filedate)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error(f"validate_add exception: {validation_exception}")
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
        if info.document_type and info.document_type == DocumentTypes.APP_FILE.value:
            return validate_patch_app(info, error_msg)
        if info.request_data and info.request_data.get("removed"):
            return error_msg
        if not is_document_modified(info) and not is_scanning_modified(info):
            error_msg += MISSING_PATCH_PARAMS
        if (
            info.request_data
            and info.request_data.get("documentClass")
            and info.request_data.get("documentClass") != info.document_class
        ):
            error_msg += INVALID_DOC_CLASS_UPDATE
        if info.request_data and info.request_data.get("documentType"):
            error_msg += validate_doc_type_class(info.request_data.get("documentType"), info.document_class)
        error_msg += validate_scanning_info(info)
        error_msg += validate_filingdate(info)
        error_msg += validate_reference_id(info)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_patch exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_patch_app(info: RequestInfo, error_msg: str) -> str:
    """Validate the application document patch request."""
    try:
        if not info.request_data:
            error_msg += MISSING_PAYLOAD_APP
        filename = info.consumer_filename
        if filename and (len(filename) < FILENAME_MIN or len(filename) > FILENAME_MAX):
            error_msg += INVALID_FILENAME.format(filename=filename)
        if info.consumer_filedate:
            try:
                test_date = model_utils.ts_from_iso_date_noon(info.consumer_filedate)
                if not test_date:
                    error_msg = INVALID_FILING_DATE_APP.format(param_date=info.consumer_filedate)
            except Exception:  # noqa: B902; eat all errors
                error_msg = INVALID_FILING_DATE_APP.format(param_date=info.consumer_filedate)
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error(f"validate_patch exception: {validation_exception}")
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_put(info: RequestInfo, error_msg: str) -> str:
    """Validate the put request."""
    try:
        if not info.content_type:
            error_msg += MISSING_CONTENT_TYPE
        elif info.content_type not in MediaTypes:
            error_msg += INVALID_CONTENT_TYPE.format(content_type=info.content_type)
        if not info.has_payload:
            error_msg += MISSING_PAYLOAD
    except Exception as validation_exception:  # noqa: B902; eat all errors
        logger.error("validate_put exception: " + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def is_modified(existing: dict, update: dict, prop_name: str) -> bool:
    """Determine if a specific property modifies the existing record."""
    if not update.get(prop_name):
        return False
    return update.get(prop_name) != existing.get(prop_name, "")


def is_document_modified(info: RequestInfo) -> bool:
    """For a document PATCH request determine if any of the allowed properties have been updated."""
    if not info.request_data or not info.request_data.get("existingDocument"):
        return False
    existing = info.request_data["existingDocument"]
    updated = info.request_data
    if (
        is_modified(existing, updated, "consumerFilename")
        or is_modified(existing, updated, "consumerIdentifier")
        or is_modified(existing, updated, "consumerFilingDateTime")
        or is_modified(existing, updated, "consumerFilingDate")
        or is_modified(existing, updated, "documentType")
    ):
        return True
    if (
        is_modified(existing, updated, "description")
        or is_modified(existing, updated, "author")
        or is_modified(existing, updated, "consumerReferenceId")
        or is_modified(existing, updated, "consumerDocumentId")
    ):
        return True
    return False


def is_scanning_modified(info: RequestInfo) -> bool:
    """For a document PATCH request determine if any of the scanning information has been modifed."""
    if (
        not info.request_data
        or not info.request_data.get("existingDocument")
        or not info.request_data["existingDocument"].get("scanningInformation")
        or not info.request_data.get("scanningInformation")
    ):
        return False
    existing = info.request_data["existingDocument"].get("scanningInformation")
    updated = info.request_data.get("scanningInformation")
    if (
        is_modified(existing, updated, "accessionNumber")
        or is_modified(existing, updated, "scanDateTime")
        or is_modified(existing, updated, "batchId")
        or is_modified(existing, updated, "author")
    ):
        return True
    if updated.get("pageCount") and existing.get("pageCount", 0) != updated.get("pageCount"):
        return True
    return False


def validate_scanning_info(info: RequestInfo) -> str:
    """Validate the PATCH scanning information: only allowed if record exists."""
    error_msg: str = ""
    if not info.request_data or not info.request_data.get("scanningInformation"):
        return error_msg
    if not info.request_data.get("existingDocument") or not info.request_data["existingDocument"].get(
        "scanningInformation"
    ):
        error_msg += MISSING_EXISTING_SCAN
    elif is_scanning_modified(info):
        error_msg += validate_scandate(info.request_data.get("scanningInformation"))
    return error_msg


def validate_doc_type(info: RequestInfo) -> str:
    """Validate the document type exists and is active."""
    error_msg: str = ""
    if not info.document_type:
        error_msg += MISSING_DOC_TYPE
    elif info.document_type and info.document_type not in DocumentTypes:
        error_msg += INVALID_DOC_TYPE.format(doc_type=info.document_type)
    else:
        doc_type: DocumentType = DocumentType.find_by_doc_type(info.document_type)
        if not doc_type:
            error_msg += INVALID_DOC_TYPE.format(doc_type=info.document_type)
        elif not doc_type.active:
            error_msg += INACTIVE_DOC_TYPE.format(doc_type=info.document_type)
    return error_msg


def validate_doc_type_class(doc_type: str, doc_class: str) -> str:
    """Validate the document class matches the document type and the combination is active."""
    error_msg: str = ""
    if not doc_type or not doc_class:
        return error_msg
    doc_types = DocumentTypeClass.find_by_doc_type(doc_type, True)
    if doc_types:
        valid_class: bool = False
        for type_class in doc_types:
            if type_class.document_class == doc_class:
                if not type_class.active:
                    error_msg += INACTIVE_DOC_CLASS_TYPE.format(doc_class=doc_class, doc_type=doc_type)
                else:
                    valid_class = True
                break
        if not valid_class and not error_msg:
            error_msg = INVALID_DOC_CLASS_TYPE.format(doc_type=doc_type, doc_class=doc_class)
    else:
        error_msg += INVALID_DOC_CLASS_TYPE.format(doc_type=doc_type, doc_class=doc_class)
    return error_msg


def validate_class_type(info: RequestInfo) -> str:
    """Validate the document class matches the document type and the combination is active."""
    if not info.document_class or not info.document_type:
        return ""
    return validate_doc_type_class(info.document_type, info.document_class)


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
        logger.error("get_doc_class exception: " + str(validation_exception))
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


def validate_report_filingdate(request_json: dict) -> str:
    """Check that the optional report event filing date is in a valid date format."""
    error_msg: str = ""
    if not request_json.get("datePublished"):
        return error_msg
    filing_date: str = request_json.get("datePublished")
    try:
        test_date = model_utils.ts_from_iso_format(filing_date)
        if test_date:
            return error_msg
        error_msg = INVALID_FILING_DATE.format(param_date=filing_date)
    except Exception:  # noqa: B902; eat all errors
        error_msg = INVALID_FILING_DATE.format(param_date=filing_date)
    return error_msg


def validate_report_event_id(request_json: dict) -> str:
    """Check that the report event id is a valid positive integer."""
    error_msg: str = ""
    request_id: str = request_json.get("requestEventIdentifier")
    if not request_id:
        return INVALID_EVENT_ID.format(event_id="(missing)")
    try:
        event_id: int = int(request_id)
        if str(event_id) != request_id:
            return INVALID_EVENT_ID.format(event_id=request_id)
        request_json["eventIdentifier"] = event_id
    except Exception:  # noqa: B902; eat all errors
        error_msg = INVALID_EVENT_ID.format(event_id=request_id)
    return error_msg


def validate_reference_id(info: RequestInfo) -> str:
    """Check that the optional consumer reference ID length is not too long."""
    error_msg: str = ""
    if not info.consumer_reference_id:
        return error_msg
    if len(info.consumer_reference_id) > 50:
        error_msg += INVALID_REFERENCE_ID
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


def checksum_valid(doc_id: str) -> bool:
    """Validate the document id with a checksum algorithm. Skip if the document ID length is not 8."""
    if not doc_id or not doc_id.isnumeric():
        return False
    if len(doc_id) != 8:
        return True
    dig1: int = int(doc_id[0:1])
    dig2: int = int(doc_id[1:2]) * 2
    dig3: int = int(doc_id[2:3])
    dig4: int = int(doc_id[3:4]) * 2
    dig5: int = int(doc_id[4:5])
    dig6: int = int(doc_id[5:6]) * 2
    dig7: int = int(doc_id[6:7])
    check_digit: int = int(doc_id[7:])
    dig_sum = dig1 + dig3 + dig5 + dig7
    if dig2 > 9:
        dig_sum += 1 + (dig2 % 10)
    else:
        dig_sum += dig2
    if dig4 > 9:
        dig_sum += 1 + (dig4 % 10)
    else:
        dig_sum += dig4
    if dig6 > 9:
        dig_sum += 1 + (dig6 % 10)
    else:
        dig_sum += dig6
    mod_sum = dig_sum % 10
    logger.debug(f"sum={dig_sum}, checkdigit= {check_digit}, mod_sum={mod_sum}")
    if mod_sum == 0:
        return mod_sum == check_digit
    return (10 - mod_sum) == check_digit
