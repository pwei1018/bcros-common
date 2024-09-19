"""
    The PDF Parser Class for PDF Gen
    It parses JSON Schemas from the original business schemas for the Generator to work
"""
import json
import os
import logging



class JSONParser:
    def __init__(self, schemas_folder_path: str) -> None:
        """The constructor for JSONParser class

        Args:
            schemas_folder_path (str): the directory where all JSON schemas are located
        """
        self.registry = {} # key: schema id, value: file_path
        self.local_path_lib = {} # store local property path with their $id {local_path : file_id}
        self.schemas_folder = schemas_folder_path
        # Set error logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._load_schemas()
        self.excluded_keys = [] # the items need to be wiped out for final output


    
    def _load_schemas(self):
        """Load all schemas to a dict for future referencing
        """
        def get_schema_id(file_path:str):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    return data['$id']
                except KeyError as e:
                    print(f"Error getting $id from the schema: {file_path}\nError: {e}")
            
        def analyze_local_ref(file_path:str, schema_id:str):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    find_refs(data, schema_id)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {file_path}")
                   
        def find_refs(obj, schema_id:str):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == '$ref' and isinstance(value, str) and value.startswith('#'):
                        self.local_path_lib[value] = schema_id
                    else:
                        find_refs(value, schema_id)
            elif isinstance(obj, list):
                for item in obj:
                    find_refs(item, schema_id)

        
        print("Loading Schemas ")
        schema_list = os.listdir(self.schemas_folder)
        for i in range(len(schema_list)):
            file_name = schema_list[i]
            file_path = os.path.join(self.schemas_folder, file_name)
            if os.path.isfile(file_path):
                schema_id = get_schema_id(file_path)
                self.registry[schema_id] = file_path
                analyze_local_ref(file_path, schema_id)

        print(f"All Schemas loaded, total: {len(schema_list)}")
        print("=" * 120)



    def _get_json(self, file_path:str):
        """Load a JSON Schema and return it as a Python Dictionary
        Args:
            file_path (str): path to the file
        Returns:
            dict: represents the json file
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Schema file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in schema file: {file_path}")
            return None
        


    def _get_schema_id_path(self, ref_link:str):
        """ Parse $ref link 
        Args:
            ref_link(str): content in the $ref
        Returns:
            Tuple: (schema_id, property_address)
        """     
        ref_data = ref_link.split("#")
        if len(ref_data) == 1:   # the $ref is a foreign schema id, no property address
            return ref_link, ''
        elif len(ref_data) == 2:  # the $ref is a local property address
            return ref_data[0], ref_data[1]
        else:
            self.logger.error(f"Abnormal Schema $ref: {ref_link}")
            return None
    
    

    def _resolve_references(self, schema):
        """Resolve all $ref in related JSON files
        Args:
            schema (dict): schema dict
        Returns:
            dict: resolved schema
        """
        print("Resolving references ......")
        resolving_refs = set()

        def resolve_single_ref(ref_link, current_schema):
            """Internal method for resolving references
            Args:
                ref_link (str): content in $ref
                current_schema (dict): the schema is currently parsing
            Returns:
                dict: resolved single $ref
            """
            try:
                schema_id_path = self._get_schema_id_path(ref_link)
                if schema_id_path is None:
                    self.logger.warning(f"Invalid $ref format: {ref_link}")
                    return {"$ref": ref_link, "error": "Invalid $ref format"}
                
                schema_id, property_path = schema_id_path

                if schema_id:
                    schema_file_path = self.registry.get(schema_id)
                    if schema_file_path is None:
                        self.logger.warning(f"Schema ID not found in registry: {schema_id}")
                        return {"$ref": ref_link, "error": "Schema ID not found"}
                    schema = self._get_json(schema_file_path)
                else:
                    schema_path_for_local_ref_id = self.local_path_lib.get(f"#{property_path}")
                    schema_path_for_local_ref = self.registry.get(schema_path_for_local_ref_id)
                    schema = self._get_json(schema_path_for_local_ref)
                
                if property_path:
                    schema = get_local_property(schema, property_path)
                
                return schema
            except Exception as e:
                self.logger.warning(f'Reference not resolved: {ref_link}. Error: {str(e)}')
                return {"$ref": ref_link, "error": str(e)}

        def get_local_property(schema, property_path:str):
            """Internal method for getting a local property
            Args:
                schema (dict): the schema is currently parsing
                property_path (str): path to the item in the given schema
            Returns:
                Any: the property
            """
            keys = property_path.split("/") # prop_path: '/xxx/xxx' --> after spliting ['', 'xxx', 'xxx']
            keys = keys[1:len(keys)] 
            result = schema
            for key in keys:
                if key:
                    if isinstance(result, dict):
                        result = result.get(key,{})
                else:
                    self.logger.warning(f"Unable to traverse path {property_path} in {schema}")
            return result

        def resolve_refs(node, current_schema):
            """Main recursive method for resolving references, including nested ones
            Args:
                node (dict | list): one node represents one item in a dictionary
                current_schema (dict): the schema is currently parsing

            Returns:
                _type_: _description_
            """
            if isinstance(node, dict):
                if '$ref' in node:
                    ref_link = node['$ref']
                    if ref_link in resolving_refs:
                        self.logger.warning(f"Circular reference detected: {ref_link}")
                    else:
                        resolving_refs.add(ref_link)
                    try:
                        resolved = resolve_single_ref(ref_link, current_schema) 
                        # Continue resolving in case the resolved object contains more refs
                        return resolve_refs(resolved, resolved)
                    finally:
                        resolving_refs.remove(ref_link)
                return {key: resolve_refs(value, current_schema) for key, value in node.items()}
            elif isinstance(node, list):
                    return [resolve_refs(item, current_schema) for item in node]
            return node
        
        return resolve_refs(schema, schema)
    


    def _flatten_schema(self, schema):
        """Flattening a schema
        Args:
            schema (dict): the schema need to flatten
        Returns:
            dict: flattened schema
        """
        print("Flattening schema ......")

        def flatten(node):
            if isinstance(node, dict):
                result = {}
                for key, value in node.items():
                    if key == 'properties':
                        # Move properties up one level
                        for prop_key, prop_value in value.items():
                            result[prop_key] = flatten(prop_value)
                    else:
                        result[key] = flatten(value)
                return result
            elif isinstance(node, list):
                return [flatten(item) for item in node]
            else:
                return node

        return flatten(schema)

        # flatten(schema)
        # return unflatten_json(flat_schema)         
        # #return flat_schema
    


    def _clean_schema(self, schema):
        """
        Remove elements with specified keys from a dictionary or list of dictionaries.
        
        Args:
            data (dict or list): The input data structure
            keys_to_remove (list): List of keys to remove
        
        Returns:
            dict or list: The data structure with specified keys removed
        """
        if isinstance(schema, dict):
            return {k: self._clean_schema(v) for k, v in schema.items() 
                    if k not in self.excluded_keys}
        elif isinstance(schema, list):
            return [self._clean_schema(item) for item in schema 
                    if not (isinstance(item, dict) and all(k in self.excluded_keys for k in item.keys()))]
        else:
            return schema 
                
    

    def parse(self, main_schema_file_name:str, excluded_list:list):
        """The main method in the Parser Class

        Args:
            main_schema_file (str): the main schema for the PDF to be created
            excluded_list (list): the list of unnecessary items for this schema
        Returns:
            dict: $ref resolved, flattened, cleaned schema
        """
        file_path = f"{self.schemas_folder}/{main_schema_file_name}.json"
        self.excluded_keys = excluded_list
        main_schema_file = self._get_json(file_path)
        if main_schema_file is None or main_schema_file == {}:
            self.logger.error("Failed to load main schema file")
            return None
        
        
        resolved_schame = self._resolve_references(main_schema_file)
        flattened_schema = self._flatten_schema(resolved_schame)
        print("Cleaning up schema ......")
        cleaned_schema = self._clean_schema(flattened_schema)
        return cleaned_schema
