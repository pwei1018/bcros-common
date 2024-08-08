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
"""Helper/utility functions for report generation."""
import copy
from pathlib import Path

import pycountry
from flask import current_app
from jinja2 import Template
from doc_api.models import utils as model_utils
from doc_api.utils.base import BaseEnum
from doc_api.utils.logging import logger


HEADER_PATH = '/static/header_replace.html'
HEADER_COVER_PATH = '/static/header_cover.html'
HEADER_REG_PATH = '/static/header_registration.html'
HEADER_REG_COVER_PATH = '/static/header_registration_cover.html'
FOOTER_PATH = '/static/footer.html'
FOOTER_COVER_PATH = '/static/footer_cover.html'
FOOTER_REG_COVER_PATH = '/static/footer_registration_cover.html'
HEADER_TITLE_REPLACE = '{{TITLE}}'
HEADER_SUBTITLE_REPLACE = '{{SUBTITLE}}'
HEADER_SUBJECT_REPLACE = '{{SUBJECT}}'
FOOTER_TEXT_REPLACE = '{{FOOTER-TEXT}}'
MARGIN_TOP_REG_REPORT = 1.93
# marginTop 1.5 bottom 0.75
REPORT_META_DATA = {
    'marginTop': 1.25,
    'marginBottom': 0.9,
    'marginLeft': 0.4,
    'marginRight': 0.4,
    'printBackground': True
}
REPORT_FILES = {
    'index.html': '',
    'header.html': '',
    'footer.html': ''
}


class ReportTypes(BaseEnum):
    """Render an Enum of the document service PDF report types."""

    DOC_RECORD = 'document_record'


class Config:  # pylint: disable=too-few-public-methods
    """Configuration that loads report template static data."""

    HEADER_TEMPLATE: str = None
    HEADER_COVER_TEMPLATE: str = None
    HEADER_REG_TEMPLATE: str = None
    HEADER_REG_COVER_TEMPLATE: str = None
    FOOTER_TEMPLATE: str = None
    FOOTER_COVER_TEMPLATE: str = None
    FOOTER_REG_COVER_TEMPLATE: str = None

    @classmethod
    def get_header_template(cls) -> str:
        """Fetch header template data from the file system."""
        if not cls.HEADER_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + HEADER_PATH
            try:
                cls.HEADER_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded header file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading header template from path={file_path}: ' + str(err))
        return cls.HEADER_TEMPLATE

    @classmethod
    def get_reg_header_template(cls) -> str:
        """Fetch registration header template data from the file system."""
        if not cls.HEADER_REG_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + HEADER_REG_PATH
            try:
                cls.HEADER_REG_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded registration header file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading reg header template from path={file_path}: ' + str(err))
        return cls.HEADER_REG_TEMPLATE

    @classmethod
    def get_cover_header_template(cls) -> str:
        """Fetch mail cover letter header template data from the file system."""
        if not cls.HEADER_COVER_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + HEADER_COVER_PATH
            try:
                cls.HEADER_COVER_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded mail cover header file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading mail cover header template from path={file_path}: ' + str(err))
        return cls.HEADER_COVER_TEMPLATE

    @classmethod
    def get_cover_reg_header_template(cls) -> str:
        """Fetch mail cover letter header template data from the file system."""
        if not cls.HEADER_REG_COVER_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + HEADER_REG_COVER_PATH
            try:
                cls.HEADER_REG_COVER_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded reg cover header file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading reg cover header template from path={file_path}: ' + str(err))
        return cls.HEADER_REG_COVER_TEMPLATE

    @classmethod
    def get_footer_template(cls) -> str:
        """Fetch footer template data from the file system."""
        if not cls.FOOTER_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + FOOTER_PATH
            try:
                cls.FOOTER_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded footer file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading footer template from path={file_path}: ' + str(err))
        return cls.FOOTER_TEMPLATE

    @classmethod
    def get_cover_footer_template(cls) -> str:
        """Fetch cover letter footer template data from the file system."""
        if not cls.FOOTER_COVER_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + FOOTER_COVER_PATH
            try:
                cls.FOOTER_COVER_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded mail cover footer file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading mail cover footer template from path={file_path}: ' + str(err))
        return cls.FOOTER_COVER_TEMPLATE

    @classmethod
    def get_cover_reg_footer_template(cls) -> str:
        """Fetch staff registration cover letter footer template data from the file system."""
        if not cls.FOOTER_REG_COVER_TEMPLATE:
            file_path = current_app.config.get('REPORT_TEMPLATE_PATH', '') + FOOTER_REG_COVER_PATH
            try:
                cls.FOOTER_REG_COVER_TEMPLATE = Path(file_path).read_text(encoding='UTF-8')
                logger.info(f'Loaded staff registration cover footer file from path {file_path}')
            except Exception as err:  # noqa: B902; just logging
                logger.error(f'Error loading reg cover footer template from path={file_path}: ' + str(err))
        return cls.FOOTER_REG_COVER_TEMPLATE


