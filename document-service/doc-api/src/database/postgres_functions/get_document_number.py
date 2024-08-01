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
"""Maintain db function get_document_number here."""
from alembic_utils.pg_function import PGFunction


get_document_number = PGFunction(
    schema="public",
    signature="get_document_number()",
    definition="""
    RETURNS VARCHAR
    LANGUAGE plpgsql
    AS
    $$
    BEGIN
        RETURN trim(to_char(nextval('document_number_seq'), '0000000000'));
    END
    ;
    $$;
    """
)
