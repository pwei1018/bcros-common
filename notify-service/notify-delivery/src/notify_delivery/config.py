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

import os

from cloud_sql_connector import DBConfig


class Config:
    """Config object."""

    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    DEPLOYMENT_PLATFORM = os.getenv("DEPLOYMENT_PLATFORM", "GCP")
    DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_NAME = os.getenv("NOTIFY_DATABASE_NAME", "")
    DB_USER = os.getenv("NOTIFY_DATABASE_USERNAME", "")
    DB_SCHEMA = os.getenv("NOTIFY_DATABASE_SCHEMA", "public")

    # POSTGRESQL - using cloud-sql-connector
    if DB_INSTANCE_CONNECTION_NAME := os.getenv("NOTIFY_DATABASE_INSTANCE_CONNECTION_NAME", None):
        # Cloud SQL connection using cloud-sql-connector
        db_config = DBConfig(
            instance_name=DB_INSTANCE_CONNECTION_NAME,
            database=DB_NAME,
            user=DB_USER,
            ip_type="private" if DEPLOYMENT_PLATFORM == "GCP" else "public",
            schema=DB_SCHEMA,
            enable_iam_auth=True,
            driver="pg8000",
        )
        SQLALCHEMY_DATABASE_URI = "postgresql+pg8000://"
        SQLALCHEMY_ENGINE_OPTIONS = db_config.get_engine_options()
    else:
        # Direct connection fallback
        DB_PASSWORD = os.getenv("NOTIFY_DATABASE_PASSWORD", "")
        DB_HOST = os.getenv("NOTIFY_DATABASE_HOST", "")
        DB_PORT = os.getenv("NOTIFY_DATABASE_PORT", "5432")
        SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        SQLALCHEMY_ENGINE_OPTIONS = {}

    if DEPLOYMENT_PLATFORM == "OCP":
        DB_IP_TYPE = "public"

        # Email SMTP
        MAIL_SERVER = os.getenv("MAIL_SERVER", "")
        MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
        MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "")
        MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "")
        MAIL_PORT = int(os.getenv("MAIL_PORT", "25"))
        MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
        MAIL_FROM_ID = os.getenv("MAIL_FROM_ID", "")
        MAIL_DEBUG = os.getenv("MAIL_DEBUG", "False")
    else:
        DB_IP_TYPE = "private"

        # GC Notify
        GC_NOTIFY_API_URL = os.getenv("GC_NOTIFY_API_URL", "")
        GC_NOTIFY_API_KEY = os.getenv("GC_NOTIFY_API_KEY", "")
        GC_NOTIFY_TEMPLATE_ID = os.getenv("GC_NOTIFY_TEMPLATE_ID", "")
        GC_NOTIFY_SMS_TEMPLATE_ID = os.getenv("GC_NOTIFY_SMS_TEMPLATE_ID", "")
        GC_NOTIFY_EMAIL_REPLY_TO_ID = os.getenv("GC_NOTIFY_EMAIL_REPLY_TO_ID", "")
        GC_NOTIFY_HOUSING_API_KEY = os.getenv("GC_NOTIFY_HOUSING_API_KEY", "")
        GC_NOTIFY_HOUSING_TEMPLATE_ID = os.getenv("GC_NOTIFY_HOUSING_TEMPLATE_ID", "")
        GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID = os.getenv("GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID", "")

    # GCP PubSub
    GCP_AUTH_KEY = os.getenv("GCP_AUTH_KEY", "")
    AUDIENCE = os.getenv("AUDIENCE", "https://pubsub.googleapis.com/google.pubsub.v1.Subscriber")
    PUBLISHER_AUDIENCE = os.getenv("PUBLISHER_AUDIENCE", "https://pubsub.googleapis.com/google.pubsub.v1.Publisher")
    VERIFY_PUBSUB_EMAIL = os.getenv("VERIFY_PUBSUB_EMAIL", None)
    VERIFY_PUBSUB_VIA_JWT = os.getenv("VERIFY_PUBSUB_VIA_JWT", "true").lower() == "true"
    NOTIFY_SUB_AUDIENCE = os.getenv("NOTIFY_SUB_AUDIENCE", None)
    NOTIFY_HOUSING_SUB_AUDIENCE = os.getenv("NOTIFY_HOUSING_SUB_AUDIENCE", None)


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
    DEPLOYMENT_PLATFORM = "GCP"

    # POSTGRESQL - direct connection for testing
    DB_USER = os.getenv("DATABASE_TEST_USERNAME", "")
    DB_PASSWORD = os.getenv("DATABASE_TEST_PASSWORD", "")
    DB_NAME = os.getenv("DATABASE_TEST_NAME", "")
    DB_HOST = os.getenv("DATABASE_TEST_HOST", "")
    DB_PORT = os.getenv("DATABASE_TEST_PORT", "5432")
    SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{int(DB_PORT)}/{DB_NAME}"
    SQLALCHEMY_ENGINE_OPTIONS = {}


class UnitTestingSMTPConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for unit testing environment."""

    DEVELOPMENT = False
    TESTING = True
    DEBUG = True
    DEPLOYMENT_PLATFORM = "OCP"

    # POSTGRESQL - direct connection for testing
    DB_USER = os.getenv("DATABASE_TEST_USERNAME", "")
    DB_PASSWORD = os.getenv("DATABASE_TEST_PASSWORD", "")
    DB_NAME = os.getenv("DATABASE_TEST_NAME", "")
    DB_HOST = os.getenv("DATABASE_TEST_HOST", "")
    DB_PORT = os.getenv("DATABASE_TEST_PORT", "5432")
    SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{int(DB_PORT)}/{DB_NAME}"
    SQLALCHEMY_ENGINE_OPTIONS = {}


config = {
    "development": DevelopmentConfig,
    "test": TestingConfig,
    "sandbox": SandboxConfig,
    "production": ProductionConfig,
    "unitTesting": UnitTestingConfig,
    "unitTestingSMTP": UnitTestingSMTPConfig,
}
