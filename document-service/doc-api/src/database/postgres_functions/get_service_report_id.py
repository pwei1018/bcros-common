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
"""Maintain db function get_service_report_id here."""
from alembic_utils.pg_function import PGFunction

get_service_report_id = PGFunction(
    schema="public",
    signature="get_service_report_id()",
    definition="""
    RETURNS VARCHAR
    LANGUAGE plpgsql
    AS
    $$
    BEGIN
        RETURN 'DSR' || trim(to_char(nextval('service_report_id_seq'), '0000000000'));
    END
    ;
    $$;
    """,
)
