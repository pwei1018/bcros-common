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
"""Model helper utilities for processing search requests.

Common methods for searching for document record information by different query parameters.
"""
from flask import current_app
from sqlalchemy.sql import text

from doc_api.resources.request_info import RequestInfo
from doc_api.utils.logging import logger

from .db import db
from .utils import format_ts, ts_from_iso_date_end, ts_from_iso_date_start

QUERY_DOC_TYPE_CLAUSE = " and d.document_type = '{doc_type}'"
QUERY_CONSUMER_ID_CLAUSE = " and d.consumer_identifier = '{consumer_id}'"
QUERY_DEFAULT_ORDER_BY = " order by d.consumer_document_id"
QUERY_DATES_DEFAULT = """
select d.document_service_id, d.add_ts, d.consumer_document_id, d.consumer_identifier, d.consumer_filename,
       d.consumer_filing_date, d.document_type, dt.document_type_desc, dc.document_class, d.doc_storage_url,
       dc.document_class_desc, d.description
  from documents d, document_types dt, document_classes dc
 where d.document_type = dt.document_type
   and d.document_class = dc.document_class and d.document_class != 'DELETED'
   and d.document_class = :query_val1
   and d.add_ts between to_timestamp(:query_val2, 'YYYY-MM-DD HH24:MI:SS')
                    and to_timestamp(:query_val3, 'YYYY-MM-DD HH24:MI:SS')
"""
SEARCH_ANY_BASE = """
select d2.document_service_id, d2.add_ts, d2.consumer_document_id, d2.consumer_identifier, d2.consumer_filename,
       d2.consumer_filing_date, d2.document_type, dt.document_type_desc, d2.document_class, dc.document_class_desc,
       d2.description, d2.doc_storage_url
  from documents d2, document_types dt, document_classes dc
 where d2.document_type = dt.document_type
   and d2.document_class = dc.document_class and dc.document_class != 'DELETED'
   and d2.consumer_document_id in (?)
 order by d2.add_ts desc
"""
SEARCH_CLASS_BASE = """
select d2.document_service_id, d2.add_ts, d2.consumer_document_id, d2.consumer_identifier, d2.consumer_filename,
       d2.consumer_filing_date, d2.document_type, dt.document_type_desc, d2.document_class, dc.document_class_desc,
       d2.description, d2.doc_storage_url
  from documents d2, document_types dt, document_classes dc
 where d2.document_type = dt.document_type
   and d2.document_class = dc.document_class and dc.document_class != 'DELETED'
   and d2.document_class = '??'
   and d2.consumer_document_id in (?)
 order by d2.add_ts desc
"""
SEARCH_COUNT_ANY_BASE = """
select count(distinct d.consumer_document_id)
  from documents d, document_types dt
 where d.document_type = dt.document_type and d.document_class != 'DELETED'
"""
SEARCH_FILTER_BASE = """
select distinct consumer_document_id
  from (select d.consumer_document_id
          from documents d, document_types dt2
         where d.document_type = dt2.document_type and d.document_class != 'DELETED'
"""
SEARCH_SORT_DEFAULT = " ORDER BY d.add_ts DESC"
SEARCH_SORT_DOC_ID = " ORDER BY d.consumer_document_id, d.add_ts DESC"
SEARCH_FILTER_DOC_CLASS = " AND d.document_class = '?'"
SEARCH_FILTER_DOC_TYPE = " AND d.document_type = '?'"
SEARCH_FILTER_DOC_ID_PARTIAL = " AND d.consumer_document_id LIKE '%?%'"
SEARCH_FILTER_DOC_ID_EXACT = " AND d.consumer_document_id = '?'"
SEARCH_FILTER_CONS_ID_PARTIAL = " AND d.consumer_identifier LIKE '%?%'"
SEARCH_FILTER_CONS_ID_EXACT = " AND d.consumer_identifier = '?'"
SEARCH_FILTER_FILENAME = " AND LOWER(d.consumer_filename) LIKE '%?%'"
SEARCH_FILTER_CREATE_DATE = (
    " AND d.add_ts BETWEEN TO_TIMESTAMP('query_start', 'YYYY-MM-DD HH24:MI:SS') AND "
    + "TO_TIMESTAMP('query_end', 'YYYY-MM-DD HH24:MI:SS')"
)
SEARCH_PAGE_SIZE: int = 100
SEARCH_PAGE_OFFSET = " as q LIMIT " + str(SEARCH_PAGE_SIZE) + " OFFSET ?"


