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

"""Tests to assure the User Model.

Test-Suite to ensure that the User Model is working as expected.
"""
import pytest

from doc_api.models import User
from doc_api.utils.logging import logger


TOKEN1 = {
    'username': 'username',
    'given_name': 'given_name',
    'family_name': 'family_name',
    'iss': 'issuer',
    'sub': 'subject',
    'idp_userid': '123',
    'loginSource': 'IDIR'
}
TOKEN2 = {
    'username': 'username',
    'firstname': 'given_name',
    'lastname': 'family_name',
    'iss': 'issuer',
    'sub': 'subject',
    'idp_userid': '123',
    'loginSource': 'IDIR'
}
TEST_TOKEN = {
    'username': 'username_TEST1',
    'firstname': 'given_name_TEST1',
    'lastname': 'family_name_TEST1',
    'iss': 'issuer_TEST1',
    'sub': 'subject_TEST1',
    'idp_userid': 'idp_userid_TEST1',
    'loginSource': 'source_TEST1'
}
TEST_TOKEN_DATA = [
    (TOKEN1),
    (TOKEN2)
]


@pytest.mark.parametrize('token', TEST_TOKEN_DATA)
def test_jwt_properties(session, client, jwt, token):
    """Assert that user jwt properties are as expected."""
    assert jwt
    firstname = token.get('given_name', None)
    if not firstname:
        firstname = token.get('firstname', None)
    lastname = token.get('family_name', None)
    if not lastname:
        lastname = token.get('lastname', None)
    user = User(
        username=token.get('username', None),
        firstname=firstname,
        lastname=lastname,
        iss=token['iss'],
        sub=token['sub'],
        idp_userid=token['idp_userid'],
        login_source=token['loginSource']
    )
    assert user.username == 'username'
    assert user.iss == 'issuer'
    assert user.sub == 'subject'
    assert user.firstname == 'given_name'
    assert user.lastname == 'family_name'
    assert user.idp_userid == '123'
    assert user.login_source == 'IDIR'


def test_find_by_id(session, client, jwt):
    """Assert that user find by id is working as expected."""
    user = User.find_by_id(1)
    if not user:
        user2 = User.create_from_jwt_token(TEST_TOKEN, 'UT1234')
        user = User.find_by_id(user2.id)

    assert user
    assert user.id
    assert user.username == 'username_TEST1'
    assert user.iss == 'issuer_TEST1'
    assert user.sub == 'subject_TEST1'
    assert user.firstname == 'given_name_TEST1'
    assert user.lastname == 'family_name_TEST1'
    assert user.idp_userid == 'idp_userid_TEST1'
    assert user.login_source == 'source_TEST1'

def test_find_by_jwt_token(session, client, jwt):
    """Assert that user find by jwt token is working as expected."""
    user = User.find_by_jwt_token(TEST_TOKEN)
    if not user:
        User.create_from_jwt_token(TEST_TOKEN, 'UT1234')
        user = User.find_by_jwt_token(TEST_TOKEN)

    assert user
    assert user.id
    assert user.username == 'username_TEST1'
    assert user.iss == 'issuer_TEST1'
    assert user.sub == 'subject_TEST1'
    assert user.firstname == 'given_name_TEST1'
    assert user.lastname == 'family_name_TEST1'
    assert user.idp_userid == 'idp_userid_TEST1'
    assert user.login_source == 'source_TEST1'

def test_find_by_username(session, client, jwt):
    """Assert that user find by username is working as expected."""
    user = User.find_by_username(TEST_TOKEN['username'])
    if not user:
        User.create_from_jwt_token(TEST_TOKEN, 'UT1234')
        user = User.find_by_username(TEST_TOKEN['username'])

    assert user
    assert user.id
    assert user.username == 'username_TEST1'
    assert user.iss == 'issuer_TEST1'
    assert user.sub == 'subject_TEST1'
    assert user.firstname == 'given_name_TEST1'
    assert user.lastname == 'family_name_TEST1'
    assert user.idp_userid == 'idp_userid_TEST1'
    assert user.login_source == 'source_TEST1'

def test_find_by_subject(session, client, jwt):
    """Assert that user find by subject is working as expected."""
    user = User.find_by_sub(TEST_TOKEN['sub'])
    if not user:
        User.create_from_jwt_token(TEST_TOKEN, 'UT1234')
        user = User.find_by_sub(TEST_TOKEN['sub'])

    assert user
    assert user.id
    assert user.username == 'username_TEST1'
    assert user.iss == 'issuer_TEST1'
    assert user.sub == 'subject_TEST1'
    assert user.firstname == 'given_name_TEST1'
    assert user.lastname == 'family_name_TEST1'
    assert user.idp_userid == 'idp_userid_TEST1'
    assert user.login_source == 'source_TEST1'

def test_get_or_create(session, client, jwt):
    """Assert that get or create user is working as expected."""
    user = User.get_or_create_user_by_jwt(TEST_TOKEN, 'UT1234')

    assert user
    assert user.id
    assert user.username == 'username_TEST1'
    assert user.iss == 'issuer_TEST1'
    assert user.sub == 'subject_TEST1'
    assert user.firstname == 'given_name_TEST1'
    assert user.lastname == 'family_name_TEST1'
    assert user.idp_userid == 'idp_userid_TEST1'
    assert user.login_source == 'source_TEST1'
