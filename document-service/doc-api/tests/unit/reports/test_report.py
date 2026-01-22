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
import json
import pymupdf
from http import HTTPStatus

import pytest

from doc_api.reports.report import Report, report_utils
from doc_api.reports.report_utils import ReportTypes
from doc_api.utils.logging import logger

DOC_RECORD_TEST_DATAFILE = "tests/unit/reports/data/doc-record-test-example.json"
DOC_RECORD_TEST_PDFFILE = "tests/unit/reports/data/doc-record-test-example.pdf"
CERT_COPY_TEST_NOA_LEGACY_INFILE = "tests/unit/reports/data/legacy-noa.pdf"
CERT_COPY_TEST_NOA_LEGACY_OUTFILE = "tests/unit/reports/data/legacy-noa-updated.pdf"
CERT_COPY_TEST_FILING_LEGACY_INFILE = "tests/unit/reports/data/legacy-filing.pdf"
CERT_COPY_TEST_FILING_LEGACY_OUTFILE = "tests/unit/reports/data/legacy-filing-updated.pdf"
CERT_COPY_TEST_NOA_INFILE = "tests/unit/reports/data/noa.pdf"
CERT_COPY_TEST_NOA_OUTFILE = "tests/unit/reports/data/noa-updated.pdf"
CERT_COPY_TEST_FILING_INFILE = "tests/unit/reports/data/filing.pdf"
CERT_COPY_TEST_FILING_OUTFILE = "tests/unit/reports/data/filing-updated.pdf"

# testdata pattern is ({legacy}, {infile}, {outfile})
TEST_CERT_COPY_DATA = [
    (True, CERT_COPY_TEST_NOA_LEGACY_INFILE, CERT_COPY_TEST_NOA_LEGACY_OUTFILE),
    (True, CERT_COPY_TEST_FILING_LEGACY_INFILE, CERT_COPY_TEST_FILING_LEGACY_OUTFILE),
]


def test_document_record(session, client, jwt):
    """Assert that generation of a test report is as expected."""
    # setup
    json_data = get_json_from_file(DOC_RECORD_TEST_DATAFILE)
    report = Report(json_data, "PS12345", ReportTypes.DOC_RECORD)
    # test
    content, status, headers = report.get_pdf()
    assert headers
    # verify
    check_response(content, status, DOC_RECORD_TEST_PDFFILE)

def get_json_from_file(data_file: str):
    """Get json data from report data file."""
    text_data = None
    with open(data_file, "r") as data_file:
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
        err_content = content.decode("ascii")
        logger.info(f"RS Status code={status_code}. Response: {err_content}.")
    elif filename:
        with open(filename, "wb") as pdf_file:
            pdf_file.write(content)
            pdf_file.close()
    logger.debug("PDF report generation completed.")


def remove_text(session, client, jwt):
    """Assert that setup for a nil result report is as expected."""
    raw_data = None
    test_file = "tests/unit/reports/data/BC1201088-19650133-filing.pdf"
    # noa coordinates = (14.17300033569336, 40.597023010253906, 210.7009735107422, 51.589019775390625)
    # fil coordinated = (14.17300033569336, 40.34001541137695, 235.2669677734375, 52.706016540527344)
    with open(test_file, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    doc = pymupdf.Document(stream=raw_data)
    page = doc[0]
    remove_rect = pymupdf.Rect(14.0, 39.0, 275.0, 53.0)
    page.add_redact_annot(remove_rect)
    page.apply_redactions() # This permanently removes the content
    updated_pdf = doc.tobytes(garbage=3, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
    doc.close()
    with open("tests/unit/reports/data/filing-updated.pdf", "wb") as pdf_file:
        pdf_file.write(updated_pdf)
        pdf_file.close()


@pytest.mark.parametrize("legacy,infile,outfile", TEST_CERT_COPY_DATA)
def test_add_certified(session, client, jwt, legacy, infile, outfile):
    """Assert that adding a certified copy image and date and time to an app report works as expected."""
    raw_data = None
    with open(infile, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    updated_pdf = report_utils.add_certified_copy(raw_data, legacy)
    with open(outfile, "wb") as pdf_file:
        pdf_file.write(updated_pdf)
        pdf_file.close()


def add_modern_certified(session, client, jwt):
    """Assert that adding a certified copy image and date and time to an app report works as expected."""
    raw_data = None
    image_data = report_utils.get_certified_copy_image(False)
    infile = CERT_COPY_TEST_FILING_INFILE
    outfile = CERT_COPY_TEST_FILING_OUTFILE
    # noa coordinates = (14.17300033569336, 40.597023010253906, 210.7009735107422, 51.589019775390625)
    # file coordinates = (14.17300033569336, 40.34001541137695, 235.2669677734375, 52.706016540527344)
    with open(infile, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    doc = pymupdf.Document(stream=raw_data)
    page = doc[0]
    remove_rect = pymupdf.Rect(450.0, 145.0, 600.0, 225.0)
    page.add_redact_annot(remove_rect)
    page.apply_redactions() # This permanently removes the content
    point = pymupdf.Point(433, 210)
    add_text = report_utils.get_app_report_datetime()
    image_rect = pymupdf.Rect(460.0, 142.0, 535.0, 202.0)
    page.insert_text(point, add_text, fontsize=7, fontname="Helvetica-Oblique", color=(0, 0, 0)) # Black color
    page.insert_image(image_rect, stream=image_data)
    updated_pdf = doc.tobytes(garbage=3, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
    doc.close()
    with open(outfile, "wb") as pdf_file:
        pdf_file.write(updated_pdf)
        pdf_file.close()
