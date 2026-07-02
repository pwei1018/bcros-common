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
"""All of the database connection and changes for the job are captured here.

Define SQL statements
Create database connections and cursors for the job.
Execute queries, updates, and inserts.
Close database connections and cursors on job completion.
"""
import copy
import json
from contextlib import suppress

import oracledb
import psycopg2

from doc_legacy_migration.config import Config
from doc_legacy_migration.utils.logging import logger

ALL_COUNT_SUMMARY = {
    "COOP": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "CORP": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "FIRM": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "LP_LLP": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "MHR": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "NR": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "PPR": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
    "SOCIETY": {"document_class": "", "max_doc_key": 0, "max_scan_date": "", "new_count": 0, "update_count": 0},
}

QUERY_DRS_COUNTS: str = """
select sld.document_class, max(sld.doc_key),
       (select to_char((max(ds.scan_date) + interval '1 days'), 'YYYY-MM-DD')
          from document_scanning ds
         where cast(ds.document_class as character varying) = sld.document_class)
  from staging_legacy_documents sld
group by sld.document_class
"""
QUERY_LEGACY_COUNTS: str = """
select (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('CP', 'XC')
           and d.document_id > {coop_key}) as coop_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('CP', 'XC')
           and d.document_id <= {coop_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{coop_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as coop_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and (substr(d.legal_entity_key, 1, 1) in ('A','B','C','Q','0','1','2','3','4','5','6','7','8','9') or
                substr(d.legal_entity_key, 1, 3) = 'LLC')
           and substr(d.legal_entity_key, 1, 2) != 'CP'
           and d.document_id > {corp_key}) as corp_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and (substr(d.legal_entity_key, 1, 1) in ('A','B','C','Q','0','1','2','3','4','5','6','7','8','9') or
                substr(d.legal_entity_key, 1, 3) = 'LLC')
           and substr(d.legal_entity_key, 1, 2) != 'CP'
           and d.document_id <= {corp_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{corp_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as corp_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('FM', 'GP', 'SP', 'MF')
           and d.document_id > {firm_key}) as firm_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('FM', 'GP', 'SP', 'MF')
           and d.document_id <= {firm_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{firm_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as firm_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('LP', 'LL', 'XL', 'XP')
           and substr(d.legal_entity_key, 1, 3) != 'LLC'
           and d.document_id > {lp_llp_key}) as lp_llp_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('LP', 'LL', 'XL', 'XP')
           and substr(d.legal_entity_key, 1, 3) != 'LLC'
           and d.document_id <= {lp_llp_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{lp_llp_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as lp_llp_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) = 'MH'
           and d.document_id > {mhr_key}) as mhr_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) = 'MH'
           and d.document_id <= {mhr_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{mhr_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as mhr_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('NR', 'nr')
           and d.document_id > {nr_key}) as nr_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) in ('NR', 'nr')
           and d.document_id <= {nr_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{nr_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as nr_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) = 'PP'
           and d.document_id > {ppr_key}) as ppr_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and substr(d.legal_entity_key, 1, 2) = 'PP'
           and d.document_id <= {ppr_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{ppr_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as ppr_update_count,
       (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and (substr(d.legal_entity_key, 1, 2) in ('XS') or substr(d.legal_entity_key, 1, 1) = 'S')
           and d.document_id > {society_key}) as soc_new_count,
        (select count(d.document_id)
          from correspondence.client_document d
         where d.legal_entity_key is not null
           and (substr(d.legal_entity_key, 1, 2) in ('XS') or substr(d.legal_entity_key, 1, 1) = 'S')
           and d.document_id <= {society_key}
           and d.scanned_date is not null
           and d.scanned_date >= to_date('{society_scan_date}', 'YYYY-MM-DD')
           and d.document_blob is not null) as soc_update_count
  from dual
"""
QUERY_LEGACY_CLASS = """
select d.document_id as doc_key,
       to_char(d.created_date, 'YYYY-MM-DD HH24:MM:DD') as created_date,
       to_char(d.barcode_num) as document_id,
       d.document_type_code,
       d.legal_entity_key as entity_id,
       d.document_filename,
       replace(replace(replace(d.document_desc, ',', ''), chr(13), ' '), chr(10), ' ') as document_desc,
       (select a.first_name || ' ' || a.last_name
          from author a
         where d.author_id = a.author_id) AS author,
       NVL(d.version, 1) as version,
       to_char(d.filed_date, 'YYYY-MM-DD HH24:MM:DD') as filed_date,
       TO_CHAR(d.scanned_date, 'YYYY-MM-DD HH24:MM:DD') as scanned_date,
       TO_CHAR(d.ACCESSION_NUM) as accession_number,
       NVL(d.PAGE_COUNT, 0) as page_count,
       TO_CHAR(d.batch_id) as batch_id,
       d.event_id,
       d.document_blob
  from correspondence.client_document d
 where d.legal_entity_key is not null
"""
QUERY_LEGACY_CLASS_MHR = """
select d.document_id as doc_key,
       to_char(d.created_date, 'YYYY-MM-DD HH24:MM:DD') as created_date,
       to_char(d.barcode_num) as document_id,
       DECODE(d.document_type_code,
             '101', 'REG_101',
             '103', 'REG_103',
             '102', 'REG_102', d.document_type_code) as document_type_code,
       'MH' || substr(d.legal_entity_key, -6) as entity_id,
       d.document_filename,
       replace(replace(replace(d.document_desc, ',', ''), chr(13), ' '), chr(10), ' ') as document_desc,
       (select a.first_name || ' ' || a.last_name
          from author a
         where d.author_id = a.author_id) AS author,
       NVL(d.version, 1) as version,
       to_char(d.filed_date, 'YYYY-MM-DD HH24:MM:DD') as filed_date,
       TO_CHAR(d.scanned_date, 'YYYY-MM-DD HH24:MM:DD') as scanned_date,
       TO_CHAR(d.ACCESSION_NUM) as accession_number,
       NVL(d.PAGE_COUNT, 0) as page_count,
       TO_CHAR(d.batch_id) as batch_id,
       d.event_id,
       d.document_blob
  from correspondence.client_document d
 where d.legal_entity_key is not null
"""
QUERY_CLAUSE_COMMON = " and d.document_id > {doc_id}"
QUERY_CLAUSE_COOP = QUERY_CLAUSE_COMMON + " and substr(d.legal_entity_key, 1, 2) in ('CP', 'XC')"
QUERY_CLAUSE_CORP = (
    QUERY_CLAUSE_COMMON
    + """
   and (substr(d.legal_entity_key, 1, 1) in ('A', 'B', 'C', 'Q','0', '1', '2', '3', '4', '5', '6' ,'7', '8', '9') or
        substr(d.legal_entity_key, 1, 3) = 'LLC')
   and substr(d.legal_entity_key, 1, 2) != 'CP'
   and d.document_id != 62317053
"""
)
QUERY_CLAUSE_FIRM = QUERY_CLAUSE_COMMON + " and substr(d.legal_entity_key, 1, 2) in ('FM', 'GP', 'SP', 'MF')"
QUERY_CLAUSE_LP_LLP = (
    QUERY_CLAUSE_COMMON
    + """
   and substr(d.legal_entity_key, 1, 2) in ('LP', 'LL', 'XL', 'XP')
   and substr(d.legal_entity_key, 1, 3) != 'LLC'
"""
)
QUERY_CLAUSE_MHR = QUERY_CLAUSE_COMMON + " and substr(d.legal_entity_key, 1, 2) = 'MH'"
QUERY_CLAUSE_NR = QUERY_CLAUSE_COMMON + " and upper(substr(d.legal_entity_key, 1, 2)) = 'NR'"
QUERY_CLAUSE_PPR = QUERY_CLAUSE_COMMON + " and substr(d.legal_entity_key, 1, 2) = 'PP'"
QUERY_CLAUSE_SOCIETY = (
    QUERY_CLAUSE_COMMON
    + """
 and (substr(d.legal_entity_key, 1, 2) in ('XS') or substr(d.legal_entity_key, 1, 1) = 'S')
"""
)

