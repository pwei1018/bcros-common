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
"""This module executes all the job steps."""
import copy

# import io
import json
import shutil
import stat
import sys

# from contextlib import suppress
from datetime import datetime as _datetime
from datetime import timedelta, timezone
from pathlib import Path

import paramiko
import psycopg2
import pytz

from doc_bcmail_transfer.config import Config
from doc_bcmail_transfer.database import Database
from doc_bcmail_transfer.services.document_storage.storage_service import GoogleStorageService
from doc_bcmail_transfer.services.notify import Notify
from doc_bcmail_transfer.utils.logging import logger

LOCAL_TZ = pytz.timezone("America/Los_Angeles")
DOCUMENT_CLASSES = ["COOP", "CORP", "FIRM", "LP_LLP", "MHR", "NR", "OTHER", "PPR", "SOCIETY"]
STORAGE_DOC_NAME = "{legacy_date}/{doc_type}-{doc_key}.pdf"
CSV_FILENAME = "{bucket_path}/{storage_date}/status-bcmail-lan-to-drs.csv"
CSV_HEADER: str = (
    '"BCMail_filename","DRS_business_identifier","DRS_added_UTC","DRS_filename","BCMail_filesize",'
    + '"DRS_filesize","DRS_document_id","Error_message","Status"\n'
)
CSV_LINE: str = '"{name}","{drs_id}","{drs_ts}","{drs_name}",{bcmail_size},{drs_size},"{drs_doc_id}","{msg}",{status}\n'
ERROR_DRS_MISSING = "No DRS information found for file."
ERROR_FILE_SIZE_MISMATCH = "BCMail+ file size does not match DRS file size."
STATUS_SUCCESS = 200
STATUS_ERROR = 500
FILE_SUMMARY = {
    "bcmail_filename": "",
    "bcmail_dirname": "",
    "bcmail_filesize": 0,
    "bcmail_identifier": "",
    "drs_added_utc": "",
    "drs_identifier": "",
    "drs_filename": "",
    "drs_filesize": 0,
    "drs_document_id": "",
    "status_msg": "",
    "status": STATUS_SUCCESS,
}
NOTIFY_STATUS_DATA = {
    "job_date": "",
    "total_dir_count": 0,
    "total_file_count": 0,
    "total_error_count": 0,
    "csv_file_url": -1,
}


def sftp_migrate_bcmail(config: Config):
    """
    Migrate the bcmail scanned documents in the remote sftp directory. If JOB_INTERVAL_DAYS > 0, only include
    directories more recent than now - JOB_INTERVAL_DAYS days.

    Args:
        config: Job configuration containing environment variables.
    """
    ssh_client = None
    files_summary: list = []
    counter: int = 0
    bcmail_dirs: list = []
    try:
        logger.info("sftp migrate docs connecting.")
        ssh_client = sftp_connect(config)
        with ssh_client.open_sftp() as sftp:
            logger.info(f"sftp migrate docs to {config.SFTP_DIR}.")
            sftp.chdir(config.SFTP_DIR)
            listing = sorted(sftp.listdir_attr("."), key=lambda x: x.filename)
            cutoff_date = sftp_cutoff_date(config)
            logger.info(f"sftp {config.SFTP_DIR} number of items {len(listing)} cutoff_date={cutoff_date}.")
            for rdir in listing:
                dir_ts = _datetime.fromtimestamp(rdir.st_mtime)
                if stat.S_ISDIR(rdir.st_mode) and (cutoff_date is None or dir_ts > cutoff_date):
                    current_dir = rdir.filename
                    bcmail_dirs.append(current_dir)
                    sftp.chdir(current_dir)
                    files = sorted(sftp.listdir_attr("."), key=lambda x: x.filename)
                    logger.info(f"{current_dir} file count={len(files)}")
                    for entry in files:
                        if not stat.S_ISDIR(entry.st_mode):
                            counter += 1
                            file_info: dict = sftp_upload_to_bcmail_bucket(sftp, current_dir, counter, entry)
                            files_summary.append(file_info)
                            if counter % 20 == 0:
                                logger.info(f"{current_dir} migration count: {counter}")
                    sftp.chdir("..")
                elif stat.S_ISDIR(rdir.st_mode) and cutoff_date and dir_ts <= cutoff_date:
                    logger.info(
                        f"Skipping {rdir.filename} modified date {dir_ts} <= last job run cutoff date {cutoff_date}."
                    )
                else:
                    logger.warning(
                        f"Unexpected file ignored {rdir.filename} size {rdir.st_size} bytes modified {dir_ts}"
                    )
    except Exception as sftp_exception:  # noqa: B902; return nicer error
        logger.error(f"BCMail sftp migrate docs remote errors dir={config.SFTP_DIR}: {sftp_exception}")
    finally:
        if ssh_client:
            ssh_client.close()
    return files_summary, bcmail_dirs


