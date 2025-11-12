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
"""Endpoints to check and manage payments."""
import gzip
import json
from http import HTTPStatus

from flask import Response, abort, request, stream_with_context
from flask_restx import Namespace, Resource
from jinja2 import TemplateNotFound

from api.services import CsvService, ReportService
from api.utils.auth import jwt as _jwt


API = Namespace('Reports', description='Service - Reports')


def _parse_request_json():
    """Parse request JSON, handling GZIP decompression if needed."""
    content_encoding = request.headers.get('Content-Encoding', '').lower()
    if content_encoding == 'gzip':
        try:
            compressed_data = request.get_data()
            decompressed_data = gzip.decompress(compressed_data)
            return json.loads(decompressed_data.decode('utf-8'))
        except (gzip.BadGzipFile, json.JSONDecodeError, UnicodeDecodeError) as e:
            abort(HTTPStatus.BAD_REQUEST, f'Failed to decompress or parse GZIP data: {str(e)}')
    return request.get_json()


def _generate_csv_report(request_json):
    """Generate CSV report from request data."""
    report_name = request_json.get('reportName', 'report')
    file_name = f'{report_name}.csv'
    template_vars = request_json.get('templateVars', {})
    if not template_vars.get('columns'):
        return None, file_name
    report = CsvService.create_report(template_vars)
    return report, file_name


def _generate_pdf_report(request_json):
    """Generate PDF report from request data."""
    report_name = request_json.get('reportName', 'report')
    file_name = f'{report_name}.pdf'
    template_vars = request_json['templateVars']
    populate_page_number = bool(request_json.get('populatePageNumber', None))

    if 'templateName' in request_json:
        template_name = request_json['templateName']
        try:
            report = ReportService.create_report_from_stored_template(
                template_name, template_vars, populate_page_number
            )
        except TemplateNotFound:
            abort(HTTPStatus.NOT_FOUND, 'Template not found')
        except ValueError as e:
            abort(HTTPStatus.BAD_REQUEST, str(e))
    elif 'template' in request_json:
        report = ReportService.create_report_from_template(
            request_json['template'], template_vars, populate_page_number
        )
    else:
        report = None

    return report, file_name


def _create_response(report, file_name, content_type):
    """Create streaming HTTP response with report data."""
    if report is None:
        abort(HTTPStatus.BAD_REQUEST, 'Report cannot be generated')

    content_disposition = f'attachment; filename="{file_name}"'  # noqa: E702

    if content_type == 'text/csv':
        response_data = stream_with_context(report)
    else:
        def pdf_generator():
            yield report
        response_data = stream_with_context(pdf_generator())

    return Response(
        response_data,
        mimetype=content_type,
        headers={
            'Content-Disposition': content_disposition
        }
    )


@API.route('')
class Report(Resource):
    """Payment endpoint resource."""

    @staticmethod
    def get():
        """Get Status of the report service."""
        return {'message': 'Report generation up and running'}, HTTPStatus.OK

    @staticmethod
    @_jwt.requires_auth
    def post():
        """Create a report."""
        request_json = _parse_request_json()
        response_content_type = request.headers.get('Accept', 'application/pdf')
        if response_content_type == 'text/csv':
            report, file_name = _generate_csv_report(request_json)
        else:
            report, file_name = _generate_pdf_report(request_json)
        return _create_response(report, file_name, response_content_type)
