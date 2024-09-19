from pdf_gen_api.models import Generator, JSONParser
from pdf_gen_api.resources import (
    GenerableItem,
    common_excluded_keys,
    pdf_configs
)

SCHEMAS_FOLDER = 'business_schemas'

def test_render_pdf_with_config(item: GenerableItem):
    print(f"Test rendering a PDF with configs - {item.value}")
    # Get the predefined config
    pdf_config = pdf_configs[item]
        
    # Parse the schema
    test_parser = JSONParser(SCHEMAS_FOLDER)
    parsed_schema = test_parser.parse(item.value, common_excluded_keys)
        
    # Create a Generator instance with the config and parsed schema
    test_generator = Generator(item.value, pdf_config, parsed_schema)
        
    # Generate the PDF
    test_generator.generate()
        

def main():
    
    test_items = [
        GenerableItem.REGULAR_AMALGAMATION_APPLICATION,
        GenerableItem.AGM_LOCATION_CHANGE
    ]
    
    for item in test_items:
        test_render_pdf_with_config(item)


if __name__ == '__main__':
    main()
