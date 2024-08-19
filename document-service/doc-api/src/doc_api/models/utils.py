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
"""Model helper utilities for processing requests.

Common constants used across models and utilities for mapping type codes
between the API and the database in both directions.
"""
from datetime import date  # noqa: F401 pylint: disable=unused-import
from datetime import datetime as _datetime
from datetime import time, timedelta, timezone

import pytz
from datedelta import datedelta
from flask import current_app
from sqlalchemy.sql import text

from doc_api.utils.logging import logger

from .db import db


QUERY_DOC_TYPE_CLAUSE = " and d.document_type = '{doc_type}'"
QUERY_CONSUMER_ID_CLAUSE = " and d.consumer_identifier = '{consumer_id}'"
QUERY_DEFAULT_ORDER_BY = ' order by d.consumer_document_id'
QUERY_DATES_DEFAULT = """
select d.document_service_id, d.add_ts, d.consumer_document_id, d.consumer_identifier, d.consumer_filename,
       d.consumer_filing_date, d.scan_date, d.document_type, dt.document_type_desc, dc.document_class,
       dc.document_class_desc
  from documents d, document_types dt, document_classes dc
 where d.document_type = dt.document_type
   and dt.document_class = dc.document_class
   and dc.document_class = :query_val1
   and d.add_ts between to_timestamp(:query_val2, 'YYYY-MM-DD HH24:MI:SS')
                    and to_timestamp(:query_val3, 'YYYY-MM-DD HH24:MI:SS')
"""
# Local timzone
LOCAL_TZ = pytz.timezone('America/Los_Angeles')
CONTENT_TYPE_CSV = 'text/csv'
CONTENT_TYPE_GIF = 'image/gif'
CONTENT_TYPE_JPEG = 'image/jpeg'
CONTENT_TYPE_PNG = 'image/png'
CONTENT_TYPE_TIFF = 'image/tiff'
CONTENT_TYPE_PDF = 'application/pdf'
CONTENT_TYPE_EXCEL = 'application/vnd.ms-excel'
CONTENT_TYPE_WORD = 'application/msword'
CONTENT_TYPE_EXCELX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
CONTENT_TYPE_WORDX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
CONTENT_TYPE_ZIP = 'application/zip'
# Map from API search type to DB search type
TO_FILE_TYPE = {
    CONTENT_TYPE_CSV: 'csv',
    CONTENT_TYPE_GIF: 'gif',
    CONTENT_TYPE_JPEG: 'jpg',
    'image/jpg': 'jpg',
    CONTENT_TYPE_PNG: 'png',
    'image/tif': 'tif',
    CONTENT_TYPE_TIFF: 'tif',
    CONTENT_TYPE_PDF: 'pdf',
    CONTENT_TYPE_EXCEL: 'xls',
    CONTENT_TYPE_WORD: 'doc',
    CONTENT_TYPE_EXCELX: 'xlsx',
    CONTENT_TYPE_WORDX: 'docx',
    CONTENT_TYPE_ZIP: 'zip',
    'default': 'pdf'
}
DEFAULT_FILE_TYPE = 'pdf'
STORAGE_DOC_NAME = '{doc_type}-{doc_service_id}.{file_type}'


def now_ts():
    """Create a timestamp representing the current date and time in the UTC time zone."""
    return _datetime.now(timezone.utc)


def format_ts(time_stamp):
    """Build a UTC ISO 8601 date and time string with no microseconds."""
    formatted_ts = None
    if time_stamp:
        try:
            formatted_ts = time_stamp.replace(tzinfo=timezone.utc).replace(microsecond=0).isoformat()
        except Exception as format_exception:   # noqa: B902; return nicer error
            current_app.logger.error('format_ts exception: ' + str(format_exception))
            formatted_ts = time_stamp.isoformat()
    return formatted_ts


