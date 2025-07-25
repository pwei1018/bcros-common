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
"""Common resource helper class to store new request information."""

from doc_api.models.utils import DEFAULT_FILE_EXTENSION


class RequestInfo:
    """Contains parameter values and other common request information."""

    account_id: str
    staff: bool = False
    from_ui: bool = False
    content_type: str = None
    accept: str = None
    query_start_date: str = None
    query_end_date: str = None
    document_service_id: str = None
    consumer_doc_id: str = None
    consumer_filename: str = None
    consumer_filedate: str = None
    consumer_identifier: str = None
    consumer_reference_id: str = None
    request_type: str = None
    request_path: str = None
    document_type: str = None
    document_storage_type: str = None
    document_class: str = None
    has_payload: bool = False
    page_number: int = 1
    description: str = None
    request_data: dict = None

    def __init__(self, request_type: str, request_path: str, doc_type: str, doc_storage_type):
        """Set common base initialization."""
        self.request_type = request_type
        self.request_path = request_path
        self.document_type = doc_type
        self.document_storage_type = doc_storage_type
        self.staff = False

    @property
    def json(self) -> dict:
        """Return the request info as a json object for storing in document requests."""
        info = {
            "documentServiceId": self.document_service_id if self.document_service_id else "",
            "staff": self.staff,
            "accept": self.accept if self.accept else "",
            "contentType": self.content_type if self.content_type else "",
            "consumerDocumentId": self.consumer_doc_id if self.consumer_doc_id else "",
            "consumerFilename": self.consumer_filename if self.consumer_filename else "",
            "consumerFilingDate": self.consumer_filedate if self.consumer_filedate else "",
            "consumerIdentifier": self.consumer_identifier if self.consumer_identifier else "",
            "consumerReferenceId": self.consumer_reference_id if self.consumer_reference_id else "",
            "documentType": self.document_type if self.document_type else "",
            "documentClass": self.document_class if self.document_class else "",
        }
        if self.description:
            info["description"] = self.description
        if self.request_path:
            info["requestPath"] = self.request_path
        if self.page_number:
            info["pageNumber"] = self.page_number
        if self.request_data:
            info["requestData"] = self.request_data
            if self.request_data.get("author"):
                info["author"] = self.request_data.get("author")
        # Files are always saved as PDF: using the original file extension may mess up the download.
        if self.consumer_filename and not self.consumer_filename.lower().endswith(DEFAULT_FILE_EXTENSION):
            info["consumerFilename"] = self.consumer_filename + DEFAULT_FILE_EXTENSION
        return info
