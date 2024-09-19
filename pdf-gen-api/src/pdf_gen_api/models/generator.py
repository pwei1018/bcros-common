""" 
    The Generator Class for PDF Gen
    It composes modules and content to one fillable PDF
"""

from pdf_gen_api.modules import (
    add_header, 
    add_certification_section, 
    add_top_notes, 
    add_footer, 
    add_effective_date_section,
    add_radios_group,
    add_dropdown_menu,
    add_textfield,
    add_single_checkbox,
    add_instruction_section
)


from pdf_gen_api.resources import (
    common_extra_modules, default_top_notes_content, default_render_order, default_footer_info, CommonConfigKeys,
    PdfModule, PdfFontSize, PdfFontStyle, PdfConfigOption,
    TITLE_X, MARGIN_BOTTOM, ONE_LINE_HEIGHT
)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import os
from enum import Enum

class Generator:
    # define _special_functions as a class variable
    _special_functions = {
        add_header: lambda args: (args[1],),
        add_top_notes: lambda args: (args[1], args[2]),
        add_certification_section: lambda args: (args[1], args[2], args[3]),
        add_effective_date_section: lambda args: (args[1], args[2]),
        add_radios_group: lambda args: (args[1], args[2], args[3]),
        add_dropdown_menu: lambda args: (args[1], args[2], args[3]),
        add_textfield: lambda args: (args[1], args[2], args[3], args[4], args[5]),
        add_single_checkbox: lambda args: (args[1], args[2], args[3], args[4]),
        add_instruction_section: lambda args: (args[1], args[2], args[3])
    }


    def __init__(self, pdf_selection:str, pdf_config:dict, props_dict:dict, fee:float=0.0) -> None:
        """PDF Generator Class

        Args:
            file_name (str): The PDF file name
            props_dict (dict): $ref resolved, flattened property dictionary
            extra_modules (set): List of extra modules needed, default=None
            fee (float): (Currently not using this)
            form_title (str): Human Edited Form Title, default=''
        """
        self.file_name = pdf_selection # must-have
        self.props_dict = self._get_props_data(pdf_selection, props_dict)
        self.fee = fee
        self.page_height = 792
        self.current_y = self.page_height - inch
        self.page_number = 1
        self.pdf_config = pdf_config
        self.extra_modules = pdf_config.get(PdfConfigOption.EXTRA_MODULE, common_extra_modules) # must-have
        self.form_title = pdf_config.get(PdfConfigOption.FORM_TITLE, pdf_selection) # must-have
        self.top_note_info = pdf_config.get(PdfConfigOption.TOP_NOTE_INFO, default_top_notes_content)
        self.footer_info = pdf_config.get(PdfConfigOption.FOOTER_INFO, default_footer_info)
        self.section_order = pdf_config.get(PdfConfigOption.SECTION_ORDER, default_render_order)
        self.component_configs = pdf_config.get(PdfConfigOption.COMPONENT_CONFIGS, None)
        self.rendered_content:set = {}
        self.instructions:dict = {} # {ref_code: instruction content} -- this is reserved for the instruction ticket
        self.jump_keys = {'allOf', 'if', 'then', 'items'} # directly jump into the keys without rendering
        self.default_rerender_times = 2
        self.pdf_canvas = None
        self.rendered_content_with_config = set()


    def generate(self) -> None:
        """Generate a fillable PDF with all modules and core content"""
        if self.props_dict == None:
            raise ValueError("Cannot get props data, please check the parsed schema or debug the _get_props_date method in the Generator")
        file_path = self._generate_file_path()
        
        self.pdf_canvas = canvas.Canvas(file_path, pagesize=letter)
        print(f'Generating {self.file_name} ......')

        if len(self.pdf_config) == 0:
            # no config is available, purely rendering content using the parsed schema
            self._generate_by_parsed_schema()
        else:
            # rendering with configs
            self._generate_with_configs()

        # add the instruction module
        self._add_instruction()

        self._finish_page()
        self.pdf_canvas.save()
        print(f'PDF Generated:\n{file_path}')


    ######################################################################
    ###### Helpers for the constructor and the main generate method ######
    ######################################################################
    def _generate_file_path(self) -> str:
        """Generate file path for a new pdf file"""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        output_dir = os.path.join(project_root, "demo_output")
        os.makedirs(output_dir, exist_ok=True)
        start_path = os.path.join(output_dir, self.file_name)
        file_path = f"{start_path}.pdf"
        exist_count = 1
        while os.path.exists(file_path):
            file_path = f"{start_path}_{exist_count}.pdf"
            exist_count += 1
        return file_path


    def _get_props_data(self, pdf_selection_name:str, props_dict:dict) -> dict:
        """From the outer most layer, get the main data using the form name key"""
        try:
            camel_case_key = ''.join(word.capitalize() for word in pdf_selection_name.split('_'))
            camel_case_key = camel_case_key[0].lower() + camel_case_key[1:]
            return props_dict[camel_case_key]
        except Exception as e:
            print(f"Error Getting Props Data, {e}")
            return None


    def _generate_by_parsed_schema(self):
        """Rendering content only use parsed schema file"""
        # Rendering the modules
        for item in self.section_order:
            if isinstance(item, PdfModule):
                self._add_module(item)
        
        # Render everything else (except modules with no configs)
        self._render_schema_content_no_configs(self.props_dict)
    

    def _render_schema_content_no_configs(self, data, current_path='') -> None:
        """Recursively find out and render the content in the props_dict"""
        if isinstance(data, dict):
            for key, value in data.items() :
                if key in self.jump_keys:
                    self._render_schema_content_no_configs(value, current_path)
                else:
                    new_path = f"{current_path}.{key}" if current_path else key
                    if isinstance(value, dict):
                        # render the item name, except boolean items as they will have the title on the right side of the checkbox
                        if value.get('type') != 'boolean':
                            self._add_text(self._convert_to_title_case(key))
                        # render enum as single selections or dropdowns
                        if value.get('enum'):
                            self._create_from_enum_obj(value['enum'])
                        # add instruction content to the dict
                        if value.get('examples') or value.get('description'):
                            current_key_dict = self.instructions.get(key, {
                                'examples': value.get('examples', []),
                                'description': value.get('description', ''),
                            })
                            self.instructions[key] = current_key_dict
                        # render content by types
                        if value.get('type') : # and value.get('type') != 'object'
                            current_type_value = value['type']
                            # render a text field
                            if ((((isinstance(current_type_value, list)) and \
                                (('string' in current_type_value) or ('number' in current_type_value)))) \
                            or (current_type_value in ['string', 'number', 'integer'])) and (not value.get('enum')):
                                self._add_textfield()
                            # render a multiple times
                            if current_type_value == 'array':
                                ######### enable this for loop after fix individual component issues, the multiple-time render may have some issues ###########
                                # for i in range(self.default_rerender_times): 
                                self._render_schema_content_no_configs(value, new_path)
                            # render a checkbox
                            if current_type_value == 'boolean':
                                self._add_single_checkbox(self._convert_to_title_case(key))
                        # dig deeper
                        self._render_schema_content_no_configs(value, new_path)
                    elif isinstance(value, list):
                        for item in value:
                            self._render_schema_content_no_configs(value, new_path)
        elif isinstance(data, list):
            for item in data:
                self._render_schema_content_no_configs(item, current_path)
                                

    def _generate_with_configs(self):
        """Generate PDF content using both parsed schema and pdf config"""
        self.props_dict = self._process_schema(self.props_dict)

        # Collect all instructions
        self._collect_instructions(self.props_dict)

        # Render content based on section_order
        for item in self.section_order:
            if isinstance(item, PdfModule):
                self._add_module(item)
            elif isinstance(item, str):
                self._render_component_with_config(item)

        # Then, render any remaining content from the props_dict that wasn't covered by the section order
        for key in self.props_dict:
            if key not in self.rendered_content_with_config:
                self._render_component_with_config(key)


    def _process_schema(self, schema):
        """
        Process allOf structure and update props_dict without rendering.

        Args:
            schema: The schema to process

        Returns:
            The processed schema
        """
        if isinstance(schema, dict):
            if 'allOf' in schema:
                merged_schema = {}
                for item in schema['allOf']:
                    if isinstance(item, dict):
                        if 'then' in item:
                            # handle then structure
                            merged_schema.update(self._process_schema(item['then']))
                        else:
                            merged_schema.update(self._process_schema(item))
                schema.pop('allOf')
                schema.update(merged_schema)
            return {k: self._process_schema(v) for k, v in schema.items() if k not in ['if', 'then']}
        elif isinstance(schema, list):
            return [self._process_schema(item) for item in schema]
        else:
            return schema

    def _render_component_with_config(self, key, parent_path=''):
        """
        Render a component using its configuration.

        Args:
            key: The key of the component to render
            parent_path (str): The parent path of the component
        """
        current_path = f"{parent_path}.{key}" if parent_path else key

        # Check if we're trying to render a nested array element
        if '[' in current_path and ']' in current_path:
            return  # Skip rendering nested array elements

        if current_path in self.rendered_content_with_config:
            return

        value = self._get_nested_value(self.props_dict, current_path)
        config = self._get_nested_value(self.component_configs, current_path, {})

        # Handle components rendering
        self._process_component_rendering(current_path, value, config)

        self.rendered_content_with_config.add(current_path)


    def find_config(self, config, config_keys):
        """
        Find configuration based on provided keys.

        Args:
            config: The configuration to search in
            config_keys: The keys to search for

        Returns:
            The found configuration or None
        """
        for key in config_keys:
            if isinstance(key, Enum):
                found_config = next((config[k] for k in config if isinstance(k, Enum) and k.value == key.value), None)

                if found_config:
                    return found_config
            else:
                found_config = config.get(key)
                if found_config:
                    return found_config
        return None


    def _process_component_rendering(self, component_path, value, config):
        """
        Process and render a component based on its value and configuration.

        Args:
            component_path (str): The path of the component
            value: The value of the component
            config: The configuration of the component
        """
        component_config = self.find_config(config, [CommonConfigKeys.SECTION, CommonConfigKeys.ITEM])
        label = component_config.get('label') if component_config else (value.get('title') if isinstance(value, dict) else None)
        styles = component_config.get('styles', {}) if component_config else {}

        if label:
            self._add_text(label, styles)

        if isinstance(value, dict):
            value_type = value.get('type')
            if isinstance(value_type, list):
                value_type = next((t for t in value_type if t != 'null'), value_type[0])

            if value_type == 'object':
                for key, sub_value in value.items():
                    if key not in ['type', 'title']:
                        sub_config = config.get(key, {})
                        self._process_nested_component(f"{component_path}.{key}", sub_value, sub_config)
            elif value_type == 'string':
                if 'enum' in value:
                    self._create_from_enum_obj(value['enum'], config)
                else:
                    self._add_textfield(styles)
            elif value_type == 'array':
                self._render_array_component(component_path, value, config)
            elif 'enum' in value:
                self._create_from_enum_obj(value['enum'], config)
            elif value_type == 'boolean':
                self._add_single_checkbox(label, styles)
            else:
                for key, sub_value in value.items():
                    sub_config = config.get(key, {})
                    self._process_nested_component(f"{component_path}.{key}", sub_value, sub_config)


    def _render_array_component(self, component_path, value, config):
        """
        Render an array component.

        Args:
            component_path (str): The path of the component
            value: The value of the array component
            config: The configuration of the array component
        """
        items = value.get('items', {})
        section_config = self.find_config(config, [CommonConfigKeys.SECTION, CommonConfigKeys.ITEM])
        item_config = self.find_config(config, [CommonConfigKeys.ITEM])
        reps = section_config.get('reps') if section_config else 1

        for i in range(reps):
            if item_config and 'label' in item_config:
                item_label = item_config['label']
                item_styles = item_config.get('styles', {})
                self._add_text(item_label, item_styles)

            if isinstance(items, dict):
                items_type = items.get('type')
                if items_type == 'string':
                    self._add_textfield(item_config.get('styles', {}))
                elif items_type == 'object':
                    for key, sub_value in items.items():
                        if key not in ['type', 'title']:
                            sub_config = config.get(key, {})
                            if isinstance(sub_value, dict):
                                if 'enum' in sub_value:
                                    self._create_from_enum_obj(sub_value['enum'], sub_config)
                                elif sub_value.get('type') == 'array':
                                    self._render_array_component(f"{component_path}[{i}].{key}", sub_value, sub_config)
                                else:
                                    self._process_nested_component(f"{component_path}[{i}].{key}", sub_value, sub_config)
                            else:
                                self._process_nested_component(f"{component_path}[{i}].{key}", sub_value, sub_config)
                else:
                    # Handle other types of arrays
                    for key, sub_value in items.items():
                        sub_config = config.get(key, {})
                        if isinstance(sub_value, dict) and sub_value.get('type') == 'array':
                            self._render_array_component(f"{component_path}[{i}].{key}", sub_value, sub_config)
                        else:
                            self._process_nested_component(f"{component_path}[{i}].{key}", sub_value, sub_config)


    def _process_nested_component(self, component_path, value, config):
        """
        Process and render a nested component based on its value and configuration

        Args:
            component_path (str): The path of the component in the nested structure
            value: The value of the component
            config: The configuration for the component
        """
        component_config = self.find_config(config, [CommonConfigKeys.SECTION, CommonConfigKeys.ITEM])
        label = component_config.get('label') if component_config else config.get('label', component_path.split('.')[-1])
        styles = component_config.get('styles', {}) if component_config else config.get('styles', {})

        if label and label not in ['RESOLUTION DATE', 'SHARE CLASS']:
            self._add_text(label, styles)

        if isinstance(value, dict):
            value_type = value.get('type')
            if isinstance(value_type, list):
                value_type = next((t for t in value_type if t != 'null'), value_type[0])

            if value_type == 'object':
                for key, sub_value in value.items():
                    if key not in ['type', 'title']:
                        sub_config = config.get(key, {})
                        self._process_nested_component(f"{component_path}.{key}", sub_value, sub_config)
            elif value_type == 'array':
                self._render_array_component(component_path, value, config)
            elif value_type == 'string':
                if 'enum' in value:
                    self._create_from_enum_obj(value['enum'], config)
                else:
                    self._add_textfield(styles)
            elif value_type in ['number', 'integer']:
                self._add_textfield(styles)
            elif value_type == 'boolean':
                self._add_single_checkbox(label, styles)
            else:
                for key, sub_value in value.items():
                    sub_config = config.get(key, {})
                    self._process_nested_component(f"{component_path}.{key}", sub_value, sub_config)


    def _get_nested_value(self, data, path, default=None):
        """
        Retrieve a nested value

        Args:
            data: The data used to search in
            path (str): The path to the desired value
            default: The default value to return if the path is not found

        Returns:
            The value at the specified path, or the default value if not found
        """
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, list):
                try:
                    index = int(key.strip('[]'))
                    data = data[index] if 0 <= index < len(data) else default
                except ValueError:
                    return default
            else:
                return default
        return data


    def _collect_instructions(self, data, current_path=''):
        """
        Recursively collect instructions (examples and descriptions) from the data

        Args:
            data: The data to search for instructions
            current_path (str): The current path in the nested structure
        """
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{current_path}.{key}" if current_path else key
                if isinstance(value, dict) and ('examples' in value or 'description' in value):
                    simple_key = key.split('.')[-1]
                    self.instructions[simple_key] = {
                        'examples': value.get('examples', []),
                        'description': value.get('description', ''),
                    }
                self._collect_instructions(value, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._collect_instructions(item, f"{current_path}[{i}]")

    def _convert_to_title_case(self, key:str):
        result = key[0].upper()
        for char in key[1:]:
            if char.isupper():
                result += f" {char}"
            else:
                result += char
        # deal with Agm all upper case
        words = result.split(' ')
        for i in range(len(words)):
            if words[i] == 'Agm':
                words[i] = 'AGM'
            elif words[i] == 'Nr':
                words[i] = 'NR'
        result = ''.join(f"{word} " for word in words)
        return result[:-1]

        


    ######################################################################
    ############# Helpers for rendering different components #############
    ######################################################################
    def _add_module(self, module_name:PdfModule):
        """Add selected module"""
        if module_name == PdfModule.HEADER:
            self._add_header()
        elif module_name == PdfModule.TOP_NOTE:
            self._add_top_notes()
        elif module_name == PdfModule.CERTIFICATION:
            self._add_certification_section(self.pdf_config.get(PdfConfigOption.NUM_OF_CERTIFICATION, 1))
        elif module_name == PdfModule.EFFECTIVE_DATE:
            self._add_effective_date_section()


    def _add_header(self):
        """Add the header modules."""
        header_height = self._measure_content(add_header, self.pdf_canvas, self.form_title)
        self._check_page_break(header_height)
        self.current_y = add_header(self.pdf_canvas, self.form_title)


    def _add_top_notes(self):
        """Add top notes module"""
        notes_height = self._measure_content(add_top_notes, self.pdf_canvas, self.current_y, self.top_note_info, self.fee)
        self._check_page_break(notes_height)
        self.current_y = add_top_notes(self.pdf_canvas, self.current_y, self.top_note_info, self.fee)


    def _add_instruction(self):
        """Add the instruction module."""
        instruction_height = self._measure_content(add_instruction_section, self.pdf_canvas, self.current_y, self.instructions, self.file_name)
        self._check_page_break(instruction_height)
        self.current_y = add_instruction_section(self.pdf_canvas, self.current_y, self.instructions, self.file_name)


    def _add_textfield(self, config:dict={}) -> None:
        """Render a text field"""
        font_size = PdfFontSize.CONTENT
        font_style = PdfFontStyle.REGULAR
        length = 70
        if len(config) > 0:
            # reserved for rendering with configs
            print("Reserved Place")
        self.current_y -= 20
        self.current_y = add_textfield(self.pdf_canvas, self.current_y, font_style, font_size, length)  
        field_height = ONE_LINE_HEIGHT
        self._check_page_break(field_height)   


    def _add_text(self, title:str, config:dict={}) -> None:
        """Render a string"""
        font_size = PdfFontSize.CONTENT
        font_style = PdfFontStyle.REGULAR
        field_title = str(title)
        if len(config) > 0:
            font_size = config.get('font_size', font_size)
            font_style = config.get('font_style', font_style)

        self.pdf_canvas.setFont(font_style.value, font_size.value)
        self.current_y -= 15 # margin after text 
        self.pdf_canvas.drawString(TITLE_X, self.current_y, field_title)
        self.current_y -= 20 # margin after text 
        text_height = ONE_LINE_HEIGHT
        self._check_page_break(text_height) 


    def _add_single_checkbox(self, title:str, config:dict={}) -> None:
        """Render a checkbox + label to the pdf"""
        font_size = PdfFontSize.CONTENT
        font_style = PdfFontStyle.REGULAR
        field_title = title
        if len(config) > 0:
            # reserved for rendering with configs
            print("Reserved Place")
        self.current_y = add_single_checkbox(self.pdf_canvas, self.current_y, field_title, font_style, font_size)
        field_height = ONE_LINE_HEIGHT
        self._check_page_break(field_height)

    
    def _create_from_enum_obj(self, content_list:list, config:dict={}) -> int:
        """Add a radios group(len(enum) < 5) otherwise, dropdown component depending on the length of enum"""
        font_size = PdfFontSize.CONTENT
        font_style = PdfFontStyle.REGULAR
        if len(config) > 0:
            # reserved for rendering with configs
            print("Reserved Place")

        if len(content_list) < 5 and len(content_list) > 1:
            self.current_y = add_radios_group(self.pdf_canvas, self.current_y, content_list, font_style, font_size)
            component_height = (ONE_LINE_HEIGHT + 10) * len(content_list)
            self._check_page_break(component_height)
        else:
            if content_list[0] != ' ':
                content_list.insert(0, ' ')
            self.current_y = add_dropdown_menu(self.pdf_canvas, self.current_y, content_list, font_style, font_size)
            dropdown_height = ONE_LINE_HEIGHT
            self._check_page_break(dropdown_height)


    def _add_certification_section(self, num_of_items:int):
        """Add the certification modules."""
        # Calculate the total height needed for the certification section
        cert_config = self.pdf_config.get(PdfConfigOption.CERTIFICATION_INFO, {})
        cert_height = self._measure_content(add_certification_section, self.pdf_canvas, self.current_y, num_of_items, cert_config)

        self._check_page_break(cert_height)

        # Add the certification section
        self.current_y = add_certification_section(self.pdf_canvas, self.current_y, num_of_items, cert_config)

        # Check if we need to start a new page after adding the certification section
        if self.current_y < MARGIN_BOTTOM:
            self._start_new_page()


    def _add_effective_date_section(self):
        """Add the effective date modules."""
        filing_name = self.form_title.lower().split()[0]
        date_section_height = ONE_LINE_HEIGHT * 6
        self._check_page_break(date_section_height)
        self.current_y = add_effective_date_section(self.pdf_canvas, self.current_y, filing_name)
        


    ######################################################################
    ################## Helpers for multi-page rendering ##################
    ######################################################################
    def _check_page_break(self, needed_height):
        """Check if a new page is needed and create one if necessary."""
        if self.current_y - needed_height < MARGIN_BOTTOM:
            self._finish_page()
            self._start_new_page()


    def _finish_page(self):
        """Finish the current page by adding footer and page number."""
        add_footer(self.pdf_canvas, self.footer_info, self.page_number)
        self.pdf_canvas.showPage()


    def _start_new_page(self):
        """Start a new page by incrementing page number and resetting current_y."""
        self.page_number += 1
        self.current_y = self.page_height - 60


    def _measure_field(self, field_value):
        """Measure the height of a field based on its length."""
        length = field_value['pdfProps']['styles']['length']
        lines = max(1, length // 400)
        return 20 + (20 * lines + 2)


    def _measure_content(self, content_function, *args):
        """Measure the height of content to be added to the PDF.
        Args:
            content_function: The function that adds content to the PDF
            *args: Arguments to be passed to the content_function
        Returns:
            float: The height of the content
        """
        dummy_canvas = canvas.Canvas(None)
        start_y = self.page_height - 10

        if content_function in self._special_functions:
            function_args = self._special_functions[content_function](args)
            end_y = content_function(dummy_canvas, *function_args)
        else:
            end_y = content_function(dummy_canvas, *args)

        return start_y - end_y + 20

