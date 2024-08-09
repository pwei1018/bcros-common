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
"""API endpoints for requests to maintain name request (NR) documents."""

from http import HTTPStatus

from flask import Blueprint
from flask import g, request, jsonify
from doc_api.utils.auth import jwt
from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.services.authz import is_staff
from doc_api.models.type_tables import RequestTypes, DocumentClasses
from doc_api.services.abstract_storage_service import DocumentTypes as StorageDocTypes
from doc_api.resources import utils as resource_utils
from doc_api.resources.request_info import RequestInfo
from doc_api.utils.logging import logger

POST_REQUEST_PATH = '/nro/{doc_type}'
GET_REQUEST_PATH = '/nro'
DOC_STORAGE_TYPE = StorageDocTypes.NR.value
DOCUMENT_CLASS = DocumentClasses.NR.value

bp = Blueprint('NAMEREQUEST1',  # pylint: disable=invalid-name
               __name__, url_prefix='/nro')


@bp.route('/<string:doc_type>', methods=['POST', 'OPTIONS'])
@jwt.requires_auth
def post_name_request_docs(doc_type: str):  # pylint: disable=too-many-return-statements
    """Save a new name request document."""
    account_id = ''
    try:
        req_path: str = POST_REQUEST_PATH.format(doc_type=doc_type)
        info: RequestInfo = RequestInfo(RequestTypes.ADD, req_path, doc_type, DOC_STORAGE_TYPE)
        info = resource_utils.get_request_info(request, info, is_staff(jwt))
        info.document_class = DOCUMENT_CLASS
        logger.info(f'Starting new name request doc request {req_path}, account={info.account_id}')
        if not info.account_id:
            return resource_utils.account_required_response()
        account_id = info.account_id
        if not is_staff(jwt):
            logger.error('User not staff: currently requests are staff only.')
            return resource_utils.unauthorized_error_response(account_id)
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != '':
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        response_json = resource_utils.save_add(info, g.jwt_oidc_token_info, request.get_data())
        return jsonify(response_json), HTTPStatus.CREATED
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id,
                                                    'POST nr doc id=' + account_id)
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:   # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


@bp.route('', methods=['GET', 'OPTIONS'])
@jwt.requires_auth
def get_name_request_docs():
    """Get name request documents matching the query parameters."""
    try:
        req_path: str = GET_REQUEST_PATH
        info: RequestInfo = RequestInfo(RequestTypes.GET, req_path, None, DOC_STORAGE_TYPE)
        info = resource_utils.get_request_info(request, info, is_staff(jwt))
        info.document_class = DOCUMENT_CLASS
        logger.info(f'Starting get name request docs request {req_path}, account={info.account_id}')
        if not info.account_id:
            return resource_utils.account_required_response()
        account_id = info.account_id
        if not is_staff(jwt):
            logger.error('User not staff: currently requests are staff only.')
            return resource_utils.unauthorized_error_response(account_id)
        # Additional validation not covered by the schema.
        extra_validation_msg = resource_utils.validate_request(info)
        if extra_validation_msg != '':
            return resource_utils.extra_validation_error_response(extra_validation_msg)
        response_json = resource_utils.get_docs(info)
        if not response_json:
            req_json = info.json
            logger.info(f'No name request documents found for request {req_json}.')
            return resource_utils.not_found_error_response('name request documents information', account_id)
        return jsonify(response_json), HTTPStatus.OK
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id, 'GET name request info')
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:   # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)
