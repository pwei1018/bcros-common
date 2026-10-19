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
from doc_api.resources.utils import get_certified_copy_config, get_form_stamp_config
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
CERT_COPY_TEST_AR_LEGACY_INFILE = "tests/unit/reports/data/legacy-conv-ar-filing.pdf"
CERT_COPY_TEST_AR_LEGACY_OUTFILE = "tests/unit/reports/data/legacy-conv-ar-filing-updated.pdf"
CERT_COPY_TEST_COOP_INFILE = "tests/unit/reports/data/coop-mem-filing-1.pdf"
CERT_COPY_TEST_COOP_OUTFILE = "tests/unit/reports/data/coop-mem-filing-ex1.pdf"
CERT_COPY_TEST_COOP_STAFF_INFILE = "tests/unit/reports/data/coop-rules-filing-staff-1.pdf"
CERT_COPY_TEST_COOP_STAFF_OUTFILE = "tests/unit/reports/data/coop-rules-filing-staff-ex1.pdf"
CERT_COPY_TEST_COOP_STAFF_INFILE2 = "tests/unit/reports/data/coop-mem-filing-staff-1.pdf"
CERT_COPY_TEST_COOP_STAFF_OUTFILE2 = "tests/unit/reports/data/coop-mem-filing-staff-ex1.pdf"
CERT_COPY_TEST_FORM_INFILE = "tests/unit/reports/data/form47-correction.pdf"
CERT_COPY_TEST_FORM_OUTFILE = "tests/unit/reports/data/form-stamp-{doc_type}.pdf"


