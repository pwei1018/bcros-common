from src.pdf_gen_api.resources.utils import GenerableItem
from tests import run_tests
import os


SCHEMA_FOLDER = 'business_schemas'



def test_correct_file_names():
    print("Validate all file names added to GenerableItem")
    schema_file_list = os.listdir(SCHEMA_FOLDER)
    for option in GenerableItem:
        file_path = f"{option.value}.json"
        if not (file_path in schema_file_list):
            print("Test Failed")
            return
    print("Test Passed")



def main():
    test_list = [
        test_correct_file_names
    ]
    run_tests(test_list, "Generable Items")



if __name__ == '__main__':
    main()
