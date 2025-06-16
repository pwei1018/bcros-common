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

"""Tests to verify the PDF file data conversion service.

Test-Suite to ensure that the PDF convert service is working as expected.
"""
import json
from http import HTTPStatus

import doc_api.models.utils as model_utils
from doc_api.services.pdf_convert import PdfConvert
from doc_api.utils.logging import logger

CONVERT_TEST_JPG = "tests/unit/services/data/test-image.jpg"
CONVERT_TEST_JPG_OUT = "tests/unit/services/data/test-image-jpg.pdf"
CONVERT_TEST_CSV = "tests/unit/services/data/test-csv.csv"
CONVERT_TEST_CSV_OUT = "tests/unit/services/data/test-csv.pdf"
CONVERT_TEST_PNG = "tests/unit/services/data/test-image.png"
CONVERT_TEST_PNG_OUT = "tests/unit/services/data/test-image-png.pdf"
CONVERT_TEST_DOCX = "tests/unit/services/data/test-doc.docx"
CONVERT_TEST_DOCX_OUT = "tests/unit/services/data/test-docx.pdf"
CONVERT_TEST_XLSX = "tests/unit/services/data/test-xlsx.xlsx"
CONVERT_TEST_XLSX_OUT = "tests/unit/services/data/test-xlsx.pdf"
CONVERT_TEST_PDF = "tests/unit/services/data/test-in-pdf.pdf"
CONVERT_TEST_PDF_OUT = "tests/unit/services/data/test-out-pdf.pdf"
CONVERT_TEST_SVG = "tests/unit/services/data/test-image.svg"
CONVERT_TEST_SVG_OUT = "tests/unit/services/data/test-image-svg.pdf"
CONVERT_TEST_TIF = "tests/unit/services/data/test-image.tif"
CONVERT_TEST_TIF_OUT = "tests/unit/services/data/test-image-tif.pdf"
CONVERT_TEST_GIF = "tests/unit/services/data/test-image.gif"
CONVERT_TEST_GIF_OUT = "tests/unit/services/data/test-image-gif.pdf"
CONVERT_TEST_TXT = "tests/unit/services/data/test-text.txt"
CONVERT_TEST_TXT_OUT = "tests/unit/services/data/test-text-txt.pdf"
CONVERT_TEST_PPTX = "tests/unit/services/data/test-pptx.pptx"
CONVERT_TEST_PPTX_OUT = "tests/unit/services/data/test-pptx.pdf"


def test_convert_pptx(session, client, jwt):
    """Assert that converting a test pptx file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_PPTX)
    pdf_converter = PdfConvert(doc_data, "test-pptx.pptx", model_utils.CONTENT_TYPE_PPTX)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_PPTX_OUT)


def test_convert_txt(session, client, jwt):
    """Assert that converting a test txt file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_TXT)
    pdf_converter = PdfConvert(doc_data, "test-text.txt", model_utils.CONTENT_TYPE_TEXT)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_TXT_OUT)


def test_convert_gif(session, client, jwt):
    """Assert that converting a test gif file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_GIF)
    pdf_converter = PdfConvert(doc_data, "test-image.gif", model_utils.CONTENT_TYPE_GIF)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_GIF_OUT)


def test_convert_tif(session, client, jwt):
    """Assert that converting a test tiff file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_TIF)
    pdf_converter = PdfConvert(doc_data, "test-image.tif", model_utils.CONTENT_TYPE_TIFF)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_TIF_OUT)


def test_convert_svg(session, client, jwt):
    """Assert that converting a test svg file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_SVG)
    pdf_converter = PdfConvert(doc_data, "test-image.svg", model_utils.CONTENT_TYPE_SVG)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_SVG_OUT)


def test_convert_jpg(session, client, jwt):
    """Assert that converting a test jpg file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_JPG)
    pdf_converter = PdfConvert(doc_data, "test-image.jpg", model_utils.CONTENT_TYPE_JPEG)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_JPG_OUT)


def test_convert_csv(session, client, jwt):
    """Assert that converting a test csv file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_CSV)
    pdf_converter = PdfConvert(doc_data, "test-csv.csv", model_utils.CONTENT_TYPE_CSV)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_CSV_OUT)


def test_convert_png(session, client, jwt):
    """Assert that converting a test png file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_PNG)
    pdf_converter = PdfConvert(doc_data, "test-image.png", model_utils.CONTENT_TYPE_PNG)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_PNG_OUT)


def test_convert_docx(session, client, jwt):
    """Assert that converting a test docx file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_DOCX)
    pdf_converter = PdfConvert(doc_data, "test-doc.docx", model_utils.CONTENT_TYPE_WORDX)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_DOCX_OUT)


def test_convert_xlsx(session, client, jwt):
    """Assert that converting a test excel file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_XLSX)
    pdf_converter = PdfConvert(doc_data, "test-xlsx.xlsx", model_utils.CONTENT_TYPE_EXCELX)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_XLSX_OUT)


def test_convert_pdf(session, client, jwt):
    """Assert that converting a test pdf file to pdf is as expected."""
    # setup
    doc_data = get_convert_file(CONVERT_TEST_PDF)
    pdf_converter = PdfConvert(doc_data, "test-pdf.pdf", model_utils.CONTENT_TYPE_PDF)
    # test
    content, status, headers = pdf_converter.convert()
    assert headers
    # verify
    check_response(content, status, CONVERT_TEST_PDF_OUT)

def get_convert_file(data_file: str):
    """Get binary data from report data file."""
    binary_data = None
    with open(data_file, "rb") as data_file:
        binary_data = data_file.read()
        data_file.close()
    return binary_data

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
