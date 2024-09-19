from pdf_gen_api.models import Coordinator
from pdf_gen_api.resources import GenerableItem, PdfConfigOption
from tests import run_tests


def test_updated_select_config_no_configs():
    print("Test when there is no configs for the selected PDF")
    try:
        test_coordinator = Coordinator()
        test_result = test_coordinator._select_config(GenerableItem.AGM_EXTENSION)
        if len(test_result) == 0:
            print("Test Passed, wrong results")
            return
        print("Test Failed")
    except Exception as e:
        print(f"Test Failed, Error Msg: {e}")


def test_updated_select_config_has_config():
    print("Test when a config is available")
    try:
        test_coordinator = Coordinator()
        test_result = test_coordinator._select_config(GenerableItem.REGULAR_AMALGAMATION_APPLICATION)
        if (test_result[PdfConfigOption.FORM_TITLE] == 'AMALGAMATION APPLICATION') and (len(test_result) == 9):
            print("Test Passed")
            return
        print("Test Failed, wrong results")
    except Exception as e:
        print(f"Test Failed, Error Msg: {e}")




def main():
    test_list = [
        test_updated_select_config_no_configs,
        test_updated_select_config_has_config
    ]
    run_tests(test_list, "Updated select_config")


if __name__ == '__main__':
    main()
