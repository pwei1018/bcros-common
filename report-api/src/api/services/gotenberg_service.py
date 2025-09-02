"""Service for Gotenberg PDF generation operations."""
import asyncio
import gc
from typing import List, Tuple

import aiohttp
import requests
from flask import current_app


class GotenbergService:
    """Service for interacting with Gotenberg PDF generation service."""

    @staticmethod
    def _get_gotenberg_url() -> str:
        """Get the Gotenberg service URL from configuration."""
        return current_app.config.get('GOTENBERG_URL')

    @staticmethod
    async def _render_pdf_bytes_worker_gotenberg_with_session(args: Tuple[str, str], session: aiohttp.ClientSession) -> bytes:
        """Worker used to render HTML string to PDF bytes using Gotenberg with shared session."""
        html_out = args[0]
        gc.collect()
        gotenberg_url = GotenbergService._get_gotenberg_url()

        html_data = html_out.encode('utf-8')

        data = aiohttp.FormData()
        data.add_field('index.html', html_data, filename='index.html', content_type='text/html')

        async with session.post(
            f'{gotenberg_url}/forms/chromium/convert/html',
            data=data,
            timeout=aiohttp.ClientTimeout(total=500)
        ) as response:
            if response.status == 200:
                pdf_content = await response.read()
                gc.collect()
                return pdf_content
            error_text = await response.text()
            raise Exception(f"Gotenberg conversion failed with status {response.status}: {error_text}") # pylint: disable=broad-exception-raised

    @staticmethod
    async def render_tasks_parallel_async(
        tasks: List[Tuple[int, str]],
        base_url: str,
    ) -> List[bytes]:
        """Render HTML tasks in parallel using shared session for better performance."""
        results: List[Tuple[int, bytes]] = []

        async with aiohttp.ClientSession() as session:
            async_tasks = []
            order_ids = []
            for oid, html_out in tasks:
                task = GotenbergService._render_pdf_bytes_worker_gotenberg_with_session(
                    (html_out, base_url), session
                )
                async_tasks.append(task)
                order_ids.append(oid)

            pdf_contents = await asyncio.gather(*async_tasks)

            for oid, pdf_content in zip(order_ids, pdf_contents):
                results.append((oid, pdf_content))

        return [pdf for _, pdf in sorted(results, key=lambda x: x[0])]

    @staticmethod
    def convert_html_to_pdf_sync(html_content: str, timeout: int = 500) -> requests.Response:
        """Convert HTML content to PDF using Gotenberg synchronously."""
        gotenberg_url = GotenbergService._get_gotenberg_url()
        endpoint = f"{gotenberg_url}/forms/chromium/convert/html"

        files = [("files", ("index.html", html_content, "text/html"))]
        data = {}

        resp = requests.post(
            endpoint,
            files=files,
            data=data,
            timeout=timeout
        )
        resp.raise_for_status()
        return resp