UPDATE_CLAUSE_COMMON = """
   and d.document_id <= {doc_id}
   and d.scanned_date is not null
   and d.scanned_date >= to_date('{scan_date}', 'YYYY-MM-DD')
"""
UPDATE_CLAUSE_COOP = " and substr(d.legal_entity_key, 1, 2) in ('CP', 'XC')" + UPDATE_CLAUSE_COMMON
UPDATE_CLAUSE_CORP = (
    """
   and (substr(d.legal_entity_key, 1, 1) in ('A', 'B', 'C', 'Q','0', '1', '2', '3', '4', '5', '6' ,'7', '8', '9') or
        substr(d.legal_entity_key, 1, 3) = 'LLC')
   and substr(d.legal_entity_key, 1, 2) != 'CP'
"""
    + UPDATE_CLAUSE_COMMON
)
UPDATE_CLAUSE_FIRM = " and substr(d.legal_entity_key, 1, 2) in ('FM', 'GP', 'SP', 'MF')" + UPDATE_CLAUSE_COMMON
UPDATE_CLAUSE_LP_LLP = (
    """
   and substr(d.legal_entity_key, 1, 2) in ('LP', 'LL', 'XL', 'XP')
   and substr(d.legal_entity_key, 1, 3) != 'LLC'
"""
    + UPDATE_CLAUSE_COMMON
)
UPDATE_CLAUSE_MHR = " and substr(d.legal_entity_key, 1, 2) = 'MH'" + UPDATE_CLAUSE_COMMON
UPDATE_CLAUSE_NR = " and upper(substr(d.legal_entity_key, 1, 2)) = 'NR'" + UPDATE_CLAUSE_COMMON
UPDATE_CLAUSE_PPR = " and substr(d.legal_entity_key, 1, 2) = 'PP'" + UPDATE_CLAUSE_COMMON
UPDATE_CLAUSE_SOCIETY = (
    """
   and (substr(d.legal_entity_key, 1, 2) in ('XS') or substr(d.legal_entity_key, 1, 1) = 'S')
"""
    + UPDATE_CLAUSE_COMMON
)

