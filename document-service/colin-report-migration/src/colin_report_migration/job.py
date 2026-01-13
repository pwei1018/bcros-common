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
import copy
import sys
from http import HTTPStatus

import psycopg2
import requests

from colin_report_migration.config import Config
from colin_report_migration.database import Database
from colin_report_migration.services.document_storage.storage_service import GoogleStorageService
from colin_report_migration.services.utils.exceptions import ScrapingException
from colin_report_migration.utils.logging import logger

REPORT_TYPE_CERT = "cert"
REPORT_TYPE_FILING = "filing"
REPORT_TYPE_NOA = "noa"
REPORT_TYPE_RECEIPT = "receipt"
STORAGE_DOC_NAME = "{report_date}/{corp_num}-{event_id}-{report_type}.pdf"
REPORT_PATH = "/reprint/report.do?action={report_type}Report&check_token=no&historyIndex={filing_index}"
SCRAPING_MENU_PATH = "/accesstransaction/menu.do?action=overview&filingTypeCode=RPRNT&from=main"
SCRAPING_OVERVIEW_PATH = "/accesstransaction/menu.do"
SCRAPING_SEARCH_PATH = "/identcorp/searchCorp.do"
SCRAPING_HEADERS_MENU = {"Connection": "keep-alive", "Content-Type": "text/plain; charset=ISO-8859-1"}
SCRAPING_OVERVIEW_DATA = {"formType": "overview", "navigationAction": "next", "nextButton.x": 28, "nextButton.y": 13}
SCRAPING_SEARCH_DATA = {
    "defaultAction": "next",
    "formType": "search",
    "corpNum": "",
    "password": "",
    "navigationAction": "next",
    "nextButton.x": 27,
    "nextButton.y": 7,
}


def get_storage_name(filing_date: str, corp_num: str, event_id: int, report_type: str) -> str:
    """Get doc storage name for a legacy document record."""
    report_date: str = filing_date[:10].replace("-", "/")
    storage_name = STORAGE_DOC_NAME.format(
        report_date=report_date, corp_num=corp_num, event_id=event_id, report_type=report_type
    )
    return storage_name


def get_corp_filings_page(corp_num: str, corp_password: str, colin_url: str) -> dict:
    """COLIN UI screen scraping to retrieve filing history by corp num and password."""
    menu_url = colin_url + SCRAPING_MENU_PATH
    overview_url = colin_url + SCRAPING_OVERVIEW_PATH
    search_url = colin_url + SCRAPING_SEARCH_PATH

    try:
        response = requests.get(menu_url, headers=SCRAPING_HEADERS_MENU)
        if response.status_code != 200:
            logger.info("menu error")
            raise ScrapingException(f"Scraping get menu failed for url={menu_url}.")
        cookie: str = response.cookies["JSESSIONID"]
        cookies = {"JSESSIONID": cookie}
        response = requests.post(overview_url, data=SCRAPING_OVERVIEW_DATA, cookies=cookies)
        if response.status_code != 200:
            logger.info("overview error")
            raise ScrapingException(f"Scraping get overview failed for url={overview_url}.")
        search_data = copy.deepcopy(SCRAPING_SEARCH_DATA)
        search_data["corpNum"] = corp_num
        search_data["password"] = corp_password
        response = requests.post(search_url, data=search_data, cookies=cookies)
        if response.status_code != 200:
            raise ScrapingException(f"Scraping get search failed for url={search_url}.")
        page_text = response.text
        filing_info: dict = {"colin_url": colin_url, "filings_page": page_text, "cookies": cookies}
        filing_info["no_reports"] = page_text.find("check_token=no&historyIndex=") < 1
        # logger.info(f"get_corp_filings_page length={len(response.text)}")
        return filing_info
    except ScrapingException:
        raise
    except Exception as err:
        raise ScrapingException(f"Scraping failed for corp num={corp_num}. {err}") from err


def has_report(filings_page: str, filing_index: int, report_type: str) -> bool:
    """Determine if filing has a specific report by examining the company history page."""
    test_report = REPORT_PATH.format(report_type=report_type, filing_index=filing_index) + "&"
    return filings_page.find(test_report) > 0


def is_stale_extract(filing_rows: list, filings_info: dict) -> bool:
    """Determine if the colin extract company history is stale: the screen scrape first filing is more recent."""
    if not filing_rows:
        return False
    filings_page = filings_info.get("filings_page")
    filing_row = filing_rows[0]
    expected_first_filing_date: str = str(filing_row[3])
    logger.debug(f"expected_first_filing_date={expected_first_filing_date}")
    index_first_filing_date = filings_page.find(expected_first_filing_date)
    index_first_report = filings_page.find("historyIndex=0")
    return index_first_report < index_first_filing_date