def get_header_data(title: str, subtitle: str = '') -> str:
    """Get report header with the provided titles."""
    template = Config().get_header_template()
    if template:
        return template.replace(HEADER_TITLE_REPLACE, title).replace(HEADER_SUBTITLE_REPLACE, subtitle)
    return None


def get_reg_header_data(title: str, subtitle: str, subject: str, mail: bool = False) -> str:
    """Get registration report header with the provided titles and subject."""
    template = Config().get_reg_header_template()
    if template:
        rep_template = template.replace(HEADER_TITLE_REPLACE, title).replace(HEADER_SUBTITLE_REPLACE, subtitle)
        return rep_template.replace(HEADER_SUBJECT_REPLACE, subject)
    return None


def get_cover_header_data(title: str, subtitle: str, subject: str) -> str:
    """Get a mail cover letter report header with the provided titles and subject."""
    template = Config().get_cover_header_template()
    if template:
        rep_template = template.replace(HEADER_TITLE_REPLACE, title).replace(HEADER_SUBTITLE_REPLACE, subtitle)
        return rep_template.replace(HEADER_SUBJECT_REPLACE, subject)
    return None


def get_cover_reg_header_data(title: str, subtitle: str) -> str:
    """Get a mail cover letter report header with the provided titles and subject."""
    template = Config().get_cover_reg_header_template()
    if template:
        rep_template = template.replace(HEADER_TITLE_REPLACE, title).replace(HEADER_SUBTITLE_REPLACE, subtitle)
        return rep_template
    return None


def get_footer_data(footer_text: str, mail: bool = False) -> str:
    """Get report footer with the provided text."""
    template = Config().get_footer_template()
    if template:
        return template.replace(FOOTER_TEXT_REPLACE, footer_text)
    return None


def get_cover_footer_data(footer_text: str) -> str:
    """Get mail cover letter report footer with the provided text."""
    template = Config().get_cover_footer_template()
    if template:
        return template.replace(FOOTER_TEXT_REPLACE, footer_text)
    return None


def get_cover_reg_footer_data() -> str:
    """Get staff registration cover letter report footer."""
    template = Config().get_cover_reg_footer_template()
    return template


def get_report_meta_data(report_type: str = '') -> dict:
    """Get gotenberg report configuration data."""
    if not report_type or report_type not in (ReportTypes.DOC_RECORD):
        return copy.deepcopy(REPORT_META_DATA)
    data = copy.deepcopy(REPORT_META_DATA)
    data['marginTop'] = MARGIN_TOP_REG_REPORT
    return data


def get_report_files(request_data: dict,  # pylint: disable=too-many-branches
                     report_type: str,
                     mail: bool = False) -> dict:
    """Get gotenberg report generation source file data."""
    files = copy.deepcopy(REPORT_FILES)
    files['index.html'] = get_html_from_data(request_data)
    title_text = request_data['templateVars'].get('meta_title', '')
    subtitle_text = request_data['templateVars'].get('meta_subtitle', '')
    footer_text = request_data['templateVars'].get('footer_content', '')
    files['header.html'] = get_header_data(title_text, subtitle_text)
    if report_type == ReportTypes.DOC_RECORD and not mail:
        files['footer.html'] = get_cover_reg_footer_data()
    else:
        files['footer.html'] = get_footer_data(footer_text, False)
    return files


def get_html_from_data(request_data) -> str:
    """Get html by merging the template with the report data."""
    template_ = Template(request_data['template'], autoescape=True)
    html_output = template_.render(request_data['templateVars'])
    return html_output


def set_cover(report_data):  # pylint: disable=too-many-branches, too-many-statements
    """Add cover page report data. Cover page envelope window lines up to a maximum of 4."""
    cover_info = {}
    if report_data.get('submittingParty'):
        party = report_data.get('submittingParty')
        name = ''
        line1: str = ''
        line2: str = ''
        line3: str = ''
        line4: str = ''
        address = party['address']
        country = address.get('country', '')
        region = address.get('region', '')
        if 'businessName' in party:
            name = party['businessName']
        elif 'personName' in party:
            name = party['personName']['first'] + ' ' + party['personName']['last']
        if name:
            line1 = name
            if len(line1) > 40:
                line1 = line1[0:40]
        if country == 'CA':
            postal_code: str = address.get('postalCode', '')
            postal_code = postal_code.replace('-', ' ')
            if len(postal_code) == 6:
                line4 = region + '\n' + postal_code[0:3] + ' ' + postal_code[3:]
            else:
                line4 = region + '\n' + postal_code
        else:
            line4 = region + ' ' + address.get('postalCode', '')

        if (len(address['city']) + len(line4)) < 40:
            line4 = address['city'] + ' ' + line4
        else:
            line3 = address['city']
        if 'street' in address:
            street = address['street']
            if not line2:
                line2 = street
                if len(street) > 40 and line3 == '':
                    line3 = street[40:80]
                    line2 = street[0:40]
            else:
                line3 = street
        if not line3 and 'streetAdditional' in address:
            line3 = address['streetAdditional']
        if line2 and len(line2) > 40:
            line2 = line2[0:40]
        if line3 and len(line3) > 40:
            line3 = line3[0:40]
        if country != 'CA':
            if not line3:
                line3 = line4
                line4 = country
            else:
                line4 = line4 + ' ' + country
        cover_info['line1'] = line1.strip()
        if line2:
            cover_info['line2'] = line2.strip()
        if line3:
            cover_info['line3'] = line3.strip()
        cover_info['line4'] = line4.strip()
    return cover_info


