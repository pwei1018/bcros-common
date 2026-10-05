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
import time
from contextlib import suppress

import psycopg2

from doc_bcmail_transfer.config import Config
from doc_bcmail_transfer.utils.logging import logger

QUERY_BCMAIL_DOCS = """
select TO_CHAR(d.add_ts, 'YYYY-MM-DD HH24:MI:SS') as added_utc,
       d.consumer_identifier as drs_business_identifier, d.consumer_document_id as drs_document_id,
       d.consumer_filename as drs_filename,
       dr.request_data -> 'requestData' -> 'legacyScanInfo' ->> 'size' as drs_filesize
  from documents d, document_requests dr
 where d.add_ts > now() at time zone 'utc' - interval '3 hours'
   and document_type = 'PRE'
   and d.id = dr.document_id
  order by d.id
"""


class Database:  # pylint: disable=too-few-public-methods
    """Database object."""

    doc_db_conn: psycopg2.extensions.connection
    doc_db_cursor: psycopg2.extensions.cursor

    @staticmethod
    def init_app(config: Config):
        """Set up the job database connections and cursors."""
        logger.info("Job getting doc database connection and cursor.")
        Database.doc_db_conn = psycopg2.connect(dsn=config.DOC_DB_URI)
        Database.doc_db_cursor = Database.doc_db_conn.cursor()

    @staticmethod
    def close_app():
        """Close the database cursors and connections."""
        with suppress(Exception):
            Database.doc_db_cursor.close()
        with suppress(Exception):
            Database.doc_db_conn.close()

    @classmethod
    def update_status_drs_info(cls, files_summary: list) -> list:
        """
        Add information from the DRS database about recent DRS BCMail documents to the files_summary.
        """
        try:
            # Wait for a short period for the creattion of new DRS documents to complete.
            time.sleep(10)
            bus_id: str = ""
            Database.doc_db_cursor.execute(QUERY_BCMAIL_DOCS)
            rows = Database.doc_db_cursor.fetchall()
            for row in rows:
                bus_id = str(row[1])
                for summary in files_summary:
                    if summary.get("bcmail_identifier") == bus_id:
                        summary["drs_identifier"] = bus_id
                        summary["drs_added_utc"] = str(row[0])
                        summary["drs_document_id"] = str(row[2])
                        summary["drs_filename"] = str(row[3])
                        summary["drs_filesize"] = int(row[4])
                        break
        except Exception as ex:  # noqa: B902; return nicer error
            logger.error(f"Update status info from DRS database query failed business identifer = {bus_id}: {ex}")
        return files_summary
