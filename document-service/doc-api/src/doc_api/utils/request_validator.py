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
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import RequestTypes, DocumentTypes, DocumentClasses
from doc_api.resources.request_info import RequestInfo
from doc_api.utils.logging import logger


VALIDATOR_ERROR = 'Error performing new request extra validation. '
INVALID_DOC_TYPE = 'Request invalid: unrecognized document type {doc_type}. '
MISSING_DOC_TYPE = 'Request invalid: required request document type is missing. '
INVALID_DOC_CLASS = 'Request invalid: unrecognized document class {doc_class}. '
MISSING_CONTENT_TYPE = 'Request invalid: required request header Content-Type is missing. '
INVALID_CONTENT_TYPE = 'Request invalid: unsupported request header Content-type {content_type}. '
MISSING_QUERY_PARAMS = 'Request invalid: get documents is missing one of the required parameters. '
MISSING_DOC_CLASS = 'Request invalid: required request document class is missing. '
INVALID_DATE_PARAMS = 'Request invalid: get documents require both query start date and query end date. '


def validate_request(info: RequestInfo) -> str:
    """Perform all extra data validation checks on a new request not covered by schema validation."""
    logger.info(f'Validating {info.request_type} account id={info.account_id} staff={info.staff}')
    error_msg: str = ''
    if not info.request_type or info.request_type not in (RequestTypes.GET, RequestTypes.UPDATE):
        if not info.document_type:
            error_msg += MISSING_DOC_TYPE
        elif info.document_type and info.document_type not in DocumentTypes:
            error_msg += INVALID_DOC_TYPE.format(doc_type=info.document_type)
    if info.document_class and info.document_class not in DocumentClasses:
        error_msg += INVALID_DOC_CLASS.format(doc_class=info.document_class)

    if info.request_type and info.request_type == RequestTypes.ADD:
        return validate_add(info, error_msg)
    if info.request_type and info.request_type == RequestTypes.GET:
        return validate_get(info, error_msg)
    return error_msg


def validate_add(info: RequestInfo, error_msg: str) -> str:
    """Validate the add request."""
    try:
        if not info.content_type:
            error_msg += MISSING_CONTENT_TYPE
        elif not model_utils.TO_FILE_TYPE.get(info.content_type):
            error_msg += INVALID_CONTENT_TYPE.format(content_type=info.content_type)
    except Exception as validation_exception:   # noqa: B902; eat all errors
        logger.error('validate_add exception: ' + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg


def validate_get(info: RequestInfo, error_msg: str) -> str:
    """Validate the get request."""
    try:
        if not info.document_class:
            error_msg += MISSING_DOC_CLASS
        if not info.consumer_doc_id and not info.consumer_identifier and not info.document_service_id and \
                not info.query_start_date and not info.query_end_date:
            error_msg += MISSING_QUERY_PARAMS
        elif (not info.query_end_date and info.query_start_date) or (info.query_end_date and not info.query_start_date):
            error_msg += INVALID_DATE_PARAMS
    except Exception as validation_exception:   # noqa: B902; eat all errors
        logger.error('validate_get exception: ' + str(validation_exception))
        error_msg += VALIDATOR_ERROR
    return error_msg
