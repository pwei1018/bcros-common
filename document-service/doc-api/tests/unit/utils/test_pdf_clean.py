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

"""Tests to verify the pdf_clean function.

Test-Suite to ensure that cleaning pdf file data is working as expected.
"""

from doc_api.models import utils as model_utils
from doc_api.services.pdf_convert import MediaTypes, PdfConvert
from doc_api.utils.pdf_clean import clean_pdf, get_pdf_form_fields
from doc_api.utils.logging import logger


CLEAN_TEST_PDF = "tests/unit/services/data/test-in-pdf.pdf"
CLEAN_TEST_PDF_OUT = "tests/unit/services/data/test-out-pdf-clean.pdf"
CLEAN_TEST_PDF_FORM = "tests/unit/services/data/test-in-pdf-form.pdf"
CLEAN_TEST_PDF_FORM_OUT = "tests/unit/services/data/test-out-pdf-form-clean.pdf"
CLEAN_TEST_JPG = "tests/unit/services/data/test-image.jpg"
CLEAN_TEST_JPG_OUT = "tests/unit/services/data/test-image-jpg-clean.pdf"
CLEAN_TEST_PPTX = "tests/unit/services/data/test-pptx.pptx"
CLEAN_TEST_PPTX_OUT = "tests/unit/services/data/test-pptx-clean.pdf"


def test_clean_pdf(session, client, jwt):
    """Assert that cleaning a test pdf file is as expected."""
    # setup
    doc_data = get_file(CLEAN_TEST_PDF)
    # test
    cleaned_pdf = clean_pdf(doc_data)
    # verify
    check_response(cleaned_pdf, CLEAN_TEST_PDF_OUT)


def test_clean_pdf_form(session, client, jwt):
    """Assert that cleaning a test pdf form file is as expected."""
    # setup
    doc_data = get_file(CLEAN_TEST_PDF_FORM)
    # test
    fields: dict = get_pdf_form_fields(doc_data)
    logger.info(f"Found form fields {fields}")
    cleaned_pdf = clean_pdf(doc_data)
    # verify
    check_response(cleaned_pdf, CLEAN_TEST_PDF_FORM_OUT)


def test_clean_pdf_image(session, client, jwt):
    """Assert that cleaning a test image file is as expected."""
    # setup
    doc_data = get_file(CLEAN_TEST_JPG)
    # test
    pdf_converter = PdfConvert(doc_data, "test-image.jpg", model_utils.CONTENT_TYPE_JPEG)
    # test
    pdf_data, status, headers = pdf_converter.convert()
    assert headers    
    cleaned_pdf = clean_pdf(pdf_data)
    # verify
    check_response(cleaned_pdf, CLEAN_TEST_JPG_OUT)


def test_clean_pdf_pptx(session, client, jwt):
    """Assert that cleaning a test pptx file is as expected."""
    # setup
    doc_data = get_file(CLEAN_TEST_PPTX)
    # test
    pdf_converter = PdfConvert(doc_data, "test-pptx.pptx", MediaTypes.CONTENT_TYPE_PPTX.value)
    # test
    pdf_data, status, headers = pdf_converter.convert()
    assert headers    
    cleaned_pdf = clean_pdf(pdf_data)
    # verify
    check_response(cleaned_pdf, CLEAN_TEST_PPTX_OUT)


def check_response(content, filename: str = None):
    """Assert that the response is as expected."""
    assert content
    if filename:
        with open(filename, "wb") as pdf_file:
            pdf_file.write(content)
            pdf_file.close()
    logger.info("Cleaned PDF saved.")


def get_file(data_file: str):
    """Get binary data from report data file."""
    binary_data = None
    with open(data_file, "rb") as data_file:
        binary_data = data_file.read()
        data_file.close()
    return binary_data
