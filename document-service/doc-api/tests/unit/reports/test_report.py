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

"""Tests to verify the V2 registration PDF report setup.

Test-Suite to ensure that the report service registration report is working as expected.
"""
from http import HTTPStatus
import json

from doc_api.reports.report import Report
from doc_api.reports.report_utils import ReportTypes
from doc_api.utils.logging import logger


DOC_RECORD_TEST_DATAFILE = 'tests/unit/reports/data/doc-record-test-example.json'
DOC_RECORD_TEST_PDFFILE = 'tests/unit/reports/data/doc-record-test-example.pdf'


def test_document_record(session, client, jwt):
    """Assert that generation of a test report is as expected."""
    # setup
    json_data = get_json_from_file(DOC_RECORD_TEST_DATAFILE)
    report = Report(json_data, 'PS12345', ReportTypes.DOC_RECORD)
    # test
    content, status, headers = report.get_pdf()
    assert headers
    # verify
    check_response(content, status, DOC_RECORD_TEST_PDFFILE)


def get_json_from_file(data_file: str):
    """Get json data from report data file."""
    text_data = None
    with open(data_file, 'r') as data_file:
        text_data = data_file.read()
        data_file.close()
    # print(text_data)
    json_data = json.loads(text_data)
    return json_data


def check_response(content, status_code, filename: str = None):
    """Assert that report api response is as expected."""
    assert status_code
    assert content
    if status_code != HTTPStatus.OK:
        err_content = content.decode('ascii')
        logger.info(f'RS Status code={status_code}. Response: {err_content}.')
    elif filename:
        with open(filename, "wb") as pdf_file:
            pdf_file.write(content)
            pdf_file.close()
    logger.debug('PDF report generation completed.')
