from pdf_gen_api.models import Generator
from pdf_gen_api.resources import PdfModule, PdfConfigOption
from tests import run_tests



TEST_SECTIONS = [
    PdfModule.HEADER,
    PdfModule.TOP_NOTE,
    PdfModule.CERTIFICATION,
    PdfModule.EFFECTIVE_DATE
]

TEST_PROPS = {
    "test":{
        "prop1":{
            "type": "string"
        },
        "prop2":{
            "type": "string"
        },
        "prop3":{
            "type": "string"
        },
        "prop4":{
            "type": "string"
        },
        "prop5":{
            "type": "string"
        },
        "prop6":{
            "type": "string"
        },
        "prop7":{
            "type": "string"
        },
        "prop8":{
            "type": "string"
        }
    }
}



def test_title():
    test_body = Generator("test", {PdfConfigOption.NUM_OF_CERTIFICATION: 5}, TEST_PROPS)
    test_body.section_order = TEST_SECTIONS
    test_body.generate()



def main():
    test_list = [
        test_title
    ]
    run_tests(test_list, "Certification Module Rendering")


if __name__ == '__main__':
    main()
