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
"""This exports all of the models and schemas used by the application."""

from .db import db  # noqa: I001
from .document import Document
from .document_request import DocumentRequest
from .document_scanning import DocumentScanning
from .scanning_author import ScanningAuthor
from .scanning_box import ScanningBox
from .scanning_parameter import ScanningParameter
from .scanning_schedule import ScanningSchedule
from .type_tables import DocumentClass, DocumentType, RequestType
from .user import User

__all__ = (
    "db",
    "Document",
    "DocumentClass",
    "DocumentType",
    "DocumentRequest",
    "DocumentScanning",
    "RequestType",
    "ScanningBox",
    "ScanningAuthor",
    "ScanningParameter",
    "ScanningSchedule",
    "User",
)
