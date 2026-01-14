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
import json
from contextlib import suppress

import psycopg2

from colin_report_migration.config import Config
from colin_report_migration.utils.logging import logger

QUERY_JOB_CORPS_BASE = """
select m.corp_num, c.corp_password
  from mig_colin_reports m, colin_extract.corporation c
 where c.corp_num = m.corp_num
   and m.migrated_ts is null
   and c.corp_password is not null
"""
QUERY_CORPS_JOB_ID_CLAUSE = " and m.job_id is not null and m.job_id = {job_id}"
QUERY_CORPS_CORP_STATE_CLAUSE = " and m.op_state_type_cd = '{corp_state}'"
QUERY_CORPS_YEAR_CLAUSE = " and m.recognition_dts is not null and EXTRACT(year from m.recognition_dts) = {corp_year}"
QUERY_CORPS_SIZE_LIMIT = " fetch first {job_size} rows only"
QUERY_FILINGS = """
select to_char(e.event_timerstamp, 'YYYY-MM-DD HH24:MI:SS') as filing_date, f.event_id, f.filing_type_cd,
       trim(to_char((e.event_timerstamp at time zone 'PST'), 'Month')) ||
       to_char((e.event_timerstamp at time zone 'PST'), ' DD, YYYY') as report_date
  from colin_extract.filing f, colin_extract.event e
 where e.event_id = f.event_id
   and e.corp_num = '{corp_num}'
 order by f.effective_dt desc
"""
QUERY_JOB_CORP_UPDATE = """
update mig_colin_reports
   set migrated_ts = now() at time zone 'utc',
       report_count = {report_count},
       error_count = {err_count},
       migration_summary = '{summary}'
 where corp_num = '{corp_num}'
 """
INSERT_DRS_STATEMENT = """
INSERT INTO application_reports(id, document_service_id, product_code, create_ts, entity_id, event_id,
                                report_type, filing_date, filename, doc_storage_url)
    VALUES(nextval('application_report_id_seq'),
           get_service_report_id(),
           'BUSINESS',
           now() at time zone 'utc',
           '{corp_num}',
           {event_id},
           '{report_type}',
           (TO_TIMESTAMP('{filing_date}', 'YYYY-MM-DD HH24:MI:SS') at time zone 'utc'),
           '{filename}',
           '{doc_storage_url}')
"""
FILE_NAME = "{corp_num}-{filing_type}-{report_type}.pdf"


class Database:  # pylint: disable=too-few-public-methods
    """Database object."""

    bus_db_conn: psycopg2.extensions.connection
    doc_db_conn: psycopg2.extensions.connection
    bus_db_cursor: psycopg2.extensions.cursor
    doc_db_cursor: psycopg2.extensions.cursor

    @staticmethod
    def init_app(config: Config):
        """Set up the job database connections and cursors."""
        logger.info(f"Job {config.JOB_ID} Getting doc database connection and cursor.")
        Database.doc_db_conn = psycopg2.connect(dsn=config.DOC_DATABASE_URI)
        Database.doc_db_cursor = Database.doc_db_conn.cursor()
        logger.info(f"Job {config.JOB_ID} Getting business database connection and cursor.")
        Database.bus_db_conn = psycopg2.connect(dsn=config.BUS_DATABASE_URI)
        Database.bus_db_cursor = Database.bus_db_conn.cursor()

    @staticmethod
    def close_app():
        """Close the database cursors and connections."""
        with suppress(Exception):
            Database.bus_db_cursor.close()
        with suppress(Exception):
            Database.bus_db_conn.close()
        with suppress(Exception):
            Database.doc_db_cursor.close()
        with suppress(Exception):
            Database.doc_db_conn.close()

    @classmethod
    def get_job_corps_query(cls, config: Config) -> str:
        """Build the job run companies query based on the job env variables"""
        sql_statement: str = QUERY_JOB_CORPS_BASE
        if config.JOB_ID and config.JOB_ID > 0:
            sql_statement += QUERY_CORPS_JOB_ID_CLAUSE.format(job_id=config.JOB_ID)
        if config.JOB_CORP_STATE and config.JOB_CORP_STATE != "":
            sql_statement += QUERY_CORPS_CORP_STATE_CLAUSE.format(corp_state=config.JOB_CORP_STATE)
        if config.JOB_YEAR and config.JOB_YEAR > 0:
            sql_statement += QUERY_CORPS_YEAR_CLAUSE.format(corp_year=config.JOB_YEAR)
        if config.JOB_BATCH_SIZE and config.JOB_BATCH_SIZE > 0:
            sql_statement += QUERY_CORPS_SIZE_LIMIT.format(job_size=config.JOB_BATCH_SIZE)
        return sql_statement

    @classmethod
    def get_job_corps(cls, config: Config) -> list:
        """Get job run companies."""
        sql_statement: str = cls.get_job_corps_query(config)
        logger.info(f"Executing query to get job companies: {sql_statement}")
        Database.bus_db_cursor.execute(sql_statement)
        return Database.bus_db_cursor.fetchall()

    @classmethod
    def get_corp_filings(cls, corp_num: str) -> list:
        """Get COLIN filing history information for the company."""
        sql_statement: str = QUERY_FILINGS.format(corp_num=corp_num)
        Database.bus_db_cursor.execute(sql_statement)
        return Database.bus_db_cursor.fetchall()

    @classmethod
    def create_document_record(cls, corp_num: str, doc_storage_url: str, report_type: str, result: dict):
        """Create an individual document record service application report record for a migrated report."""
        filename: str = FILE_NAME.format(
            corp_num=corp_num, filing_type=result.get("filing_type"), report_type=report_type
        )
        sql_statement: str = INSERT_DRS_STATEMENT.format(
            corp_num=corp_num,
            event_id=result.get("event_id"),
            report_type=report_type,
            filing_date=result.get("filing_date"),
            filename=filename,
            doc_storage_url=doc_storage_url,
        )
        Database.doc_db_cursor.execute(sql_statement)
        Database.doc_db_conn.commit()

    @classmethod
    def update_company_migration(cls, corp_num: str, report_count: int, err_count: int, summary: list):
        """Update company reports migration status in the business database after all reports saved."""
        sql_statement: str = QUERY_JOB_CORP_UPDATE.format(
            corp_num=corp_num, report_count=report_count, err_count=err_count, summary=json.dumps(summary)
        )
        Database.bus_db_cursor.execute(sql_statement)
        Database.bus_db_conn.commit()
