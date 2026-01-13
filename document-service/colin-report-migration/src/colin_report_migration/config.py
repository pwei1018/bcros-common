# Copyright © 2026 Province of British Columbia
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

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class Config:  # pylint: disable=too-few-public-methods
    """Config object."""

    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    DEPLOYMENT_PLATFORM = os.getenv("DEPLOYMENT_PLATFORM", "gcp")
    DEPLOYMENT_PROJECT = os.getenv("DEPLOYMENT_PROJECT", "c4hnrd-dev")
    DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "production")

    COLIN_URL = os.getenv("COLIN_URL")

    DB_USER = os.getenv("DOC_DATABASE_USERNAME", "")
    DB_PASSWORD = os.getenv("DOC_DATABASE_PASSWORD", "")
    DB_NAME = os.getenv("DOC_DATABASE_NAME", "")
    DB_HOST = os.getenv("DOC_DATABASE_HOST", "")
    DB_PORT = os.getenv("DOC_DATABASE_PORT", "5432")  # POSTGRESQL

    # POSTGRESQL DOC database
    if DB_UNIX_SOCKET := os.getenv("DOC_DATABASE_UNIX_SOCKET", None):
        DOC_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_UNIX_SOCKET}"
    else:
        DOC_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Remove after legacy migration to Postgres
    BUS_DB_USER = os.getenv("BUS_DATABASE_USERNAME")
    BUS_DB_PASSWORD = os.getenv("BUS_DATABASE_PASSWORD")
    BUS_DB_NAME = os.getenv("BUS_DATABASE_NAME")
    BUS_DB_HOST = os.getenv("BUS_DATABASE_HOST")
    BUS_DB_PORT = os.getenv("BUS_DATABASE_PORT")

    # POSTGRESQL BUSINESS database
    if BUS_UNIX_SOCKET := os.getenv("BUS_DATABASE_UNIX_SOCKET", None):
        BUS_DATABASE_URI = f"postgresql://{BUS_DB_USER}:{BUS_DB_PASSWORD}@/{BUS_DB_NAME}?host={BUS_UNIX_SOCKET}"
    else:
        BUS_DATABASE_URI = f"postgresql://{BUS_DB_USER}:{BUS_DB_PASSWORD}@{BUS_DB_HOST}:{BUS_DB_PORT}/{BUS_DB_NAME}"

    GCP_AUTH_KEY = os.getenv("GCP_AUTH_KEY")
    GCP_CS_SA_SCOPES = os.getenv("GCP_CS_SA_SCOPES", "https://www.googleapis.com/auth/cloud-platform")
    GCP_CS_BUCKET_ID = os.getenv("GCP_CS_BUCKET_ID")
    JOB_ID: int = int(os.getenv("MIGRATION_JOB_ID", "0"))
    JOB_YEAR: int = int(os.getenv("MIGRATION_JOB_YEAR", "0"))
    JOB_BATCH_SIZE: int = int(os.getenv("MIGRATION_JOB_BATCH_SIZE", "0"))
    JOB_CORP_STATE: str = os.getenv("MIGRATION_CORP_STATE")
