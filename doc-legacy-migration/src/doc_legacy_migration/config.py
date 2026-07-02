# Copyright © 2026 Province of British Columbia
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
"""The application common configuration."""
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class BaseConfig:
    """Base configuration."""


class Config(BaseConfig):
    """Production configuration."""

    DB_USER = os.getenv("DOC_DATABASE_USERNAME", "")
    DB_PASSWORD = os.getenv("DOC_DATABASE_PASSWORD", "")
    DB_NAME = os.getenv("DOC_DATABASE_NAME", "")
    DB_HOST = os.getenv("DOC_DATABASE_HOST", "")
    DB_PORT = os.getenv("DOC_DATABASE_PORT", "5432")  # POSTGRESQL

    # POSTGRESQL DOC database
    if DB_UNIX_SOCKET := os.getenv("DOC_DATABASE_UNIX_SOCKET", None):
        DOC_DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_UNIX_SOCKET}"
    else:
        DOC_DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Remove after legacy migration to Postgres
    O_DB_USER = os.getenv("ORACLE_DATABASE_USERNAME")
    O_DB_PASSWORD = os.getenv("ORACLE_DATABASE_PASSWORD")
    O_DB_NAME = os.getenv("ORACLE_DATABASE_NAME")
    O_DB_HOST = os.getenv("ORACLE_DATABASE_HOST")
    O_DB_PORT = os.getenv("ORACLE_DATABASE_PORT")
    # {user}:{password}@(DESCRIPTION = (ADDRESS = (PROTOCOL = TCP)(HOST = {host})(PORT = {port})) (CONNECT_DATA = (SID = {name})))  # noqa: E501
    # LEGACY_DB_URI = f'{O_DB_USER}/{O_DB_PASSWORD}@{O_DB_HOST}:{O_DB_PORT}/{O_DB_NAME}'
    LEGACY_DB_URI = "{user}/{password}@(DESCRIPTION = (ADDRESS = (PROTOCOL = TCP)(HOST = {host})(PORT = {port})) (CONNECT_DATA = (SID = {name})))".format(  # noqa: E501
        user=O_DB_USER,
        password=O_DB_PASSWORD,
        host=O_DB_HOST,
        port=int(O_DB_PORT),
        name=O_DB_NAME,
    )

    GCP_AUTH_KEY = os.getenv("GCP_AUTH_KEY")
    GCP_CS_SA_SCOPES = os.getenv("GCP_CS_SA_SCOPES", "https://www.googleapis.com/auth/cloud-platform")
    # For storage
    GCP_CS_BUCKET_ID_BUS = os.getenv("GCP_CS_BUCKET_ID_BUS", "")
    GCP_CS_BUCKET_ID_MHR = os.getenv("GCP_CS_BUCKET_ID_MHR", "")
    GCP_CS_BUCKET_ID_NR = os.getenv("GCP_CS_BUCKET_ID_NR", "")
    GCP_CS_BUCKET_ID_PPR = os.getenv("GCP_CS_BUCKET_ID_PPR", "")
    CSV_TRACKING = os.getenv("CSV_TRACKING", "false")
