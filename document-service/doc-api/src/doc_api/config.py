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
"""All of the configuration for the service is captured here.

All items are loaded, or have Constants defined here that
are loaded into the Flask configuration.
All modules and lookups get their configuration from the
Flask config, rather than reading environment variables directly
or by accessing this configuration directly.
"""
import json
import os

import requests


def get_mock_auth() -> str:
    """For CI unit tests get mock auth value."""
    try:
        url: str = "https://test.api.connect.gov.bc.ca/mockTarget/auth/api/v1/testing/mock-sa-doc"
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=10.0)
        if response and response.text:
            resp_json = json.loads(response.text)
            return resp_json.get("response", "")
        return ""
    except Exception:
        return ""


class Config:  # pylint: disable=too-few-public-methods
    """Config object."""

    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    DEPLOYMENT_PLATFORM = os.getenv("DEPLOYMENT_PLATFORM", "gcp")
    DEPLOYMENT_PROJECT = os.getenv("DEPLOYMENT_PROJECT", "c4hnrd-dev")
    FLASK_PYDANTIC_VALIDATION_ERROR_RAISE = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALEMBIC_INI = "migrations/alembic.ini"

    DB_USER = os.getenv("DOC_DATABASE_USERNAME", "")
    DB_PASSWORD = os.getenv("DOC_DATABASE_PASSWORD", "")
    DB_NAME = os.getenv("DOC_DATABASE_NAME", "")
    DB_HOST = os.getenv("DOC_DATABASE_HOST", "")
    DB_PORT = os.getenv("DOC_DATABASE_PORT", "5432")  # POSTGRESQL

    # POSTGRESQL
    if DB_UNIX_SOCKET := os.getenv("DOC_DATABASE_UNIX_SOCKET", None):
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?unix_sock={DB_UNIX_SOCKET}/.s.PGSQL.5432"
        )
    else:
        SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # MILLIONVERIFIER
    # MILLIONVERIFIER_API_URL = os.getenv("MILLIONVERIFIER_API_URL", "")
    # MILLIONVERIFIER_API_KEY = os.getenv("MILLIONVERIFIER_API_KEY", "")

    # JWT_OIDC Settings
    JWT_OIDC_WELL_KNOWN_CONFIG = os.getenv("JWT_OIDC_WELL_KNOWN_CONFIG")
    JWT_OIDC_ALGORITHMS = os.getenv("JWT_OIDC_ALGORITHMS")
    JWT_OIDC_JWKS_URI = os.getenv("JWT_OIDC_JWKS_URI")
    JWT_OIDC_ISSUER = os.getenv("JWT_OIDC_ISSUER")
    JWT_OIDC_AUDIENCE = os.getenv("ACCOUNT_SERVICES_SERVICE_ACCOUNT_CLIENT_ID")
    JWT_OIDC_CLIENT_SECRET = os.getenv("JWT_OIDC_CLIENT_SECRET")
    JWT_OIDC_CACHING_ENABLED = os.getenv("JWT_OIDC_CACHING_ENABLED")
    JWT_OIDC_TOKEN_URL = os.getenv("JWT_OIDC_TOKEN_URL")
    try:
        JWT_OIDC_JWKS_CACHE_TIMEOUT = int(os.getenv("JWT_OIDC_JWKS_CACHE_TIMEOUT"))
    except (TypeError, ValueError):
        JWT_OIDC_JWKS_CACHE_TIMEOUT = 300

    GCP_AUTH_KEY = os.getenv("GCP_AUTH_KEY")
    GCP_CS_SA_SCOPES = os.getenv("GCP_CS_SA_SCOPES", "https://www.googleapis.com/auth/cloud-platform")
    # For reports
    REPORT_SVC_URL = os.getenv("REPORT_SVC_URL", "https://report-api-gotenberg-dev-5qwaveuroa-nn.a.run.app")
    REPORT_TEMPLATE_PATH = os.getenv("REPORT_TEMPLATE_PATH", "report-templates")
    # For storage
    GCP_CS_BUCKET_ID_BUS = os.getenv("GCP_CS_BUCKET_ID_BUS", "docs_business_dev")
    GCP_CS_BUCKET_ID_MHR = os.getenv("GCP_CS_BUCKET_ID_MHR", "docs_mhr_dev")
    GCP_CS_BUCKET_ID_NR = os.getenv("GCP_CS_BUCKET_ID_NR", "docs_nr_dev")
    GCP_CS_BUCKET_ID_PPR = os.getenv("GCP_CS_BUCKET_ID_PPR", "docs_ppr_dev")
    # For pub/sub subscription (queue/async requests)
    GCP_PS_DOC_CREATE_REC_TOPIC = os.getenv("GCP_PS_DOC_CREATE_REC_TOPIC", "doc-api-app-create-record")
    SUBSCRIPTION_API_KEY = os.getenv("SUBSCRIPTION_API_KEY")

    DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "development")
    if not GCP_AUTH_KEY and DEPLOYMENT_ENV in ("unitTesting", "testing"):
        GCP_AUTH_KEY = get_mock_auth()


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for production environment."""

    DEBUG = False


class SandboxConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for sandbox environment."""

    DEBUG = False


class TestingConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for testing(staging) environment."""

    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for development environment."""

    DEVELOPMENT = True
    DEBUG = True


class UnitTestingConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for unit testing environment."""

    DEVELOPMENT = False
    TESTING = True
    DEBUG = True

    # POSTGRESQL
    DB_USER = os.getenv("DATABASE_TEST_USERNAME", "")
    DB_PASSWORD = os.getenv("DATABASE_TEST_PASSWORD", "")
    DB_NAME = os.getenv("DATABASE_TEST_NAME", "")
    DB_HOST = os.getenv("DATABASE_TEST_HOST", "")
    DB_PORT = os.getenv("DATABASE_TEST_PORT", "5432")
    SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    LD_SDK_KEY = os.getenv("LD_SDK_KEY", None)
    SECRET_KEY = "a secret"

    # JWT OIDC settings
    # JWT_OIDC_TEST_MODE will set jwt_manager to use
    JWT_OIDC_TEST_MODE = True
    JWT_OIDC_TEST_AUDIENCE = "example"
    JWT_OIDC_TEST_ISSUER = "https://example.localdomain/auth/realms/example"
    JWT_OIDC_TEST_KEYS = {
        "keys": [
            {
                "kid": "flask-jwt-oidc-test-client",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "AN-fWcpCyE5KPzHDjigLaSUVZI0uYrcGcc40InVtl-rQRDmAh-C2W8H4_Hxhr5VLc6crsJ2LiJTV_E72S03pzpOOaaYV6-TzAjCou2GYJIXev7f6Hh512PuG5wyxda_TlBSsI-gvphRTPsKCnPutrbiukCYrnPuWxX5_cES9eStR",  # noqa: E501
                "e": "AQAB",
            }
        ]
    }

    JWT_OIDC_TEST_PRIVATE_KEY_JWKS = {
        "keys": [
            {
                "kid": "flask-jwt-oidc-test-client",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "AN-fWcpCyE5KPzHDjigLaSUVZI0uYrcGcc40InVtl-rQRDmAh-C2W8H4_Hxhr5VLc6crsJ2LiJTV_E72S03pzpOOaaYV6-TzAjCou2GYJIXev7f6Hh512PuG5wyxda_TlBSsI-gvphRTPsKCnPutrbiukCYrnPuWxX5_cES9eStR",  # noqa: E501
                "e": "AQAB",
                "d": "C0G3QGI6OQ6tvbCNYGCqq043YI_8MiBl7C5dqbGZmx1ewdJBhMNJPStuckhskURaDwk4-8VBW9SlvcfSJJrnZhgFMjOYSSsBtPGBIMIdM5eSKbenCCjO8Tg0BUh_xa3CHST1W4RQ5rFXadZ9AeNtaGcWj2acmXNO3DVETXAX3x0",  # noqa: E501
                "p": "APXcusFMQNHjh6KVD_hOUIw87lvK13WkDEeeuqAydai9Ig9JKEAAfV94W6Aftka7tGgE7ulg1vo3eJoLWJ1zvKM",
                "q": "AOjX3OnPJnk0ZFUQBwhduCweRi37I6DAdLTnhDvcPTrrNWuKPg9uGwHjzFCJgKd8KBaDQ0X1rZTZLTqi3peT43s",
                "dp": "AN9kBoA5o6_Rl9zeqdsIdWFmv4DB5lEqlEnC7HlAP-3oo3jWFO9KQqArQL1V8w2D4aCd0uJULiC9pCP7aTHvBhc",
                "dq": "ANtbSY6njfpPploQsF9sU26U0s7MsuLljM1E8uml8bVJE1mNsiu9MgpUvg39jEu9BtM2tDD7Y51AAIEmIQex1nM",
                "qi": "XLE5O360x-MhsdFXx8Vwz4304-MJg-oGSJXCK_ZWYOB_FGXFRTfebxCsSYi0YwJo-oNu96bvZCuMplzRI1liZw",
            }
        ]
    }

    JWT_OIDC_TEST_PRIVATE_KEY_PEM = """
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDfn1nKQshOSj8xw44oC2klFWSNLmK3BnHONCJ1bZfq0EQ5gIfg
tlvB+Px8Ya+VS3OnK7Cdi4iU1fxO9ktN6c6TjmmmFevk8wIwqLthmCSF3r+3+h4e
ddj7hucMsXWv05QUrCPoL6YUUz7Cgpz7ra24rpAmK5z7lsV+f3BEvXkrUQIDAQAB
AoGAC0G3QGI6OQ6tvbCNYGCqq043YI/8MiBl7C5dqbGZmx1ewdJBhMNJPStuckhs
kURaDwk4+8VBW9SlvcfSJJrnZhgFMjOYSSsBtPGBIMIdM5eSKbenCCjO8Tg0BUh/
xa3CHST1W4RQ5rFXadZ9AeNtaGcWj2acmXNO3DVETXAX3x0CQQD13LrBTEDR44ei
lQ/4TlCMPO5bytd1pAxHnrqgMnWovSIPSShAAH1feFugH7ZGu7RoBO7pYNb6N3ia
C1idc7yjAkEA6Nfc6c8meTRkVRAHCF24LB5GLfsjoMB0tOeEO9w9Ous1a4o+D24b
AePMUImAp3woFoNDRfWtlNktOqLel5PjewJBAN9kBoA5o6/Rl9zeqdsIdWFmv4DB
5lEqlEnC7HlAP+3oo3jWFO9KQqArQL1V8w2D4aCd0uJULiC9pCP7aTHvBhcCQQDb
W0mOp436T6ZaELBfbFNulNLOzLLi5YzNRPLppfG1SRNZjbIrvTIKVL4N/YxLvQbT
NrQw+2OdQACBJiEHsdZzAkBcsTk7frTH4yGx0VfHxXDPjfTj4wmD6gZIlcIr9lZg
4H8UZcVFN95vEKxJiLRjAmj6g273pu9kK4ymXNEjWWJn
-----END RSA PRIVATE KEY-----"""


config = {
    "development": DevelopmentConfig,
    "test": TestingConfig,
    "sandbox": SandboxConfig,
    "production": ProductionConfig,
    "unitTesting": UnitTestingConfig,
}
