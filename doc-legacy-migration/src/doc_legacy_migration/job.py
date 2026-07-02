# Copyright © 2025 Province of British Columbia
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
# import copy
# import io
import json
import sys

# from contextlib import suppress
from datetime import datetime as _datetime

import psycopg2

from doc_legacy_migration.config import Config
from doc_legacy_migration.database import Database
from doc_legacy_migration.services.abstract_storage_service import DocumentTypes
from doc_legacy_migration.services.document_storage.storage_service import GoogleStorageService
from doc_legacy_migration.utils.logging import logger

# import pytz


DOCUMENT_CLASSES = ["COOP", "CORP", "FIRM", "LP_LLP", "MHR", "NR", "PPR", "SOCIETY"]
STORAGE_DOC_NAME = "{legacy_date}/{doc_type}-{doc_key}.pdf"
CSV_FILENAME = "csv/tracking-{doc_class}-{change_type}-{job_date}.csv"
CSV_LINE = (
    "{status},{key},'{create_dt}','{doc_id}','{doc_type}','{entity_id}','{fname}',{version},'{file_dt}',"
    + "'{doc_url}','{scan_dt}','{a_num}','{batch_id}',{event_id},'{err}'\n"
)
TO_STORAGE_TYPE = {
    "MHR": DocumentTypes.MHR,
    "NR": DocumentTypes.NR,
    "PPR": DocumentTypes.PPR,
    "CORP": DocumentTypes.BUSINESS,
    "COOP": DocumentTypes.BUSINESS,
    "FIRM": DocumentTypes.BUSINESS,
    "LP_LLP": DocumentTypes.BUSINESS,
    "SOCIETY": DocumentTypes.BUSINESS,
}


def get_storage_name(created_date: str, doc_key: int, doc_type: str) -> str:
    """Get doc storage name for a legacy document record."""
    legacy_date: str = created_date[0:10].replace("-", "/")
    storage_name = STORAGE_DOC_NAME.format(legacy_date=legacy_date, doc_type=doc_type, doc_key=doc_key)
    return storage_name


def update_tracking_info(tracking_info: str, rec_json: dict) -> str:
    """Record the result of a single record change as a csv formatted line."""
    line: str = CSV_LINE.format(
        status=rec_json.get("status"),
        key=rec_json.get("doc_key"),
        create_dt=rec_json.get("created_date"),
        doc_id=rec_json.get("document_id"),
        doc_type=rec_json.get("document_type"),
        entity_id=rec_json.get("entity_id"),
        fname=rec_json.get("filename") if rec_json.get("filename") else "",
        version=rec_json.get("version"),
        file_dt=rec_json.get("filed_date"),
        doc_url=rec_json.get("doc_storage_url") if rec_json.get("doc_storage_url") else "",
        scan_dt=rec_json.get("scanned_date") if rec_json.get("scanned_date") else "",
        a_num=rec_json.get("accession_number") if rec_json.get("accession_number") else "",
        batch_id=rec_json.get("batch_id") if rec_json.get("batch_id") else "",
        event_id=rec_json.get("event_id") if rec_json.get("event_id") else "",
        err=rec_json.get("error_msg"),
    )
    tracking_info += line
    return tracking_info


def save_tracking_info(tracking_info: str, doc_class: str, change_type: str, current_date: str):
    """Save the results of all record changes for a document class to a csv formatted file."""
    fname: str = CSV_FILENAME.format(doc_class=doc_class, change_type=change_type, job_date=current_date[0:10])
    with open(fname, "w") as csv_file:
        csv_file.write(tracking_info)
        csv_file.close()