def save_report(corp_num: str, report_type: str, filing_info: dict, result: dict) -> dict:
    """Save an individual report to doc storage and create a DRS app report record."""
    storage_name: str = get_storage_name(result.get("filing_date"), corp_num, result.get("event_id"), report_type)
    save_storage_key = report_type + "_storage_name"
    result[save_storage_key] = storage_name
    try:
        colin_url = filing_info.get("colin_url")
        filing_index: int = filing_info.get("filing_index")
        cookies: dict = filing_info.get("cookies")
        report_url = colin_url + REPORT_PATH.format(report_type=report_type, filing_index=filing_index)
        # logger.info(f"report_url={report_url} storage_name={storage_name}")
        response = requests.get(report_url, cookies=cookies)
        # logger.info(f"save_report status={response.status_code}")
        if response.status_code == HTTPStatus.OK:
            GoogleStorageService.save_document(storage_name, response.content)
            Database.create_document_record(corp_num, storage_name, report_type.upper(), result)
            result["report_count"] = result.get("report_count") + 1
        else:
            result["error_count"] = result.get("error_count") + 1
            result["error_message"] = result.get("error_message") + f" {response.status_code} {response.text}"
    except Exception as err:
        result["error_count"] = result.get("error_count", 0) + 1
        result["error_message"] = result.get("error_message") + " " + str(err)
    return result


def migrate_filing(filing_row, corp_num: str, filing_info: dict) -> dict:
    """Migrage reports for a single filing."""
    result: dict = {"error_count": 0, "report_count": 0}
    try:
        result["filing_date"] = str(filing_row[0])
        result["event_id"] = int(filing_row[1])
        result["filing_type"] = str(filing_row[2])
        # logger.info(f"{result.get("event_id")} {result.get("filing_type")}")
        if has_report(filing_info.get("filings_page"), filing_info.get("filing_index"), REPORT_TYPE_RECEIPT):
            result = save_report(corp_num, REPORT_TYPE_RECEIPT, filing_info, result)
        if has_report(filing_info.get("filings_page"), filing_info.get("filing_index"), REPORT_TYPE_FILING):
            result = save_report(corp_num, REPORT_TYPE_FILING, filing_info, result)
        if has_report(filing_info.get("filings_page"), filing_info.get("filing_index"), REPORT_TYPE_NOA):
            result = save_report(corp_num, REPORT_TYPE_NOA, filing_info, result)
        if has_report(filing_info.get("filings_page"), filing_info.get("filing_index"), REPORT_TYPE_CERT):
            result = save_report(corp_num, REPORT_TYPE_CERT, filing_info, result)
    except Exception as err:
        result["error_count"] = result.get("error_count") + 1
        result["error_message"] = str(err)
    return result


def migrate_reports(config: Config, rows: list) -> dict:
    """
    Migrate reports for each company in the rows list following the steps outlined in the job description.

    Args:
        config: Job configuration containing environment variables.
        rows: The business database mig_colin_reports table query results with the set of company identifiers.

    Returns:
        Updated status_data with zip file counts zip_file_count and zip_file_error_count
    """
    total_error_count: int = 0
    total_report_count: int = 0
    corp_num: str = ""
    corp_count: int = 0
    filing_summary: dict
    for row in rows:
        summary_json = []
        error_count: int = 0
        report_count: int = 0
        corp_count += 1
        try:
            corp_num = str(row[0])
            filing_info: dict = get_corp_filings_page(corp_num, str(row[1]), config.COLIN_URL)
            if filing_info.get("no_reports"):
                filing_summary = {
                    "skipped": True,
                    "warning_message": "No report links in filing history page. Company frozen?",
                }
                summary_json.append(filing_summary)
            else:
                filing_rows = Database.get_corp_filings(corp_num)
                if is_stale_extract(filing_rows, filing_info):
                    filing_summary = {
                        "skipped": True,
                        "warning_message": "STALE: page first report date more recent than query first filing date.",
                    }
                    summary_json.append(filing_summary)
                else:
                    filing_info["filing_index"] = 0
                    for filing_row in filing_rows:
                        filing_summary = migrate_filing(filing_row, corp_num, filing_info)
                        report_count += filing_summary.get("report_count", 0)
                        error_count += filing_summary.get("error_count", 0)
                        filing_info["filing_index"] = filing_info.get("filing_index") + 1
                        summary_json.append(filing_summary)
                    total_error_count += error_count
                    total_report_count += report_count
            Database.update_company_migration(corp_num, report_count, error_count, summary_json)
        except Exception as report_err:
            logger.error(f"Job {config.JOB_ID} unexpected error for corp_num={corp_num}: {report_err}")
            total_error_count += 1
        if corp_count % 50 == 0:
            logger.info(f"Job {config.JOB_ID} company migration count: {corp_count}")
    logger.info(f"Final counts companies={corp_count} errors={total_error_count} reports={total_report_count}.")


def job(config: Config):
    """
    Execute the job:
        Run a business database mig_colin_reports query to get the company identifiers to migrate filing reports for.
        Depending on the job environment variable values, filter on job id, recognition year, and company state.
        The number of companies to migrate per job run can also be configured by env variable.
        For each company:
            1. Screen scrape the colin application to get the report links.
            2. Query the business database colin_extract schema to get the company filing history.
            3. Match the query filing to the scraped history link reports.
            4. Retrieve each filing report with the scraped history link.
            5. Save the report to the DRS document storage business bucket.
            6. Insert a DRS application_reports table record in the DRS docs database.

    Args:
        config: Job configuration containing environment variables.

    Returns:
    """
    try:
        Database.init_app(config)
        rows = Database.get_job_corps(config)
        migrate_reports(config, rows)
    except (psycopg2.Error, Exception) as err:
        job_message: str = f"Run failed: {str(err)}."
        logger.error(job_message)
        sys.exit(1)  # Retry Job Task by exiting the process
    finally:
        # Clean up: Close the database cursor and connection
        Database.close_app()