# testdata pattern is ({legacy}, {conversion}, {infile}, {outfile})
TEST_CERT_COPY_DATA = [
    (True, False, CERT_COPY_TEST_NOA_LEGACY_INFILE, CERT_COPY_TEST_NOA_LEGACY_OUTFILE),
    (True, False, CERT_COPY_TEST_FILING_LEGACY_INFILE, CERT_COPY_TEST_FILING_LEGACY_OUTFILE),
    (True, True, CERT_COPY_TEST_AR_LEGACY_INFILE, CERT_COPY_TEST_AR_LEGACY_OUTFILE),
]
# testdata pattern is ({doc_class}, {doc_type}, {infile}, {outfile})
TEST_DOC_CERT_COPY_DATA = [
    ("COOP", "COOP_MEMORANDUM", CERT_COPY_TEST_COOP_INFILE, CERT_COPY_TEST_COOP_OUTFILE),
    ("COOP", "COOP_RULES", CERT_COPY_TEST_COOP_STAFF_INFILE, CERT_COPY_TEST_COOP_STAFF_OUTFILE),
    ("COOP", "COOP_MEMORANDUM", CERT_COPY_TEST_COOP_STAFF_INFILE2, CERT_COPY_TEST_COOP_STAFF_OUTFILE2),
]
# testdata pattern is ({doc_class}, {doc_type}, {infile}, {outfile})
TEST_DOC_FORM_STAMP_DATA = [
    ("CORP", "APCO", CERT_COPY_TEST_FORM_INFILE, CERT_COPY_TEST_FORM_OUTFILE),
    ("CORP", "JUNK", CERT_COPY_TEST_FORM_INFILE, CERT_COPY_TEST_FORM_OUTFILE),
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


@pytest.mark.parametrize("legacy,conversion,infile,outfile", TEST_CERT_COPY_DATA)
def test_add_certified(session, client, jwt, legacy, conversion, infile, outfile):
    """Assert that adding a certified copy image and date and time to an app report works as expected."""
    raw_data = None
    with open(infile, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    updated_pdf = report_utils.add_certified_copy(raw_data, legacy, conversion)
    with open(outfile, "wb") as pdf_file:
        pdf_file.write(updated_pdf)
        pdf_file.close()


@pytest.mark.parametrize("doc_class,doc_type,infile,outfile", TEST_DOC_CERT_COPY_DATA)
def test_doc_add_certified(session, client, jwt, doc_class, doc_type, infile, outfile):
    """Assert that adding a certified copy image and date and time to an client document works as expected."""
    raw_data = None
    certified_config = get_certified_copy_config(doc_class, doc_type)
    if certified_config:
        with open(infile, 'rb') as data_file:
            raw_data = data_file.read()
            data_file.close()

        updated_pdf = report_utils.add_doc_certified_copy(raw_data, certified_config)
        with open(outfile, "wb") as pdf_file:
            pdf_file.write(updated_pdf)
            pdf_file.close()


@pytest.mark.parametrize("doc_class,doc_type,infile,outfile", TEST_DOC_FORM_STAMP_DATA)
def test_doc_add_form_stamp(session, client, jwt, doc_class, doc_type, infile, outfile):
    """Assert that adding a certified copy image and date and time to an client document works as expected."""
    raw_data = None
    stamp_config = get_form_stamp_config(doc_type)
    if stamp_config:
        with open(infile, 'rb') as data_file:
            raw_data = data_file.read()
            data_file.close()

        updated_pdf = report_utils.add_doc_form_stamp(raw_data, stamp_config)
        with open(outfile.format(doc_type=doc_type), "wb") as pdf_file:
            pdf_file.write(updated_pdf)
            pdf_file.close()


def test_add_modern_certified(session, client, jwt):
    """Assert that adding a certified copy image and date and time to an app report works as expected."""
    raw_data = None
    image_data = report_utils.get_certified_copy_image(False)
    infile = CERT_COPY_TEST_NOA_INFILE
    outfile = CERT_COPY_TEST_NOA_OUTFILE
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


def test_add_coop_certified(session, client, jwt):
    """Assert that adding a certified copy image and date and time to an app report works as expected."""
    raw_data = None
    image_data = report_utils.get_certified_copy_image(False)
    # infile = CERT_COPY_TEST_COOP_INFILE
    # outfile = CERT_COPY_TEST_COOP_OUTFILE
    infile = CERT_COPY_TEST_COOP_STAFF_INFILE
    outfile = CERT_COPY_TEST_COOP_STAFF_OUTFILE
    with open(infile, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    doc = pymupdf.Document(stream=raw_data)
    page = doc[0]

    remove_rect = pymupdf.Rect(485.0, 30.0, 560.0, 105.0)
    page.add_redact_annot(remove_rect)
    page.apply_redactions() # This permanently removes the content

    point = pymupdf.Point(483, 78)
    add_text = report_utils.get_app_report_datetime()
    image_rect = pymupdf.Rect(510.0, 10.0, 585.0, 70.0)
    page.insert_text(point, add_text, fontsize=7, fontname="Helvetica-Oblique", color=(0, 0, 0)) # Black color
    page.insert_image(image_rect, stream=image_data)
    updated_pdf = doc.tobytes(garbage=3, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
    doc.close()
    with open(outfile, "wb") as pdf_file:
        pdf_file.write(updated_pdf)
        pdf_file.close()


def test_add_form_stamp(session, client, jwt):
    """Assert that adding a certified copy image and date and time to a new formxx report works as expected."""
    raw_data = None
    image_data = report_utils.get_form_stamp_image()
    infile = CERT_COPY_TEST_FORM_INFILE
    outfile = CERT_COPY_TEST_FORM_OUTFILE
    with open(infile, 'rb') as data_file:
        raw_data = data_file.read()
        data_file.close()
    doc = pymupdf.Document(stream=raw_data)
    page = doc[0]

    point = pymupdf.Point(223, 30)  # pymupdf.Point(483, 78)
    add_text = report_utils.get_form_stamp_date()
    # print(f"stamp date={add_text}")
    image_rect = pymupdf.Rect(205.0, 10.0, 280.0, 50.0) # pymupdf.Rect(510.0, 10.0, 585.0, 70.0)
    page.insert_image(image_rect, stream=image_data)
    page.insert_text(point, add_text, fontsize=6, fontname="Helvetica-Bold", color=(0, 0, 0)) # Black color
    updated_pdf = doc.tobytes(garbage=3, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
    doc.close()
    with open(outfile.format(doc_type="APCO"), "wb") as pdf_file:
        pdf_file.write(updated_pdf)
        pdf_file.close()
