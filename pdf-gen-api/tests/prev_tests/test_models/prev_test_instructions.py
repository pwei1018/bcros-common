from pdf_gen_api.models import Generator, JSONParser
from pdf_gen_api.resources import (
    GenerableItem,
    common_excluded_keys,
)
from tests import run_tests
import os


SCHEMAS_FOLDER = 'business_schemas'

def test_render_pdf_without_config_modified_agm():
    print("Test rendering a PDF without configs - AGM Extension")
 
    # Mimicking Coordinator process (partially, without generate() call)
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
                    }
                }
            }
        }
    test_generator.props_dict = modified_props_dict
    test_generator.generate()
    # Use the actual file path from the generator
    actual_pdf_path = test_generator._generate_file_path()
    
    # Verify the file exists
    if os.path.exists(actual_pdf_path):
        print(f"PDF successfully generated at: {actual_pdf_path}")
        print(f"File size: {os.path.getsize(actual_pdf_path)} bytes")
    else:
        print(f"Failed to generate PDF. File not found at: {actual_pdf_path}")


def test_generate_pdf_without_configs_aa():
    print("Test rendering a PDF without configs - Amalgamation Application")
        
    # Mimicking Coordinator process (partially, without generate() call)
    test_parser = JSONParser(SCHEMAS_FOLDER)
    parsed_schema = test_parser.parse(GenerableItem.REGULAR_AMALGAMATION_APPLICATION.value, common_excluded_keys)
    test_generator = Generator(GenerableItem.REGULAR_AMALGAMATION_APPLICATION.value, {}, parsed_schema)
    test_generator.generate()
    
    # Use the actual file path from the generator
    actual_pdf_path = test_generator._generate_file_path()
    
    # Verify the file exists
    if os.path.exists(actual_pdf_path):
        print(f"PDF successfully generated at: {actual_pdf_path}")
        print(f"File size: {os.path.getsize(actual_pdf_path)} bytes")
    else:
        print(f"Failed to generate PDF. File not found at: {actual_pdf_path}")


def main():
    test_list = [
        test_render_pdf_without_config_modified_agm,
        test_generate_pdf_without_configs_aa
    ]
    run_tests(test_list, "Instructions")



if __name__ == '__main__':
    main()
