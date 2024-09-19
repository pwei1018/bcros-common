# Testing schema parsing feature as expected

from tests import run_tests
from pdf_gen_api.models import JSONParser
from pprint import pprint
import sys


SCHEMAS_FOLDER_PATH = 'business_schemas' #if running from root directory
EXCLUDED_KEYS = [ 
            '$schema',
            '$id',
            'dependencies',
            'definitions',
            'required',
            'if'
        ]



def test_schemas_loading():
    print("Test loading schemas")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    if len(json_parser.registry) == 48:
        print("Test Passed. All schemas loaded")
        print("Local path library:")
        pprint(json_parser.local_path_lib)
    else:
        print("Test Failed")
        print(f"Actual: {len(json_parser.registry)}")



def test_get_json():
    print("Test load a json file and return a Python Dictionary")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    test_res = json_parser._get_json('business_schemas/agm_location_change.json')
    if test_res['$id'] == 'https://bcrs.gov.bc.ca/.well_known/schemas/agm_location_change':
        print("Test Passed.")
    else:
        print("Test Failed.")
        print(f"Actual: {test_res['$id']}")



def test_get_schema_id_path():
    print("Test parse a $ref link and return a Tuple: (schema_id, property_address)")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    is_test_passed = True
    
    test_ref_1 = 'https://bcrs.gov.bc.ca/.well_known/schemas/name_request'
    part1_res = json_parser._get_schema_id_path(test_ref_1)
    if part1_res[0] == 'https://bcrs.gov.bc.ca/.well_known/schemas/name_request' and part1_res[1] == '':
        print("Part 1 Passed")
    else:
        is_test_passed = False
        print("Part 1 Failed")

    test_ref_2 = '#/definitions/nrNumber'
    part2_res = json_parser._get_schema_id_path(test_ref_2)
    if part2_res[0] == '' and part2_res[1] == '/definitions/nrNumber':
        print("Part 2 Passed")
    else:
        is_test_passed = False
        print("Part 2 Failed")

    test_ref_3 = 'https://bcrs.gov.bc.ca/.well_known/schemas/business#/definitions/legalType'
    part3_res = json_parser._get_schema_id_path(test_ref_3)
    if part3_res[0] == 'https://bcrs.gov.bc.ca/.well_known/schemas/business' and part3_res[1] == '/definitions/legalType':
        print("Part 3 Passed")
    else:
        is_test_passed = False
        print("Part 3 Failed")
    
    if is_test_passed:
        print("Test Passed")
    else:
        print("Test Failed")



def test_resolve_references():
    print("Test resolve $ref(s)")
    print("This test's results need to be eye-balled")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    schema_dict = json_parser._get_json('business_schemas/office.json')
    print("The original version:")
    pprint(schema_dict)
    print("-" * 100)
    resolved_schema = json_parser._resolve_references(schema_dict)
    print("-" * 100)
    print("Resolved version:")
    pprint(resolved_schema)



def test_flatten_resolved_schemas():
    print("Test flatten resolved schemas")
    print("This test's results need to be eye-balled")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    schema_dict = json_parser._get_json('business_schemas/office.json')
    resolved_schema = json_parser._resolve_references(schema_dict)
    print("The resolved version:")
    pprint(resolved_schema)
    print("-"*100)
    print("Flattened version:")
    flattened_schema = json_parser._flatten_schema(resolved_schema)
    pprint(flattened_schema)



def test_clean_schema():
    print("Test the functionality of removing unnecessary items from schemas")
    is_cleaned = True
    def check_schema(schema):
        if isinstance(schema, dict):
            for key in schema.keys():
                if key in EXCLUDED_KEYS:
                    is_cleaned = False
                    return
            for value in schema.values():
                check_schema(value)
    
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    json_parser.excluded_keys = EXCLUDED_KEYS
    schema_dict = json_parser._get_json('business_schemas/office.json')
    resolved_schema = json_parser._resolve_references(schema_dict)
    flattened_schema = json_parser._flatten_schema(resolved_schema)
    cleaned_schema = json_parser._clean_schema(flattened_schema)
    
    check_schema(cleaned_schema)
    if is_cleaned:
        print("Test Passed.")
    else:
        print("Test Failed")
    pprint(cleaned_schema)



def test_parse():
    print("The main parsing functionality")
    print("This test's results need to be eye-balled")
    print("Some known issues are documented, like there will be 2 item not cleaned up")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    full_path = 'business_schemas/name_request.json'
    main_schema_file_name = 'name_request'
    original_version = json_parser._get_json(full_path)
    print("Original version:")
    pprint(original_version)
    print("-" * 100)
    parsed_version = json_parser.parse(main_schema_file_name, EXCLUDED_KEYS)
    print("Parsed version:")
    pprint(parsed_version)



def test_parse_nested_ref_in_schema():
    print("Test parsing Amalgamation Application Schema (nested)")
    print("This test's results need to be eye-balled")
    json_parser = JSONParser(SCHEMAS_FOLDER_PATH)
    full_path = 'business_schemas/amalgamation_application.json'
    main_schema_file_name = 'amalgamation_application'
    original_version = json_parser._get_json(full_path)
    print("Original version:")
    pprint(original_version)
    print("-" * 100)
    parsed_version = json_parser.parse(main_schema_file_name, EXCLUDED_KEYS)
    print("Parsed version:")
    pprint(parsed_version) 



def main():
    sys.stdout = open('tests/test_json_parser/test_results.txt', 'w')
    tests_list = [
        test_schemas_loading, 
        test_get_json, 
        test_get_schema_id_path, 
        test_resolve_references,
        test_flatten_resolved_schemas,
        test_clean_schema,
        test_parse,
        test_parse_nested_ref_in_schema
    ]
    run_tests(tests_list, "Parsing Business Schemas")
    sys.stdout.close()



if __name__ == '__main__':
    main()
