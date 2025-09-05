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
"""Centralized setup of logging for the service."""
import logging
import logging.config
import sys
from os import path
from importlib import resources
from tempfile import NamedTemporaryFile
from structured_logging import StructuredLogging


def setup_logging(conf):
    """Create the services logger."""
    if conf and path.isfile(conf):
        logging.config.fileConfig(conf)
        print(f'Configure logging, from conf: {conf}', file=sys.stdout)
    else:
        try:
            conf_path = resources.files('api') / 'logging.conf'
            if conf_path.exists():
                with NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as tmp_file:
                    tmp_file.write(conf_path.read_text())
                    tmp_file.flush()
                    logging.config.fileConfig(tmp_file.name)
                    print(f'Configure logging from package resources: {conf_path}', file=sys.stdout)
                    return
        except Exception as e:  # noqa: B902 pylint: disable=broad-exception-caught
            print(f'Unable to configure logging from package resources: {e}', file=sys.stderr)
        print(f'Unable to configure logging, attempted conf: {conf}', file=sys.stderr)


class StructuredLogHandler(logging.Handler):
    """StructuredLogHandler that wraps StructuredLogging."""

    def __init__(self, structured_logger=None):
        """Initialize the StructuredLogHandler."""
        super().__init__()
        self.structured_logger = structured_logger or StructuredLogging.get_logger()

    def emit(self, record):
        """Emit a record."""
        msg = self.format(record)
        level = record.levelname.lower()

        if level == 'debug':
            self.structured_logger.debug(msg)
        elif level == 'info':
            self.structured_logger.info(msg)
        elif level == 'warning':
            self.structured_logger.warning(msg)
        elif level == 'error':
            self.structured_logger.error(msg)
        elif level == 'critical':
            self.structured_logger.critical(msg)
