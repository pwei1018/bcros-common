from pdf_gen_api.models import Generator, JSONParser
from pdf_gen_api.resources import (
    GenerableItem,
    common_extra_modules,
    common_excluded_keys,
    default_render_order,
    default_footer_info,
    default_top_notes_content
)
from tests import run_tests
from pprint import pprint
import os, sys
from datetime import datetime


SCHEMAS_FOLDER = 'business_schemas'


def test_initialize_without_config():
    print("Test initializing the Generator without any configs")
    try:
        # mimicking Coordinator process (partially, without generate() call)
        test_parser = JSONParser(SCHEMAS_FOLDER)
        parsed_schema = test_parser.parse(GenerableItem.AGM_EXTENSION.value, common_excluded_keys)
        test_generator = Generator(GenerableItem.AGM_EXTENSION.value, {}, parsed_schema)
        if test_generator.form_title == GenerableItem.AGM_EXTENSION.value \
            and len(test_generator.extra_modules) == len(common_extra_modules) \
            and len(test_generator.top_note_info) == len(default_top_notes_content) \
            and len(test_generator.footer_info) == len(default_footer_info) \
            and len(test_generator.section_order) == len(default_render_order) \
            and len(test_generator.pdf_config) == 0 \
            and test_generator.component_configs == None:
            print("Test Passed")
            return
        print("Test Failed, mismatched results")
        print(f"{test_generator.form_title}\n{test_generator.extra_modules}\n{test_generator.top_note_info}\n{test_generator.footer_info}\n{test_generator.section_order}\n{test_generator.component_configs}")
    except Exception as e:
        print(f"Test Failed, Error Msg: {e}")



def test_get_props_data_agm_extension():
    print("Test the get_props_data method - AGM EXTENSION")
    try:
        # mimicking Coordinator process (partially, without generate() call)
        test_parser = JSONParser(SCHEMAS_FOLDER)
        parsed_schema = test_parser.parse(GenerableItem.AGM_EXTENSION.value, common_excluded_keys)
        test_generator = Generator(GenerableItem.AGM_EXTENSION.value, {}, parsed_schema)
        print("Test processed, please check the result")
        pprint(test_generator.props_dict)
    except Exception as e:
        print(f"Test Failed {e}")



def test_get_props_data_amalgamation_application():
    print("Test the get_props_data method - Amalgamation Application")
    try:
        # mimicking Coordinator process (partially, without generate() call)
        test_parser = JSONParser(SCHEMAS_FOLDER)
        parsed_schema = test_parser.parse(GenerableItem.REGULAR_AMALGAMATION_APPLICATION.value, common_excluded_keys)
        test_generator = Generator(GenerableItem.REGULAR_AMALGAMATION_APPLICATION.value, {}, parsed_schema)
        print("Test processed, please check the result")
        pprint(test_generator.props_dict)
    except Exception as e:
        print(f"Test Failed {e}")



def test_render_pdf_without_config_modified_agm():
    print("Test rendering a PDF without configs")
    try:
        # mimicking Coordinator process (partially, without generate() call)
        test_parser = JSONParser(SCHEMAS_FOLDER)
        parsed_schema = test_parser.parse(GenerableItem.AGM_EXTENSION.value, common_excluded_keys)
        test_generator = Generator(GenerableItem.AGM_EXTENSION.value, {}, parsed_schema)
        modified_props_dict = {
            "expireDateApprovedExt": {
                "description": "Expiration date for approved " "extension.",
                "examples": ["2023-10-10"],
                "format": "date",
                "type": "array",
                "test-enum-prop": {
                    "type": "string",
                    "enum": ["1", "2", "3"]
                },
                "test-text-prop":{
                    "type": "string"
                }
            },
            "expireDateCurrExt": {
                "description": "Date of expiration for current " "extension.",
                "examples": ["2023-10-10"],
                "format": "date",
                "type": "string",
            },
            "extReqForAgmYear": {
                "title": "Has an extension been requested for this AGM " "year?",
                "type": "boolean",
            },
            "extensionDuration": {
                "description": "Duration of extension approved for this "
                "request, measured in months.",
                "type": "integer",
            },
            "isFirstAgm": {"title": "Is this the first AGM?", "type": "boolean"},
            "prevAgmRefDate": {
                "description": "Point of reference from which companies "
                "have 15 months to either file an AGM or "
                "request an extension.",
                "examples": ["2023-10-10"],
                "format": "date",
                "type": "string",
            },
            "totalApprovedExt": {
                "description": "Total duration of extension approved, " "measured in months.",
                "type": "integer",
            },
            "type": "object",
            "year": {
                "description": "Year of AGM Extension Request, longest extension "
                "granted at one time is six months.",
                "type": "string",
            },
            "testOjb": {
                "type": ["string", "null"],
            },
            "testObjNested": {
                "type": "object",
                "objNested": {
                    "nestedText":{
                       "type": "string"
                    },
                    "nestedEnum": {
                        "enum": ["q", "w", "e"]
                    },
                    "type": 'object'
                }
            },
            "wildItems": {
                        "items": {"format": "date", "type": "string"},
                        "type": "array",
                    },
        }
        test_generator.props_dict = modified_props_dict
        test_generator.generate()
        print("PDF has been generated, please check in demo_output folder")
    except Exception as e:
        print(f"Test Failed, {e}")


def test_generate_pdf_without_configs_aa():
    print("Test rendering a PDF without configs - Amalgamation Application")
    try:
        # mimicking Coordinator process (partially, without generate() call)
        test_parser = JSONParser(SCHEMAS_FOLDER)
        parsed_schema = test_parser.parse(GenerableItem.REGULAR_AMALGAMATION_APPLICATION.value, common_excluded_keys)
        test_generator = Generator(GenerableItem.REGULAR_AMALGAMATION_APPLICATION.value, {}, parsed_schema)
        test_generator.generate()
        print("PDF has been generated, please check in demo_output folder")
    except Exception as e:
        print(f"Test Failed, {e}")


def main():
    output_dir = 'tests/test_generator'
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = f'{output_dir}/test_results_updated_generator_{timestamp}.txt'
    sys.stdout = open(output_file, 'w')
    
    test_list = [
        test_initialize_without_config,
        test_get_props_data_agm_extension,
        test_get_props_data_amalgamation_application,
        test_render_pdf_without_config_modified_agm,
        test_generate_pdf_without_configs_aa
    ]
    focus_list = [
        test_render_pdf_without_config_modified_agm,
        test_generate_pdf_without_configs_aa
    ]
    run_tests(focus_list, "Generator - V.0.3 - Focus")

    sys.stdout.close()


if __name__ == '__main__':
    main()
