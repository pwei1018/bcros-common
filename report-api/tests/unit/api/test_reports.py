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


"""Tests to assure the Template.

Test suite for reports
"""

import base64
import gzip
import json

from .base_test import get_claims, token_header
from api.services import report_service


def test_get_generate(client):
    """Status check."""
    rv = client.get('/api/v1/reports')
    assert rv.status_code == 200


def test_generate_report_with_existing_template(client, jwt, app, mock_gotenberg_requests):
    """Generate PDF via Gotenberg with stored template (mocked call)."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}

    request_url = '/api/v1/reports'
    request_data = {
        'templateName': 'invoice',
        'templateVars': {'title': 'This is a sample request'},
        'reportName': 'sample'
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 200
    assert rv.content_type == 'application/pdf'


def test_generate_report_with_invalid_template(client, jwt, app):
    """Call to generate report with invalid template."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}

    request_url = '/api/v1/reports'
    request_data = {
        'templateName': 'some-really-random-values',
        'templateVars': {
            'title': 'This is a sample request'
        },
        'reportName': 'sample'
    }
    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 404


def test_generate_report_with_template(client, jwt, app):
    """Call to generate report with new template."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
    template = '<html><body><h1>Sample Report</h1><h2>{{ title }}</h2></body></html>'
    template = base64.b64encode(bytes(template, 'utf-8')).decode('utf-8')
    request_url = '/api/v1/reports'
    request_data = {
        'template': template,
        'templateVars': {
            'title': 'This is a sample request'
        },
        'reportName': 'Test Report'
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 200
    assert rv.content_type == 'application/pdf'


def test_generate_report_with_page_number(client, jwt, app):
    """Call to generate report with new template."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
    template = '<html><body><h1>Sample Report</h1><h2>{{ title }}</h2></body></html>'
    template = base64.b64encode(bytes(template, 'utf-8')).decode('utf-8')
    request_url = '/api/v1/reports'
    request_data = {
        'template': template,
        'templateVars': {
            'title': 'This is a sample request'
        },
        'reportName': 'Test Report',
        'populatePageNumber': 'true'
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 200
    assert rv.content_type == 'application/pdf'


def test_generate_report_with_invalid_request(client, jwt, app):
    """Call to generate report with invalid request."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
    request_url = '/api/v1/reports'
    request_data = {
        'templateVars': {
            'title': 'This is a sample request'
        },
        'reportName': 'Test Report'
    }
    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 400


def test_csv_report(client, jwt, app):
    """Call to generate report with invalid request."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {
        'Authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'Accept': 'text/csv'
    }
    request_url = '/api/v1/reports'
    request_data = {
        'reportName': 'test',
        'templateVars': {
            'columns': [
                'a',
                'b',
                'c'
            ],
            'values': [
                [
                    '1',
                    '2',
                    '3'
                ],
                [
                    '4',
                    '5',
                    '6'
                ]
            ]
        }
    }
    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 200


