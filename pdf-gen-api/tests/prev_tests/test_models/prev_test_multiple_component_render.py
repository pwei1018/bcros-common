from pdf_gen_api.models import Generator
from tests import run_tests
from enum import Enum


class DataType(Enum):
    STRING = "string"
    BOOLEAN = "boolean"
    ENUM = "enum"
    OBJECT = "object"
    ARRAY = "array"



def _create_dummy_props_dict(data_type:DataType, reps:int, is_dropdown:bool=False):
    primary_key = f"dummyData{data_type.value.capitalize()}"
    dummy_data = {primary_key: {}}
    if data_type != DataType.ENUM:
        for i in range(reps):
            dummy_data[primary_key][f"Dummy-{data_type.value}-{i+1}"] = {
                "type": f"{data_type.value}"
            }
    else:
        if is_dropdown:
            option_list = [f"option {i+1}" for i in range(20)]
        else:
            option_list = [f"option {i+1}" for i in range(3)]
        for i in range(reps):
            dummy_data[primary_key][f"Dummy-{data_type.value}-{i+1}"] = {
                "type": "string",
                "enum": option_list
            }
    return dummy_data



def _test_render_multiple_component(data_type:DataType, component_type:str, reps:int=20, is_dropdown:bool=False):
    print(f"Test render multiple {component_type}")
    try:
        file_name = f"dummy_data_{data_type.value}"
        dummy_data = _create_dummy_props_dict(data_type, reps, is_dropdown)
        generator = Generator(file_name, {}, dummy_data)
        generator.generate()
    except Exception as e:
        print(f"Test Failed, {e}")


def test_multiple_textfield():
    _test_render_multiple_component(DataType.STRING, "textfield")

def test_multiple_text():
    _test_render_multiple_component(DataType.OBJECT, "text", 80)

def test_multiple_checkbox():
    _test_render_multiple_component(DataType.BOOLEAN, "checkbox")

def test_radio_group():
    _test_render_multiple_component(DataType.ENUM, "radio group")

def test_dropdown():
    _test_render_multiple_component(DataType.ENUM, "dropdown", is_dropdown=True)


def main():
    test_list = [
        test_multiple_textfield,
        test_multiple_text,
        test_multiple_checkbox,
        test_radio_group,
        test_dropdown
    ]
    run_tests(test_list, "Render Multiple Components")


if __name__ == '__main__':
    main()
