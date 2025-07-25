# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Exposes all of the resource endpoints mounted in Flask-Blueprints."""
from .application_documents import bp as app_document_bp
from .application_reports import bp as app_report_bp
from .business_requests import bp as business_bp
from .callbacks import bp as callback_bp
from .documents import bp as document_bp
from .mhr_requests import bp as mhr_bp
from .nr_requests import bp as nr_bp
from .pdf_conversions import bp as pdf_convert_bp
from .ppr_requests import bp as ppr_bp
from .reports import bp as report_bp
from .scanning import bp as scanning_bp
from .searches import bp as search_bp
