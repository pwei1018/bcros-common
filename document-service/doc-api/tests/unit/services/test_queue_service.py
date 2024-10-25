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
"""Google queue service publish tests."""
import os

from flask import current_app

from doc_api.services.queue_service import GoogleQueueService


TEST_DOC_REC = {
    "accountId": "123456",
    "consumerDocumentId": "99990950",
    "consumerIdentifier": "108924",
    "documentType": "MHR_MISC",
    "documentClass": "MHR",
    "author": "John Smitl"
}


def test_publish_document_rec(session):
    """Assert that enqueuing/publishing a new document record request works as expected (no exception thrown)."""
    if not is_ci_testing():
        payload = TEST_DOC_REC
        GoogleQueueService().publish_create_doc_record(payload)


def is_ci_testing() -> bool:
    """Check unit test environment: exclude pub/sub for CI testing."""
    return  current_app.config.get("DEPLOYMENT_ENV", "testing") == "testing"
