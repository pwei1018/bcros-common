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
"""API endpoints to convert documents to clean pdfs."""

from http import HTTPStatus

from flask import Blueprint, request

from doc_api.models import EventTracking
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import EventTrackingTypes
from doc_api.resources import utils as resource_utils
from doc_api.services.authz import is_convert_authorized
from doc_api.services.pdf_convert import HEADER_CONTENT_TYPE_PDF, MEDIA_TO_FILE_EXTENSION, MediaTypes, PdfConvert
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger
from doc_api.utils.pdf_clean import clean_pdf

MISSING_CONTENT_TYPE = "Request invalid: required Content-Type header is missing. "
INVALID_CONTENT_TYPE = "Request invalid: the pdf converter does not support the {content_type} content type. "


bp = Blueprint("PDF_CONVERSIONS1", __name__, url_prefix="/pdf-conversions")  # pylint: disable=invalid-name


@bp.route("", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_pdf_conversions():
    """Convert a document to a clean PDF."""
    account_id = ""
    try:
        if not is_convert_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        if not request.get_data():
            logger.error("New pdf convert request no payload.")
            return resource_utils.bad_request_response("New pdf convert request invalid: no payload.")
        account_id: str = resource_utils.get_account_id(request)
        content_type: str = get_content_type(request)
        logger.info(f"Starting new pdf convert request content type= {content_type}, account={account_id}")
        validation_msg = validate_content_type(content_type)
        if validation_msg != "":
            return resource_utils.extra_validation_error_response(validation_msg)
        filename: str = get_filename(account_id, content_type)
        if content_type == MediaTypes.CONTENT_TYPE_PDF.value:
            cleaned_pdf = clean_pdf(request.get_data())
            track_event(EventTrackingTypes.PDF_CLEAN.value, int(HTTPStatus.OK), filename)
            return cleaned_pdf, HTTPStatus.OK, HEADER_CONTENT_TYPE_PDF
        pdf_converter: PdfConvert = PdfConvert(request.get_data(), filename, content_type)
        pdf_data, status, headers = pdf_converter.convert()
        if status != HTTPStatus.OK:
            msg: str = f"PDF conver failed for {filename}: {pdf_data}"
            track_event(EventTrackingTypes.PDF_CONVERT.value, int(status), msg)
            return pdf_data, status, headers
        logger.info(f"Pdf convert successful for file={filename}, data length={len(pdf_data)}, starting pdf clean.")
        cleaned_pdf = clean_pdf(pdf_data)
        track_event(EventTrackingTypes.PDF_CONVERT.value, int(status), filename)
        return cleaned_pdf, status, headers
    except Exception as default_exception:  # noqa: B902; return nicer default error
        msg: str = f"PDF convert failed: {default_exception}"
        track_event(EventTrackingTypes.PDF_CONVERT.value, int(HTTPStatus.INTERNAL_SERVER_ERROR), msg)
        return resource_utils.default_exception_response(default_exception)


def get_content_type(req: request) -> str:
    """Get content type from request headers."""
    return req.headers.get(resource_utils.PARAM_CONTENT_TYPE)


def get_filename(account_id: str, content_type: str) -> str:
    """Get a request filename for the pdf converter."""
    now: str = str(int(model_utils.now_ts().timestamp()))
    file_ext: str = MEDIA_TO_FILE_EXTENSION.get(content_type)
    filename: str = account_id if account_id else "na"
    filename += "-" + now + file_ext
    return filename


def validate_content_type(content_type: str) -> str:
    """Verify the Content-Type request header value: must be present and a supported value."""
    if not content_type:
        return INVALID_CONTENT_TYPE
    if content_type not in MediaTypes:
        return INVALID_CONTENT_TYPE.format(content_type=content_type)
    return ""


def track_event(tracking_type: str, status_code: int, message: str = None):
    """Capture a pdf convert event in the event tracking table."""
    if status_code not in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        logger.error(message)
    else:
        logger.info(message)
    try:
        key_id: int = int(model_utils.now_ts().timestamp())
        event: EventTracking = EventTracking.create(key_id, tracking_type, status_code, message)
        event.save()
    except Exception as err:  # noqa: B902; return nicer default error
        logger.error(f"track_event failed: {err}")
