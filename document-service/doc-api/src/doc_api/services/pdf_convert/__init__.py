# Copyright © 2025 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""Converts documents in various common formats to PDF."""
import copy
from http import HTTPStatus

import requests
from flask import current_app, jsonify

from doc_api.exceptions import ResourceErrorCodes
from doc_api.services.gcp_auth.auth_service import GoogleAuthService
from doc_api.utils.base import BaseEnum
from doc_api.utils.logging import logger

CONVERT_URI = "/forms/libreoffice/convert"
DEFAULT_META_DATA = {
    "flatten": True,
    "exportFormFields": False,
    "updateIndexes": False,
    "exportBookmarks": False,
}
LANDSCAPE_META_DATA = {
    "flatten": True,
    "exportFormFields": False,
    "updateIndexes": False,
    "exportBookmarks": False,
    "landscape": True,
}
HEADER_CONTENT_TYPE_PDF = {"Content-Type": "application/pdf"}
HEADER_CONTENT_TYPE_JSON = {"Content-Type": "application/json"}


class MediaTypes(BaseEnum):
    """Render an Enum of the document media types supported by the PDF Converter."""

    CONTENT_TYPE_CSV = "text/csv"
    CONTENT_TYPE_GIF = "image/gif"
    CONTENT_TYPE_JPEG = "image/jpeg"
    CONTENT_TYPE_PNG = "image/png"
    CONTENT_TYPE_TIFF = "image/tiff"
    CONTENT_TYPE_SVG = "image/svg+xml"
    CONTENT_TYPE_PDF = "application/pdf"
    CONTENT_TYPE_PPT = "application/vnd.ms-powerpoint"
    CONTENT_TYPE_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    CONTENT_TYPE_EXCEL = "application/vnd.ms-excel"
    CONTENT_TYPE_WORD = "application/msword"
    CONTENT_TYPE_EXCELX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    CONTENT_TYPE_WORDX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    CONTENT_TYPE_ZIP = "application/zip"
    CONTENT_TYPE_TEXT = "text/plain"


# Map from API media type to file extension
MEDIA_TO_FILE_EXTENSION = {
    MediaTypes.CONTENT_TYPE_CSV.value: ".csv",
    MediaTypes.CONTENT_TYPE_GIF.value: ".gif",
    MediaTypes.CONTENT_TYPE_JPEG.value: ".jpg",
    MediaTypes.CONTENT_TYPE_PNG.value: ".png",
    MediaTypes.CONTENT_TYPE_TIFF.value: ".tif",
    MediaTypes.CONTENT_TYPE_SVG.value: ".svg",
    MediaTypes.CONTENT_TYPE_PDF.value: ".pdf",
    MediaTypes.CONTENT_TYPE_PPT.value: ".ppt",
    MediaTypes.CONTENT_TYPE_PPTX.value: ".pptx",
    MediaTypes.CONTENT_TYPE_EXCEL.value: ".xls",
    MediaTypes.CONTENT_TYPE_EXCELX.value: ".xlsx",
    MediaTypes.CONTENT_TYPE_WORD.value: ".doc",
    MediaTypes.CONTENT_TYPE_WORDX.value: ".docx",
    MediaTypes.CONTENT_TYPE_TEXT.value: ".txt",
}


class PdfConvert:  # pylint: disable=too-few-public-methods
    """Service to convert documents to PDF."""

    def __init__(self, document_data, filename: str, media_type: str = None):
        """Create the PDF Converter instance."""
        self._document_data = document_data
        self._filename = filename
        self._media_type = media_type

    def convert(self):
        """Convert the document data to pdf. Include the media type if available."""
        logger.info(f"Convert starting for filename={self._filename} size={len(self._document_data)}.")
        url = current_app.config.get("REPORT_SVC_URL") + CONVERT_URI
        meta_data = self._get_meta_data()
        files = self._get_file_data()
        headers = PdfConvert.get_headers()
        response = requests.post(url=url, headers=headers, data=meta_data, files=files, timeout=30.0)
        logger.info(f"Convert {self._filename} response {response.status_code}")
        if response.status_code != HTTPStatus.OK:
            content = ResourceErrorCodes.REPORT_ERR + ": " + response.content.decode("ascii")
            logger.error(f"Convert response status: {response.status_code} error: {content}.")
            return jsonify(message=content), response.status_code, HEADER_CONTENT_TYPE_JSON
        return response.content, response.status_code, HEADER_CONTENT_TYPE_PDF

    @staticmethod
    def get_headers() -> dict:
        """Build the report service request headers."""
        headers = {}
        token = GoogleAuthService.get_report_api_token()
        if token:
            headers["Authorization"] = "Bearer {}".format(token)
        return headers

    def _get_meta_data(self) -> dict:
        """Set up the pdf converter request configurable properties."""
        if self._media_type and self._media_type in (
            MediaTypes.CONTENT_TYPE_CSV.value,
            MediaTypes.CONTENT_TYPE_EXCEL.value,
            MediaTypes.CONTENT_TYPE_EXCELX.value,
        ):
            return copy.deepcopy(LANDSCAPE_META_DATA)
        meta_data = copy.deepcopy(DEFAULT_META_DATA)
        return meta_data

    def _get_file_data(self) -> dict:
        """Set up the pdf converter request document file data."""
        if self._media_type:
            file_data: dict = {"file": (self._filename, self._document_data, self._media_type, {"Expires": "0"})}
            logger.info(f"Pdf converter request file data setup for {self._filename} media={self._media_type}.")
            return file_data
        file_data: dict = {"file": (self._filename, self._document_data)}
        logger.info(f"Pdf converter request file data setup for {self._filename}")
        return file_data