def test_csv_report_with_invalid_request(client, jwt, app):
    """Call to generate report with invalid request."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {
        'Authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'Accept': 'text/csv'
    }
    request_url = '/api/v1/reports'
    request_data = {
        'reportName': 'test',
        'templateVars': {

        }
    }
    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 400


def _inline_tpl():
    html = '<html><body>ok</body></html>'
    return base64.b64encode(html.encode('utf-8')).decode('utf-8')


def test_statement_grouped_invoices(client, jwt, app, monkeypatch):
    """Test statement grouped invoices."""
    monkeypatch.setattr(
        report_service.ChunkReportService,
        '_build_chunk_html',
        staticmethod(lambda *a, **k: '<html><body>ok</body></html>')
    )

    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
    data = {
        'template': _inline_tpl(),
        'templateVars': {
            'grouped_invoices': [{'transactions': [1]}],
            'reportName': 'statement_report',
        },
        'reportName': 'statement_report',
    }
    resp = client.post('/api/v1/reports', data=json.dumps(data), headers=headers)
    assert resp.status_code == 200
    assert resp.content_type == 'application/pdf'


def test_response_is_streaming(client, jwt, app, mock_gotenberg_requests):
    """Verify that PDF response is streaming (no Content-Length header set)."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}

    request_url = '/api/v1/reports'
    request_data = {
        'templateName': 'invoice',
        'templateVars': {'title': 'This is a sample request'},
        'reportName': 'sample'
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 200
    assert rv.content_type == 'application/pdf'
    assert 'Content-Disposition' in rv.headers
    assert 'attachment' in rv.headers['Content-Disposition']
    assert 'Content-Length' not in rv.headers
    assert len(rv.data) > 0
    assert rv.data.startswith(b'%PDF')


def test_csv_response_is_streaming(client, jwt, app):
    """Verify that CSV response is streaming."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {
        'Authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'Accept': 'text/csv'
    }
    request_url = '/api/v1/reports'
    request_data = {
        'reportName': 'test',
        'templateVars': {
            'columns': ['a', 'b', 'c'],
            'values': [['1', '2', '3'], ['4', '5', '6']]
        }
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 200
    assert rv.content_type.startswith('text/csv')
    assert 'Content-Disposition' in rv.headers
    assert 'attachment' in rv.headers['Content-Disposition']
    assert 'Content-Length' not in rv.headers
    assert len(rv.data) > 0
    assert b'a,b,c' in rv.data or b'a,b,c\r\n' in rv.data


def test_gzip_request_compression(client, jwt, app, mock_gotenberg_requests):
    """Verify that GZIP compressed request body is properly decompressed and processed."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)

    request_url = '/api/v1/reports'
    request_data = {
        'templateName': 'invoice',
        'templateVars': {'title': 'This is a GZIP compressed request'},
        'reportName': 'gzip_test'
    }

    json_data = json.dumps(request_data).encode('utf-8')
    compressed_data = gzip.compress(json_data)

    headers = {
        'Authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'Content-Encoding': 'gzip'
    }

    rv = client.post(
        request_url,
        data=compressed_data,
        headers=headers
    )

    assert rv.status_code == 200
    assert rv.content_type == 'application/pdf'
    assert len(rv.data) > 0


def test_gzip_request_compression_csv(client, jwt, app):
    """Verify that GZIP compressed request body works for CSV reports."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)

    request_url = '/api/v1/reports'
    request_data = {
        'reportName': 'gzip_csv_test',
        'templateVars': {
            'columns': ['col1', 'col2'],
            'values': [['val1', 'val2']]
        }
    }

    json_data = json.dumps(request_data).encode('utf-8')
    compressed_data = gzip.compress(json_data)

    headers = {
        'Authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'Content-Encoding': 'gzip',
        'Accept': 'text/csv'
    }

    rv = client.post(
        request_url,
        data=compressed_data,
        headers=headers
    )

    assert rv.status_code == 200
    assert rv.content_type.startswith('text/csv')
    assert len(rv.data) > 0
    assert b'col1' in rv.data or b'col1,col2' in rv.data


def test_gzip_request_invalid_compression(client, jwt, app):
    """Verify that invalid GZIP data returns appropriate error."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)

    request_url = '/api/v1/reports'
    invalid_compressed_data = b'not valid gzip data'

    headers = {
        'Authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'Content-Encoding': 'gzip'
    }

    rv = client.post(
        request_url,
        data=invalid_compressed_data,
        headers=headers
    )

    assert rv.status_code == 400
    response_data = rv.get_json()
    assert response_data is not None
    assert 'message' in response_data
    assert 'Failed to decompress' in response_data['message']


def test_template_name_sanitization(client, jwt, app, mock_gotenberg_requests):
    """Verify that template names are sanitized to prevent path traversal attacks."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}

    request_url = '/api/v1/reports'

    request_data = {
        'templateName': '../../etc/passwd',
        'templateVars': {'title': 'Test'},
        'reportName': 'test'
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 400
    response_data = rv.get_json()
    assert response_data is not None
    assert 'message' in response_data
    message_lower = response_data['message'].lower()
    assert 'invalid path characters' in message_lower or 'path traversal' in message_lower


def test_template_name_sanitization_invalid_chars(client, jwt, app, mock_gotenberg_requests):
    """Verify that template names with invalid characters are sanitized."""
    token = jwt.create_jwt(get_claims(app_request=app), token_header)
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}

    request_url = '/api/v1/reports'

    request_data = {
        'templateName': 'invoice<script>alert(1)</script>',
        'templateVars': {'title': 'Test'},
        'reportName': 'test'
    }

    rv = client.post(request_url, data=json.dumps(request_data), headers=headers)
    assert rv.status_code == 400
