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
"""Report helper function tests."""
import json

import pytest

from doc_api.reports import report_utils
from doc_api.reports.report import Report
from doc_api.reports.report_utils import ReportTypes
from doc_api.utils.logging import logger

TEST_DATAFILE = "tests/unit/reports/data/doc-record-test-example.json"
# testdata pattern is ({test_ts}, {is_timetsamp}, {expected})
TEST_DATA_DATE_FORMAT = [
    ("2024-08-01T19:00:00+00:00", False, "August 1, 2024"),
    ("2024-08-01T19:00:00+00:00", True, "August 1, 2024 at 12:00:00 pm Pacific time"),
    ("2024-08-20T17:20:20+00:00", True, "August 20, 2024 at 10:20:20 am Pacific time"),
    ("2024-12-01T20:00:00+00:00", True, "December 1, 2024 at 12:00:00 pm Pacific time"),
    ("2024-12-05T18:20:20+00:00", True, "December 5, 2024 at 10:20:20 am Pacific time"),
    ("2024-12-20T01:30:30+00:00", True, "December 19, 2024 at 5:30:30 pm Pacific time"),
]
# testdata pattern is ({filename}, {legacy})
TEST_LEGACY_REPORT_FILENAME = [
    ("BC1191518-ICORP-FILING.pdf", True),
    ("BC1191518-ICORP-RECEIPT.pdf", True),
    ("BC1191518-ICORP-NOA.pdf", True),
    ("BC1191518-ICORP-CERT.pdf", True),
    ("changeOfAddress", False),
    ("BC1191518-annualReport-FILING.pdf", False),
    ("BC1191518-ANNBC.pdf", False),
    ("BC1191518-NOA-annualReport.pdf", False),
    ("BC1191518-FILING-annualReport.pdf", False),
    ("BC1191518-CERT-annualReport.pdf", False),
    ("BC1191518-RECEIPT-annualReport.pdf", False),
]


@pytest.mark.parametrize("filename, is_legacy", TEST_LEGACY_REPORT_FILENAME)
def test_is_legacy_report(session, filename, is_legacy):
    """Assert that determing if a report is legacy works as expected."""
    assert is_legacy == report_utils.is_legacy_report(filename)


@pytest.mark.parametrize("test_ts,is_timestamp,expected", TEST_DATA_DATE_FORMAT)
def test_report_date_format(session, test_ts, is_timestamp, expected):
    """Assert that report date/timstamp formatting works as expected."""
    formatted = report_utils.to_report_datetime(test_ts, is_timestamp)
    assert formatted == expected


def test_get_header_data(session):
    """Assert that getting the report header data works as expected."""
    # setup
    title = "Test Title"
    # test
    data = report_utils.get_header_data(title)
    # verify
    assert data
    assert data.find(title) != -1


def test_get_footer_data(session):
    """Assert that getting the report footer data works as expected."""
    # setup
    text = "Test Text"
    # test
    data = report_utils.get_footer_data(text)
    # verify
    assert data
    assert data.find(text) != -1


def test_get_report_meta_data(session):
    """Assert that getting the report generaton meta data works as expected."""
    data = report_utils.get_report_meta_data()
    assert data
    assert data.get("marginTop")
    assert data.get("marginBottom")
    assert data.get("marginLeft")
    assert data.get("marginRight")
    assert data.get("printBackground")


def test_get_html_from_data(session):
    """Assert that getting the report source html from report data works as expected."""
    json_data = get_json_from_file(TEST_DATAFILE)
    report = Report(json_data, "PS12345", ReportTypes.DOC_RECORD)
    request_data = report._setup_report_data()
    html_data = report_utils.get_html_from_data(request_data)
    assert html_data
    logger.info("html_data length=" + str(len(html_data)))


def test_get_report_files(session):
    """Assert that getting the report source files from report data works as expected."""
    json_data = get_json_from_file(TEST_DATAFILE)
    report = Report(json_data, "PS12345", ReportTypes.DOC_RECORD)
    request_data = report._setup_report_data()
    files = report_utils.get_report_files(request_data, ReportTypes.DOC_RECORD)
    assert files
    assert files.get("index.html")
    assert files.get("header.html")
    assert files.get("footer.html")
    logger.info("file body length=" + str(len(files.get("index.html"))))
    logger.info("file header length=" + str(len(files.get("header.html"))))
    logger.info("file footer length=" + str(len(files.get("footer.html"))))


def get_json_from_file(data_file: str):
    """Get json data from report data file."""
    text_data = None
    with open(data_file, "r") as data_file:
        text_data = data_file.read()
        data_file.close()
    # print(text_data)
    json_data = json.loads(text_data)
    return json_data
