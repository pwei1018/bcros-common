"""Shared helpers for populating page numbers in WeasyPrint documents, get rid of the cyclic dependency."""

from weasyprint.formatting_structure.boxes import InlineBox


def populate_page_info(document):
    """Iterate through pages and populate page number info."""
    total_pages = len(document.pages)
    count = 1
    for page in document.pages:
        populate_page_count(page._page_box, count, total_pages)  # pylint: disable=protected-access
        count += 1
    return document


def populate_page_count(box, count, total):
    """Populate page info under pageinfo tag for a single box tree."""
    if getattr(box, 'element_tag', None):
        if box.element_tag == 'pageinfo':
            page_info_text = f'Page {count} of {total}'
            if isinstance(box, InlineBox):
                box.children[0].text = page_info_text
                # pango_layout may not exist in some cases; guard access
                if hasattr(box.children[0], 'pango_layout'):
                    box.children[0].pango_layout.text = page_info_text
            box.text = page_info_text
    if hasattr(box, 'all_children') and box.all_children():
        for child in box.children:
            populate_page_count(child, count, total)


def populate_page_info_with_offset(document, start_index: int, total_pages: int):
    """Populate page numbers starting from a given index (1-based)."""
    count = max(1, int(start_index))
    for page in document.pages:
        populate_page_count(page._page_box, count, total_pages)  # pylint: disable=protected-access
        count += 1
    return document