def format_local_date(base_date):
    """Build a local timezone ISO 8601 date."""
    formatted_ts = None
    if not base_date or base_date.year == 1:
        return formatted_ts
    try:
        # Naive time
        local_time = time(9, 0, 0, tzinfo=None)
        base_ts = _datetime.combine(base_date, local_time)
        # Explicitly set to local timezone.
        local_ts = LOCAL_TZ.localize(base_ts)
        formatted_ts = local_ts.replace(tzinfo=LOCAL_TZ).replace(microsecond=0).isoformat()
    except Exception as format_exception:   # noqa: B902; return nicer error
        current_app.logger.error(f'format_local_date exception ({base_date.isoformat()}): ' + str(format_exception))
        formatted_ts = base_date.isoformat()
    return formatted_ts  # [0:10]


def ts_from_iso_date_noon(timestamp_iso: str):
    """Create a datetime object from a date string in the ISO format set to 12:00 PM using the local time zone."""
    local_time = time(12, 0, 0, tzinfo=None)
    base_date = date_from_iso_format(timestamp_iso)
    ts = _datetime.combine(base_date, local_time)
    local_ts = LOCAL_TZ.localize(ts, is_dst=True)
    # Return as UTC
    return local_ts.astimezone(timezone.utc)


def ts_from_iso_date_start(timestamp_iso: str):
    """Create a datetime object from a date string in the ISO format set to 12:00 PM using the local time zone."""
    local_time = time(0, 0, 0, tzinfo=None)
    base_date = date_from_iso_format(timestamp_iso)
    ts = _datetime.combine(base_date, local_time)
    local_ts = LOCAL_TZ.localize(ts, is_dst=True)
    # Return as UTC
    return local_ts.astimezone(timezone.utc)


def ts_from_iso_date_end(timestamp_iso: str):
    """Create a datetime object from a date string in the ISO format set to 12:00 PM using the local time zone."""
    local_time = time(23, 59, 59, tzinfo=None)
    base_date = date_from_iso_format(timestamp_iso)
    ts = _datetime.combine(base_date, local_time)
    local_ts = LOCAL_TZ.localize(ts, is_dst=True)
    # Return as UTC
    return local_ts.astimezone(timezone.utc)


def get_doc_storage_name(document, content_type: str) -> str:
    """Get a document storage name from the registration in the format YYYY/MM/DD/doc_type-doc_service_id.file_type."""
    name: str = document.add_ts.isoformat()[:10]
    ftype: str = TO_FILE_TYPE.get(content_type, DEFAULT_FILE_TYPE)
    name = name.replace('-', '/') + '/' + STORAGE_DOC_NAME.format(doc_type=document.document_type.lower(),
                                                                  doc_service_id=document.document_service_id,
                                                                  file_type=ftype)
    return name


def ts_from_iso_format_no_tz(timestamp_iso: str):
    """Create a datetime object from a timestamp string in the ISO format using the local time zone."""
    if len(timestamp_iso) > 19:
        return ts_from_iso_format(timestamp_iso)
    ts: _datetime = _datetime.fromisoformat(timestamp_iso)
    local_ts = LOCAL_TZ.localize(ts, is_dst=True)
    # Return as UTC
    return local_ts.astimezone(timezone.utc)


def now_ts_offset(offset_days: int = 1, add: bool = False):
    """Create a timestamp representing the current date and time adjusted by offset number of days."""
    now = now_ts()
    if add:
        return now + timedelta(days=offset_days)

    return now - timedelta(days=offset_days)


def today_ts_offset(offset_days: int = 1, add: bool = False):
    """Create a timestamp representing the current date at 00:00:00 adjusted by offset number of days."""
    today = date.today()
    day_time = time(0, 0, 0, tzinfo=timezone.utc)
    today_ts = _datetime.combine(today, day_time)
    if add:
        return today_ts + timedelta(days=offset_days)

    return today_ts - timedelta(days=offset_days)


def ts_from_iso_format(timestamp_iso: str):
    """Create a datetime object from a timestamp string in the ISO format."""
    time_stamp = _datetime.fromisoformat(timestamp_iso).timestamp()
    return _datetime.utcfromtimestamp(time_stamp).replace(tzinfo=timezone.utc)