def sftp_migrate_bcmail_dirs(config: Config):
    """
    List the bcmail remote sftp directory scanned document sub-directories/subfolders.

    Args:
        config: Job configuration containing environment variables.
    """
    ssh_client = None
    try:
        logger.info("sftp list dir connecting.")
        ssh_client = sftp_connect(config)
        with ssh_client.open_sftp() as sftp:
            logger.info(f"sftp list dir changing to {config.SFTP_DIR}.")
            sftp.chdir(config.SFTP_DIR)
            listing = sorted(sftp.listdir_attr("."), key=lambda x: x.filename)
            logger.info(f"sftp {config.SFTP_DIR} number of items {len(listing)}.")
            for entry in listing:
                if stat.S_ISDIR(entry.st_mode):
                    print(f"Dir {entry.filename} last modified {entry.st_mtime}")
                else:
                    print(f"File {entry.filename} size {entry.st_size} bytes last modified {entry.st_mtime}")
    except Exception as sftp_exception:  # noqa: B902; return nicer error
        logger.error(f"BCMail sftp list remote errors dir={config.SFTP_DIR}: {sftp_exception}")
    finally:
        if ssh_client:
            ssh_client.close()


def sftp_connect(config: Config):
    """Create and return an ssh client for SFTP."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=config.SFTP_HOST, port=config.SFTP_PORT, username=config.SFTP_USERID, pkey=config.SFTP_PRIVATE_KEY
    )
    return ssh


def sftp_cutoff_date(config: Config):
    """Create and return an ssh client for SFTP."""
    if config.JOB_INTERVAL_DAYS < 1:
        return None
    now_ts = _datetime.now()
    return now_ts - timedelta(days=config.JOB_INTERVAL_DAYS)


def sftp_upload_to_bcmail_bucket(sftp, current_dir: str, counter: int, entry) -> dict:
    """
    Fetch the remote directory file data in memory and upload it to the BCMail CS bucket.

        Args:
        sftp: SFTP session to read remote file.
        current_dir: The current remote directory.
        counter: The running tally of migrated documents.
        entry: Holds remote file information including name and size in bytes.
    """
    status_msg = f"File# {counter} name={entry.filename} size={entry.st_size} bytes."
    file_info = copy.deepcopy(FILE_SUMMARY)
    try:
        file_info["bcmail_filename"] = entry.filename
        file_info["bcmail_dirname"] = current_dir
        file_info["bcmail_filesize"] = entry.st_size
        file_info["bcmail_identifier"] = str(entry.filename).removesuffix(".pdf").replace(" ", "")
        fname: str = file_info.get("bcmail_filename")
        if fname.startswith("BC") and not fname.startswith("BC "):
            fname = fname.replace("BC", "BC ")
        elif fname.startswith("C") and not fname.startswith("C "):
            fname = fname.replace("C", "C ")
        # Upload file to DRS bucket.
        with sftp.open(entry.filename, "rb") as remote_file:
            remote_file.prefetch()
            binary_data = remote_file.read()
            GoogleStorageService.save_bcmail_document(fname, binary_data)
    except Exception as file_exception:  # noqa: B902; return nicer error
        logger.error(f"sftp file {current_dir}/{entry.name} migrate/upload failed: {file_exception}")
        file_info["status_msg"] = status_msg + " SFTP migrate/upload file failed."
        file_info["status"] = 500
    return file_info


def lan_migrate_bcmail_dirs(config: Config):
    """
    List the bcmail lan scanned document sub-directories/subfolders.

    Args:
        config: Job configuration containing environment variables.
    """
    bcmail_lan_dir: str = config.BCMAIL_LAN_DIR
    scan_path = Path(bcmail_lan_dir)
    sorted_dir = sorted(scan_path.iterdir())
    for entry in sorted_dir:
        if entry.is_dir():
            last_modified = _datetime.fromtimestamp(entry.stat().st_mtime)
            print(f"{entry.name} last modified {last_modified}")


def lan_migrate_bcmail(config: Config, dirs: list) -> list:
    """
    Migrate bcmail lan documents to DRS

    Args:
        config: Job configuration containing environment variables.
        dirs: list of BCMail sub-directories/sub-folders containing documents to migrate.
    """
    bcmail_lan_dir: str = config.BCMAIL_LAN_DIR
    temp_dir: str = config.BCMAIL_TEMP_DIR
    counter: int = 0
    files_summary: list = []
    for dir_migrate in dirs:
        status_msg: str = ""
        scan_dir = f"{bcmail_lan_dir}/{dir_migrate}" if dir_migrate != "" else bcmail_lan_dir
        logger.info(f"Migrating files from lan folder {scan_dir}.")
        try:
            scan_path = Path(scan_dir)
            sorted_dir = sorted(scan_path.iterdir())
            for entry in sorted_dir:
                if entry.is_file() and entry.name != ".DS_Store":
                    counter += 1
                    status_msg = f"File# {counter} name={entry.name} size={entry.stat().st_size} bytes."
                    file_info = copy.deepcopy(FILE_SUMMARY)
                    try:
                        file_info["bcmail_filename"] = entry.name
                        file_info["bcmail_dirname"] = dir_migrate
                        file_info["bcmail_filesize"] = entry.stat().st_size
                        file_info["bcmail_identifier"] = str(entry.name).removesuffix(".pdf").replace(" ", "")
                        file_info["drs_identifier"] = file_info.get("bcmail_identifier")
                        file_info = lan_copy_file_to_temp(f"{scan_dir}/{entry.name}", temp_dir, file_info, status_msg)
                        # Upload file to DRS bucket, then delete file from local temp dir
                        file_info = lan_upload_to_bcmail_bucket(temp_dir + entry.name, file_info, status_msg)
                        files_summary.append(file_info)
                    except Exception as file_exception:  # noqa: B902; return nicer error
                        logger.error(f"lan_migrate_bcmail {scan_dir}/{entry.name} failed: {file_exception}")
                        file_info["status_msg"] = status_msg + " Migrate file from LAN failed."
                        file_info["status"] = 500
                    if counter % 20 == 0:
                        logger.info(f"{dir_migrate} migration count: {counter}")
        except Exception as mi_exception:  # noqa: B902; return nicer error
            logger.error(f"BCMail migration error dir={scan_dir} {status_msg}: {mi_exception}")
    return files_summary


def lan_copy_file_to_temp(lan_path: str, temp_dir: str, file_info: dict, status_msg: str) -> dict:
    """
    Copy the lan file to a local temp directory.

    Args:
        lan_path: Full path to the LAN document.
        temp_dir: Local directory to copy the document to.
        file_info: Contains information about the file.
        status_msg: Message to save if there is an error.
    """
    try:
        shutil.copy(lan_path, temp_dir)
    except Exception as copy_exception:  # noqa: B902; return nicer error
        logger.error(f"File {lan_path} copy to {temp_dir} failed: {copy_exception}")
        file_info["status_msg"] = status_msg + " Copy file from LAN failed."
        file_info["status"] = 500
    return file_info


def lan_upload_to_bcmail_bucket(temp_file: str, file_info: dict, status_msg: str) -> dict:
    """
    Upload the local temp file contents to the BCMail CS bucket as the file_info BCMail file name.
    Delete the local copy of the file after uploading.

        Args:
        temp_file: Local temporary file to upload to cloud storage.
        file_info: Contains information about the file.
        status_msg: Message to save if there is an error.
    """
    try:
        binary_data = None
        with open(temp_file, "rb") as data_file:
            binary_data = data_file.read()
            data_file.close()
        fname: str = file_info.get("bcmail_filename")
        if fname.startswith("BC") and not fname.startswith("BC "):
            fname = fname.replace("BC", "BC ")
        elif fname.startswith("C") and not fname.startswith("C "):
            fname = fname.replace("C", "C ")
        GoogleStorageService.save_bcmail_document(fname, binary_data)
        # Delete file from local temp dir
        delete_path = Path(temp_file)
        delete_path.unlink(missing_ok=True)
    except Exception as upload_exception:  # noqa: B902; return nicer error
        logger.error(f"File {temp_file} upload to bucket failed: {upload_exception}")
        file_info["status_msg"] = status_msg + f" Upload file {temp_file} to CS bucket failed."
        file_info["status"] = 500
    return file_info


def save_status_info(config: Config, files_summary: list) -> str:
    """
    Build CSV formatted migration information, 1 line per document, and save the result to cloud storage,
    returning a CS download URL.

    Args:
        config: Job configuration containing environment variables.
        files_summary: list of files migrated with summary information.
    """
    now_date = _datetime.now(timezone.utc).isoformat()[:10].replace("-", "/")
    bucket_path = config.CSV_STATUS_PATH
    storage_name: str = CSV_FILENAME.format(bucket_path=bucket_path, storage_date=now_date)
    doc_url: str = ""
    counter: int = 0
    status_msg: str = ""
    try:
        status_text: str = ""
        csv_lines = []
        for info in files_summary:
            counter += 1
            status_msg = f"File# {counter} BCMail filename={info.get("bcmail_filename")}"
            if info.get("drs_filesize") == 0 and info.get("status") == STATUS_SUCCESS:
                info["status_msg"] = ERROR_DRS_MISSING
                info["status"] = STATUS_ERROR
            elif info.get("drs_filesize") != info.get("bcmail_filesize") and info.get("status") == STATUS_SUCCESS:
                info["status_msg"] = ERROR_FILE_SIZE_MISMATCH
                info["status"] = STATUS_ERROR
            name = (
                f"{info.get("bcmail_dirname")}/{info.get("bcmail_filename")}"
                if info.get("bcmail_dirname")
                else info.get("bcmail_filename")
            )
            line: str = CSV_LINE.format(
                name=name,
                drs_id=info.get("drs_identifier"),
                drs_ts=info.get("drs_added_utc"),
                drs_name=info.get("drs_filename"),
                bcmail_size=info.get("bcmail_filesize"),
                drs_size=info.get("drs_filesize"),
                drs_doc_id=info.get("drs_document_id"),
                msg=info.get("status_msg"),
                status=info.get("status"),
            )
            csv_lines.append(line)
        status_text: str = CSV_HEADER + "".join(csv_lines)
        doc_url = GoogleStorageService.save_status_csv(storage_name, status_text)
    except Exception as err:
        logger.error(f"save_status_info {storage_name} failed: {status_msg} {err}")
    return doc_url


def send_status_notification(config: Config, files_summary: list, doc_url: str, dir_count: int) -> dict:
    """
    Send job status notification email after migrating the BCMail scanned documents.

    Args:
        config: Job configuration containing environment variables.
        files_summary: list of files migrated with summary information.
        doc_url: Status CSV file CS download URL.
        dir_count: Number of BCMail source sub-directorires/sub-folders containing migrated documents.
    """
    status_data: dict = copy.deepcopy(NOTIFY_STATUS_DATA)
    try:
        notify_client = Notify(config)
        error_count: int = 0
        for info in files_summary:
            if info.get("status") != STATUS_SUCCESS:
                error_count += 1
        now_date = _datetime.now(timezone.utc).astimezone(LOCAL_TZ)
        status_data["job_date"] = now_date.strftime("%B %-d, %Y at %-I:%M:%S %p Pacific time")
        status_data["csv_file_url"] = doc_url
        status_data["total_dir_count"] = dir_count
        status_data["total_file_count"] = len(files_summary)
        status_data["total_error_count"] = error_count
        notify_client.send_status(status_data)
    except Exception as err:
        logger.error(f"send_status_notification failed: {status_data} {err}")
    return status_data


def log_job_summary(status_data: dict):
    """
    Log a summary of the job run.

    Args:
        status_data: Contains the job summary status information.
    """
    job_info: str = f"Run completed. BCMail directory count={status_data.get("total_dir_count")}."
    job_info += f" Migration file count={status_data.get("total_file_count")}."
    job_info += f" Migration error count={status_data.get("total_error_count")}."
    logger.info(job_info)


def job(config: Config):
    """
    Summary:
        Synchronize legacy documents recently scanned by BCMail+ with the DRS. If documents have been copied to
        the BCRS LAN network drive (initial migration), access requires running a BCGOV VPN and mounting the drive
        locally. With this configuration, where the MIGRATE_LAN env var is true, the job can only run locally.

        For connectivity testing the env var LIST_FILES can be set to true. With this setting the job simply lists the
        BCMail+ remote sub-directories containing files to be migrated. No documents are migrated.

    Detail:
        Based on the MIGRATE_LAN and LIST_FILES environmet variables determine which task to perform:
        1. List LAN sub-directories: MIGRATE_LAN=true, LIST_FILES=true:
            a. Print to the console all sub-directories an files in the BCMAIL_LAN_DIR directory.
        2. Migrate LAN sub-directory files: requires BCMAIL_LAN_DIR, BCMAIL_LAN_FOLDERS, and BCMAIL_TEMP_DIR:
           MIGRATE_LAN=true, LIST_FILES=false:
            Iterate through the LAN sub-directories identified by BCMAIL_LAN_FOLDERS:
            a. Copy each file to a local temporary directory.
            b. Upload the temporary file contents to a dedicated BCMail GCP cloud storage bucket, then delete the
               temporary file.
            After all files have been stored in GCP CS:
            a. Update the file summary information with DRS document record information.
            b. Generate a CSV formatted summary of the job migration, 1 row per document migrated, and store it in
               GCP CS.
            c. Send an email notification of the job with a link to the CSV file.
        3. List Remote SFTP sub-directories: MIGRATE_LAN=false, LIST_FILES=true:
            a. Open a SFTP session with the BCMail+ service.
            b. Print to the console all sub-directories an files in the SFTP_DIR directory.
        4. Migrate SFTP directory files: requires SFTP_* environment variables:
           MIGRATE_LAN=false, LIST_FILES=false:
            Iterate through the SFTP_DIR sub-directories. Files in SFTP_DIR are ignored:
            a. Read each remote file and load as in memory bytes.
            b. Upload the remote file contents to a dedicated BCMail GCP cloud storage bucket.
            After all files have been stored in GCP CS:
            a. Update the file summary information with DRS document record information.
            b. Generate a CSV formatted summary of the job migration, 1 row per document migrated, and store it in
               GCP CS.
            c. Send an email notification of the job with a link to the CSV file.

    Args:
        config: Job configuration containing environment variables.

    Returns:
    """
    try:
        Database.init_app(config)

        if not config.LIST_FILES:
            files_summary = []
            bcmail_dirs = []
            if config.MIGRATE_LAN:
                lan_dirs: str = config.BCMAIL_LAN_FOLDERS
                bcmail_dirs = json.loads(lan_dirs) if lan_dirs else [""]
                files_summary = lan_migrate_bcmail(config, bcmail_dirs)
            else:
                files_summary, bcmail_dirs = sftp_migrate_bcmail(config)

            # Query status from DRS DB for recently added BCMail+ scanned documents.
            files_summary = Database.update_status_drs_info(files_summary)
            # Save job run status information to CS as a CSV file
            csv_status_url = save_status_info(config, files_summary)
            # Send job notification email.
            status_data = send_status_notification(config, files_summary, csv_status_url, len(bcmail_dirs))
            log_job_summary(status_data)
        else:
            if config.MIGRATE_LAN:
                lan_migrate_bcmail_dirs(config)
            else:
                sftp_migrate_bcmail_dirs(config)
            logger.info("Job list BCMail directories completed.")
    except (psycopg2.Error, Exception) as err:
        job_message: str = f"Run failed: {err}."
        logger.error(job_message)
        sys.exit(1)  # Retry Job Task by exiting the process
    finally:
        # Clean up: Close the database cursor and connection
        Database.close_app()
