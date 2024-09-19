from pdf_gen_api.models import Generator
from tests import run_tests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os


BOOLEAN_OBJ = {
    "courtApproval": {
                    "title": "Amalgamation statement",
                    "type": "boolean"
                }
}

SHORT_ENUM_OBJ = {
    "type": {
                "type": "string",
                "title": "The type of Amalgamation",
                "enum": [
                    "regular",
                    "vertical",
                    "horizontal"
                ]
            }
}

LONG_ENUM_OBJ = {
    "legalType": {
    "type": "string",
    "title": "The Legal Type of the business.",
    "default": "BC",
    "enum": [
            "A",
            "B",
            "BC",
            "BEN",
            "CBEN",
            "C",
            "CC",
            "CCC",
            "CEM",
            "CP",
            "CS",
            "CUL",
            "EPR",
            "FI",
            "FOR",
            "GP",
            "LIC",
            "LIB",
            "LL",
            "LLC",
            "LP",
            "MF",
            "PA",
            "PAR",
            "PFS",
            "QA",
            "QB",
            "QC",
            "QD",
            "QE",
            "REG",
            "RLY",
            "S",
            "SB",
            "SP",
            "T",
            "TMY",
            "ULC",
            "UQA",
            "UQB",
            "UQC",
            "UQD",
            "UQE",
            "XCP",
            "XL",
            "XP",
            "XS"
        ]
    }
}



def _create_file_path(test_name:str) -> str:
    """Helper - create file path allow duplication"""
    start_path = f"tests/test_generator/test_pdf_output/{test_name}"
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



def test_add_single_checkbox() -> None:
    pdf_canvas = _create_empty_canvas("test_single_checkbox")
    current_y = 700
    test_body = Generator("Test", {})
    test_body.add_single_checkbox(BOOLEAN_OBJ, pdf_canvas, current_y)
    pdf_canvas.save()



def test_create_from_enum_obj() -> None:
    pdf_canvas = _create_empty_canvas("test_create_from_enum_obj")
    current_y = 700
    test_body = Generator("Test", {})
    current_y = test_body.create_from_enum_obj(SHORT_ENUM_OBJ, pdf_canvas, current_y) # short --> radios group
    current_y = test_body.create_from_enum_obj(LONG_ENUM_OBJ, pdf_canvas, current_y) # long --> dropdown
    current_y = test_body.create_from_enum_obj(SHORT_ENUM_OBJ, pdf_canvas, current_y) # short --> radios group
    test_body.create_from_enum_obj(LONG_ENUM_OBJ, pdf_canvas, current_y) # long --> dropdown
    pdf_canvas.save()


def test_mixed_creation() -> None:
    """ Test rendering mixed components - same component multiple times + different types """
    pdf_canvas = _create_empty_canvas("test_mix_creation")
    current_y = 700
    test_body = Generator("Test", {})

    for i in range(3):
        current_y = test_body.add_single_checkbox(BOOLEAN_OBJ, pdf_canvas, current_y)
    for i in range(2):
        current_y = test_body.create_from_enum_obj(LONG_ENUM_OBJ, pdf_canvas, current_y)
    current_y = test_body.create_from_enum_obj(SHORT_ENUM_OBJ, pdf_canvas, current_y)
    current_y = test_body.create_from_enum_obj(LONG_ENUM_OBJ, pdf_canvas, current_y)
    test_body.add_single_checkbox(BOOLEAN_OBJ, pdf_canvas, current_y)
    pdf_canvas.save()


def main():
    func_list = [test_add_single_checkbox, test_create_from_enum_obj, test_mixed_creation]
    run_tests(func_list, "Render Components")

if __name__ == "__main__":
    main()
