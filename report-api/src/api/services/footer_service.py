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
"""Shared helpers for rendering footer in PDF documents."""

import asyncio
import io
from io import BytesIO
from typing import Any, Dict, List, Tuple

import pikepdf
from flask import current_app
from jinja2 import Environment, FileSystemLoader

from api.services.gotenberg_service import GotenbergService
from api.utils.util import TEMPLATE_FOLDER_PATH

_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader('.'), autoescape=True
)


def get_pdf_page_count(pdf_content: bytes) -> int:
    """Extract total page count from PDF content."""
    try:
        with pikepdf.Pdf.open(BytesIO(pdf_content)) as pdf:
            return len(pdf.pages)
    except Exception as e:  # noqa: B902 pylint: disable=broad-exception-caught
        current_app.logger.warning(f'Failed to get PDF page count: {e}')
        return 1


def add_page_numbers_to_pdf(
    template_vars: Dict[str, Any],
    merged_pdf_without_footers: bytes,
    generate_page_number: bool
) -> bytes:
    """Add page numbers to PDF using footer generation logic."""
    template_vars['generate_page_number'] = generate_page_number
    total_pages = get_pdf_page_count(merged_pdf_without_footers)

    if total_pages > 500:
        return _add_footer_to_first_page_only(template_vars, merged_pdf_without_footers, total_pages)

    batch_tasks = _prepare_footer_batch_tasks(
        template_vars, total_pages, batch_size=200
    )
    footer_multi_page_pdfs = asyncio.run(
        GotenbergService.render_tasks_parallel_async(
            batch_tasks, current_app.root_path
        )
    )
    footer_pdfs: List[bytes] = []
    for pdf in footer_multi_page_pdfs:
        footer_pdfs.extend(_split_pdf_pages(pdf))

    result = _overlay_footer_pdfs_on_main_pdf(
        merged_pdf_without_footers, footer_pdfs
    )

    return result


def _add_footer_to_first_page_only(template_vars: Dict[str, Any], main_pdf_bytes: bytes, total_pages: int) -> bytes:
    """Add footer only to the first page for large documents."""
    batch_tasks = _prepare_footer_batch_tasks(template_vars, total_pages, batch_size=1, first_page_only=True)

    footer_multi_page_pdfs = asyncio.run(
        GotenbergService.render_tasks_parallel_async(
            batch_tasks, current_app.root_path
        )
    )

    if not footer_multi_page_pdfs:
        return main_pdf_bytes

    first_page_footer = _split_pdf_pages(footer_multi_page_pdfs[0])[0]

    footer_pdfs = [first_page_footer]

    return _overlay_footer_pdfs_on_main_pdf(main_pdf_bytes, footer_pdfs)


def _prepare_footer_batch_tasks(
    template_args: dict,
    total_pages: int,
    batch_size: int = 200,
    first_page_only: bool = False
) -> List[Tuple[int, str]]:
    """Prepare footer batch tasks."""
    footer_template = _TEMPLATE_ENV.get_template(
        f'{TEMPLATE_FOLDER_PATH}/generic_footer.html'
    )
    overlay_style = _TEMPLATE_ENV.get_template(
        f'{TEMPLATE_FOLDER_PATH}/styles/footer_overlay.html'
    ).render()

    tasks: List[Tuple[int, str]] = []
    batch_id = 0
    total_pages_to_process = 1 if first_page_only else total_pages
    for batch_start in range(1, total_pages_to_process + 1, batch_size):
        batch_end = min(batch_start + batch_size, total_pages_to_process + 1)

        batch_html_parts = ['<!DOCTYPE html><html><head>']

        batch_html_parts.append(overlay_style)
        batch_html_parts.append('</head><body>')

        for page_num in range(batch_start, batch_end):
            page_args = template_args.copy()
            page_args['current_page'] = page_num
            page_args['total_pages'] = total_pages

            batch_html_parts.append(
                f'<div class="footer-page" id="footer-page-{page_num}">'
                f'<div class="footer-anchor">{footer_template.render(page_args)}</div></div>'
            )

        batch_html_parts.append('</body></html>')
        batch_html = ''.join(batch_html_parts)

        tasks.append((batch_id, batch_html))
        batch_id += 1

    return tasks


def _split_pdf_pages(pdf_bytes: bytes) -> List[bytes]:
    """Split a multi-page PDF into individual page PDFs."""
    individual_pdfs = []

    try:
        with pikepdf.Pdf.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                single_page_pdf = pikepdf.Pdf.new()
                single_page_pdf.pages.append(page)

                output_buffer = io.BytesIO()
                single_page_pdf.save(output_buffer)
                individual_pdfs.append(output_buffer.getvalue())

    except Exception as e:  # noqa: B902
        current_app.logger.error(f'Error splitting PDF pages: {e}')
        raise

    return individual_pdfs


def _overlay_footer_pdfs_on_main_pdf(
    main_pdf_bytes: bytes, footer_pdfs: list
) -> bytes:
    """Overlay footer PDFs onto each page of the main PDF."""
    try:
        with pikepdf.Pdf.open(io.BytesIO(main_pdf_bytes)) as main_pdf:
            result_pdf = pikepdf.Pdf.new()

            for i, main_page in enumerate(main_pdf.pages):
                result_pdf.pages.append(main_page)
                new_page = result_pdf.pages[-1]  # Get the newly added page

                has_footer_pdf = i < len(footer_pdfs)
                if has_footer_pdf:
                    with pikepdf.Pdf.open(io.BytesIO(footer_pdfs[i])) as footer_pdf:
                        if len(footer_pdf.pages) > 0:
                            footer_page = footer_pdf.pages[0]
                            page_width, band_height = _prepare_footer_page_for_overlay(footer_page, new_page)
                            _overlay_page_content(new_page, footer_page, page_width=page_width, band_height=band_height)

            output_buffer = io.BytesIO()
            result_pdf.save(output_buffer)
            return output_buffer.getvalue()

    except Exception as e:  # noqa: B902 pylint: disable=broad-exception-caught
        current_app.logger.error(f'Error overlaying footer PDFs: {e}')
        return main_pdf_bytes


def _prepare_footer_page_for_overlay(footer_page, base_page) -> tuple:
    """Set footer page CropBox to bottom band; return (page_width, band_height)."""
    media_box = getattr(base_page, 'MediaBox', None)
    page_width = float(media_box[2]) if media_box and len(media_box) >= 3 else 612.0  # Letter width (8.5in × 72pt)
    page_height = float(media_box[3]) if media_box and len(media_box) >= 4 else 792.0  # Letter height (11in × 72pt)
    band_height = 90.0  # footer band; spacious for logo + page number; adjustable
    footer_page.MediaBox = pikepdf.Array([0, 0, page_width, page_height])
    footer_page.CropBox = pikepdf.Array([0, 0, page_width, band_height])
    return page_width, band_height


def _overlay_page_content(base_page, overlay_page, page_width: float, band_height: float):
    """Overlay content from overlay_page onto base_page using pikepdf."""
    try:
        if hasattr(base_page, 'add_overlay'):
            rect = pikepdf.Rectangle(0, 0, page_width, band_height)
            base_page.add_overlay(overlay_page, rect=rect)
            return
    except Exception as e:  # noqa: B902 pylint: disable=broad-exception-caught
        current_app.logger.warning(f'Could not overlay page content: {e}')
