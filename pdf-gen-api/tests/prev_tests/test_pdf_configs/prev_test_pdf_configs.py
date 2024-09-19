from tests import run_tests
from pdf_gen_api.resources import _create_top_note_config, _create_component_config, PdfFontSize, PdfFontStyle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter



def test_create_top_note_config():
    print("Test create_top_note_config")
    test_left = 'this is left'
    test_right = 'this is right'
    res = _create_top_note_config(test_left, test_right)
    if isinstance(res, dict):
        if res['left_column'][0] == 'this is left' and res['right_column'][0] == 'this is right':
            print("Test Passed")
            return
    print("Test Faild")



def test_rendering_paragraphs():
    print("Test rendering paragraphs")
    print("Please check test results in tests/test_pdf_configs/test_paragram_render.pdf")
    try:
        new_canv = canvas.Canvas('tests/test_pdf_configs/test_paragram_render.pdf', pagesize=letter)
        test_config = _create_top_note_config('DO NOT MAIL THIS FORM to BC Registry Services\nunless you are instructed to do so by registry staff.\nThe Regulation under the Business Corporations Act \nrequires the electronic version of this form to be filed \non the Internet at www.corporateonline.gov.bc.ca ', 'Freedom of Information and Protection of Privacy Act (FOIPPA):\nPersonal information provided on this form is collected, used and \ndisclosed under the authority of the FOIPPA and the Business \nCorporations Act for the purposes of assessment. Questions regarding \nthe collection, use and disclosure of personal information can be \ndirected to the Manager of Registries Operations at 1 877 526-1526, \nPO Box 9431 Stn Prov Govt, Victoria BC V8W 9V3.')
        current_y = 740
        new_canv.drawString(10, current_y, 'This is the left column content')
        current_y -= 20
        for item in test_config['left_column']:
            new_canv.drawString(10, current_y, item)
            current_y -= 15
        current_y -= 10
        new_canv.drawString(10, current_y, 'This is the right column content')
        current_y -= 20
        for item in test_config['right_column']:
            new_canv.drawString(10, current_y, item)
            current_y -= 15
        new_canv.save()
        print("Test Passed")
    except Exception as e:
        print(f"Test Failed {e}")



def test_create_component_config():
    print("Test create component config helper function")
    label_name = 'Test_Label'
    test_font_size = PdfFontSize.CONTENT
    test_font_style = PdfFontStyle.ITALIC
    test_length = 400
    test_reps = 10
    test_config = _create_component_config(label_name, test_font_size, test_font_style, test_length, test_reps)
    if(
        test_config['label'] == label_name
        and test_config['styles']['length'] == test_length
        and test_config['styles']['font_size'] == test_font_size
        and test_config['styles']['font_style'] == test_font_style
        and test_config['reps'] == test_reps
    ):
        print("Test Passed")
    else:
        print("Test Failed")



def test_create_component_config_default_value():
    print("Test create component config helper function with default value")
    label_name = 'Test_default'
    default_font_size = PdfFontSize.CONTENT
    default_font_style = PdfFontStyle.REGULAR
    default_length = None
    default_reps = 1
    test_config = _create_component_config(label_name)
    if(
        test_config['label'] == label_name
        and test_config['styles']['length'] == default_length
        and test_config['styles']['font_size'] == default_font_size
        and test_config['styles']['font_style'] == default_font_style
        and test_config['reps'] == default_reps
    ):
        print("Test Passed")
    else:
        print("Test Failed")



def test_create_component_config_only_length():
    print("Test create component config helper function with only length value (as options)")
    label_name = 'Test_length'
    default_font_size = PdfFontSize.CONTENT
    default_font_style = PdfFontStyle.REGULAR
    test_length = 200
    default_reps = 1
    test_config = _create_component_config(label_name, length=test_length)
    if(
        test_config['label'] == label_name
        and test_config['styles']['length'] == test_length
        and test_config['styles']['font_size'] == default_font_size
        and test_config['styles']['font_style'] == default_font_style
        and test_config['reps'] == default_reps
    ):
        print("Test Passed")
    else:
        print("Test Failed")




def main():
    tests_list = [
        test_create_top_note_config,
        test_rendering_paragraphs,
        test_create_component_config,
        test_create_component_config_default_value,
        test_create_component_config_only_length
    ]
    run_tests(tests_list, "PDF Configs")




if __name__ == '__main__':
    main()
