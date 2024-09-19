
from pdf_gen_api.models import Generator
from tests import run_tests
from pdf_gen_api.resources import PdfModule, GenerableItem
import os
import PyPDF2

def _create_file_path(test_name: str) -> str:
    """Helper function to create a unique file path for test output.

    Args:
        test_name (str): The base name for the test file

    Returns:
        str: A unique file path for the test output
    """
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    output_dir = os.path.join(PROJECT_ROOT, "demo_output")
    os.makedirs(output_dir, exist_ok=True)
    start_path = os.path.join(output_dir, test_name)
    file_path = f"{start_path}.pdf"
    exist_count = 1
    while os.path.exists(file_path):
        file_path = f"{start_path}_{exist_count}.pdf"
        exist_count += 1
    return file_path

def _check_file_exists(file_path):
    """Check if the file exists and print path info."""
    print(f"Checking for file: {file_path}")
    if os.path.exists(file_path):
        print(f"File found at: {file_path}")
        return True
    else:
        print(f"File not found at: {file_path}")
        return False

def _get_pdf_page_count(file_path):
    """Get the number of pages in a PDF file.

    Args:
        file_path (str): The path to the PDF file

    Returns:
        int: The number of pages in the PDF
    """
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        return len(pdf_reader.pages)

def test_single_page_pdf():
    """Test generation of a single-page PDF."""
    file_path = _create_file_path("test_single_page")
    props_dict = {
        "field1": {
            "type": "string",
            "pdfProps": {
                "label": "Test Field 1",
                "styles": {"length": 30}
            }
        },
        "field2": {
            "type": "string",
            "pdfProps": {
                "label": "Test Field 2",
                "styles": {"length": 60}
            }
        }
    }
    generator = Generator(
        file_path,
        props_dict,
        {PdfModule.HEADER, PdfModule.TOP_NOTE, PdfModule.CERTIFICATION},
        10.0,
        "Single-page Test Form",
        GenerableItem.REGULAR_AMALGAMATION_APPLICATION
    )
    generator.generate()
    assert _check_file_exists(file_path), f"PDF file not created or not found: {file_path}"
    assert _get_pdf_page_count(file_path) == 1, f"Expected 1 page, got {_get_pdf_page_count(file_path)}"

def test_multi_page_pdf():
    """Test generation of a multi-page PDF."""
    file_path = _create_file_path("test_multi_page")
    large_props_dict = {f"field{i}": {
        "type": "string",
        "pdfProps": {
            "label": f"Test Field {i}",
            "styles": {"length": 200}
        }
    } for i in range(50)}

    generator = Generator(
        file_path,
        large_props_dict,
        {PdfModule.HEADER, PdfModule.TOP_NOTE, PdfModule.CERTIFICATION},
        10.0,
        "Multi-page Test Form",
        GenerableItem.REGULAR_AMALGAMATION_APPLICATION
    )
    generator.generate()
    assert _check_file_exists(file_path), f"PDF file not created or not found: {file_path}"
    assert _get_pdf_page_count(file_path) > 1, f"Expected multiple pages, got {_get_pdf_page_count(file_path)}"

def main():
    func_list = [
        test_single_page_pdf,
        test_multi_page_pdf,
    ]
    run_tests(func_list, "Generator Tests")

if __name__ == "__main__":
    main()