CLASS_NEW_CLAUSE = {
    "COOP": QUERY_CLAUSE_COOP,
    "CORP": QUERY_CLAUSE_CORP,
    "FIRM": QUERY_CLAUSE_FIRM,
    "LP_LLP": QUERY_CLAUSE_LP_LLP,
    "MHR": QUERY_CLAUSE_MHR,
    "NR": QUERY_CLAUSE_NR,
    "PPR": QUERY_CLAUSE_PPR,
    "SOCIETY": QUERY_CLAUSE_SOCIETY,
}
CLASS_UPDATE_CLAUSE = {
    "COOP": UPDATE_CLAUSE_COOP,
    "CORP": UPDATE_CLAUSE_CORP,
    "FIRM": UPDATE_CLAUSE_FIRM,
    "LP_LLP": UPDATE_CLAUSE_LP_LLP,
    "MHR": UPDATE_CLAUSE_MHR,
    "NR": UPDATE_CLAUSE_NR,
    "PPR": UPDATE_CLAUSE_PPR,
    "SOCIETY": UPDATE_CLAUSE_SOCIETY,
}
QUERY_ORDER_BY = " order by d.document_id"
INSERT_AUDIT_STATEMENT = """
INSERT INTO staging_legacy_documents(doc_key, add_ts, document_id, document_type, entity_id, filename,
                                     file_description, author, doc_version, filed_date, doc_storage_url,
                                     event_id, document_class)
    VALUES({doc_key},
           '{created_date}',
           {document_id},
           '{document_type}',
           '{entity_id}',
           {filename},
           {document_desc},
           {author},
           '{doc_version}',
           '{filed_date}',
           {doc_storage_url},
           {event_id},
           '{document_class}')
"""
INSERT_DOC_STATEMENT = """
INSERT INTO documents (id, document_service_id, add_ts, consumer_document_id, consumer_identifier, consumer_filename,
                       consumer_filing_date, doc_storage_url, document_type, document_class, description, author,
                       consumer_reference_id)
    VALUES(nextval('document_id_seq'),
           get_service_doc_id(),
           (TO_TIMESTAMP('{created_date}', 'YYYY-MM-DD HH24:MI:SS') at time zone 'utc'),
           {document_id},
           '{entity_id}',
           {filename},
           (TO_TIMESTAMP('{filed_date}', 'YYYY-MM-DD HH24:MI:SS') at time zone 'utc'),
           {doc_storage_url},
           cast('{document_type}' as documenttype),
           '{document_class}',
           {document_desc},
           {author},
           cast({event_id} as character varying))
"""
INSERT_SCANNING_STATEMENT = """
INSERT INTO document_scanning (id, consumer_document_id, document_class, create_ts, scan_date, accession_number,
                               batch_id, author, page_count)
    VALUES(nextval('doc_scanning_id_seq'),
           '{document_id}',
           '{document_class}',
           now() at time zone 'utc',
           (TO_TIMESTAMP('{scanned_date}', 'YYYY-MM-DD HH24:MI:SS') at time zone 'utc'),
           '{accession_number}',
           '{batch_id}',
           {author},
           {page_count})
 ON CONFLICT (consumer_document_id,document_class)
 DO UPDATE SET
    scan_date = (TO_TIMESTAMP('{scanned_date}', 'YYYY-MM-DD HH24:MI:SS') at time zone 'utc'),
    accession_number = '{accession_number}',
    batch_id = '{batch_id}',
    author = {author},
    page_count = {page_count};
"""