def build_page_clause(request_info: RequestInfo) -> str:
    """Build the query page limit clause."""
    clause: str = SEARCH_SORT_DEFAULT + ")"
    page_num: int = int(request_info.page_number) if request_info.page_number else 1
    if page_num <= 1:
        page_num = 0
    else:
        page_num -= 1
    offset: int = page_num * SEARCH_PAGE_SIZE
    clause += SEARCH_PAGE_OFFSET.replace("?", str(offset))
    return clause


def build_result_json(row, merge_doc_id: bool = False) -> dict:
    """Get document information for a single search match as JSON."""
    result_json = {
        "documentServiceId": str(row[0]),
        "createDateTime": format_ts(row[1]),
        "consumerDocumentId": str(row[2]) if row[2] else "",
        "consumerIdentifier": str(row[3]) if row[3] else "",
        "documentType": str(row[6]),
        "documentTypeDescription": str(row[7]),
        "documentClass": str(row[8]),
        "description": str(row[10]) if row[10] else "",
    }
    if merge_doc_id:
        filenames = []
        if row[4]:
            filenames.append(str(row[4]))
        result_json["consumerFilenames"] = filenames
    else:
        result_json["consumerFilename"] = str(row[4]) if row[4] else ""
    if row[5]:
        result_json["consumerFilingDateTime"] = format_ts(row[5])
    if row[11]:
        result_json["documentExists"] = True
    else:
        result_json["documentExists"] = False
    return result_json


def build_filter_clause(request_info: RequestInfo) -> str:
    """Build search query filter clauses from the request parameters."""
    clause: str = ""
    if request_info.document_class:
        clause += SEARCH_FILTER_DOC_CLASS.replace("?", request_info.document_class)
    if request_info.document_type:
        clause += SEARCH_FILTER_DOC_TYPE.replace("?", request_info.document_type)
    if request_info.query_start_date and request_info.query_end_date:
        start: str = format_ts(ts_from_iso_date_start(request_info.query_start_date))[:19].replace("T", " ")
        end: str = format_ts(ts_from_iso_date_end(request_info.query_end_date))[:19].replace("T", " ")
        search_dates: str = SEARCH_FILTER_CREATE_DATE.replace("query_start", start)
        clause += search_dates.replace("query_end", end)
    if request_info.consumer_identifier:
        clause += SEARCH_FILTER_CONS_ID_PARTIAL.replace("?", request_info.consumer_identifier.upper())
    if request_info.consumer_doc_id:
        clause += SEARCH_FILTER_DOC_ID_PARTIAL.replace("?", request_info.consumer_doc_id.upper())
    if request_info.consumer_filename:
        clause += SEARCH_FILTER_FILENAME.replace("?", request_info.consumer_filename.lower())
    return clause


def get_search_count(filter_clause: str) -> int:
    """Count total search results based on the request parameters."""
    result_count: int = 0
    try:
        query = text(SEARCH_COUNT_ANY_BASE + filter_clause)
        result = db.session.execute(query)
        row = result.first()
        result_count = int(row[0])
        return result_count
    except Exception as db_exception:  # noqa: B902; return nicer error
        current_app.logger.error("get_search_count exception: " + str(db_exception))
    return result_count


def get_search_results(request_info: RequestInfo, filter_clause: str) -> list:
    """Build search results based on the request parameters."""
    results = []
    try:
        query_filter_doc_id = SEARCH_FILTER_BASE + filter_clause + build_page_clause(request_info)
        query_text: str = (
            SEARCH_ANY_BASE
            if not request_info.document_class
            else SEARCH_CLASS_BASE.replace("??", request_info.document_class)
        )
        query = text(query_text.replace("?", query_filter_doc_id))
        logger.info(f"get_search_results executing query doc id filter {query_filter_doc_id}")
        qresults = db.session.execute(query)
        rows = qresults.fetchall()
        if rows is None:
            return results
        if request_info.from_ui:
            return get_ui_search_results(rows)
        for row in rows:
            result_json = build_result_json(row, False)
            results.append(result_json)
        logger.info(f"get_search_results length={len(results)}")
        return results
    except Exception as db_exception:  # noqa: B902; return nicer error
        current_app.logger.error("get_search_results exception: " + str(db_exception))
    return []


