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
"""API endpoints for requests to maintain document scanning information."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models import (
    DocumentClass,
    DocumentScanning,
    DocumentType,
    ScanningAuthor,
    ScanningBox,
    ScanningParameter,
    ScanningSchedule,
)
from doc_api.resources import utils as resource_utils
from doc_api.services.authz import is_scanner_authorized
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger

REQUEST_PATH = "/scanning/{doc_class}/{consumer_doc_id}"
DOC_CLASS_PATH = "/scanning/document-classes"
DOC_TYPE_PATH = "/scanning/document-types"
AUTHOR_PATH = "/scanning/authors"
SCHEDULE_PATH = "/scanning/schedules"
PARAMETER_PATH = "/scanning/parameters"
BATCH_ID_PATH = "/scanning/batch_id/{accession_number}"
BOX_PATH = "/scanning/boxes"
BOX_SEQUENCE_PATH = "/scanning/boxes/{sequence_number}/{schedule_number}"

bp = Blueprint("SCANNING1", __name__, url_prefix="/scanning")  # pylint: disable=invalid-name


@bp.route("/<string:doc_class>/<string:consumer_doc_id>", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_document_scanning(doc_class: str, consumer_doc_id: str):
    """Save a new document."""
    account_id = ""
    try:
        req_path: str = REQUEST_PATH.format(doc_class=doc_class, consumer_doc_id=consumer_doc_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new create document scanning request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        request_json = request.get_json(silent=True)
        request_json["documentClass"] = doc_class
        request_json["consumerDocumentId"] = consumer_doc_id
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_scanning_request(request_json, True)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        scan_doc: DocumentScanning = DocumentScanning.create_from_json(request_json, consumer_doc_id, doc_class)
        scan_doc.save()
        response_json = scan_doc.json
        logger.info(f"post_document_scanning returning response {response_json}")
        return jsonify(response_json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(
            db_exception, account_id, "POST create document scanning id=" + account_id
        )
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_class>/<string:consumer_doc_id>", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def update_document_scanning(doc_class: str, consumer_doc_id: str):
    """Update document scanning information by document class and consumer document ID."""
    try:
        req_path: str = REQUEST_PATH.format(doc_class=doc_class, consumer_doc_id=consumer_doc_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new update document scanning request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        request_json = request.get_json(silent=True)
        request_json["documentClass"] = doc_class
        request_json["consumerDocumentId"] = consumer_doc_id
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_scanning_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        doc_scan: DocumentScanning = DocumentScanning.find_by_document_id(consumer_doc_id, doc_class)
        if not doc_scan:
            logger.warning(f"No document scanning record found for doc class={doc_class} doc ID={consumer_doc_id}.")
            return resource_utils.not_found_error_response(
                f"PATCH document scanning class={doc_class}", consumer_doc_id
            )
        doc_scan.update(request_json)
        doc_scan.save()
        response_json = doc_scan.json
        logger.info(f"patch_document_scanning returning response {response_json}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH document scanning information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_class>/<string:consumer_doc_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_document_scanning(doc_class: str, consumer_doc_id: str):
    """Retrieve document scanning information by document class and consumer document ID."""
    try:
        req_path: str = REQUEST_PATH.format(doc_class=doc_class, consumer_doc_id=consumer_doc_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get document scanning request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        doc_scan: DocumentScanning = DocumentScanning.find_by_document_id(consumer_doc_id, doc_class)
        if not doc_scan:
            logger.warning(f"No document scanning record found for doc class={doc_class} doc ID={consumer_doc_id}.")
            return resource_utils.not_found_error_response(f"GET document scanning class={doc_class}", consumer_doc_id)
        response_json = doc_scan.json
        logger.info(f"get_document_scanning returning response {response_json}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET document scanning information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/document-classes", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_document_classes():
    """Retrieve scanning document classes for the scanning application."""
    try:
        req_path: str = DOC_CLASS_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning document classes request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = DocumentClass.find_all_scanning()
        if not results:
            logger.warning("No scanning document classes found.")
            return resource_utils.not_found_error_response("GET scanning document classes", account_id)
        response_json = []
        for result in results:
            if result.active:
                response_json.append(result.scanning_json)
        logger.info(f"get_document_classes returning array of length {len(response_json)}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET scanning document classes")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/document-types", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_document_types():
    """Retrieve scanning document types for the scanning application."""
    try:
        req_path: str = DOC_TYPE_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning document types request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = DocumentType.find_all_scanning()
        if not results:
            logger.warning("No scanning document types found.")
            return resource_utils.not_found_error_response("GET scanning document types", account_id)
        response_json = []
        for result in results:
            if result.active:
                response_json.append(result.scanning_json)
        logger.info(f"get_document_types returning array of length {len(response_json)}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET scanning document types")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/authors", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_authors():
    """Retrieve scanning authors for the scanning application."""
    try:
        req_path: str = AUTHOR_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning authors request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = ScanningAuthor.find_all()
        if not results:
            logger.warning("No scanning authors found.")
            return resource_utils.not_found_error_response("GET scanning authors", account_id)
        response_json = []
        for result in results:
            response_json.append(result.json)
        logger.info(f"get_authors returning array of length {len(response_json)}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET scanning authors")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/schedules", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_schedules():
    """Retrieve scanning schedules for the scanning application."""
    try:
        req_path: str = SCHEDULE_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning schedules request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = ScanningSchedule.find_all()
        if not results:
            logger.warning("No scanning schedules found.")
            return resource_utils.not_found_error_response("GET scanning schedules", account_id)
        response_json = []
        for result in results:
            response_json.append(result.json)
        logger.info(f"get_schedules returning array of length {len(response_json)}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET scanning schedules")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/parameters", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_parameters():
    """Retrieve scanning parameters for the scanning application."""
    try:
        req_path: str = PARAMETER_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning parameters request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = ScanningParameter.find()
        if not results:
            logger.warning("No scanning parameters found.")
            return resource_utils.not_found_error_response("GET scanning parameters", account_id)
        logger.info("get_parameters found values to return")
        return jsonify(results.json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET scanning parameters")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/parameters", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_parameters():
    """Create scanning parameters for the scanning application: only one record allowed."""
    try:
        req_path: str = PARAMETER_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new create scanning parameters request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        request_json = request.get_json(silent=True)
        if not request_json:
            return resource_utils.bad_request_response("POST invalid: no scanning parameters in payload.")
        results = ScanningParameter.find()
        if results:
            logger.warning("Existing scanning parameters found.")
            return resource_utils.bad_request_response("Existing scanning parameters found: use PATCH instead.")
        params: ScanningParameter = ScanningParameter.create_from_json(request_json)
        params.save()
        logger.info(f"post_parameters created parameters: {params.json}")
        return jsonify(params.json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "POST scanning parameters")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/parameters", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def patch_parameters():
    """Update scanning parameters for the scanning application: only one record allowed."""
    try:
        req_path: str = PARAMETER_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new update scanning parameters request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        request_json = request.get_json(silent=True)
        if not request_json:
            return resource_utils.bad_request_response("PATCH invalid: no scanning parameters in payload.")
        params = ScanningParameter.find()
        if not params:
            logger.warning("No existing scanning parameters found.")
            return resource_utils.bad_request_response("No existing scanning parameters found to update.")
        params.update(request_json)
        params.save()
        logger.info(f"patch_parameters updated parameters: {params.json}")
        return jsonify(params.json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH scanning parameters")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/batchid/<string:accession_number>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_max_batch_id(accession_number: str):
    """Retrieve the maximum scanning record batch id by accession number."""
    try:
        req_path: str = BATCH_ID_PATH.format(accession_number=accession_number)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning batch id request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        batch_id: int = DocumentScanning.get_max_batch_id(accession_number)
        response_json = {"batchId": batch_id}
        logger.info(f"get_max_batch_id returning batchId={batch_id}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET scanning max batch id")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/boxes", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_boxes():
    """Create a scanning document box record for the scanning application."""
    try:
        req_path: str = BOX_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new create scanning box request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        request_json = request.get_json(silent=True)
        if not request_json:
            return resource_utils.bad_request_response("POST invalid: no scanning box information in payload.")
        box: ScanningBox = ScanningBox.create_from_json(request_json)
        box.save()
        logger.info(f"post_boxes created new box id={box.id}")
        return jsonify(box.json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "POST scanning box")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/boxes", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def patch_boxes():
    """Update an existing scanning document box record for the scanning application."""
    try:
        req_path: str = BOX_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new update scanning box request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        request_json = request.get_json(silent=True)
        if not request_json or not request_json.get("boxId"):
            return resource_utils.bad_request_response("PATCH invalid: no scanning box information in payload.")
        box_id = request_json.get("boxId")
        box: ScanningBox = ScanningBox.find_by_id(box_id)
        if not box:
            logger.warning(f"No scanning box found to update for boxId={box_id}")
            return resource_utils.not_found_error_response(
                f"PATCH {req_path} no box exists for boxId={box_id}", account_id
            )
        box.update(request_json)
        box.save()
        logger.info(f"patch_boxes updated box id={box.id}")
        return jsonify(box.json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH scanning box")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/boxes", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_all_boxes():
    """Retrieve all scanning document boxes for the scanning application."""
    try:
        req_path: str = BOX_PATH
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get all scanning boxes request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = ScanningBox.find_all()
        if not results:
            logger.warning("No scanning boxes found.")
            return resource_utils.not_found_error_response("GET all scanning boxes", account_id)
        response_json = []
        for result in results:
            response_json.append(result.json)
        logger.info(f"get_all_boxes returning array of length {len(response_json)}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET all scanning boxes")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/boxes/<string:sequence_number>/<string:schedule_number>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_sequence_boxes(sequence_number: str, schedule_number: str):
    """Retrieve the boxes that match the sequence number and schedule number if any."""
    try:
        req_path: str = BOX_SEQUENCE_PATH.format(sequence_number=sequence_number, schedule_number=schedule_number)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting new get scanning boxes request {req_path}, account={account_id}")
        if account_id is None:
            return resource_utils.account_required_response()
        if not is_scanner_authorized(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        results = ScanningBox.find_by_sequence_schedule(int(sequence_number), int(schedule_number))
        if not results:
            logger.warning("No scanning boxes found.")
            return resource_utils.not_found_error_response(f"GET {req_path}", account_id)
        response_json = []
        for result in results:
            response_json.append(result.json)
        logger.info(f"get_sequence_boxes returning array of length {len(response_json)}")
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, f"GET {req_path}")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)
