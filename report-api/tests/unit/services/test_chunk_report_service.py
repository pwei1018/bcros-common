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


"""Tests to assure the ChunkReportService."""

from weasyprint import HTML

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


def _make_pdf_bytes(text: str) -> bytes:
    html = f'<html><body><p>{text}</p></body></html>'
    return HTML(string=html).write_pdf()


def test_merge_pdf_files_merges_two_pdfs(tmp_path):
    """Merge two tiny PDFs and ensure result bytes are returned."""
    p1 = tmp_path / 'a.pdf'
    p2 = tmp_path / 'b.pdf'
    p1.write_bytes(_make_pdf_bytes('A'))
    p2.write_bytes(_make_pdf_bytes('B'))

    merged = ChunkReportService._merge_pdf_files([str(p1), str(p2)])
    assert isinstance(merged, (bytes, bytearray))
    # merged file should be larger than each single input
    assert len(merged) > max(p1.stat().st_size, p2.stat().st_size)


def test_fix_page_numbers_skip_when_large_pdf():
    """When merged PDF is >10MB, function should return input unchanged."""
    big_bytes = b'x' * (10 * 1024 * 1024 + 1)
    out = ChunkReportService._fix_page_numbers_by_regeneration('statement_report', {'groupedInvoices': [{}]}, big_bytes)
    assert out == big_bytes
