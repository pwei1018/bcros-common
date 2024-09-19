""" Tests to assure the Generator Model.

Test-Suite to ensure that the Generator Model is working as expected.
"""

import pytest
from pdf_gen_api.models import Generator
from pdf_gen_api.resources import GenerableItem


def test_pdf_name_field():
    selection = GenerableItem.AGM_EXTENSION.value
    generator = Generator(selection, {}, {selection: {}})
    assert generator.file_name == selection