def save_document(rec_json: dict, storage_type: str, lob_object) -> dict:
    """Save legacy document to storage if data exists."""
    if not lob_object:
        rec_json["doc_storage_url"] = None
        return rec_json
    storage_name = get_storage_name(rec_json["created_date"], rec_json["doc_key"], rec_json["document_type"])
    try:
        doc_data = lob_object.read()
        GoogleStorageService.save_document(storage_name, doc_data, storage_type)
        rec_json["doc_storage_url"] = storage_name
    except Exception as err:
        logger.error(f"save_document {storage_name} failed: {err}")
        rec_json["status"] = 500
        rec_json["error_msg"] = rec_json.get("error_msg") + f" save_document {storage_name} failed (see log)."
    return rec_json


def get_legacy_json(row: dict, document_class: str) -> dict:
    """Load the legacy query result set row into json."""
    doc_desc: str = str(row[6]) if row[6] else None
    if doc_desc:
        doc_desc = doc_desc.replace("'", "''")
    author: str = str(row[7]) if row[7] else None
    if author:
        author = author.replace("'", "''")
    result = {
        "status": 200,
        "doc_key": int(row[0]),
        "created_date": str(row[1]),
        "document_id": str(row[2]) if row[2] else None,
        "document_type": str(row[3]),
        "entity_id": str(row[4]),
        "filename": str(row[5]) if row[5] else None,
        "document_desc": doc_desc,
        "author": author,
        "version": int(row[8]),
        "filed_date": str(row[9]) if row[9] else str(row[1]),
        "scanned_date": str(row[10]) if row[10] else None,
        "accession_number": str(row[11]) if row[11] else None,
        "page_count": int(row[12]),
        "batch_id": str(row[13]) if row[13] else None,
        "event_id": int(row[14]) if row[14] else None,
        "document_class": document_class,
        "error_msg": "",
    }
    if result.get("filename") and not str(result.get("filename")).endswith(".pdf"):
        result["filename"] = result["filename"] + ".pdf"
    return result


def synchronize_new_records(config: Config, class_info: dict, current_date: str):
    """
    Migrate legacy records created since the last job run by document class.

    Args:
        config: Job configuration containing environment variables.
        class_info: Contains the most recent legacy document key and most recent scan date for the document class.
        current_date: Used for tracking changes.
    """
    doc_class: str = class_info.get("document_class")
    new_count: int = class_info.get("new_count", 0)
    logger.info(f"synchronize_new_records starting class={doc_class}, new_count={new_count}")
    if new_count < 1:
        logger.info(f"Skipping new records for {doc_class}: count 0")
        class_info["err_count_new"] = 0
        return
    csv_tracking: bool = config.CSV_TRACKING == "true"
    tracking_info: str = ""
    storage_type: str = TO_STORAGE_TYPE[doc_class]
    legacy_rows = Database.run_legacy_query(class_info, True)
    err_count: int = 0
    for row in legacy_rows:
        rec_json: dict = get_legacy_json(row, doc_class)
        rec_json = save_document(rec_json, storage_type, row[15])
        rec_json = Database.create_audit_record(rec_json)
        rec_json = Database.create_document_record(rec_json)
        if rec_json.get("accession_number") and rec_json.get("scanned_date") and rec_json.get("document_id"):
            rec_json = Database.create_scanning_record(rec_json)
        if rec_json.get("status") != 200:
            err_count += 1
        if csv_tracking:
            tracking_info = update_tracking_info(tracking_info, rec_json)
    class_info["err_count_new"] = err_count
    if csv_tracking:
        save_tracking_info(tracking_info, doc_class, "new", current_date)


