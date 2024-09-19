import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf_gen_api.models import Generator
from pdf_gen_api.resources import PdfModule
from pdf_gen_api.modules import add_effective_date_section
from tests import run_tests


def _create_file_path(test_name: str) -> str:
    """
    Creates a unique file path for the output PDF.

    Args:
        test_name (str): Name of the test, used as part of the file name.

    Returns:
        str: A unique file path for the PDF output.
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


def test_effective_date_section():
    """Tests the generation of the effective date section."""
    file_path = _create_file_path("test_effective_date_section")
    pdf_canvas = canvas.Canvas(file_path, pagesize=letter)

    start_y = 700

    add_effective_date_section(pdf_canvas, start_y, "amalgamation")

    pdf_canvas.save()

    assert os.path.exists(file_path), f"PDF file not created or not found: {file_path}"

    print(f"Effective Date Section PDF created: {file_path}")

    file_size = os.path.getsize(file_path)
    assert file_size > 0, "PDF file is empty"


def test_effective_date_in_generator():
    """Tests the inclusion of the effective date section in the full PDF generation process."""
    file_path = _create_file_path("test_effective_date_in_generator")
    
    generator = Generator(file_path, {}, extra_modules={PdfModule.EFFECTIVE_DATE, PdfModule.HEADER}, 
                          form_title="Amalgamation Application")
    
    generator.generate()

    assert os.path.exists(file_path), f"PDF file not created or not found: {file_path}"

    print(f"Full PDF with Effective Date Section created: {file_path}")

    file_size = os.path.getsize(file_path)
    assert file_size > 0, "PDF file is empty"


def main():
    func_list = [
        test_effective_date_section,
        test_effective_date_in_generator,
    ]
    run_tests(func_list, "Effective Date Section Tests")


if __name__ == "__main__":
    main()