def set_registration_cover(report_data):  # pylint: disable=too-many-branches, too-many-statements
    """Add cover page report data. Cover page envelope window lines up to a maximum of 5."""
    cover_info = {}
    if report_data.get('submittingParty'):
        party = report_data.get('submittingParty')
        if report_data.get('nocLocation') and report_data.get('ppr') and report_data['ppr'].get('securedParty'):
            party = report_data['ppr'].get('securedParty')
        address = party['address']
        name = ''
        line1: str = ''
        line2: str = ''
        line3: str = ''
        line4: str = address.get('region', '')
        country_desc: str = ''
        country = address.get('country', '')
        if country and country == 'US':
            country_desc = 'UNITED STATES OF AMERICA'
        elif country and country != 'CA':
            try:
                country_desc = pycountry.countries.search_fuzzy(country)[0].name
                country_desc = country_desc.upper()
            except (AttributeError, TypeError):
                country_desc = country
        if 'businessName' in party:
            name = party['businessName']
        elif 'personName' in party:
            name = party['personName']['first'] + ' ' + party['personName']['last']
        if name:
            line1 = name
            if len(line1) > 40:
                line1 = line1[0:40]
        postal_code: str = address.get('postalCode', '')
        if country == 'CA' and postal_code:
            postal_code = postal_code.replace('-', ' ')
            if len(postal_code) == 6:
                postal_code = postal_code[0:3] + ' ' + postal_code[3:]
        if postal_code:
            line4 += '\n' + postal_code

        if (len(address['city']) + len(line4)) < 40:
            line4 = address['city'] + ' ' + line4
        else:
            line3 = address['city']
        if 'street' in address:
            street = address['street']
            if not line2:
                line2 = street
                if len(street) > 40 and line3 == '':
                    line3 = street[40:80]
                    line2 = street[0:40]
            else:
                line3 = street
        if not line3 and 'streetAdditional' in address:
            line3 = address['streetAdditional']
        if line2 and len(line2) > 40:
            line2 = line2[0:40]
        if line3 and len(line3) > 40:
            line3 = line3[0:40]
        if country_desc:
            if not line3:
                line3 = line4
                line4 = country_desc
            else:
                cover_info['line5'] = country_desc
        cover_info['line1'] = line1.strip()
        if line2:
            cover_info['line2'] = line2.strip()
        if line3:
            cover_info['line3'] = line3.strip()
        cover_info['line4'] = line4.strip()
    return cover_info


def format_description(description: str) -> str:
    """Format the registration description as title case."""
    if not description:
        return description
    doc_desc: str = description
    has_slash = bool(doc_desc.find('/') > 0)
    if has_slash:
        doc_desc = doc_desc.replace('/', ' / ')
    doc_desc: str = doc_desc.lower().title()
    doc_desc = doc_desc.replace(' Of ', ' of ')
    doc_desc = doc_desc.replace(' To ', ' to ')
    doc_desc = doc_desc.replace(' Or ', ' or ')
    doc_desc = doc_desc.replace(' Under ', ' under ')
    doc_desc = doc_desc.replace(' And ', ' and ')
    doc_desc = doc_desc.replace(' With ', ' with ')
    doc_desc = doc_desc.replace('(S)', '(s)')
    doc_desc = doc_desc.replace("'S", "'s")
    if has_slash:
        doc_desc = doc_desc.replace(' / ', '/')
    doc_desc = doc_desc.replace('Ppsa ', 'PPSA ')
    return doc_desc


def format_phone_number(phone: str) -> str:
    """Format the phone number as (ddd) ddd-dddd."""
    if not phone:
        return phone
    if len(phone) == 10:
        return '(' + phone[0:3] + ') ' + phone[3:6] + '-' + phone[6:]
    if len(phone) == 7:
        return phone[0:3] + '-' + phone[3:]
    return phone


def to_report_datetime(date_time: str, include_time: bool = True):
    """Convert ISO formatted date time or date string to report format."""
    if len(date_time) < 10:  # Invalid format.
        return date_time
    if len(date_time) == 10:  # Legacy has some date only data.
        report_date = model_utils.date_from_iso_format(date_time)
        return report_date.strftime('%B %-d, %Y')
    local_datetime = model_utils.to_local_timestamp(model_utils.ts_from_iso_format(date_time))
    if include_time:
        timestamp = local_datetime.strftime('%B %-d, %Y at %-I:%M:%S %p Pacific time')
        if timestamp.find(' AM ') > 0:
            return timestamp.replace(' AM ', ' am ')
        return timestamp.replace(' PM ', ' pm ')

    return local_datetime.strftime('%B %-d, %Y')
