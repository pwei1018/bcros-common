from pdf_gen_api.models import Generator
from pdf_gen_api.resources import PdfModule, START_Y
from tests import run_tests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os


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


def test_single_page_certification():
    """Tests the generation of a single-page certification section."""
    file_path = _create_file_path("test_single_page_certification")
    pdf_canvas = canvas.Canvas(file_path, pagesize=letter)
    
    # configuration for the certification section
    config = {
        'certification_info': {
            'title': 'Single-Page Certification',
            'description': 'I have read this form and found it to be correct.',
            'note': 'This form must be signed by an authorized signing authority for each of the amalgamating companies as set out in Item E.',
            'fields': ['NAME', 'SIGNATURE', 'DATE'],
            'date_format': 'YYYY/MM/DD'
        }
    }
    
    # initialize the Generator with certification module
    generator = Generator(file_path, {}, extra_modules={PdfModule.CERTIFICATION})
    generator.pdf_canvas = pdf_canvas
    generator.current_y = START_Y
    
    generator.add_certification_section(config=config, num_of_items=3)
    
    pdf_canvas.save()
    
    assert os.path.exists(file_path), f"PDF file not created or not found: {file_path}"


def test_multi_page_certification():
    """Tests the generation of a multi-page certification section."""
    file_path = _create_file_path("test_multi_page_certification")
    pdf_canvas = canvas.Canvas(file_path, pagesize=letter)
    
    # configuration for the certification section
    config = {
        'certification_info': {
            'title': 'Multi-page Certification',
            'description': 'I have read this form and found it to be correct.',
            'note': 'This form must be signed by an authorized signing authority for each of the amalgamating companies as set out in Item E.',
            'fields': ['NAME', 'SIGNATURE', 'DATE'],
            'date_format': 'YYYY/MM/DD'
        }
    }
    
    generator = Generator(file_path, {}, extra_modules={PdfModule.CERTIFICATION})
    generator.pdf_canvas = pdf_canvas
    generator.current_y = START_Y
    generator.page_height = 792
    
    # Override _start_new_page method for testing purposes
    # This simplifies the page transition by just resetting the Y position
    generator._start_new_page = lambda: setattr(generator, 'current_y', START_Y)
    
    generator.add_certification_section(config=config, num_of_items=100)
    
    pdf_canvas.save()
    
    assert os.path.exists(file_path), f"PDF file not created or not found: {file_path}"


def main():
    func_list = [
        test_single_page_certification,
        test_multi_page_certification,
    ]
    run_tests(func_list, "Certification Section Tests")


if __name__ == "__main__":
    main()
