# Copyright © 2025 Province of British Columbia
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
"""Utility function to clean PDF file data."""
import pymupdf

from doc_api.utils.logging import logger


def clean_pdf_raster(pdf_data: bytes) -> bytes:
    """Clean and compress the PDF data as a new pdf rendered as pages of raster images."""
    try:
        doc = pymupdf.Document(stream=pdf_data)
        new_doc = pymupdf.Document()
        logger.info(f"clean_pdf Document opened, scrubbing in data length={len(pdf_data)}")
        for page in doc.pages():
            new_page = new_doc.new_page()
            new_page.insert_image(rect=page.rect, pixmap=page.get_pixmap())
        cleaned_pdf = new_doc.tobytes(garbage=0, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
        doc.close()
        new_doc.close()
        logger.info(f"clean_pdf completed out data length={len(cleaned_pdf)}")
        return cleaned_pdf
    except Exception as err:  # pylint: disable=broad-except # noqa F841;
        logger.error(f"clean_pdf failed: {err}")
        raise err


def clean_pdf(pdf_data: bytes) -> bytes:
    """Clean and compress the PDF data."""
    try:
        doc = pymupdf.Document(stream=pdf_data)
        logger.info(f"clean_pdf Document opened, scrubbing in data length={len(pdf_data)}")
        for xref in range(1, doc.xref_length()):
            try:
                doc.xref_object(xref)
            except Exception:
                doc.update_object(xref, "<<>>")
        doc.scrub()
        logger.info("clean_pdf Document scrubbed, compressing content")
        cleaned_pdf = doc.tobytes(garbage=3, clean=True, deflate=True, deflate_images=True, deflate_fonts=True)
        doc.close()
        logger.info(f"clean_pdf completed out data length={len(cleaned_pdf)}")
        return cleaned_pdf
    except Exception as err:  # pylint: disable=broad-except # noqa F841;
        logger.error(f"clean_pdf failed: {err}")
        raise err


def get_pdf_form_fields(pdf_data: bytes) -> dict:
    """Clean and compress the PDF data."""
    try:
        doc = pymupdf.Document(stream=pdf_data)
        fields: dict = {}
        for page in doc.pages():
            widgets = page.widgets()
            for field in widgets:
                fields[field.field_name] = field.field_value
        doc.close()
        return fields
    except Exception as err:  # pylint: disable=broad-except # noqa F841;
        logger.error(f"get_pdf_form_fields failed: {err}")
        raise err
