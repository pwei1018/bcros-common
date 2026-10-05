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
import base64
import io
import os

import paramiko
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class BaseConfig:
    """Base configuration."""


class Config(BaseConfig):
    """Production configuration."""

    NOTIFY_API_URL = os.getenv("NOTIFY_API_URL", "")
    NOTIFY_API_VERSION = os.getenv("NOTIFY_API_VERSION", "")
    NOTIFY_SVC_URL = f"{NOTIFY_API_URL + NOTIFY_API_VERSION}"
    if not NOTIFY_SVC_URL.endswith("/notify"):
        NOTIFY_SVC_URL += "/notify"

    JWT_OIDC_TOKEN_URL = os.getenv("JWT_OIDC_TOKEN_URL")
    # service accounts
    ACCOUNT_SVC_CLIENT_ID = os.getenv("ACCOUNT_SVC_CLIENT_ID")
    ACCOUNT_SVC_CLIENT_SECRET = os.getenv("ACCOUNT_SVC_CLIENT_SECRET")

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

    GCP_AUTH_KEY = os.getenv("GCP_AUTH_KEY")
    GCP_CS_SA_SCOPES = os.getenv("GCP_CS_SA_SCOPES", "https://www.googleapis.com/auth/cloud-platform")
    # For storage
    GCP_CS_BUCKET_ID_BUS = os.getenv("GCP_CS_BUCKET_ID_BUS", "")
    GCP_CS_BUCKET_ID_BCMAIL = os.getenv("GCP_CS_BUCKET_ID_BCMAIL", "")
    # Job schedule in days, used to include recent SFTP files within the last JOB_INTERVAL_DAYS days. 0 disables.
    JOB_INTERVAL_DAYS = int(os.getenv("JOB_INTERVAL_DAYS", "7"))
    # If true then list BCMail directories and files instead of migrating. Only use for connectivity testing.
    LIST_FILES: bool = os.getenv("LIST_FILES", "") == "true"
    # If true then migrate LAN files instead of files transferred from BCMail+ via SFTP.
    MIGRATE_LAN: bool = os.getenv("MIGRATE_LAN", "") == "true"
    # business bucket base path to store job status csv files.
    CSV_STATUS_PATH = os.getenv("CSV_STATUS_PATH", "")
    SFTP_HOST = os.getenv("SFTP_HOST", "")
    SFTP_PORT: int = int(os.getenv("SFTP_PORT", "22"))
    SFTP_USERID = os.getenv("SFTP_USERID", "")
    SFTP_KEY_64 = os.getenv("SFTP_KEY", "")
    SFTP_DIR = os.getenv("SFTP_DIR", "")
    SFTP_KEY = base64.b64decode(SFTP_KEY_64)
    key_file = io.StringIO(SFTP_KEY.decode("utf-8"))
    SFTP_PRIVATE_KEY = paramiko.RSAKey.from_private_key(key_file)

    # Local migrate from LAN: requires both VPN and mounting of LAN network drive.
    BCMAIL_LAN_DIR = os.getenv("BCMAIL_LAN_DIR", "")
    # Specify the list of LAN subfolders to migrate as a JSON list
    BCMAIL_LAN_FOLDERS = os.getenv("BCMAIL_LAN_FOLDERS", "")
    BCMAIL_TEMP_DIR = os.getenv("BCMAIL_TEMP_DIR", "")

    # Notify config
    NOTIFY_STATUS_RECIPIENTS = os.getenv("NOTIFY_STATUS_RECIPIENTS", "")
    NOTIFY_STATUS_SUBJECT = os.getenv("NOTIFY_STATUS_SUBJECT", "")
    NOTIFY_STATUS_BODY = os.getenv("NOTIFY_STATUS_BODY", "")
