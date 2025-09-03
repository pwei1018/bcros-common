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


"""Service for generating large reports using chunk approach."""
import asyncio
import io
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app, url_for
from jinja2 import Environment, FileSystemLoader

from api.services.footer_service import add_page_numbers_to_pdf
from api.services.gotenberg_service import GotenbergService
from api.utils.util import TEMPLATE_FOLDER_PATH


class ChunkReportService:  # pylint:disable=too-few-public-methods
    """Service for generating large reports using chunk approach."""

    _TEMPLATE_ENV = Environment(
        loader=FileSystemLoader('.'), autoescape=True
    )

    @dataclass
    class ChunkInfo:
        """Chunk info for chunk report."""

        mode: str = 'transactions'
        invoice_index: int = 0
        current_chunk: int = 0
        slice_start: int = 0
        slice_end: int = 0
        invoice_chunks: Optional[int] = None

    @staticmethod
    def _cleanup_temp_files(temp_files: List[str]):
        """Clean up temporary files."""
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @staticmethod
    def _merge_pdf_files(temp_files: List[str]) -> bytes:
        """Merge multiple PDF files into one."""
        # Lazy import to avoid heavy module import in worker processes
        from pikepdf import Pdf  # pylint:disable=import-outside-toplevel

        with Pdf.new() as out_pdf:
            for path in temp_files:
                with Pdf.open(path) as src:
                    out_pdf.pages.extend(src.pages)
            buf = io.BytesIO()
            out_pdf.save(buf)
            return buf.getvalue()

    @staticmethod
    def _append_pdf_bytes(pdf_content: bytes, temp_files: List[str]) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_content)
            temp_files.append(temp_file.name)

    @staticmethod
    def _build_chunk_html(
        template_name: str,
        template_vars: Dict[str, Any],
        invoice_copy: Dict[str, Any],
        chunk_info: 'ChunkReportService.ChunkInfo',
    ) -> str:
        chunk_vars = template_vars.copy()
        chunk_vars['groupedInvoices'] = [invoice_copy]
        chunk_vars['_chunk_info'] = asdict(chunk_info)

        template = ChunkReportService._TEMPLATE_ENV.get_template(
            f'{TEMPLATE_FOLDER_PATH}/{template_name}.html'
        )
        bc_logo_url = url_for('static', filename='images/bcgov-logo-vert.jpg')
        registries_url = url_for('static', filename='images/reg_logo.png')
        return template.render(
            chunk_vars, bclogoUrl=bc_logo_url, registriesurl=registries_url
        )

    @staticmethod
    def _prepare_chunk_tasks(
        template_name: str,
        template_vars: Dict[str, Any],
        grouped_invoices: List[Dict[str, Any]],
        chunk_size: int,
    ) -> List[Tuple[int, str]]:
        """Prepare (order_id, html_out) tasks for all invoice transaction slices."""
        tasks: List[Tuple[int, str]] = []
        order_id = 0
        for invoice_index, original in enumerate(grouped_invoices, start=1):
            txns = original.get('transactions') or []
            if not txns:
                continue
            start = 0
            while start < len(txns):
                end = min(start + chunk_size, len(txns))
                invoice_copy = dict(original)
                invoice_copy['transactions'] = txns[start:end]
                html_out = ChunkReportService._build_chunk_html(
                    template_name,
                    template_vars,
                    invoice_copy,
                    ChunkReportService.ChunkInfo(
                        invoice_index=invoice_index,
                        current_chunk=(start // max(1, chunk_size)) + 1,
                        slice_start=start + 1,
                        slice_end=end,
                    ),
                )
                tasks.append((order_id, html_out))
                order_id += 1
                start = end
        return tasks

    @staticmethod
    def create_chunk_report(
        template_name: str,
        template_vars: Dict[str, Any],
        generate_page_number: bool = False,
        chunk_size: Optional[int] = None,
    ) -> bytes:
        """Create large reports using chunking approach."""
        overall_start_time = time.time()

        if chunk_size is None:
            chunk_size = 500  # the optimal chunk size is 500 after testing

        grouped_invoices = template_vars.get('groupedInvoices', [])
        temp_files: List[str] = []

        # Build all chunk HTMLs ahead of time (keep order id)
        tasks = ChunkReportService._prepare_chunk_tasks(
            template_name, template_vars, grouped_invoices, chunk_size
        )

        base_url = current_app.root_path

        # First pass: render all chunks to PDF bytes in parallel (no footers)
        pdf_chunks = asyncio.run(
            GotenbergService.render_tasks_parallel_async(tasks, base_url)
        )

        for pdf_content in pdf_chunks:
            ChunkReportService._append_pdf_bytes(pdf_content, temp_files)

        merged_pdf_without_footers = ChunkReportService._merge_pdf_files(temp_files)

        ChunkReportService._cleanup_temp_files(temp_files)

        result = add_page_numbers_to_pdf(template_vars, merged_pdf_without_footers, generate_page_number)

        current_app.logger.info(
            'chunk_report done: chunks=%s elapsed=%.1fs', len(tasks), time.time() - overall_start_time
        )
        return result
