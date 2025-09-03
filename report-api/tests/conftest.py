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

"""Common setup and fixtures for the py-test suite used by this service."""

import pytest
import requests as _req

from api import create_app
from api import jwt as _jwt
from api import setup_jwt_manager


@pytest.fixture(scope='session')
def jwt(app):
    """Return session-wide jwt manager."""
    return _jwt


@pytest.fixture(scope='session')
def app():
    """Return a session-wide application configured in TEST mode."""
    _app = create_app('testing')

    return _app


@pytest.fixture(scope='function')
def app_request():
    """Return a session-wide application configured in TEST mode."""
    _app = create_app('testing')

    return _app


@pytest.fixture(scope='session')
def client(app):  # pylint: disable=redefined-outer-name
    """Return a session-wide Flask test client."""
    return app.test_client()


@pytest.fixture(scope='session')
def client_ctx(app):
    """Return session-wide Flask test client."""
    with app.test_client() as _client:
        yield _client


@pytest.fixture(scope='session', autouse=True)
def keycloak(docker_services, app):
    """Spin up a keycloak instance and initialize jwt."""
    if app.config['USE_TEST_KEYCLOAK_DOCKER']:
        docker_services.start('keycloak')
        docker_services.wait_for_service('keycloak', 8081)

    setup_jwt_manager(app, _jwt)


@pytest.fixture(scope='session')
def docker_compose_files(pytestconfig):
    """Get the docker-compose.yml absolute path."""
    import os
    return [
        os.path.join(str(pytestconfig.rootdir), 'tests/docker', 'docker-compose.yml')
    ]


@pytest.fixture
def mock_gotenberg_requests(monkeypatch):
    """Mock Gotenberg PDF generation for both sync and async requests."""
    mock_pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 0>>stream\nendstream endobj
xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000047 00000 n
0000000084 00000 n
0000000121 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
148
%%EOF"""

    class MockResponse:
        status_code = 200
        content = mock_pdf_content

        def raise_for_status(self):
            pass

    class MockAsyncResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def read(self):
            return mock_pdf_content

    class MockAsyncSession:

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def post(self, *args, **kwargs):
            return MockAsyncResponse()

    monkeypatch.setattr(_req, 'post', lambda *args, **kwargs: MockResponse())
    monkeypatch.setattr('aiohttp.ClientSession', MockAsyncSession)

    return MockResponse()
