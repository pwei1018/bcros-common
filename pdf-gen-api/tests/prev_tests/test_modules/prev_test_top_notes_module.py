from tests import run_tests
from pdf_gen_api.modules import add_top_notes
from pdf_gen_api.resources import _create_top_note_config

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os



LONG_CONTENT = _create_top_note_config(
    'DO NOT MAIL THIS FORM to BC Registry Services\nunless you are instructed to do so by registry staff.\nThe Regulation under the Business Corporations Act \nrequires the electronic version of this form to be filed \non the Internet at www.corporateonline.gov.bc.ca ',
    'Freedom of Information and Protection of Privacy Act (FOIPPA):\nPersonal information provided on this form is collected, used and \ndisclosed under the authority of the FOIPPA and the Business \nCorporations Act for the purposes of assessment. Questions regarding \nthe collection, use and disclosure of personal information can be \ndirected to the Manager of Registries Operations at 1 877 526-1526, \nPO Box 9431 Stn Prov Govt, Victoria BC V8W 9V3.'
)


SHORT_CONTENT = _create_top_note_config(
    'This is a SHORT Paragraph Test\nThis test demonstrates the capability of the program\nto handle paragraphs with various lengths',
    'This is the right side of the test.\nAlso for demonstrating the dynamic rendering capability\nfor the rectangle around the paragraph'
)


dummy_content = 'Dummy content gonna repeat multiple times for testing\n'*10
ULTRA_LONG_CONTENT = _create_top_note_config(
    f'This is a Ultra Long Paragraph Test\n{dummy_content}',
    f'This is the Right side of the Ultra Long Paragraph test:\n{dummy_content}'
)



def _create_file_path(test_name:str) -> str:
    """Helper - create file path allow duplication"""
    start_path = f"tests/test_modules/test_pdf_output/{test_name}"
    file_path  = f"{start_path}.pdf"
    exist_count = 1
    while os.path.exists(file_path):
        file_path = f"{start_path}_{exist_count}.pdf"
        exist_count += 1
    return file_path



def _create_empty_canvas(test_name:str) -> canvas.Canvas:
    """Helper - create an empty pdf canvas"""
    file_path = _create_file_path(test_name)
    empty_canvas = canvas.Canvas(file_path, pagesize=letter)
    return empty_canvas



def test_rendering_real_content():
    test_name = 'Top_note_long_content'
    print("Test Render Top Note with Real Content")
    try:
        test_canvas = _create_empty_canvas(test_name)
        add_top_notes(test_canvas, 720, LONG_CONTENT)
        test_canvas.save()
        print("Test Processed, please check the PDF output.")
    except Exception as e:
        print(f"Test failed, due to: {e}")



def test_render_short_content():
    test_name = 'Top_note_short_content'
    print("Test Render Top Note with Short Content")
    try:
        test_canvas = _create_empty_canvas(test_name)
        add_top_notes(test_canvas, 720, SHORT_CONTENT)
        test_canvas.save()
        print("Test Processed, please check the PDF output.")
    except Exception as e:
        print(f"Test failed, due to: {e}")



def test_render_ultra_long_content():
    test_name = 'Top_note_ultra_long_content'
    print("Test Render Top Note with Ultra Long Content")
    try:
        test_canvas = _create_empty_canvas(test_name)
        add_top_notes(test_canvas, 720, ULTRA_LONG_CONTENT)
        test_canvas.save()
        print("Test Processed, please check the PDF output.")
    except Exception as e:
        print(f"Test failed, due to: {e}")



def main():
    tests_list = [
        test_rendering_real_content,
        test_render_short_content,
        test_render_ultra_long_content
    ]
    run_tests(tests_list, "Top Note Module")


if __name__ == '__main__':
    main()
