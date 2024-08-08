# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""Module to manage the calls and content to the reporting service."""
from http import HTTPStatus

from flask import jsonify
# from flask_babel import _
from doc_api.exceptions import BusinessException, ResourceErrorCodes
from doc_api.utils.logging import logger

from .report import Report
from .report_utils import ReportTypes


REPORT_VERSION_V2 = '2'
DEFAULT_ERROR_MSG = '{code}: Data related error generating report.'.format(code=ResourceErrorCodes.REPORT_ERR.value)


def get_pdf(report_data, account_id, report_type=None):
    """Generate a PDF of the provided report type using the provided data."""
    try:
        return Report(report_data, account_id, report_type).get_pdf()
    except FileNotFoundError:
        # We don't have a template for it, so it must only be available on paper.
        return jsonify({'message': 'No PDF report found.'}), HTTPStatus.NOT_FOUND
    except Exception as err:   # noqa: B902; return nicer default error
        logger.error(f'Generate report failed for account {account_id}, type {report_type}: ' + str(err))
        raise BusinessException(error=DEFAULT_ERROR_MSG, status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from err
