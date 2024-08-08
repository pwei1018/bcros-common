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
"""API endpoints for requests to maintain PPR documents."""
from http import HTTPStatus

from flask import Blueprint
from flask import request
from doc_api.exceptions import BusinessException, DatabaseException
from doc_api.models import Document, DocumentClass, DocumentRequest, utils as model_utils
from doc_api.models.type_tables import RequestTypes
from doc_api.reports import get_pdf
from doc_api.reports.report_utils import ReportTypes
from doc_api.resources import utils as resource_utils
from doc_api.services.authz import is_staff
from doc_api.services.utils.exceptions import ReportException, ReportDataException
from doc_api.utils.auth import jwt
from doc_api.utils.logging import logger


GET_DOC_RECORD_PATH = '/reports/document-records/{consumer_document_id}'

bp = Blueprint('REPORTS1',  # pylint: disable=invalid-name
               __name__, url_prefix='/reports')


@bp.route('/document-records/<string:consumer_document_id>', methods=['GET', 'OPTIONS'])
@jwt.requires_auth
def get_doc_record_reports(consumer_document_id: str):
    """Retrieve a document service document record report by consumer document ID."""
    account_id = ''
    try:
        req_path: str = GET_DOC_RECORD_PATH.format(consumer_document_id=consumer_document_id)
        account_id = resource_utils.get_account_id(request)
        if account_id is None:
            return resource_utils.account_required_response()
        logger.info(f'Starting new get document record report request {req_path}, account={account_id}')
        if not is_staff(jwt):
            logger.error('User not staff: currently requests are staff only.')
            return resource_utils.unauthorized_error_response(account_id)
        report_json = get_doc_record_json(consumer_document_id)
        logger.info(report_json)
        if not report_json:
            logger.warning(f'No documents found for consumer document id={consumer_document_id}.')
            return resource_utils.not_found_error_response('Documents information', consumer_document_id)
        return get_report(req_path, consumer_document_id, account_id, report_json)
    except DatabaseException as db_exception:
        return resource_utils.db_exception_response(db_exception, account_id,
                                                    'POST PPR doc id=' + account_id)
    except BusinessException as exception:
        return resource_utils.business_exception_response(exception)
    except Exception as default_exception:   # noqa: B902; return nicer default error
        return resource_utils.default_exception_response(default_exception)


def get_doc_record_json(consumer_doc_id: str) -> dict:
    """Get document information by consumer document id and build report json."""
    report_json = {}
    results = []
    if not consumer_doc_id:
        return report_json
    results = Document.find_by_document_id(consumer_doc_id)
    if results:
        upload_count: int = 0
        documents = []
        document_id: int = 0
        for result in results:
            if result.doc_storage_url:
                upload_count += 1
            if document_id == 0:
                document_id = result.id
            documents.append(result.json)
        if documents[0].get('documentClass'):
            doc_class: DocumentClass = DocumentClass.find_by_doc_class(documents[0].get('documentClass'))
            if doc_class:
                report_json['documentClassDescription'] = doc_class.document_class_desc
        report_json['documentId'] = document_id
        report_json['consumerDocumentId'] = documents[0].get('consumerDocumentId')
        report_json['consumerIdentifier'] = documents[0].get('consumerIdentifier', '')
        report_json['createDateTime'] = documents[0].get('createDateTime')
        report_json['consumerFilingDateTime'] = documents[0].get('consumerFilingDateTime', '')
        report_json['documentClass'] = documents[0].get('documentClass', '')
        report_json['documentType'] = documents[0].get('documentType', '')
        report_json['documentTypeDescription'] = documents[0].get('documentTypeDescription', '')
        report_json['uploadCount'] = upload_count
        report_json['documents'] = documents
    return report_json


def get_report(request_path: str, consumer_doc_id: str, account_id: str, report_json: dict):
    """Generate a report and track the status in document_requests."""
    report_json['requestPath'] = request_path
    doc_request: DocumentRequest = DocumentRequest(request_ts=model_utils.now_ts(),
                                                   account_id=account_id,
                                                   request_type=RequestTypes.GET.value,
                                                   document_id=report_json.get('documentId'),
                                                   request_data=report_json)
    try:
        raw_data, status, content_type = get_pdf(report_json, account_id, ReportTypes.DOC_RECORD)
        doc_request.status = status
        doc_request.save()
        return raw_data, status, content_type
    except ReportDataException as data_err:
        doc_request.status = HTTPStatus.INTERNAL_SERVER_ERROR
        err_msg: str = f'GET document record report generation failed (data error): doc id={consumer_doc_id}. '
        doc_request.status_message = err_msg
        doc_request.save()
        return resource_utils.report_exception_response(data_err, err_msg)
    except ReportException as report_err:
        doc_request.status = HTTPStatus.INTERNAL_SERVER_ERROR
        err_msg: str = f'GET document record report generation failed: doc id={consumer_doc_id}. '
        doc_request.status_message = err_msg
        doc_request.save()
        return resource_utils.report_exception_response(report_err, err_msg)