def ts_from_iso_format_local(timestamp_iso: str):
    """Create a datetime object from a timestamp string in the ISO format without adjusting for utc."""
    return _datetime.fromisoformat(timestamp_iso)


def ts_from_date_iso_format(date_iso: str):
    """Create a UTC datetime object from a date string in the ISO format.

    Use the current UTC time.
    """
    return ts_from_iso_format(date_iso)


def date_from_iso_format(date_iso: str):
    """Create a date object from a date string in the ISO format."""
    if len(date_iso) > 10:
        return date.fromisoformat(date_iso[0:10])
    return date.fromisoformat(date_iso)


def time_from_iso_format(time_iso: str):
    """Create a time object from a time string in the ISO format."""
    return time.fromisoformat(time_iso)


def to_local_timestamp(utc_ts):
    """Create a timestamp adjusted from UTC to the local timezone."""
    return utc_ts.astimezone(LOCAL_TZ)


def today_local():
    """Return today in the local timezone."""
    return now_ts().astimezone(LOCAL_TZ)


def date_offset(base_date, offset_days: int = 1, add: bool = False):
    """Create a date representing the date adjusted by offset number of days."""
    if add:
        return base_date + datedelta(days=offset_days)
    return base_date - datedelta(days=offset_days)


def is_legacy() -> bool:
    """Check that the api is using the legacy DB2 database."""
    return current_app.config.get('USE_LEGACY_DB', True)


def date_elapsed(date_iso: str):
    """Check if a date converted from a date string is in the past."""
    if not date_iso or len(date_iso) < 10:
        return False
    test_date = date.fromisoformat(date_iso[0:10])
    now = now_ts()
    today_date = date(now.year, now.month, now.day)
    # current_app.logger.info('Comparing now ' + today_date.isoformat() + ' with expiry ' + test_date.isoformat())
    return today_date > test_date


def get_docs_by_date_range(doc_class: str, start_date: str, end_date: str, doc_type: str, cons_id: str) -> dict:
    """Get document info by date range and class, type is optional."""
    results = []
    if not doc_class or not start_date or not end_date:
        logger.warning('get_docs_by_date_range missing one of required doc class, start date, end date')
        return results

    query_s = QUERY_DATES_DEFAULT
    if doc_type:
        query_s += QUERY_DOC_TYPE_CLAUSE.format(doc_type=doc_type)
    if cons_id:
        query_s += QUERY_CONSUMER_ID_CLAUSE.format(consumer_id=cons_id)
    query_s += QUERY_DEFAULT_ORDER_BY
    query = text(query_s)
    start: str = format_ts(ts_from_iso_date_start(start_date))[:19].replace('T', ' ')
    end: str = format_ts(ts_from_iso_date_end(end_date))[:19].replace('T', ' ')
    logger.info(f'get_docs class {doc_class} query by date range {start} to {end}\n query={query_s}')
    qresults = None
    qresults = db.session.execute(query, {'query_val1': doc_class, 'query_val2': start, 'query_val3': end})
    rows = qresults.fetchall()
    if rows is not None:
        for row in rows:
            result_json = {
                'documentServiceId': str(row[0]),
                'createDateTime': format_ts(row[1]),
                'consumerDocumentId': str(row[2]) if row[2] else '',
                'consumerIdentifier': str(row[3]) if row[3] else '',
                'consumerFilename': str(row[4]) if row[4] else '',
                'documentType': str(row[7]),
                'documentTypeDescription': str(row[8]),
                'documentClass': str(row[9])
            }
            if row[5]:
                result_json['consumerFilingDateTime'] = format_ts(row[5])
            if row[6]:
                result_json['consumerScanDateTime'] = format_ts(row[6])
            results.append(result_json)
    if results:
        logger.info(f'get_docs_by_date_range returning {len(results)} results.')
    else:
        logger.info('get_docs_by_date_range no results found.')
    return results