def synchronize_update_records(config: Config, class_info: dict, current_date: str):
    """
    Migrate legacy records updated since the last job run by document class.

    Args:
        config: Job configuration containing environment variables.
        class_info: Contains the most recent legacy document key and most recent scan date for the document class.
        current_date: Used for tracking changes.
    """
    doc_class: str = class_info.get("document_class")
    update_count: int = class_info.get("update_count", 0)
    logger.info(f"synchronize_update_records starting class={doc_class}, update_count={update_count}")
    if update_count < 1:
        logger.info(f"Skipping update records for {doc_class}: count 0")
        class_info["err_count_update"] = 0
        return
    csv_tracking: bool = config.CSV_TRACKING == "true"
    tracking_info: str = ""
    storage_type: str = TO_STORAGE_TYPE[doc_class]
    legacy_rows = Database.run_legacy_query(class_info, False)
    err_count: int = 0
    for row in legacy_rows:
        rec_json: dict = get_legacy_json(row, doc_class)
        rec_json = save_document(rec_json, storage_type, row[15])
        rec_json = Database.update_audit_record(rec_json)
        if rec_json.get("version") > 1:
            rec_json = Database.create_document_record(rec_json)
        else:
            rec_json = Database.update_document_record(rec_json)
        if rec_json.get("accession_number") and rec_json.get("scanned_date") and rec_json.get("document_id"):
            # Inserts or updates
            rec_json = Database.create_scanning_record(rec_json)
        if rec_json.get("status") != 200:
            err_count += 1
        if csv_tracking:
            tracking_info = update_tracking_info(tracking_info, rec_json)
    class_info["err_count_update"] = err_count
    if csv_tracking:
        save_tracking_info(tracking_info, doc_class, "update", current_date)


def log_job_summary(class_counts: dict):
    """
    Log a summary of the job run.

    Args:
        class_info: Contains the job record counts by document class.
    """
    job_info: str = "Run completed. Summary counts by document class:\n"
    line_item: str = "{dclass}: new={new}, update={update}, new errors={err_new}, update errors={err_update}\n"
    for doc_class in DOCUMENT_CLASSES:
        class_info = class_counts.get(doc_class)
        job_info += line_item.format(
            dclass=class_info.get("document_class"),
            new=class_info.get("new_count"),
            update=class_info.get("update_count"),
            err_new=class_info.get("err_count_new"),
            err_update=class_info.get("err_count_update"),
        )
    logger.info(job_info)


def job(config: Config):
    """
    Summary:
        Synchronize legacy document records in the Oracle globalp db correspondence schema with the DRS.
        Legacy database access requires running a VPN.
        Synchronization is in one direction: from legacy to DRS.
        Synchronization is in 2 steps:
        1. New document records created since the last time this job ran.
        2. Updates to document records that exist in the DRS and where changes have occurred since the last time
           this job ran (scanning a document).

    Detail:
        Execute a summary query to get the most recent DRS scanned doc timestamp and legacy document record key for
        each DRS document class.
        For each document class:
        1. Fetch new records from the legacy database. For each record:
            a. If there is a legacy document, save it to cloud storage.
            b. Insert into the tracking table staging_legacy_documents with the cloud storage path if available.
            c. Insert into the DRS documents table.
            d. Insert into the DRS document_scanning table if the legacy record includes scanning information.
        2. Fetch updated records from the legacy database that have documents.
            a. Save the legacy document to cloud storage.
            b. Update into the tracking table staging_legacy_documents with the cloud storage path and other data.
            c. Update the DRS documents table.
            d. Insert into the DRS document_scanning table if the legacy record includes scanning information.

        Optionally save csv formatted summary/status information for the job by document class.

    Args:
        config: Job configuration containing environment variables.

    Returns:
    """
    try:
        Database.init_app(config)
        current_date: str = _datetime.now().isoformat()
        class_counts: dict = Database.get_summary_counts(config)
        logger.info(f"Counts by document class:\n{json.dumps(class_counts)}")
        for doc_class in DOCUMENT_CLASSES:
            class_info = class_counts.get(doc_class)
            new_count: int = class_info.get("new_count")
            update_count: int = class_info.get("update_count")
            logger.info(f"Migrating {doc_class} new document count={new_count} update count={update_count}.")
            synchronize_new_records(config, class_info, current_date)
            synchronize_update_records(config, class_info, current_date)
        log_job_summary(class_counts)
    except (psycopg2.Error, Exception) as err:
        job_message: str = f"Run failed: {err}."
        logger.error(job_message)
        sys.exit(1)  # Retry Job Task by exiting the process
    finally:
        # Clean up: Close the database cursor and connection
        Database.close_app()
