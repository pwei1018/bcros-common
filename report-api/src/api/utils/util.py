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

"""CORS pre-flight decorator.

A simple decorator to add the options method to a Request Class.
"""
import os.path
import re

TEMPLATE_FOLDER_PATH = 'report-templates/'


def sanitize_template_name(template_name: str) -> str:
    """Sanitize template name to prevent path traversal attacks."""
    if not template_name:
        raise ValueError('Template name cannot be empty')

    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', template_name)

    if not sanitized:
        raise ValueError('Template name contains no valid characters')

    if '..' in template_name or '/' in template_name or '\\' in template_name:
        raise ValueError('Template name contains invalid path characters')

    final_path = os.path.join(TEMPLATE_FOLDER_PATH, f'{sanitized}.html')
    if not os.path.abspath(final_path).startswith(os.path.abspath(TEMPLATE_FOLDER_PATH)):
        raise ValueError('Template path traversal detected')

    return sanitized


def cors_preflight(methods: str = 'GET'):
    """Render an option method on the class."""
    def wrapper(f):
        def options(self, *args, **kwargs):  # pylint: disable=unused-argument
            return {'Allow': 'GET'}, 200, \
                   {'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': methods,
                    'Access-Control-Allow-Headers': 'Authorization, Content-Type'}

        setattr(f, 'options', options)
        return f

    return wrapper
