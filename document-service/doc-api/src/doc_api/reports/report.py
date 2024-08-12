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
"""Produces a PDF output based on templates and JSON messages."""

from http import HTTPStatus
from pathlib import Path

import requests
from flask import current_app, jsonify
from doc_api.exceptions import ResourceErrorCodes
from doc_api.reports import report_utils
from doc_api.reports.report_utils import ReportTypes
from doc_api.services.gcp_auth.auth_service import GoogleAuthService
from doc_api.utils.logging import logger


# Map from API search type to report description
SINGLE_URI = '/forms/chromium/convert/html'
MERGE_URI = '/forms/pdfengines/merge'


class Report:  # pylint: disable=too-few-public-methods
    """Service to create report outputs."""

    def __init__(self, report_data, account_id, report_type=None):
        """Create the Report instance."""
        self._report_data = report_data
        self._report_key = report_type
        self._account_id = account_id

    def get_payload_data(self):
        """Generate report data including template data for report api call."""
        return self._setup_report_data()

    def get_pdf(self, report_type=None):
        """Render a pdf for the report type and report data."""
        logger.info('Account {0} report type {1} setting up report data.'.format(self._account_id, self._report_key))
        data = self._setup_report_data()
        url = current_app.config.get('REPORT_SVC_URL') + SINGLE_URI
        logger.debug('Account {0} report type {1} calling report-api {2}.'
                     .format(self._account_id, self._report_key, url))
        meta_data = report_utils.get_report_meta_data(self._report_key)
        files = report_utils.get_report_files(data, self._report_key)
        headers = Report.get_headers()
        response = requests.post(url=url, headers=headers, data=meta_data, files=files, timeout=30.0)
        logger.info('Account {0} report type {1} response status: {2}.'
                    .format(self._account_id, self._report_key, response.status_code))
        if response.status_code != HTTPStatus.OK:
            content = ResourceErrorCodes.REPORT_ERR + ': ' + response.content.decode('ascii')
            logger.error('Account {0} response status: {1} error: {2}.'
                         .format(self._account_id, response.status_code, content))
            return jsonify(message=content), response.status_code, None
        return response.content, response.status_code, {'Content-Type': 'application/pdf'}

    @staticmethod
    def get_headers() -> dict:
        """Build the report service request headers."""
        headers = {}
        token = GoogleAuthService.get_report_api_token()
        if token:
            headers['Authorization'] = 'Bearer {}'.format(token)
        return headers

    @staticmethod
    def batch_merge(pdf_list):
        """Merge a list of pdf files into a single pdf."""
        if not pdf_list:
            return None
        logger.debug(f'Setting up batch merge for {len(pdf_list)} files.')
        count: int = 0
        files = {}
        for pdf in pdf_list:
            count += 1
            filename = 'file' + str(count) + '.pdf'
            files[filename] = pdf
        headers = Report.get_headers()
        url = current_app.config.get('REPORT_SVC_URL') + MERGE_URI
        response = requests.post(url=url, headers=headers, files=files, timeout=1800.0)
        logger.debug('Batch merge reports response status: {0}.'.format(response.status_code))
        if response.status_code != HTTPStatus.OK:
            content = ResourceErrorCodes.REPORT_ERR.value + ': ' + response.content.decode('ascii')
            logger.error('Batch merge response status: {0} error: {1}.'.format(response.status_code, content))
            return jsonify(message=content), response.status_code, None
        return response.content, response.status_code, {'Content-Type': 'application/pdf'}

    def _setup_report_data(self):
        """Set up the report service request data."""
        # logger.debug('Setup report data template starting.')
        template = self._get_template()
        logger.debug('Setup report data template completed, setup data starting.')
        data = {
            'reportName': self._get_report_filename(),
            'template': template,
            'templateVars': self._get_template_data()
        }
        logger.debug('Setup report data completed.')
        return data

    def _get_report_filename(self):
        """Generate the pdf filename from the report type and report data."""
        report_date = self._get_report_date()
        report_id = self._get_report_id()
        description = ReportMeta.reports[self._report_key]['reportDescription']
        return '{}_{}_{}.pdf'.format(report_id, report_date, description).replace(' ', '_')

    def _get_report_date(self):
        """Get the report date for the filename from the report data."""
        return self._report_data['createDateTime']

    def _get_report_id(self):
        """Get the report transaction ID for the filename from the report data."""
        report_id = ''
        if self._report_key == ReportTypes.DOC_RECORD:
            report_id = self._report_data.get('consumerDocumentId', '')
        return report_id

    def _get_template(self):
        """Load from the local file system the template matching the report type."""
        try:
            template_path = current_app.config.get('REPORT_TEMPLATE_PATH')
            template_code = Path(f'{template_path}/{self._get_template_filename()}').read_text(encoding='UTF-8')
            # substitute template parts
            template_code = self._substitute_template_parts(template_code)
        except Exception as err:  # noqa: B902; just logging
            logger.error(err)
            raise err
        return template_code

    @staticmethod
    def _substitute_template_parts(template_code):
        """Substitute template parts in main template.

        Template parts are marked by [[partname.html]] in templates.

        This functionality is restricted by:
        - markup must be exactly [[partname.html]] and have no extra spaces around file name
        - template parts can only be one level deep, ie: this rudimentary framework does not handle nested template
        parts. There is no recursive search and replace.

        :param template_code: string
        :return: template_code string, modified.
        """
        template_path = current_app.config.get('REPORT_TEMPLATE_PATH')
        template_parts = [
            'logo',
            'macros',
            'registrarSignature',
            'registrarSignatureBlack',
            'style',
            'stylePage',
            'stylePageCover',
            'stylePageRegistration',
            'stylePageRegistrationDraft'
        ]

        # substitute template parts - marked up by [[filename]]
        for template_part in template_parts:
            if template_code.find('[[{}.html]]'.format(template_part)) >= 0:
                template_part_code = \
                    Path(f'{template_path}/template-parts/{template_part}.html').read_text(encoding='UTF-8')
                for template_part_nested in template_parts:
                    template_reference = '[[{}.html]]'.format(template_part_nested)
                    if template_part_code.find(template_reference) >= 0:
                        path = Path(f'{template_path}/template-parts/{template_part_nested}.html')
                        template_nested_code = path.read_text(encoding='UTF-8')
                        template_part_code = template_part_code.replace(template_reference, template_nested_code)
                template_code = template_code.replace('[[{}.html]]'.format(template_part), template_part_code)

        return template_code

    def _get_template_filename(self):
        """Get the report template filename from the report type."""
        file_name = ReportMeta.reports[self._report_key]['fileName']
        return '{}.html'.format(file_name)

    def _get_template_data(self):
        """Get the data for the report, modifying the original for the template output."""
        self._set_meta_info()
        self._set_date_times()
        self._set_descriptions()
        return self._report_data

    def _set_date_times(self):
        """Replace API ISO UTC strings with local report format strings."""
        if self._report_key == ReportTypes.DOC_RECORD and self._report_data:
            doc = self._report_data
            doc['createDateTime'] = report_utils.to_report_datetime(doc['createDateTime'])
            if doc.get('consumerFilingDateTime'):
                doc['consumerFilingDateTime'] = report_utils.to_report_datetime(doc['consumerFilingDateTime'], False)

    def _set_descriptions(self):
        """Replace with title case."""
        if self._report_key == ReportTypes.DOC_RECORD and self._report_data:
            doc = self._report_data
            if doc.get('documentClassDescription'):
                doc['documentClassDescription'] = report_utils.format_description(doc['documentClassDescription'])
            if doc.get('documentTypeDescription'):
                doc['documentTypeDescription'] = report_utils.format_description(doc['documentTypeDescription'])

    def _set_meta_info(self):
        """Identify environment in report if non-production."""
        self._report_data['environment'] = f'{self._get_environment()}'.lstrip()
        self._report_data['meta_account_id'] = self._account_id

        # Appears in the Description section of the PDF Document Properties as Title.
        self._report_data['meta_title'] = ReportMeta.reports[self._report_key]['metaTitle'].upper()
        self._report_data['meta_subtitle'] = ReportMeta.reports[self._report_key]['metaSubtitle']
        footer_content: str = ''
        if self._get_environment() != '':
            footer_content = 'TEST DATA | ' + footer_content if footer_content else 'TEST DATA'
        self._report_data['footer_content'] = footer_content

    @staticmethod
    def _get_environment():
        """Identify environment in report if non-production."""
        env: str = current_app.config.get('DEPLOYMENT_ENV').lower()
        if env.startswith('dev'):
            return 'DEV'
        if env.startswith('test'):
            return 'TEST'
        if env.startswith('sand'):
            return 'SANDBOX'
        return ''


class ReportMeta:  # pylint: disable=too-few-public-methods
    """Helper class to maintain the report meta information."""

    reports = {
        ReportTypes.DOC_RECORD: {
            'reportDescription': 'Document Record',
            'fileName': 'document_record',
            'metaTitle': 'DOCUMENT RECORD',
            'metaSubtitle': 'BC Registries and Online Services',
            'metaSubject': ''
        }
    }
