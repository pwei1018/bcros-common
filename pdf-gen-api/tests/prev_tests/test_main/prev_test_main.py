import io
import sys
from pdf_gen_api.resources import GenerableItem
from pdf_gen_api.main import show_menu, get_user_selection, main as main_function


class MockGenerator:
    """Mock classes for testing"""
    def __init__(self):
        self.generate_called = False
        self.pdf_selection = None

    def generate(self, pdf_selection):
        self.generate_called = True
        self.pdf_selection = pdf_selection


class MockCoordinator:
    """Mock classes for testing"""
    last_instance = None

    def __init__(self):
        self.generator = MockGenerator()
        MockCoordinator.last_instance = self

    def run_app(self, pdf_selection):
        self.generator.generate(pdf_selection)


def get_console_output(func, *args):
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = func(*args)
        output = sys.stdout.getvalue()
        return result, output
    finally:
        sys.stdout = old_stdout


def test_show_menu():
    _, output = get_console_output(show_menu)
    
    # Check version number
    assert "PDF Auto Generation Demo v0.3" in output, "Incorrect version number"
    
    # Check all menu items
    for i, item in enumerate(GenerableItem, 1):
        assert f"{i}. {item.value}" in output, f"Menu item missing: {item.value}"
    
    # Check exit option
    assert f"{len(GenerableItem) + 1}. Exit" in output, "Exit option missing"
    
    print("test_show_menu passed")


def create_mock_input(input_values):
    """Function to create a mock input function"""
    input_values = input_values.copy()
    def mock_input(_):
        return input_values.pop(0) if input_values else ''
    return mock_input


def test_get_user_selection():
    # Mock user inputs
    mock_inputs = ['invalid', '0', str(len(GenerableItem) + 2), '1', str(len(GenerableItem) + 1)]

    main_function.__globals__['input'] = create_mock_input(mock_inputs)

    assert get_user_selection() == '1', "Should return '1' for valid input"
    assert get_user_selection() == 'exit', "Should return 'exit' for exit option"
    
    print("test_get_user_selection passed")


def test_main():
    original_coordinator = main_function.__globals__['Coordinator']
    main_function.__globals__['Coordinator'] = MockCoordinator

    try:
        # Mock user inputs
        inputs = ['2', str(len(GenerableItem) + 1)]
        main_function.__globals__['input'] = lambda _: inputs.pop(0)
        
        main_function()
        
        # Check MockCoordinator
        mock_coordinator = MockCoordinator.last_instance
        assert mock_coordinator is not None, "MockCoordinator not instantiated"
        
        # Check MockGenerator
        mock_generator = mock_coordinator.generator
        assert mock_generator.generate_called, "Generator's generate method not called"
        assert mock_generator.pdf_selection == GenerableItem.REGULAR_AMALGAMATION_APPLICATION, "Incorrect PDF selection"
        
        print("test_main passed")
    finally:
        # Restore original Coordinator
        main_function.__globals__['Coordinator'] = original_coordinator


def run_tests(func_list, test_name):
    print(f"\nRunning {test_name}:")
    for func in func_list:
        func()
    print(f"\nAll {test_name} passed!")


def main():
    test_functions = [
        test_show_menu,
        test_get_user_selection,
        test_main,
    ]
    run_tests(test_functions, "Main Function Tests")


if __name__ == "__main__":
    main()
