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
"""API endpoints for requests to maintain application reports."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models import ApplicationReport
from doc_api.models import utils as model_utils
from doc_api.models.type_tables import ProductCodes
from doc_api.resources import utils as resource_utils
from doc_api.services.authz import is_report_authorized
from doc_api.services.document_storage.storage_service import GoogleStorageService
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger

POST_REQUEST_PATH = "/application-reports/{entity_id}/{event_id}/{report_type}"
CHANGE_REQUEST_PATH = "/application-reports/{doc_service_id}"
HISTORY_REQUEST_PATH = "/application-reports/history/{entity_id}"
EVENT_REQUEST_PATH = "/application-reports/events/{event_id}"
POST_REQUEST_PATH_PRODUCT = "/application-reports/{product_code}/{entity_id}/{event_id}/{report_type}"
CHANGE_REQUEST_PATH_PRODUCT = "/application-reports/{product_code}/{doc_service_id}"
HISTORY_REQUEST_PATH_PRODUCT = "/application-reports/history/{product_code}/{entity_id}"
EVENT_REQUEST_PATH_PRODUCT = "/application-reports/events/{product_code}/{entity_id}/{event_id}"
CONTENT_JSON = {"Content-Type": "application/json"}
CONTENT_PDF = {"Content-Type": "application/pdf"}

bp = Blueprint("APP_REPORTS1", __name__, url_prefix="/application-reports")  # pylint: disable=invalid-name


@bp.route("/<string:prod_code>/<string:entity_id>/<string:event_id>/<string:report_type>", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_product_reports(prod_code: str, entity_id: str, event_id: str, report_type: str):
    """Save a new product application report."""
    account_id = ""
    try:
        if not is_report_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        account_id: str = resource_utils.get_account_id(request)
        req_path: str = POST_REQUEST_PATH_PRODUCT.format(
            product_code=prod_code, entity_id=entity_id, event_id=event_id, report_type=report_type
        )
        request_json: dict = {
            "productCode": prod_code,
            "entityIdentifier": entity_id,
            "requestEventIdentifier": event_id,
            "reportType": report_type,
        }
        request_json = get_new_report_params(request, request_json)
        logger.info(f"Starting new create product report request {req_path}, account={account_id}")
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_report_request(request_json, True)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        if not request.get_data():
            logger.error("Create new product report request no payload.")
            return resource_utils.bad_request_response("Create new product report request invalid: no payload.")
        response_json = save_create(request_json, request.get_data())
        return jsonify(response_json), HTTPStatus.CREATED, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "POST create report id=" + account_id)
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:prod_code>/<string:doc_service_id>", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def update_product_report_info(prod_code: str, doc_service_id: str):
    """Update product report information (excluding the report) that is associated with the document service ID."""
    try:
        account_id = resource_utils.get_account_id(request)
        if not is_report_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        req_path: str = CHANGE_REQUEST_PATH_PRODUCT.format(product_code=prod_code, doc_service_id=doc_service_id)
        logger.info(f"Starting update product report record request {req_path}, account={account_id}")
        request_json = request.get_json(silent=True)
        logger.debug(f"update_report_info product payload={request_json}")
        request_json["productCode"] = prod_code
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_report_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(doc_service_id, prod_code)
        if not app_report:
            logger.warning(f"No product report record found for {prod_code} document service id={doc_service_id}.")
            return resource_utils.not_found_error_response(f"PATCH {prod_code} report information", doc_service_id)
        app_report.update(request_json)
        app_report.save()
        response_json = app_report.json
        return jsonify(response_json), HTTPStatus.OK, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH product report information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:prod_code>/<string:doc_service_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_individual_product_report(prod_code: str, doc_service_id: str):
    """Get report information including a url that is associated with the document service ID."""
    try:
        account_id = resource_utils.get_account_id(request)
        if not is_report_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        req_path: str = CHANGE_REQUEST_PATH_PRODUCT.format(product_code=prod_code, doc_service_id=doc_service_id)
        logger.info(f"Starting get {prod_code} report record request {req_path}, account={account_id}")
        request_json: dict = {"productCode": prod_code, "isGet": True}
        extra_validation_msg = resource_utils.validate_report_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(doc_service_id, prod_code)
        if not app_report:
            logger.info(f"No {prod_code} report record found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response(f"GET {prod_code} report information", doc_service_id)
        if resource_utils.is_pdf(request):
            logger.info(f"Request {prod_code} {doc_service_id} for PDF data.")
            report_data = get_report_data(app_report)
            return report_data, HTTPStatus.OK, CONTENT_PDF
        response_json = get_report_link(app_report)
        return jsonify(response_json), HTTPStatus.OK, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET product report information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/events/<string:prod_code>/<string:entity_id>/<int:event_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_product_event_reports(prod_code: str, entity_id: str, event_id: int):
    """Get report information including a url for all product reports associated with a product entity event ID."""
    try:
        account_id = resource_utils.get_account_id(request)
        if not is_report_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        req_path: str = EVENT_REQUEST_PATH_PRODUCT.format(
            product_code=prod_code, entity_id=entity_id, event_id=event_id
        )
        logger.info(f"Starting get product report event request {req_path}, account={account_id}")
        request_json: dict = {"productCode": prod_code, "isGet": True}
        extra_validation_msg = resource_utils.validate_report_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        reports_json: list = ApplicationReport.find_by_event_id_json(event_id, entity_id, prod_code)
        if not reports_json:
            logger.warning(f"No {prod_code} report records found for {entity_id} event id={event_id}.")
            return resource_utils.not_found_error_response(
                f"GET {prod_code} report information by entity ID", str(event_id)
            )
        response_json = get_report_links(reports_json, prod_code)
        return jsonify(response_json), HTTPStatus.OK, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(
            db_exception, account_id, "GET {prod_code} report information by event ID"
        )
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/history/<string:prod_code>/<string:entity_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_product_history_reports(prod_code: str, entity_id: str):
    """Get report information including a url for all reports associated with a product entity ID."""
    try:
        account_id = resource_utils.get_account_id(request)
        if not is_report_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        req_path: str = HISTORY_REQUEST_PATH_PRODUCT.format(product_code=prod_code, entity_id=entity_id)
        logger.info(f"Starting get report entity history request {req_path}, account={account_id}")
        request_json: dict = {"productCode": prod_code, "isGet": True}
        extra_validation_msg = resource_utils.validate_report_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        reports_json: list = ApplicationReport.find_by_entity_id_json(entity_id, prod_code)
        if not reports_json:
            logger.warning(f"No {prod_code} report records found for entity id={entity_id}.")
            return resource_utils.not_found_error_response(
                f"GET {prod_code} report information by entity ID", entity_id
            )
        response_json = get_report_links(reports_json, prod_code)
        return jsonify(response_json), HTTPStatus.OK, CONTENT_JSON
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(
            db_exception, account_id, "GET product report information by entity ID"
        )
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:entity_id>/<string:event_id>/<string:report_type>", methods=["POST", "OPTIONS"])
@jwt.requires_auth
def post_reports(entity_id: str, event_id: str, report_type: str):
    """Save a new application report."""
    account_id = ""
    try:
        account_id: str = resource_utils.get_account_id(request)
        req_path: str = POST_REQUEST_PATH.format(entity_id=entity_id, event_id=event_id, report_type=report_type)
        request_json: dict = {
            "entityIdentifier": entity_id,
            "requestEventIdentifier": event_id,
            "reportType": report_type,
            "productCode": ProductCodes.BUSINESS.value,
        }
        request_json = get_new_report_params(request, request_json)
        logger.info(f"Starting new create report request {req_path}, account={account_id}")
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_report_request(request_json, True)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        if not request.get_data():
            logger.error("Create new report request no payload.")
            return resource_utils.bad_request_response("Create new report request invalid: no payload.")
        response_json = save_create(request_json, request.get_data())
        return jsonify(response_json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "POST create report id=" + account_id)
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["PATCH", "OPTIONS"])
@jwt.requires_auth
def update_report_info(doc_service_id: str):
    """Update report information (excluding the report) that is associated with the document service ID."""
    try:
        req_path: str = CHANGE_REQUEST_PATH.format(doc_service_id=doc_service_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting update report record request {req_path}, account={account_id}")
        request_json = request.get_json(silent=True)
        logger.debug(f"update_report_info payload={request_json}")
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_report_request(request_json, False)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(doc_service_id)
        if not app_report:
            logger.warning(f"No report record found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("PATCH report information", doc_service_id)
        app_report.update(request_json)
        app_report.save()
        response_json = app_report.json
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "PATCH report information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/<string:doc_service_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_individual_report(doc_service_id: str):
    """Get report information including a url that is associated with the document service ID."""
    try:
        req_path: str = CHANGE_REQUEST_PATH.format(doc_service_id=doc_service_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting get report record request {req_path}, account={account_id}")
        app_report: ApplicationReport = ApplicationReport.find_by_doc_service_id(doc_service_id)
        if not app_report:
            logger.warning(f"No report record found for document service id={doc_service_id}.")
            return resource_utils.not_found_error_response("GET report information", doc_service_id)
        response_json = get_report_link(app_report)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET report information")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/history/<string:entity_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_history_reports(entity_id: str):
    """Get report information including a url for all reports associated with an entity ID."""
    try:
        req_path: str = HISTORY_REQUEST_PATH.format(entity_id=entity_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting get report entity history request {req_path}, account={account_id}")
        reports_json: list = ApplicationReport.find_by_entity_id_json(entity_id)
        if not reports_json:
            logger.warning(f"No report records found for entity id={entity_id}.")
            return resource_utils.not_found_error_response("GET report information by entity ID", entity_id)
        response_json = get_report_links(reports_json, ProductCodes.BUSINESS.value)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET report information by entity ID")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("/events/<int:event_id>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_event_reports(event_id: int):
    """Get report information including a url for all reports associated with an event ID."""
    try:
        req_path: str = EVENT_REQUEST_PATH.format(event_id=event_id)
        account_id = resource_utils.get_account_id(request)
        logger.info(f"Starting get report event request {req_path}, account={account_id}")
        reports_json: list = ApplicationReport.find_by_event_id_json(event_id)
        if not reports_json:
            logger.warning(f"No report records found for event id={event_id}.")
            return resource_utils.not_found_error_response("GET report information by entity ID", str(event_id))
        response_json = get_report_links(reports_json, ProductCodes.BUSINESS.value)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET report information by event ID")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


def get_new_report_params(req: request, request_json: dict) -> dict:
    """Extract optional report properties from request parameters."""
    request_json["name"] = req.args.get(resource_utils.PARAM_CONSUMER_FILENAME, "")
    request_json["datePublished"] = req.args.get(resource_utils.PARAM_CONSUMER_FILEDATE, "")
    return request_json


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


def save_create(request_json: dict, raw_data) -> dict:
    """Save new app report record and request binary data to document storage. Return a download link"""
    logger.info(f"save_create starting raw data size={len(raw_data)}, created app report model.")
    app_report: ApplicationReport = ApplicationReport.create_from_json(request_json)
    logger.info("save_create saving file data to doc storage...")
    doc_link: str = save_to_doc_storage(app_report, raw_data)
    app_report.save()
    report_json = app_report.json
    report_json["url"] = doc_link
    logger.info("save_create completed...")
    return report_json


def get_report_link(app_report: ApplicationReport) -> dict:
    """Generate the report download URL link for the app report."""
    report_json: dict = app_report.json
    storage_type: str = resource_utils.STORAGE_TYPE_DEFAULT.value
    storage_name: str = app_report.doc_storage_url
    if storage_name:
        logger.info(f"getting link for type={storage_type} name={storage_name}...")
        doc_link = GoogleStorageService.get_document_link(storage_name, storage_type, 2)
        report_json["url"] = doc_link
    return report_json


def get_report_data(app_report: ApplicationReport):
    """Retrieve the report binary data for the app report."""
    storage_type: str = resource_utils.STORAGE_TYPE_DEFAULT.value
    storage_name: str = app_report.doc_storage_url
    if storage_name:
        logger.info(f"getting report data for type={storage_type} name={storage_name}...")
        rep_data = GoogleStorageService.get_document(storage_name, storage_type)
        logger.info(f"Retrieved {storage_name} report data length={len(rep_data)}.")
    return rep_data


def get_report_links(reports_json: list, product_code: str) -> list:
    """Generate the report download URL links for the list of app reports."""
    storage_type: str = resource_utils.TO_PRODUCT_STORAGE_TYPE.get(product_code)
    if not storage_type:
        storage_type = resource_utils.STORAGE_TYPE_DEFAULT.value
    for report_json in reports_json:
        storage_name: str = report_json.get("url")
        if storage_name:
            logger.info(f"getting link for type={storage_type} name={storage_name}...")
            doc_link = GoogleStorageService.get_document_link(storage_name, storage_type, 2)
            report_json["url"] = doc_link
    return reports_json
