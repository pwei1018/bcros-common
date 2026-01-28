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
QUERY_JOB_CORPS_RECENT_BASE = """
select m.corp_num, c.corp_password, to_char(m.migrated_ts, 'YYYY-MM-DD HH24:MI:SS') as migrated_ts, m.report_count,
       m.error_count, m.migration_summary
  from mig_colin_reports m, colin_extract.corporation c
 where c.corp_num = m.corp_num
   and m.migrated_ts is not null
   and c.corp_password is not null
   and not exists (select cp.id
                     from colin_extract.corp_processing cp
                    where cp.corp_num = m.corp_num
                      and cp.environment = 'prod'
                      and cp.processed_status = 'COMPLETED')
   and exists (select f.event_id
                 from colin_extract.filing f, colin_extract.event e
                where e.corp_num = m.corp_num
                  and e.event_id = f.event_id
                  and e.event_timerstamp > m.migrated_ts
                  and f.filing_type_cd in ('AMALO','CONVL','REGST','NOAPA','NORVA','NOCAA','AMEND','NOCRX','NOCNX',
                                           'ACASS','AMALX','RESTL','RESTF','NOLDS','NOCDS','APTRA','NOERA','NOTRA',
                                           'NOAPL','NOCAL','NOCEL','LIQUR','LQWOS','NWITH','COUTI','CONTO','CONTI',
                                           'ADVDS','NOCEB','ADCOL','ICORP','TRANS','TRANP','ANNBC','ANNXP','NOCDR',
                                           'NOCAD','AMALH','AMALV','AMALR','NOALA','NOARM','NOCER','RESXL','RESXF',
                                           'LQSIN','LQSCO','LQDIS','LQCON','NOCRM','AUCTI','NOFIL','NORSA','CANRG',
                                           'IAMGO','REGLL','AGMDT','AGMLC','COURT','RESTX','SRCHI','SRCHR','REXTF',
                                           'REXXL','REXXF','XREFN','REGSN','REGSO','ADVLQ','AM_AR','CO_AR','AM_AT',
                                           'CO_AT','AM_BC','CO_BC','AM_DI','CO_DI','AM_DO','CO_DO','AM_HO','CO_HO',
                                           'AM_LI','CO_LI','AM_LR','CO_LR','AM_LQ','CO_LQ','AM_XP','CO_XP','AM_PF',
                                           'CO_PF','AM_PO','CO_PO','AM_RM','CO_RM','AM_RR','CO_RR','AM_RS','CO_RS',
                                           'AM_SS','CO_SS','AM_XN','CO_XN','LITAR','AMALL','AM_TR','CO_TR','ADVD2',
                                           'REGS2','COGS1','AMLRU','AMLVU','AMLHU','CONTU','ICORU','NOALB','NOALU',
                                           'AUCTU','RUSTF','RUSTL','RUSXF','RUSXL','DISDE','TILMA','RXTF2','RSTX2',
                                           'RXXL2','NOAMX','CISET','JNPSX','AMLHC','AMLRC','AMLVC','CONTC','ICORC',
                                           'NOALC','NOCHN','NOCIX','LNKPS','NOAP2','NOCA2','NOCX2','NORV2','NOCR2',
                                           'NOCB2'))
"""

QUERY_CORPS_JOB_ID_CLAUSE = " and m.job_id is not null and m.job_id = {job_id}"
QUERY_CORPS_CORP_STATE_CLAUSE = " and m.op_state_type_cd = '{corp_state}'"
QUERY_CORPS_YEAR_CLAUSE = " and m.recognition_dts is not null and EXTRACT(year from m.recognition_dts) = {corp_year}"
QUERY_CORPS_SIZE_LIMIT = " fetch first {job_size} rows only"
QUERY_FILINGS_BASE = """
select to_char(e.event_timerstamp, 'YYYY-MM-DD HH24:MI:SS') as filing_date, f.event_id, f.filing_type_cd,
       trim(to_char((e.event_timerstamp at time zone 'PST'), 'Month')) ||
       to_char((e.event_timerstamp at time zone 'PST'), ' DD, YYYY') as report_date
  from colin_extract.filing f, colin_extract.event e
 where e.event_id = f.event_id
   and f.filing_type_cd in ('AMALO','CONVL','REGST','NOAPA','NORVA','NOCAA','AMEND','NOCRX','NOCNX','ACASS','AMALX',
                            'RESTL','RESTF','NOLDS','NOCDS','APTRA','NOERA','NOTRA','NOAPL','NOCAL','NOCEL','LIQUR',
                            'LQWOS','NWITH','COUTI','CONTO','CONTI','ADVDS','NOCEB','ADCOL','ICORP','TRANS','TRANP',
                            'ANNBC','ANNXP','NOCDR','NOCAD','AMALH','AMALV','AMALR','NOALA','NOARM','NOCER','RESXL',
                            'RESXF','LQSIN','LQSCO','LQDIS','LQCON','NOCRM','AUCTI','NOFIL','NORSA','CANRG','IAMGO',
                            'REGLL','AGMDT','AGMLC','COURT','RESTX','SRCHI','SRCHR','REXTF','REXXL','REXXF','XREFN',
                            'REGSN','REGSO','ADVLQ','AM_AR','CO_AR','AM_AT','CO_AT','AM_BC','CO_BC','AM_DI','CO_DI',
                            'AM_DO','CO_DO','AM_HO','CO_HO','AM_LI','CO_LI','AM_LR','CO_LR','AM_LQ','CO_LQ','AM_XP',
                            'CO_XP','AM_PF','CO_PF','AM_PO','CO_PO','AM_RM','CO_RM','AM_RR','CO_RR','AM_RS','CO_RS',
                            'AM_SS','CO_SS','AM_XN','CO_XN','LITAR','AMALL','AM_TR','CO_TR','ADVD2','REGS2','COGS1',
                            'AMLRU','AMLVU','AMLHU','CONTU','ICORU','NOALB','NOALU','AUCTU','RUSTF','RUSTL','RUSXF',
                            'RUSXL','DISDE','TILMA','RXTF2','RSTX2','RXXL2','NOAMX','CISET','JNPSX','AMLHC','AMLRC',
                            'AMLVC','CONTC','ICORC','NOALC','NOCHN','NOCIX','LNKPS','NOAP2','NOCA2','NOCX2','NORV2',
                            'NOCR2','NOCB2')
   and e.corp_num = '{corp_num}'
"""
QUERY_FILINGS_ORDER_BY = " order by f.effective_dt desc"
QUERY_FILINGS = QUERY_FILINGS_BASE + QUERY_FILINGS_ORDER_BY
QUERY_FILINGS_RECENT_CLAUSE = "   and e.event_timerstamp > to_timestamp('{migrated_ts}', 'YYYY-MM-DD HH24:MI:SS')"
QUERY_FILINGS_RECENT = QUERY_FILINGS_BASE + QUERY_FILINGS_RECENT_CLAUSE + QUERY_FILINGS_ORDER_BY
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
        sql_statement: str = QUERY_JOB_CORPS_BASE if not config.UPDATE_PREVIOUS else QUERY_JOB_CORPS_RECENT_BASE
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
    def get_corp_filings(cls, corp_num: str, migrated_ts: str = None) -> list:
        """Get COLIN filing history information for the company. Get recent filings if migrated_ts is present."""
        sql_statement: str = QUERY_FILINGS.format(corp_num=corp_num)
        if migrated_ts:
            sql_statement = QUERY_FILINGS_RECENT.format(corp_num=corp_num, migrated_ts=migrated_ts)
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
