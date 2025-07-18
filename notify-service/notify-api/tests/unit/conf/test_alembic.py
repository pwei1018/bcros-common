# Copyright © 2021 Province of British Columbia.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests to assure that the alembic setup is correct.

Test-Suite to ensure that Alembic and Migration are working as expected.
"""

from pathlib import Path
import string

from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest

from tests.conftest import not_raises


class TestAlembicSetup:
    """Test suite for Alembic database migration configuration."""

    @pytest.fixture
    @staticmethod
    def alembic_config():
        """Create an Alembic configuration object."""
        config = Config()
        config.set_main_option("script_location", "migrations")
        return config

    @pytest.fixture
    @staticmethod
    def script_directory(alembic_config):
        """Create a ScriptDirectory object from the config."""
        return ScriptDirectory.from_config(alembic_config)

    @staticmethod
    def test_migrations_directory_exists():
        """Test that the migrations directory exists."""
        migrations_path = Path("migrations")
        assert migrations_path.exists(), "migrations directory should exist"
        assert migrations_path.is_dir(), "migrations should be a directory"

    @staticmethod
    def test_alembic_ini_exists():
        """Test that alembic.ini file exists in migrations directory."""
        alembic_ini_path = Path("migrations/alembic.ini")
        assert alembic_ini_path.exists(), "alembic.ini should exist in migrations directory"

    @staticmethod
    def test_versions_directory_exists():
        """Test that the versions directory exists and contains migration files."""
        versions_path = Path("migrations/versions")
        assert versions_path.exists(), "versions directory should exist"
        assert versions_path.is_dir(), "versions should be a directory"

        # Check that there are migration files
        migration_files = list(versions_path.glob("*.py"))
        assert len(migration_files) > 0, "versions directory should contain migration files"

    @staticmethod
    def test_no_branches_in_versions(script_directory):
        """Test that there are no branches in the migration versions."""
        with not_raises(Exception):
            head = script_directory.get_current_head()
            assert head is not None, "Should have a current head revision"

    @staticmethod
    def test_migration_heads_are_consistent(script_directory):
        """Test that migration heads are consistent and there's only one head."""
        heads = script_directory.get_heads()
        assert len(heads) == 1, f"Should have exactly one head, found {len(heads)}: {heads}"

    @staticmethod
    def test_migration_chain_is_linear(script_directory):
        """Test that the migration chain is linear (no branches)."""
        revisions = list(script_directory.walk_revisions())

        # Check that each revision (except the first) has exactly one down_revision
        for revision in revisions:
            if revision.down_revision is not None:
                # If it has a down_revision, it should be a single revision (not a tuple)
                assert isinstance(revision.down_revision, str), (
                    f"Revision {revision.revision} has branched down_revision: {revision.down_revision}"
                )

    @staticmethod
    def test_all_migration_files_are_valid():
        """Test that all migration files in versions directory are valid Python files."""
        versions_path = Path("migrations/versions")
        migration_files = list(versions_path.glob("*.py"))

        for migration_file in migration_files:
            # Skip __pycache__ and other non-migration files
            if migration_file.name.startswith("__"):
                continue

            # Try to compile the file to check for syntax errors
            with open(migration_file, encoding="utf-8") as f:
                content = f.read()
                try:
                    compile(content, migration_file, "exec")
                except SyntaxError as e:
                    pytest.fail(f"Migration file {migration_file} has syntax errors: {e}")

    @staticmethod
    def test_migration_file_naming_convention():
        """Test that migration files follow the expected naming convention."""
        versions_path = Path("migrations/versions")
        migration_files = [f for f in versions_path.glob("*.py") if not f.name.startswith("__")]

        for migration_file in migration_files:
            filename = migration_file.name
            # Migration files should start with a number or follow alembic's naming pattern
            assert any([
                filename.startswith(tuple(string.digits)),  # Numbered migrations
                "_" in filename,  # Alembic generated names with revision_description format
            ]), f"Migration file {filename} doesn't follow expected naming convention"

    @staticmethod
    def test_env_py_exists_and_is_valid():
        """Test that env.py exists and is a valid Python file."""
        env_py_path = Path("migrations/env.py")
        assert env_py_path.exists(), "env.py should exist in migrations directory"

        # Check that it's a valid Python file
        with open(env_py_path, encoding="utf-8") as f:
            content = f.read()
            try:
                compile(content, env_py_path, "exec")
            except SyntaxError as e:
                pytest.fail(f"env.py has syntax errors: {e}")

    @staticmethod
    def test_script_py_mako_exists():
        """Test that script.py.mako template exists."""
        template_path = Path("migrations/script.py.mako")
        assert template_path.exists(), "script.py.mako template should exist in migrations directory"