def get_search_docs(request_info: RequestInfo) -> dict:
    """Search for document information by any combination of request parameters."""
    results = []
    filter_clause: str = build_filter_clause(request_info)
    logger.info(f"Search query filter {filter_clause}")
    search_count: int = get_search_count(filter_clause)
    search_results = {"resultCount": search_count, "results": results}
    if search_count <= 0:
        logger.info(f"get_search_docs count=0 for filter {filter_clause}.")
        return search_results
    results = get_search_results(request_info, filter_clause)
    if results:
        search_results["results"] = results
        logger.info(f"get_search_docs returning {len(results)} results.")
    else:
        logger.info("get_search_docs no results found.")
    return search_results


def get_docs_by_date_range(doc_class: str, start_date: str, end_date: str, doc_type: str, cons_id: str) -> dict:
    """Get document info by date range and class, type is optional."""
    results = []
    if not doc_class or not start_date or not end_date:
        logger.warning("get_docs_by_date_range missing one of required doc class, start date, end date")
        return results

    query_s = QUERY_DATES_DEFAULT
    if doc_type:
        query_s += QUERY_DOC_TYPE_CLAUSE.format(doc_type=doc_type)
    if cons_id:
        query_s += QUERY_CONSUMER_ID_CLAUSE.format(consumer_id=cons_id)
    query_s += QUERY_DEFAULT_ORDER_BY
    query = text(query_s)
    start: str = format_ts(ts_from_iso_date_start(start_date))[:19].replace("T", " ")
    end: str = format_ts(ts_from_iso_date_end(end_date))[:19].replace("T", " ")
    logger.info(f"get_docs class {doc_class} query by date range {start} to {end}\n query={query_s}")
    qresults = None
    qresults = db.session.execute(query, {"query_val1": doc_class, "query_val2": start, "query_val3": end})
    rows = qresults.fetchall()
    if rows is not None:
        for row in rows:
            result_json = {
                "documentServiceId": str(row[0]),
                "createDateTime": format_ts(row[1]),
                "consumerDocumentId": str(row[2]) if row[2] else "",
                "consumerIdentifier": str(row[3]) if row[3] else "",
                "consumerFilename": str(row[4]) if row[4] else "",
                "documentType": str(row[6]),
                "documentTypeDescription": str(row[7]),
                "documentClass": str(row[8]),
                "description": str(row[11]) if row[11] else "",
            }
            if row[5]:
                result_json["consumerFilingDateTime"] = format_ts(row[5])
            if row[9]:
                result_json["documentExists"] = True
            else:
                result_json["documentExists"] = False
            results.append(result_json)
    if results:
        logger.info(f"get_docs_by_date_range returning {len(results)} results.")
    else:
        logger.info("get_docs_by_date_range no results found.")
    return results


def get_ui_search_results(rows) -> list:
    """Build the UI view of the search results with a single item per document ID."""
    if rows is None:
        return []
    results = []
    temp_results = {}
    doc_ids = []
    for row in rows:
        result_json = build_result_json(row, True)
        temp_key = result_json.get("consumerDocumentId") + "-" + result_json.get("documentClass")
        if not temp_results or not temp_results.get(temp_key):
            temp_results[temp_key] = result_json
            doc_ids.append(temp_key)
        elif result_json.get("consumerFilenames") and temp_results.get(temp_key):
            temp_results[temp_key]["consumerFilenames"].append(result_json["consumerFilenames"][0])
        elif result_json.get("consumerFilename") and temp_results.get(temp_key):
            if not temp_results[temp_key].get("otherDocuments"):
                temp_results[temp_key]["otherDocuments"] = []
            temp_results[temp_key]["otherDocuments"].append(result_json)
    logger.info(f"get_ui_search_results doc id length={len(doc_ids)}")
    for doc_id in doc_ids:
        results.append(temp_results.get(doc_id))
    return results
