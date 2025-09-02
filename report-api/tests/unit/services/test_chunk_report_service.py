# Copyright © 2025 Province of British Columbia
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


import types
from api.services.chunk_report_service import ChunkReportService


def test_prepare_chunk_tasks_splits_transactions(monkeypatch):
    """Should split one invoice's transactions into multiple chunk tasks."""

    captured = []

    def fake_build_chunk_html(template_name, template_vars, invoice_copy, chunk_info):
        captured.append(
            {
                'start': chunk_info.slice_start,
                'end': chunk_info.slice_end,
                'len': len(invoice_copy.get('transactions') or []),
            }
        )
        return '<html><body>ok</body></html>'

    monkeypatch.setattr(ChunkReportService, '_build_chunk_html', staticmethod(fake_build_chunk_html))

    grouped_invoices = [
        {
            'invoiceId': 'A',
            'transactions': list(range(12)),  # 12 rows
        }
    ]

    tasks = ChunkReportService._prepare_chunk_tasks('statement_report', {'foo': 'bar'}, grouped_invoices, chunk_size=5)
    assert len(tasks) == 3
    # verify chunk boundaries 1-5, 6-10, 11-12
    assert captured[0] == {'start': 1, 'end': 5, 'len': 5}
    assert captured[1] == {'start': 6, 'end': 10, 'len': 5}
    assert captured[2] == {'start': 11, 'end': 12, 'len': 2}


class _DummyPdf:
    def __init__(self, pages=None):
        self.pages = list(pages or [])

    # context manager compat
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def save(self, buf):
        # Write bytes proportional to number of pages so len > 0
        buf.write(b"X" * (len(self.pages) + 1))


def test_merge_pdf_files_merges_two_pdfs(tmp_path, monkeypatch):
    """Merge two tiny PDFs and ensure result bytes are returned."""
    p1 = tmp_path / 'a.pdf'
    p2 = tmp_path / 'b.pdf'
    p1.write_bytes(b'A')
    p2.write_bytes(b'B')

    fake_module = types.SimpleNamespace()

    def _open(_path):
        # one page per file
        return _DummyPdf(pages=[b'pg'])

    def _new():
        return _DummyPdf()

    fake_module.open = staticmethod(_open)
    fake_module.new = staticmethod(_new)

    import pikepdf as _pike
    monkeypatch.setattr(_pike, 'Pdf', fake_module)

    merged = ChunkReportService._merge_pdf_files([str(p1), str(p2)])
    assert isinstance(merged, (bytes, bytearray))
    assert len(merged) > 0


