# Copyright © 2025 Province of British Columbia
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

"""Chunk PDF generation service for handling large datasets."""

import gc
import io
import os
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app, url_for
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from api.services.page_info import (
    populate_page_info,
    populate_page_info_with_offset,
)
from api.utils.util import TEMPLATE_FOLDER_PATH


class ChunkReportService:  # pylint:disable=too-few-public-methods
    """Service for generating large reports using chunk approach."""

    _TEMPLATE_ENV = Environment(
        loader=FileSystemLoader("."), autoescape=True
    )

    @dataclass
    class ChunkInfo:
        """Chunk info for chunk report."""

        mode: str = "transactions"
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
        from pikepdf import Pdf # pylint:disable=import-outside-toplevel

        with Pdf.new() as out_pdf:
            for path in temp_files:
                with Pdf.open(path) as src:
                    out_pdf.pages.extend(src.pages)
            buf = io.BytesIO()
            out_pdf.save(buf)
            return buf.getvalue()


    @staticmethod
    def _append_pdf_bytes(pdf_content: bytes, temp_files: List[str]) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_content)
            temp_files.append(temp_file.name)

    @staticmethod
    def _render_pdf_bytes_worker(args: Tuple[str, str]) -> bytes:
        """Worker used in process pool to render HTML string to PDF bytes."""
        html_out, base_url = args
        gc.collect()
        html = HTML(string=html_out, base_url=base_url)
        pdf_content = html.write_pdf()
        del html
        gc.collect()
        return pdf_content

    @staticmethod
    def _render_pdf_with_offset_worker(args: Tuple[str, str, int, int]) -> bytes:
        """Render HTML then populate page numbers with offset and total, return PDF bytes."""
        html_out, base_url, start_index, total_pages = args
        gc.collect()
        doc = HTML(string=html_out, base_url=base_url).render()
        doc = populate_page_info_with_offset(doc, start_index, total_pages)
        pdf_content = doc.write_pdf()
        del doc
        gc.collect()
        return pdf_content

    @staticmethod
    def _build_chunk_html(
        template_name: str,
        template_vars: Dict[str, Any],
        invoice_copy: Dict[str, Any],
        chunk_info: "ChunkReportService.ChunkInfo",
    ) -> str:
        chunk_vars = template_vars.copy()
        chunk_vars["groupedInvoices"] = [invoice_copy]
        chunk_vars["_chunk_info"] = asdict(chunk_info)
        template = ChunkReportService._TEMPLATE_ENV.get_template(
            f"{TEMPLATE_FOLDER_PATH}/{template_name}.html"
        )
        bc_logo_url = url_for("static", filename="images/bcgov-logo-vert.jpg")
        registries_url = url_for("static", filename="images/reg_logo.png")
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
            txns = original.get("transactions") or []
            if not txns:
                continue
            start = 0
            while start < len(txns):
                end = min(start + chunk_size, len(txns))
                invoice_copy = dict(original)
                invoice_copy["transactions"] = txns[start:end]
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
    def _render_tasks_parallel(
        tasks: List[Tuple[int, str]],
        base_url: str,
        worker_count: int,
    ) -> List[bytes]:
        """Render HTML tasks in parallel and return ordered PDF bytes list."""
        results: List[Tuple[int, bytes]] = []
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(
                    ChunkReportService._render_pdf_bytes_worker,
                    (html_out, base_url),
                ): oid
                for oid, html_out in tasks
            }
            for fut in as_completed(future_map):
                results.append((future_map[fut], fut.result()))
        return [pdf for _, pdf in sorted(results, key=lambda x: x[0])]

    @staticmethod
    def _count_pdf_pages(pdf_bytes: bytes) -> int:
        """Return page count using pikepdf (fast, no render)."""
        # Lazy import to avoid heavy module import in worker processes
        from pikepdf import Pdf  # pylint:disable=import-outside-toplevel

        with Pdf.open(io.BytesIO(pdf_bytes)) as pdf:
            return len(pdf.pages)

    @staticmethod
    def _render_second_pass_to_temp_files(
        ordered_htmls: List[str],
        base_url: str,
        worker_count: int,
        first_pass_pdfs: List[bytes],
    ) -> List[str]:
        """Second pass render: render with page offsets and persist to temp files."""
        temp_files: List[str] = []

        page_counts = [ChunkReportService._count_pdf_pages(pdf) for pdf in first_pass_pdfs]
        offsets: List[int] = []
        total_pages = 0
        for count in page_counts:
            offsets.append(total_pages + 1)
            total_pages += count

        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(
                    ChunkReportService._render_pdf_with_offset_worker,
                    (ordered_htmls[i], base_url, offsets[i], total_pages),
                ): i
                for i in range(len(ordered_htmls))
            }
            ordered_results: Dict[int, bytes] = {}
            for fut in as_completed(future_map):
                ordered_results[future_map[fut]] = fut.result()
            for i in range(len(ordered_htmls)):
                ChunkReportService._append_pdf_bytes(ordered_results[i], temp_files)
        # Help GC in very large runs
        del ordered_results
        gc.collect()
        return temp_files

    @dataclass
    class MergeContext:
        """Merge context for chunk report."""

        template_name: str
        template_vars: Dict[str, Any]
        temp_files: List[str]
        generate_page_number: bool

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
            chunk_size = 500 # the optimal chunk size is 500 after testing

        grouped_invoices = template_vars.get("groupedInvoices", [])
        temp_files: List[str] = []

        # Build all chunk HTMLs ahead of time (keep order id)
        tasks = ChunkReportService._prepare_chunk_tasks(
            template_name, template_vars, grouped_invoices, chunk_size
        )

        base_url = current_app.root_path
        worker_count = max(1, (os.cpu_count() or 2) - 1)

        # Preserve original order of HTML chunks
        ordered_htmls: List[str] = [html for _, html in sorted(tasks, key=lambda x: x[0])]

        # First pass: quick render to PDF bytes and collect page counts
        first_pass_pdfs = ChunkReportService._render_tasks_parallel(
            tasks, base_url, worker_count
        )

        # Second pass: render again with page offsets and write PDFs
        temp_files = ChunkReportService._render_second_pass_to_temp_files(
            ordered_htmls, base_url, worker_count, first_pass_pdfs
        )

        # Merge and finalize output
        result = ChunkReportService._merge_and_finalize(
            ChunkReportService.MergeContext(
                template_name=template_name,
                template_vars=template_vars,
                temp_files=temp_files,
                generate_page_number=generate_page_number
            )
        )

        elapsed = time.time() - overall_start_time
        current_app.logger.info(
            "chunk_report done: chunks=%s elapsed=%.1fs", len(tasks), elapsed
        )
        return result


    @staticmethod
    def _merge_and_finalize(ctx: "ChunkReportService.MergeContext") -> bytes:
        """Merge temp PDFs, optionally fix page numbers, log and return final bytes."""
        merged_pdf = ChunkReportService._merge_pdf_files(ctx.temp_files)
        return merged_pdf
