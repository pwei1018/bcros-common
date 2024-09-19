from pdf_gen_api.models import Generator
from pdf_gen_api.resources import GenerableItem
from tests import run_tests



SCHEMAS_FOLDER = 'business_schemas'

def test_convert_to_title_case_agm():
    print("Test Convert AGM related string to Title Case")
    test_generator = Generator(GenerableItem.AGM_EXTENSION.value, {}, {"agmExtension": {}})
    test_case = 'agmLocationChange'
    result = test_generator._convert_to_title_case(test_case)
    if result == 'AGM Location Change':
        print("Test Passed")
    else:
        print("Test Failed")
        print(result)


def test_convert_to_title_case_normal():
    print("Test Convert Normal string to Title Case")
    test_generator = Generator(GenerableItem.AGM_EXTENSION.value, {}, {"agmExtension": {}})
    test_case = 'legalName'
    result = test_generator._convert_to_title_case(test_case)
    if result == 'Legal Name':
        print("Test Passed")
    else:
        print("Test Failed")
        print(result)


def test_convert_to_title_case_nr():
    print("Test Convert NR to Title Case")
    test_generator = Generator(GenerableItem.AGM_EXTENSION.value, {}, {"agmExtension": {}})
    test_case = 'nrNumber'
    result = test_generator._convert_to_title_case(test_case)
    if result == 'NR Number':
        print("Test Passed")
    else:
        print("Test Failed")
        print(result)


def main():
    test_list = [
        test_convert_to_title_case_agm,
        test_convert_to_title_case_normal,
        test_convert_to_title_case_nr
    ]
    run_tests(test_list, "Convert to Title Case")


if __name__ == '__main__':
    main()
