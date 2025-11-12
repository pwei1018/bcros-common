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

"""Service to  manage report-templates."""

import csv
import io
from typing import Dict, Iterator


class CsvService:  # pylint: disable=too-few-public-methods
    """Service for all template related operations."""

    @classmethod
    def create_report(cls, payload: Dict) -> Iterator[bytes]:
        """Create a streaming CSV report generator from the input parameters."""
        columns = payload.get('columns', None)
        values = payload.get('values', None)
        if not columns:
            return

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(columns)
        yield buffer.getvalue().encode('utf-8')
        buffer.seek(0)
        buffer.truncate(0)

        for row in values:
            writer.writerow(row)
            yield buffer.getvalue().encode('utf-8')
            buffer.seek(0)
            buffer.truncate(0)
