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
import re
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app, url_for
from jinja2 import Environment, FileSystemLoader
from PyPDF2 import PdfMerger
from weasyprint import HTML

from api.services.page_info import populate_page_info
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
        with PdfMerger() as merger:
            for temp_file in temp_files:
                with open(temp_file, "rb") as pdf_file:
                    merger.append(pdf_file)

            output = io.BytesIO()
            merger.write(output)
            return output.getvalue()

    @staticmethod
    def _optimize_html_if_large(html_out: str) -> str:
        html_size_mb = len(html_out.encode("utf-8")) / (1024 * 1024)
        if html_size_mb > 10:
            html_out = re.sub(r"<!--.*?-->", "", html_out, flags=re.DOTALL)
            html_out = re.sub(r">\s+<", "><", html_out)
            html_out = re.sub(r"\s+", " ", html_out)
        return html_out

    @staticmethod
    def _render_pdf_fast(html_out: str) -> bytes:
        gc.collect()
        html = HTML(string=html_out)
        pdf_content = html.write_pdf()
        del html
        gc.collect()
        return pdf_content

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
                tasks.append(
                    (order_id, ChunkReportService._optimize_html_if_large(html_out))
                )
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

    @dataclass
    class MergeContext:
        """Merge context for chunk report."""

        template_name: str
        template_vars: Dict[str, Any]
        temp_files: List[str]
        generate_page_number: bool
        overall_start_time: float

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
            chunk_size = 500

        grouped_invoices = template_vars.get("groupedInvoices", [])
        temp_files: List[str] = []

        # Build all chunk HTMLs ahead of time (keep order id)
        tasks = ChunkReportService._prepare_chunk_tasks(
            template_name, template_vars, grouped_invoices, chunk_size
        )

        # Parallel render using process pool
        base_url = current_app.root_path
        worker_count = max(1, (os.cpu_count() or 2) - 1)

        for pdf_bytes in ChunkReportService._render_tasks_parallel(
            tasks, base_url, worker_count
        ):
            ChunkReportService._append_pdf_bytes(pdf_bytes, temp_files)

        # Merge and finalize output
        return ChunkReportService._merge_and_finalize(
            ChunkReportService.MergeContext(
                template_name=template_name,
                template_vars=template_vars,
                temp_files=temp_files,
                generate_page_number=generate_page_number,
                overall_start_time=overall_start_time,
            )
        )

    @staticmethod
    def _fix_page_numbers_by_regeneration(
        template_name: str, template_vars: Dict[str, Any], merged_pdf: bytes
    ) -> bytes:
        """
        Fix page numbers by regenerating the PDF with proper page numbering.

        This is more reliable than trying to edit the merged PDF directly.
        """

        # For large outputs, regenerating the entire document is too heavy; skip
        merged_size_mb = len(merged_pdf) / (1024 * 1024)
        if merged_size_mb > 10:
            return merged_pdf

        # For large datasets, regenerating might still be too slow, so we skip it
        invoice_count = len(template_vars.get("groupedInvoices", []))
        if invoice_count > 10:
            return merged_pdf

        # Render the complete template
        env = Environment(loader=FileSystemLoader("."), autoescape=True)
        template = env.get_template(f"{TEMPLATE_FOLDER_PATH}/{template_name}.html")
        bc_logo_url = url_for("static", filename="images/bcgov-logo-vert.jpg")
        registries_url = url_for("static", filename="images/reg_logo.png")
        html_out = template.render(
            template_vars, bclogoUrl=bc_logo_url, registriesurl=registries_url
        )

            # Generate PDF with page numbering using shared helper
        html_rendered = HTML(string=html_out).render(
            optimize_size=("fonts", "images")
        )
        html_with_pages = populate_page_info(html_rendered)
        return html_with_pages.write_pdf()

    @staticmethod
    def _merge_and_finalize(ctx: "ChunkReportService.MergeContext") -> bytes:
        """Merge temp PDFs, optionally fix page numbers, log and return final bytes."""
        merged_pdf = ChunkReportService._merge_pdf_files(ctx.temp_files)

        if ctx.generate_page_number:
            merged_pdf = ChunkReportService._fix_page_numbers_by_regeneration(
                ctx.template_name, ctx.template_vars, merged_pdf
            )

        return merged_pdf