class Database:  # pylint: disable=too-few-public-methods
    """Database object."""

    doc_db_conn: psycopg2.extensions.connection
    doc_db_cursor: psycopg2.extensions.cursor
    legacy_db_conn: oracledb.Connection
    legacy_db_cursor: oracledb.Cursor

    @staticmethod
    def init_app(config: Config):
        """Set up the job database connections and cursors."""
        logger.info("Job getting doc database connection and cursor.")
        Database.doc_db_conn = psycopg2.connect(dsn=config.DOC_DB_URI)
        Database.doc_db_cursor = Database.doc_db_conn.cursor()
        logger.info("Job getting legacy database connection and cursor.")
        Database.legacy_db_conn = oracledb.connect(dsn=config.LEGACY_DB_URI)
        Database.legacy_db_cursor = Database.legacy_db_conn.cursor()

    @staticmethod
    def close_app():
        """Close the database cursors and connections."""
        with suppress(Exception):
            Database.legacy_db_cursor.close()
        with suppress(Exception):
            Database.legacy_db_conn.close()
        with suppress(Exception):
            Database.doc_db_cursor.close()
        with suppress(Exception):
            Database.doc_db_conn.close()

    @classmethod
    def run_legacy_query(cls, class_info: dict, new: bool) -> list:
        """Perform legacy query new or update changes by document class."""
        try:
            doc_class: str = class_info.get("document_class")
            class_query: str = QUERY_LEGACY_CLASS if doc_class != "MHR" else QUERY_LEGACY_CLASS_MHR
            clause: str = CLASS_NEW_CLAUSE.get(doc_class) if new else CLASS_UPDATE_CLAUSE.get(doc_class)
            if new:
                clause = clause.format(doc_id=class_info.get("max_doc_key"))
            else:
                clause = clause.format(doc_id=class_info.get("max_doc_key"), scan_date=class_info.get("max_scan_date"))
            class_query += clause + QUERY_ORDER_BY
            logger.info(f"run_legacy_query query={class_query}")
            Database.legacy_db_cursor.execute(class_query)
            legacy_rows = Database.legacy_db_cursor.fetchall()
            logger.info("Legacy documents query execution completed.")
            return legacy_rows
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error(f"run_legacy_query failed: {db_exception}")
            return []

    @classmethod
    def get_legacy_counts_query(cls, summary: dict) -> str:
        """Build the legacy counts query using the previous migration DRS document keys and scan dates by class."""
        statement: str = QUERY_LEGACY_COUNTS.format(
            coop_key=summary["COOP"].get("max_doc_key"),
            coop_scan_date=summary["COOP"].get("max_scan_date"),
            corp_key=summary["CORP"].get("max_doc_key"),
            corp_scan_date=summary["CORP"].get("max_scan_date"),
            firm_key=summary["FIRM"].get("max_doc_key"),
            firm_scan_date=summary["FIRM"].get("max_scan_date"),
            lp_llp_key=summary["LP_LLP"].get("max_doc_key"),
            lp_llp_scan_date=summary["LP_LLP"].get("max_scan_date"),
            mhr_key=summary["MHR"].get("max_doc_key"),
            mhr_scan_date=summary["MHR"].get("max_scan_date"),
            nr_key=summary["NR"].get("max_doc_key"),
            nr_scan_date=summary["NR"].get("max_scan_date"),
            ppr_key=summary["PPR"].get("max_doc_key"),
            ppr_scan_date=summary["PPR"].get("max_scan_date"),
            society_key=summary["SOCIETY"].get("max_doc_key"),
            society_scan_date=summary["SOCIETY"].get("max_scan_date"),
        )
        return statement

    @classmethod
    def get_summary_counts(cls, config: Config) -> dict:
        """Get job summary counts from DRS and the legacy database by document class."""
        drs_statement: str = QUERY_DRS_COUNTS
        summary: dict = copy.deepcopy(ALL_COUNT_SUMMARY)
        logger.debug(f"Executing query to get DRS summary counts: {drs_statement}")
        Database.doc_db_cursor.execute(drs_statement)
        drs_rows = Database.doc_db_cursor.fetchall()
        for row in drs_rows:
            doc_class: str = str(row[0])
            summary[doc_class]["document_class"] = doc_class
            summary[doc_class]["max_doc_key"] = int((row[1]))
            summary[doc_class]["max_scan_date"] = str((row[2]))
        legacy_statement: str = cls.get_legacy_counts_query(summary)
        logger.debug(f"Executing query to get legacy summary counts: {legacy_statement}")
        Database.legacy_db_cursor.execute(legacy_statement)
        legacy_rows = Database.legacy_db_cursor.fetchall()
        legacy_row = legacy_rows[0]
        summary["COOP"]["new_count"] = int(legacy_row[0])
        summary["COOP"]["update_count"] = int(legacy_row[1])
        summary["CORP"]["new_count"] = int(legacy_row[2])
        summary["CORP"]["update_count"] = int(legacy_row[3])
        summary["FIRM"]["new_count"] = int(legacy_row[4])
        summary["FIRM"]["update_count"] = int(legacy_row[5])
        summary["LP_LLP"]["new_count"] = int(legacy_row[6])
        summary["LP_LLP"]["update_count"] = int(legacy_row[7])
        summary["MHR"]["new_count"] = int(legacy_row[8])
        summary["MHR"]["update_count"] = int(legacy_row[9])
        summary["NR"]["new_count"] = int(legacy_row[10])
        summary["NR"]["update_count"] = int(legacy_row[11])
        summary["PPR"]["new_count"] = int(legacy_row[12])
        summary["PPR"]["update_count"] = int(legacy_row[13])
        summary["SOCIETY"]["new_count"] = int(legacy_row[14])
        summary["SOCIETY"]["update_count"] = int(legacy_row[15])
        logger.info(f"Loaded summary info: {json.dumps(summary)}")
        return summary

    @classmethod
    def create_audit_record(cls, rec_json: dict) -> dict:
        """Create an individual staging/audit record from a single legacy query result."""
        if rec_json.get("status") != 200:
            logger.info(f"Doc key {rec_json.get("doc_key")} error status skipping audit record creation")
            rec_json["error_msg"] = rec_json.get("error_msg") + " Skipping audit record creation."
            return rec_json
        storage_url = "'" + rec_json.get("doc_storage_url") + "'" if rec_json.get("doc_storage_url") else "null"
        filename = "'" + rec_json.get("filename") + "'" if rec_json.get("filename") else "null"
        doc_desc = "'" + rec_json.get("document_desc") + "'" if rec_json.get("document_desc") else "null"
        author = "'" + rec_json.get("author") + "'" if rec_json.get("author") else "null"
        event_id = rec_json.get("event_id") if rec_json.get("event_id") else "null"
        # Allow for no document ID (not scanned): NR and SOCIETY
        document_id = "'" + rec_json.get("document_id") + "'" if rec_json.get("document_id") else "null"
        sql_statement: str = INSERT_AUDIT_STATEMENT.format(
            doc_key=rec_json.get("doc_key"),
            created_date=rec_json.get("created_date"),
            document_id=document_id,
            document_type=rec_json.get("document_type"),
            entity_id=rec_json.get("entity_id"),
            filename=filename,
            document_desc=doc_desc,
            author=author,
            doc_version=rec_json.get("version"),
            filed_date=rec_json.get("filed_date"),
            doc_storage_url=storage_url,
            event_id=event_id,
            document_class=rec_json.get("document_class"),
        )
        try:
            Database.doc_db_cursor.execute(sql_statement)
            Database.doc_db_conn.commit()
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error(f"create_audit_record failed for key {rec_json.get("doc_key")}: {db_exception}")
            rec_json["error_msg"] = rec_json.get("error_msg") + " create_audit_record failed see log."
            rec_json["status"] = 500
        return rec_json

    @classmethod
    def create_document_record(cls, rec_json: dict) -> dict:
        """Create an individual document record service document record from the legacy record."""
        if rec_json.get("status") != 200:
            logger.info(f"Doc key {rec_json.get("doc_key")} error status skipping document record creation")
            rec_json["error_msg"] = rec_json.get("error_msg") + " Skipping document record creation."
            return rec_json
        storage_url = "'" + rec_json.get("doc_storage_url") + "'" if rec_json.get("doc_storage_url") else "null"
        filename = "'" + rec_json.get("filename") + "'" if rec_json.get("filename") else "null"
        doc_desc = "'" + rec_json.get("document_desc") + "'" if rec_json.get("document_desc") else "null"
        author = "'" + rec_json.get("author") + "'" if rec_json.get("author") else "null"
        event_id = "'" + str(rec_json.get("event_id")) + "'" if rec_json.get("event_id") else "null"
        # Allow for no document ID (not scanned): NR and SOCIETY
        document_id = "'" + str(rec_json.get("document_id")) + "'"
        if not rec_json.get("document_id"):
            document_id = "get_document_number()"
        sql_statement: str = INSERT_DOC_STATEMENT.format(
            created_date=rec_json.get("created_date"),
            document_id=document_id,
            entity_id=rec_json.get("entity_id"),
            filename=filename,
            filed_date=rec_json.get("filed_date"),
            doc_storage_url=storage_url,
            document_type=rec_json.get("document_type"),
            document_class=rec_json.get("document_class"),
            document_desc=doc_desc,
            author=author,
            event_id=event_id,
        )
        try:
            Database.doc_db_cursor.execute(sql_statement)
            Database.doc_db_conn.commit()
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error(f"create_doc_record failed for key {rec_json.get("doc_key")}: {db_exception}")
            rec_json["error_msg"] = rec_json.get("error_msg") + " create_doc_record failed see log."
            rec_json["status"] = 500
        return rec_json

    @classmethod
    def create_scanning_record(cls, rec_json: dict):
        """Create an individual document scanning information record from the legacy record."""
        if rec_json.get("status") != 200:
            logger.info(f"Doc key {rec_json.get("doc_key")} error status skipping scanning record creation")
            rec_json["error_msg"] = rec_json.get("error_msg") + " Skipping scanning record creation."
            return rec_json
        author = "'" + rec_json.get("author") + "'" if rec_json.get("author") else "null"
        sql_statement: str = INSERT_SCANNING_STATEMENT.format(
            document_id=rec_json.get("document_id"),
            document_class=rec_json.get("document_class"),
            scanned_date=rec_json.get("scanned_date"),
            accession_number=rec_json.get("accession_number"),
            batch_id=rec_json.get("batch_id"),
            author=author,
            page_count=rec_json.get("page_count"),
        )
        try:
            Database.doc_db_cursor.execute(sql_statement)
            Database.doc_db_conn.commit()
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error(f"create_scan_record failed for key {rec_json.get("doc_key")}: {db_exception}")
            rec_json["error_msg"] = rec_json.get("error_msg") + " create_scan_record failed see log."
            rec_json["status"] = 500
        return rec_json

    @classmethod
    def update_audit_record(cls, rec_json: dict) -> dict:
        """Update an individual staging/audit record from a single legacy query result."""
        if rec_json.get("status") != 200:
            logger.info(f"Doc key {rec_json.get("doc_key")} error status skipping audit record update")
            rec_json["error_msg"] = rec_json.get("error_msg") + " Skipping audit record update."
            return rec_json
        sql_statement: str = (
            f"update staging_legacy_documents set doc_storage_url = '{rec_json.get("doc_storage_url")}'"
        )
        if rec_json.get("filename"):
            sql_statement += f", filename = '{rec_json.get("filename")}'"
        if rec_json.get("entity_id"):
            sql_statement += f", entity_id = '{rec_json.get("entity_id")}'"
        if rec_json.get("event_id"):
            sql_statement += f", event_id = {rec_json.get("event_id")}"
        if rec_json.get("filed_date"):
            sql_statement += f", filed_date = '{rec_json.get("filed_date")}'"
        if rec_json.get("document_desc"):
            sql_statement += f", file_description = '{rec_json.get("document_desc")}'"
        if rec_json.get("author"):
            sql_statement += f", author = '{rec_json.get("author")}'"
        if rec_json.get("version"):
            sql_statement += f", doc_version = {rec_json.get("version")}"
        sql_statement += f" where doc_key = {rec_json.get("doc_key")}"
        try:
            Database.doc_db_cursor.execute(sql_statement)
            Database.doc_db_conn.commit()
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error(f"update_audit_record failed for key {rec_json.get("doc_key")}: {db_exception}")
            rec_json["error_msg"] = rec_json.get("error_msg") + " update_audit_record failed see log."
        return rec_json

    @classmethod
    def update_document_record(cls, rec_json: dict) -> dict:
        """Update an individual document record service document record from the legacy record."""
        if rec_json.get("status") != 200:
            logger.info(f"Doc key {rec_json.get("doc_key")} error status skipping document record update")
            rec_json["error_msg"] = rec_json.get("error_msg") + " Skipping document record update."
            return rec_json
        sql_statement: str = f"update documents set doc_storage_url = '{rec_json.get("doc_storage_url")}'"
        if rec_json.get("filename"):
            sql_statement += f", consumer_filename = '{rec_json.get("filename")}'"
        if rec_json.get("filed_date"):
            fts: str = f"(TO_TIMESTAMP('{rec_json.get("filed_date")}', 'YYYY-MM-DD HH24:MI:SS') at time zone 'utc')"
            sql_statement += f", consumer_filing_date = {fts}"
        if rec_json.get("event_id"):
            sql_statement += f", consumer_reference_id = cast({rec_json.get("event_id")} as character varying)"
        if rec_json.get("document_desc"):
            sql_statement += f", description = '{rec_json.get("document_desc")}'"
        if rec_json.get("author"):
            sql_statement += f", author = '{rec_json.get("author")}'"
        sql_statement += f" where document_class = '{rec_json.get("document_class")}'"
        sql_statement += f" and consumer_document_id = '{rec_json.get("document_id")}'"
        try:
            Database.doc_db_cursor.execute(sql_statement)
            Database.doc_db_conn.commit()
        except Exception as db_exception:  # noqa: B902; return nicer error
            logger.error(f"update_doc_record failed for key {rec_json.get("doc_key")}: {db_exception}")
            rec_json["error_msg"] = rec_json.get("error_msg") + " update_doc_record failed see log."
            rec_json["status"] = 500
        return rec_json
