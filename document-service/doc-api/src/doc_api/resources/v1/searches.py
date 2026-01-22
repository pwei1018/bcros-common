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
"""API endpoints for searching/querying document information."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models.search_utils import get_search_docs
from doc_api.models.type_tables import RequestTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.services.authz import is_search_authorized, is_staff
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger

GET_REQUEST_PATH = "/searches/{doc_class}"

bp = Blueprint("SEARCHES1", __name__, url_prefix="/searches")  # pylint: disable=invalid-name


@bp.route("/<string:doc_class>", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_searches_by_class(doc_class: str):
    """Get document information by document class for records that match the query parameters."""
    try:
        req_path: str = GET_REQUEST_PATH.format(doc_class=doc_class)

        info: RequestInfo = RequestInfo(
            RequestTypes.GET, req_path, None, resource_utils.get_doc_storage_type(doc_class)
        )
        info = resource_utils.get_request_info(request, info, is_staff(jwt))
        info.document_class = doc_class
        logger.info(f"Starting search request {req_path}, account={info.account_id}")
        if not info.account_id:
            return resource_utils.account_required_response()
        account_id = info.account_id
        if not is_search_authorized(jwt):
            logger.error("User unuauthorized for this endpoint: not staff or service account.")
            return resource_utils.unauthorized_error_response(account_id)
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        response_json = resource_utils.get_docs(info)
        if not response_json:
            req_json = info.json
            logger.info(f"No results found for request {req_json}.")
            return resource_utils.not_found_error_response("search documents information", account_id)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET search for documents info")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route("", methods=["GET", "OPTIONS"])
@jwt.requires_auth
def get_searches():
    """Get document information by any combination of query parameters."""
    try:
        req_path: str = GET_REQUEST_PATH.format(doc_class="*")

        info: RequestInfo = RequestInfo(RequestTypes.GET, req_path, None, None)
        info = resource_utils.get_request_info(request, info, is_staff(jwt))
        logger.info(f"Starting search request {req_path}, account={info.account_id}")
        if not info.account_id:
            return resource_utils.account_required_response()
        account_id = info.account_id
        if not is_staff(jwt):
            logger.error("User not staff: currently requests are staff only.")
            return resource_utils.unauthorized_error_response(account_id)
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != "":
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        response_json = get_search_docs(info)
        if not response_json:
            req_json = info.json
            logger.info(f"No results found for request {req_json}.")
            return resource_utils.not_found_error_response("search documents information", account_id)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, "GET search for documents info")
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:  # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)
