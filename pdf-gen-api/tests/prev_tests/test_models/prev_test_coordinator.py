import sys
import os
from datetime import datetime
from tests import run_tests
from pdf_gen_api.models import Coordinator, JSONParser
from pdf_gen_api.resources import GenerableItem, PdfConfigOption
from pprint import pprint


def test_pass_invalid_pdf_name():
    """Test when passing an invalid pdf name"""
    print("Test Passing Invalid Pdf Name")
    coordinator = Coordinator()
    try:
        coordinator._select_config("test_pdf")
        print("Test Failed")
    except TypeError as e:
        print(f'Test passed, caught error: {e}')


def test_pass_valid_pdf_name():
    """Test when passing a valid pdf name"""
    print("Test Passing valid Pdf Name")
    coordinator = Coordinator()
    try:
        coordinator._select_config(GenerableItem.AGM_LOCATION_CHANGE)
        print("Test Passed")
    except:
        print("Test Failed")


def test_pass_valid_pdf_name_regular_amalgamation():
    """Test when passing a valid pdf name"""
    print("Test Passing valid Pdf Name")
    coordinator = Coordinator()
    try:
        config = coordinator._select_config(GenerableItem.REGULAR_AMALGAMATION_APPLICATION)
        print("Test Passed")
        print("Selected Config:")
        pprint(config)
    except:
        print("Test Failed")


def test_coordinator_init():
    """Test Coordinator initialization"""
    print("Test Coordinator Initialization")
    coordinator = Coordinator()
    print(f"schemas_folder: {coordinator.schemas_folder}")
    if coordinator.schemas_folder == 'business_schemas':
        print("Test Passed")
    else:
        print("Test Failed")


def test_run_app():
    """Test run_app method"""
    print("Test run_app method")
    coordinator = Coordinator()

    try:
        config = coordinator._select_config(GenerableItem.REGULAR_AMALGAMATION_APPLICATION)
        print("Selected Config:")
        pprint(config)

        main_schema_file_name = config[PdfConfigOption.USED_SCHEMAS] ## need to refactor this later when updating tests, not having this anymore
        excluded_keys = config.get(PdfConfigOption.EXCLUDED_KEYS, [])

        json_parser = JSONParser(coordinator.schemas_folder)
        props_dict = json_parser.parse(main_schema_file_name, excluded_keys)

        print("\nParsed props_dict:")
        pprint(props_dict)

        if props_dict is not None:
            print("Test Passed: Successfully retrieved config and parsed props_dict")
        else:
            print("Test Failed: props_dict is None")

    except Exception as e:
        print(f"Test Failed. An exception occurred: {e}")


def main():
    output_dir = 'tests/test_coordinator'
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = f'{output_dir}/test_results_{timestamp}.txt'
    sys.stdout = open(output_file, 'w')

    print(f"Test run started at: {datetime.now()}")
    print("=" * 50)
    
    func_list = [
        test_pass_invalid_pdf_name,
        test_pass_valid_pdf_name,
        test_coordinator_init,
        test_run_app
    ]
    run_tests(func_list, "Coordinator Tests")

    print("=" * 50)
    print(f"Test run completed at: {datetime.now()}")

    sys.stdout.close()
    sys.stdout = sys.__stdout__

    print(f"Test results have been written to: {output_file}")

if __name__ == '__main__':
    main()
