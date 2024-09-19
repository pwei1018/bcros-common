"""
    The Coordinator Class for PDF Gen
    It coordinates the work flow for generating a PDF file
"""

from pdf_gen_api.resources import GenerableItem, PdfConfigOption, pdf_configurations, common_excluded_keys
from .json_parser import JSONParser
from .generator import Generator
import os



class Coordinator:
    def __init__(self) -> None:
        self.schemas_folder = self._get_schema_root_folder_path()



    def _get_schema_root_folder_path(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        schema_root_dir = os.path.join(project_root, 'business_schemas')
        return schema_root_dir
    


    def run_app(self, pdf_selection: GenerableItem) -> None:
        """Run the Demo App

        Args:
            pdf_selection (GenerableItem): the PDF selection to generate
        """
        # Get selected config
        pdf_config = self._select_config(pdf_selection)

        # Create JSONParser
        json_parser = JSONParser(self.schemas_folder)

        # Get the main schema file name and excluded keys from pdf_config
        main_schema_file_name = pdf_selection.value
        excluded_keys = pdf_config.get(PdfConfigOption.EXCLUDED_KEYS, common_excluded_keys)

        # Parse JSON schema
        props_dict = json_parser.parse(main_schema_file_name, excluded_keys)

        if props_dict is None:
            print("Failed to parse JSON schema. Aborting PDF generation.")
            return

        # Calculate fee for now the fee is just 0, need fee calculation API or services
        fee = 0.0

        # Generate a fillable PDF
        generator = Generator(pdf_selection.value, pdf_config, props_dict, fee)
        generator.generate()

    
    def _select_config(self, pdf_name: GenerableItem) -> dict:
        """Return selected PDF generator configuration

        Args:
            pdf_name (str): pdf file name

        Raises:
            ValueError: when the given pdf name not in the generable item list

        Returns:
            (dict): dictionary for the config, or an error
        """
        try:
            return pdf_configurations[pdf_name]
        except KeyError:
            return {}
